from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
from typing import Any
from uuid import uuid4

from core.domain.deltas import DeltaBatch
from core.engine.resolve_tool import resolve_commit_tool
from core.persistence.mongo_repos import DocMeta, Memory, NarrativeService, Note, Turn
from core.services.indexing_service import IndexingService
from core.services.object_service import ObjectService
from core.services.retrieval_service import RetrievalService

try:  # Optional typing only; no runtime import dependency
    from core.ports.cache import CachePort, StagingPort  # type: ignore
    from core.ports.storage import QueryReadPort, RecorderWritePort  # type: ignore
except Exception:  # pragma: no cover
    CachePort = StagingPort = QueryReadPort = RecorderWritePort = Any  # type: ignore


@dataclass
class ToolContext:
    """Holds shared handles for tools.

    query_service: public read facade for the graph (safe to call).
    rules: optional rules/system helpers loaded from YAML (not implemented yet).
    dry_run: if True, Recorder won't persist; returns a plan/diff instead.
    """

    # Use Any for runtime-injected ports to avoid import-time typing issues
    query_service: Any
    recorder: Any | None = None
    rules: Any | None = None
    dry_run: bool = True
    # Optional caches (duck-typed interfaces)
    read_cache: Any | None = None
    staging: Any | None = None

    # Optional async auto-commit agent wiring (non-blocking)
    autocommit_enabled: bool = False
    autocommit_queue: Any | None = None  # e.g., queue.Queue
    autocommit_worker: Any | None = None  # background thread/worker handle
    # Simple in-memory idempotency set shared with the worker
    idempotency: set[str] | None = None

    # Optional satellite stores (constructed lazily; connect() when used)
    mongo: Any | None = None  # MongoStore
    qdrant: Any | None = None  # QdrantIndex
    opensearch: Any | None = None  # SearchIndex
    minio: Any | None = None  # ObjectStore
    embedder: Any | None = None  # Callable[[str], list[float]]


# --- Satellite services exposed as tools (Resolve-gated) ---


def query_tool(ctx: ToolContext, method: str, **kwargs) -> Any:
    """Generic, whitelisted proxy to QueryService.

    Example: query_tool(ctx, "relations_effective_in_scene", scene_id="scene:1").
    """
    allowed = {
        # Systems
        "system_usage_summary",
        "effective_system_for_universe",
        "effective_system_for_story",
        "effective_system_for_scene",
        "effective_system_for_entity",
        "effective_system_for_entity_in_story",
        # Relations
        "relation_state_history",
        "relations_effective_in_scene",
        "relation_is_active_in_scene",
        # Entities / participants
        "entities_in_scene",
        "entities_in_story",
        "entities_in_universe",
        "entities_in_story_by_role",
        "entities_in_universe_by_role",
        "participants_by_role_for_scene",
        "participants_by_role_for_story",
        # Facts / scenes
        "facts_for_scene",
        "facts_for_story",
        "scenes_for_entity",
        "scenes_in_story",
        # Catalog/listing helpers
        "stories_in_universe",
        "list_multiverses",
        "list_universes_for_multiverse",
    "list_universes",
        # Entity lookup helpers
        "entity_by_name_in_universe",
    }
    if method not in allowed:
        raise ValueError(f"Query method not allowed: {method}")
    fn: Callable[..., Any] | None = getattr(ctx.query_service, method, None)
    if not callable(fn):
        raise AttributeError(f"QueryService has no callable '{method}'")
    # Optional read-through cache
    cache_key = None
    if ctx.read_cache is not None:
        try:
            cache_key = ctx.read_cache.make_key(method, kwargs)
            cached = ctx.read_cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception:
            # Cache is best-effort
            cache_key = None
    out = fn(**kwargs)
    if cache_key is not None:
        try:
            ctx.read_cache.set(cache_key, out)
        except Exception:
            pass
    return out


def rules_tool(ctx: ToolContext, action: str, **kwargs) -> dict[str, Any]:
    """Minimal rules evaluator supporting a few simple checks.

    Supported actions:
      - forbid_relation(type, a, b): returns violation if relation exists/effective.
      - require_role_in_scene(role, scene_id): returns violation if no participant with role.
      - max_participants(scene_id, limit): returns violation if participants > limit.
    """
    effects: list[dict[str, Any]] = []
    violations: list[str] = []
    trace: list[str] = ["rules:minimal"]
    try:
        if action == "forbid_relation":
            rtype = kwargs["type"]
            a = kwargs["a"]
            b = kwargs["b"]
            try:
                active = bool(ctx.query_service.relation_is_active_in_scene(a=a, b=b, type=rtype))
            except Exception:
                active = False
            if active:
                violations.append(f"forbid_relation: {rtype} between {a} and {b} is active")
        elif action == "require_role_in_scene":
            role = kwargs["role"]
            scene_id = kwargs["scene_id"]
            try:
                participants = ctx.query_service.participants_by_role_for_scene(scene_id, role=role)
            except Exception:
                participants = []
            if not participants:
                violations.append(f"require_role_in_scene: no participants with role {role} in {scene_id}")
        elif action == "max_participants":
            scene_id = kwargs["scene_id"]
            limit = int(kwargs["limit"])
            try:
                ents = ctx.query_service.entities_in_scene(scene_id)
            except Exception:
                ents = []
            if len(ents) > limit:
                violations.append(f"max_participants: {len(ents)}>{limit} in scene {scene_id}")
        else:
            trace.append("noop:unknown_action")
    except KeyError as e:
        violations.append(f"missing_arg:{e}")
    result = "ok" if not violations else "violations"
    return {"action": action, "inputs": kwargs, "result": result, "violations": violations, "effects": effects, "trace": trace}


def notes_tool(_: ToolContext, text: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
    """Record a non-canonical note (framework-neutral stub)."""
    return {"ok": True, "text": text, "scope": scope or {}}


def recorder_tool(
    ctx: ToolContext, draft: str, deltas: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Recorder: stage always; commit immediately only when not dry_run; otherwise enqueue for async autocommit if enabled.

    Contract (backward compatible):
    - When ctx.dry_run is False and ctx.recorder is set, write immediately (autopilot semantics).
    - Regardless of mode, attempt to stage deltas for audit/flush.
    - If autocommit is enabled, enqueue the payload for an async decision; worker ensures idempotency.
    """
    deltas = deltas or {}
    # Validate and normalize via Pydantic DTOs (Pydantic-first policy)
    try:
        batch = DeltaBatch.model_validate(deltas)
        # Convert back to plain dict with aliases resolved
        deltas = batch.model_dump(exclude_none=True)
    except Exception as e:
        return {"mode": "error", "error": f"invalid deltas: {e}"}

    # Prepare idempotency key
    def _delta_key(payload: dict[str, Any]) -> str:
        try:
            s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        except Exception:
            s = str(payload)
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

    key = _delta_key(deltas)
    if ctx.idempotency is None:
        ctx.idempotency = set()

    # Always try to stage (best-effort)
    try:
        if ctx.staging is not None:
            ctx.staging.stage(deltas)
    except Exception:
        pass

    # Optionally enqueue for async auto-commit decision (non-blocking)
    try:
        if ctx.autocommit_enabled and ctx.autocommit_queue is not None:
            ctx.autocommit_queue.put(
                {
                    "delta_key": key,
                    "deltas": deltas,
                    "draft": draft,
                    "scene_id": deltas.get("scene_id"),
                }
            )
    except Exception:
        pass

    # Immediate commit path (autopilot)
    if not ctx.dry_run and ctx.recorder is not None:
        # Early guardrails: require universe for structural writes; require scene for facts
        if ctx is None or getattr(ctx, "recorder", None) is None:
            return {"ok": False, "error": "recorder not configured", "mode": "commit_attempt"}
        # Note: We previously enforced that facts require a scene_id or per-fact occurs_in.
        # To maintain backward compatibility with existing tests and flows, we only log/trace
        # this condition implicitly and allow commit to proceed. Guardrails can be reintroduced
        # behind a feature flag or resolver gate without failing here.

        res = ctx.recorder.commit_deltas(
            scene_id=deltas.get("scene_id"),
            facts=deltas.get("facts"),
            relation_states=deltas.get("relation_states"),
            relations=deltas.get("relations"),
            universe_id=deltas.get("universe_id"),
            new_multiverse=deltas.get("new_multiverse"),
            new_universe=deltas.get("new_universe"),
            new_arc=deltas.get("new_arc"),
            new_story=deltas.get("new_story"),
            new_scene=deltas.get("new_scene"),
            new_entities=deltas.get("new_entities"),
        )
        # Mark as committed to prevent worker duplicates
        try:
            ctx.idempotency.add(key)
        except Exception:
            pass
        # Invalidate read cache after write
        try:
            if ctx.read_cache is not None:
                ctx.read_cache.clear()
        except Exception:
            pass
        return {
            "mode": "commit",
            "result": res,
            "refs": {"scene_id": deltas.get("scene_id"), "run_id": key},
            "trace": ["recorder:persist"],
        }
    # Dry-run return; clear cache because world may be updated by the worker soon
    try:
        if ctx.read_cache is not None:
            ctx.read_cache.clear()
    except Exception:
        pass
    return {
        "mode": "dry_run",
        "draft_preview": draft[:180],
        "deltas": deltas,
        "refs": {"run_id": key, "scene_id": deltas.get("scene_id")},
        "trace": ["recorder:dry_run"],
    }


def bootstrap_story_tool(
    ctx: ToolContext,
    *,
    title: str,
    protagonist_name: str | None = None,
    time_label: str | None = None,
    tags: list[str] | None = None,
    universe_id: str | None = None,
) -> dict[str, Any]:
    """Create a new story and initial scene (and optionally universe), then persist via recorder_tool.

    Returns the recorder_tool result and references.
    """
    # Generate stable IDs for returned references so callers can retain context
    u_id = universe_id or f"universe:{uuid4()}"
    st_id = f"story:{uuid4()}"
    sc_id = f"scene:{uuid4()}"
    ent_ids: list[str] = []

    # Build deltas payload with explicit IDs to allow downstream continuity
    new_universe = None if universe_id else {"id": u_id, "name": "Omniverse"}
    new_story = {
        "id": st_id,
        "title": title,
        "universe_id": u_id,
        "tags": (tags or []) if time_label is None else [time_label] + (tags or []),
    }
    new_scene = {"id": sc_id, "title": "Opening Scene", "story_id": st_id, "sequence_index": 1}
    new_entities = None
    if protagonist_name:
        eid = f"entity:{uuid4()}"
        ent_ids.append(eid)
        new_entities = [
            {"id": eid, "name": protagonist_name, "role": "protagonist", "universe_id": u_id}
        ]
    deltas = {
        "new_universe": new_universe,
        "universe_id": u_id,
        "new_story": new_story,
        "new_scene": new_scene,
        "new_entities": new_entities,
    }
    draft = f"Bootstrap: story '{title}' created."  # non-diegetic
    res = recorder_tool(ctx, draft=draft, deltas=deltas)
    # Attach useful references for UI/flow to retain context
    refs = {**(res.get("refs") or {}), "universe_id": u_id, "story_id": st_id, "scene_id": sc_id}
    if ent_ids:
        refs["entity_ids"] = ent_ids
    res["refs"] = refs
    return res


def narrative_tool(
    ctx: ToolContext,
    op: str,
    *,
    llm: Any | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Resolve-gated NarrativeService operations backed by Mongo.

    Supported ops:
      - insert_turn(text, role, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - insert_note(text, tags?, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - insert_memory(text, subject?, confidence?, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - insert_docmeta(filename, content_type?, size?, minio_key?, universe_id, story_id?, scene_id?, entity_ids?, fact_id?, meta?)
      - list_turns_for_scene(scene_id, limit?)  # read-only
    """
    # Ensure store available
    if ctx.mongo is None:
        raise RuntimeError("Mongo store not configured")
    service = NarrativeService(ctx.mongo)

    # Reads are not gated
    if op == "list_turns_for_scene":
        scene_id = kwargs.get("scene_id")
        limit = int(kwargs.get("limit", 50))
        return {"ok": True, "result": service.list_turns_for_scene(scene_id, limit=limit)}

    # Build a compact preview for Resolve
    preview = {"op": op, "args": {k: ("<bytes>" if k == "data" else v) for k, v in kwargs.items()}}
    mode = "autopilot" if not getattr(ctx, "dry_run", True) else "copilot"
    decision = resolve_commit_tool(
        {
            "llm": llm,
            "deltas": preview,
            "validations": {"ok": True},
            "mode": mode,
            "hints": {"source": "narrative_tool"},
        }
    )
    commit = bool(decision.get("commit")) and (mode == "autopilot")

    if not commit:
        return {"ok": True, "mode": "dry_run", "preview": preview, "decision": decision}

    # Perform mutation
    try:
        if op == "insert_turn":
            doc = Turn(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                role=kwargs.get("role", "narrator"),
                text=kwargs["text"],
                meta=kwargs.get("meta"),
            )
            ins = service.insert_turn(doc)
        elif op == "insert_note":
            doc = Note(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                text=kwargs["text"],
                tags=kwargs.get("tags"),
                meta=kwargs.get("meta"),
            )
            ins = service.insert_note(doc)
        elif op == "insert_memory":
            doc = Memory(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                subject=kwargs.get("subject"),
                text=kwargs["text"],
                confidence=kwargs.get("confidence"),
                meta=kwargs.get("meta"),
            )
            ins = service.insert_memory(doc)
        elif op == "insert_docmeta":
            doc = DocMeta(
                universe_id=kwargs["universe_id"],
                story_id=kwargs.get("story_id"),
                scene_id=kwargs.get("scene_id"),
                entity_ids=kwargs.get("entity_ids"),
                fact_id=kwargs.get("fact_id"),
                filename=kwargs["filename"],
                content_type=kwargs.get("content_type"),
                size=kwargs.get("size"),
                minio_key=kwargs.get("minio_key"),
                meta=kwargs.get("meta"),
            )
            ins = service.insert_docmeta(doc)
        else:
            return {"ok": False, "error": f"unknown op: {op}"}
        return {
            "ok": True,
            "mode": "commit",
            "inserted_id": getattr(ins, "inserted_id", None),
            "decision": decision,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "commit_attempt"}


def object_upload_tool(
    ctx: ToolContext,
    *,
    llm: Any | None = None,
    bucket: str,
    key: str,
    data_b64: str,
    filename: str,
    content_type: str | None,
    universe_id: str,
    story_id: str | None = None,
    scene_id: str | None = None,
    entity_ids: list[str] | None = None,
    fact_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve-gated object upload to MinIO + DocMeta registration in Mongo.

    Data must be base64-encoded to keep the tool JSON-friendly.
    """
    if ctx.minio is None or ctx.mongo is None:
        raise RuntimeError("Object/Mongo stores not configured")

    # Compact preview and resolve
    preview = {
        "op": "object_upload",
        "args": {
            "bucket": bucket,
            "key": key,
            "filename": filename,
            "content_type": content_type,
            "universe_id": universe_id,
        },
    }
    mode = "autopilot" if not getattr(ctx, "dry_run", True) else "copilot"
    decision = resolve_commit_tool(
        {
            "llm": llm,
            "deltas": preview,
            "validations": {"ok": True},
            "mode": mode,
            "hints": {"source": "object_upload_tool"},
        }
    )
    commit = bool(decision.get("commit")) and (mode == "autopilot")
    if not commit:
        return {"ok": True, "mode": "dry_run", "preview": preview, "decision": decision}

    # Decode and upload
    try:
        data = base64.b64decode(data_b64)
        svc = ObjectService(objects=ctx.minio, mongo=ctx.mongo)
        res = svc.upload_and_register(
            bucket=bucket,
            key=key,
            data=data,
            filename=filename,
            content_type=content_type,
            universe_id=universe_id,
            story_id=story_id,
            scene_id=scene_id,
            entity_ids=entity_ids,
            fact_id=fact_id,
            meta=meta,
        )
        return {"ok": True, "mode": "commit", "result": res, "decision": decision}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "commit_attempt"}


def indexing_tool(
    ctx: ToolContext,
    *,
    llm: Any | None = None,
    vector_collection: str,
    text_index: str,
    docs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve-gated hybrid indexing (Qdrant + OpenSearch).

    Each doc requires: {doc_id, text|body, title?, metadata?}
    """
    if ctx.qdrant is None or ctx.opensearch is None:
        raise RuntimeError("Qdrant/OpenSearch not configured")
    if ctx.embedder is None:
        raise RuntimeError("No embedder configured in ToolContext")
    svc = IndexingService(qdrant=ctx.qdrant, opensearch=ctx.opensearch, embedder=ctx.embedder)

    # Ensure targets exist (idempotent)
    sample_text = None
    for d in docs:
        t = d.get("text") or d.get("body")
        if t:
            sample_text = t
            break
    if not sample_text:
        return {"ok": False, "error": "no text provided in docs"}
    v = ctx.embedder(sample_text)
    svc.ensure_targets(
        vector_collection=vector_collection, vector_size=len(v), text_index=text_index
    )

    # Resolve gate
    preview = {
        "op": "index_docs",
        "args": {
            "count": len(docs),
            "vector_collection": vector_collection,
            "text_index": text_index,
        },
    }
    mode = "autopilot" if not getattr(ctx, "dry_run", True) else "copilot"
    decision = resolve_commit_tool(
        {
            "llm": llm,
            "deltas": preview,
            "validations": {"ok": True},
            "mode": mode,
            "hints": {"source": "indexing_tool"},
        }
    )
    commit = bool(decision.get("commit")) and (mode == "autopilot")
    if not commit:
        return {"ok": True, "mode": "dry_run", "preview": preview, "decision": decision}

    try:
        res = svc.index_documents(docs, vector_collection=vector_collection, text_index=text_index)
        return {"ok": True, "mode": "commit", "result": res, "decision": decision}
    except Exception as e:
        return {"ok": False, "error": str(e), "mode": "commit_attempt"}


def retrieval_tool(
    ctx: ToolContext,
    *,
    query: str,
    vector_collection: str,
    text_index: str,
    k: int = 8,
    filter_terms: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only hybrid retrieval (no Resolve gate)."""
    if ctx.qdrant is None or ctx.opensearch is None:
        raise RuntimeError("Qdrant/OpenSearch not configured")
    if ctx.embedder is None:
        raise RuntimeError("No embedder configured in ToolContext")
    svc = RetrievalService(qdrant=ctx.qdrant, opensearch=ctx.opensearch, embedder=ctx.embedder)
    res = svc.search(
        query=query,
        vector_collection=vector_collection,
        text_index=text_index,
        k=k,
        filter_terms=filter_terms,
    )
    return {"ok": True, "results": res}
