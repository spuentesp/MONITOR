# 🛰️ M.O.N.I.T.O.R.

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

M.O.N.I.T.O.R. is a personal system for **worldbuilding and assisted narration** across multiple universes. It combines a **graph-first ontology**, **hybrid search (FTS + vectors)**, and **multi-agent orchestration** to generate, validate, and archive stories with strong continuity and provenance.

> Goal: make it easy to create and explore canon and “what-if” branches, while keeping timelines, relations, and evidence consistent.

M.O.N.I.T.O.R. is a local-first, multi-agent system for worldbuilding and assisted narration across multiple universes. It uses a harmonized graph-based ontology (Omniverse → Multiverse → Universe → Story → Scene) to model narrative continuity, facts, entities, and relations. The system supports hybrid search (full-text + vector), document ingestion, and branching for "what-if" scenarios. Agents (Director, Librarian, Steward, Narrator, Critic, Character, Chat Host) orchestrate planning, evidence retrieval, validation, drafting, and critique. Canonical data is modeled with Pydantic (Pydantic-first). LangGraph nodes extract structured outputs into Pydantic models and persist via Recorder/Projector to the graph. YAML is used only for light configuration, prompts, and developer fixtures. The architecture is modular, with FastAPI backend, Streamlit frontend, and Dockerized services (Neo4j/Memgraph, Meilisearch, Qdrant/Weaviate, MinIO, Redis, Langfuse, ClickHouse).

---

## 🔭 Objectives

1. **Model multiverses coherently**: Omniverse → Multiverse → Universe → Story → Scene.
2. **Assist storytelling**: agents plan beats, retrieve evidence, maintain continuity, and draft text.
3. **Ensure continuity**: temporal graph + validations (axioms, archetype coverage, relation lifecycles).
4. **Enable “what-if” safely**: branch from scenes, isolate changes, promote back to canon with diffs.
5. **Run locally**: lightweight Streamlit UI, Dockerized services, minimal ops burden.

See also: `docs/development_plan.md` for the current phased roadmap.

---

---

## 🧱 Core Concepts (Ontology)

* **Omniverse**: The application platform (agents, engine, data, UI).
* **Multiverse**: A family of universes sharing canonical axioms and (optionally) a default rule system.
* **Universe**: Concrete worldline; holds Entities, Relations, Stories, Scenes, Facts; inherits/overrides axioms.
* **Story**: Narrative thread within a Universe; orders Scenes (narrative/chronological/mixed).
* **Scene**: Atomic narrative unit with world time and optional session time, participants, and location.
* **Axiom**: Declarative rule/tendency governing universes; inherited/overridden.
* **Archetype**: Reusable blueprint for entities; constrains kind/tags/traits.
* **Entity**: Character/place/object/organization/concept in a Universe; may instantiate an Archetype.
* **Fact**: First-class, time-stamped event/assertion with participants and provenance (occurs-in Scene).
* **Relation**: Inter-entity link (timeless, interval, or versioned with per-scene change logs).
* **ContextToken**: Selects omniverse/multiverse/universe and time-ref; scopes reads/writes and agent runs.

> Full ontology details live in the canvas **“Ontology Model — Updated With Facts (v2)”**.

---

## 🗃️ Storage Mode: Pydantic‑first → Polyglot projections

**Canonical models are Pydantic.** LangGraph nodes extract structured outputs into Pydantic DTOs and persist via Recorder/Projector to the graph spine (Neo4j) and satellites. YAML is used for prompts/configuration and developer fixtures; exports to YAML are optional for human review.

**Where YAML is used (non‑canonical):**

* `config/agents.yaml` prompts and small settings
* Test/seed fixtures under `scaffolds/` or `stories/`
* Optional human‑readable exports (snapshotting)

**Projection services (read‑optimized):**

* **Neo4j/Memgraph** (Graph): universes, entities, relations, stories/scenes, **Facts**, axioms/archetypes, branches.
* **Meilisearch** (FTS): documents & notes with scoped metadata (universe/story/scene/type).
* **Qdrant/Weaviate** (Vectors): embeddings for semantic retrieval; filtered by universe/story/scene.
* **MinIO (S3):** PDFs/HTML/MD + derivatives (OCR text) referenced from YAML via URIs.
* **Redis:** cache, task queues, rate control.
* **Langfuse:** traces/metrics for AgentOps.

**Write policy**

* Runtime writes: extract → validate (Pydantic + Steward) → persist via Recorder/Projector.
* Copilot stages deltas; Autopilot commits. Flush at scene boundaries or via resolve gate.
* YAML stays out of the hot path; keep it for config/fixtures/exports.

---

## 🧠 Agent Roles

Orchestration stack: **LangGraph** (default). Optional LangChain tools can be enabled.

* **Director**: Plans narrative beats given constraints (tone, tags, rating).
* **Librarian**: Hybrid retrieval across Meilisearch (FTS) + Qdrant/Weaviate (vectors); returns citations.
* **Steward**: Validates continuity (axioms, archetype coverage, temporal overlaps, relation lifecycles).
* **Narrator**: Drafts narrative text (co-pilot and auto-pilot modes).
* **Critic**: Scores clarity, tone, coherence; suggests revisions.
* **Character** (optional): Chats as NPCs; scene-level roleplay.
* **Chat Host**: UI guardrails, ContextToken enforcement.

---

## 🏗️ Architecture (Polyglot, Local-first)

**Frontend**

* **Streamlit**: context selector, narration console, evidence viewer, graph/timeline pane, branch manager, AgentOps dashboards.

**Backend**

* **FastAPI**: API gateway, ContextToken enforcement, agents orchestration endpoints.

**Data & Indexing**

* **Neo4j/Memgraph** (Graph DB): universes, entities, relations, scenes, **Facts**, axioms/archetypes, branches.
* **Meilisearch** (FTS): documents & notes with scoped metadata (universe/story/scene/type).
* **Qdrant or Weaviate** (Vector DB): embeddings for semantic retrieval; filters by universe/story/scene.
* **MinIO (S3)**: PDFs/HTML/MD + derivatives (e.g., OCR text).
* **Redis**: cache, task queues, rate-control.
* **Langfuse**: traces, metrics, evaluation hooks (latency, token usage, coherence proxies).
* **Apache Tika** (ingestion): text extraction → chunking → embedding → FTS/vector indexing.

**Data & Indexing Stack**

* **Neo4j/Memgraph**: Graph DB for universes, entities, relations, scenes, Facts, axioms/archetypes, branches.
* **Meilisearch**: Full-text search for documents & notes with scoped metadata.
* **Qdrant/Weaviate**: Vector DB for semantic retrieval; filters by universe/story/scene.
* **MinIO (S3)**: Storage for PDFs/HTML/MD + derivatives (OCR text).
* **Redis**: Cache, task queues, rate control.
* **Langfuse**: Traces, metrics, evaluation hooks.
* **ClickHouse**: Analytics/traces (used for AgentOps dashboard).
* **Apache Tika**: Text extraction for ingestion pipeline.

**Models (pluggable)**

* **LLMs**: any OpenAI-compatible or local model (quality↔cost configurable).
* **Embeddings**: instruct/ctx-length-friendly models for robust RAG (local or API).
* **Safety/tone**: optional classifiers for rating (PG-13, Mature, +18) at Story scope.

---

## 🔁 High-Level Flow

1. **Context**: user selects omniverse/multiverse/universe (+ optional time-ref).
2. **Plan** (Director): produce beats within constraints (tone, rating, system of rules if attached).
3. **Retrieve** (Librarian): hybrid search FTS+vector; return **evidence + citations**.
4. **Validate** (Steward): axioms, archetypes, temporal/relational consistency; warnings if needed.
5. **Draft** (Narrator) → **Critique** (Critic) → optional **Revise**.
6. **Persist**: narrative, Facts, relation deltas; index to FTS & vectors with scoped metadata.
7. **Branching** (optional): branch **from a Scene**; isolate changes; compare **diffs**; promote to canon.

---

## 🧪 Primary Use Cases

* **GM campaign manager (DM workflow):** track sessions, scenes, PCs/NPCs, rules/stats lookups, dice logs, and session summaries. Persist updates as **Facts**, entity state changes, and relation deltas tied to Scenes; auto‑index notes for retrieval.
* **Solo / 1‑on‑1 runtime with dice systems:** run scene‑by‑scene narration using a selected YAML rule system (e.g., PbtA, D\&D 3.5, City of Mist). Manage character sheets/resources, perform rolls (success/partial/failure, contested checks, crits), and carry memory across Scenes/Stories.
* **Assisted narration:** co-pilot outlines beats and drafts scenes with evidence-backed details.
* **Continuity checks:** ensure events and relations don’t violate canon or timelines.
* **What-if exploration:** branch from key scenes, simulate consequences, compare and selectively promote.
* **Knowledge-backed storytelling:** import PDFs/notes, cite sources in output, link to graph entities and scenes.
* **NPC conversations** (optional): run scene-bound dialogue with memory tied to entities and Facts.

> Both GM and Solo modes rely on the **rules YAML** (stats/resources/roll mechanics) and produce auditable **Facts** and **RelationState** changes with Scene provenance.

---

## 🛠️ Components & Responsibilities

* **Narrative Engine**: YAML loaders (systems of rules), scene/story ordering policies, relation lifecycle helpers, fact/scene provenance guards.
* **Steward**: invariants (DAGs for NEXT\_\* chains, contiguous sequence indices, non-overlapping intervals), axiom coverage, archetype constraints, fact-backed transitions.
* **Search Indexer**: Tika extraction → chunking → embeddings → Meilisearch/Qdrant with (omniverse/multiverse/universe/story/scene/type) metadata.
* **AgentOps**: Langfuse traces per phase (plan/evidence/continuity/draft/critique/persist); Streamlit dashboard.
* **Branch Manager**: DERIVES\_FROM lineage, typed diffs (new Facts, relation changes, state edits).

---

## 🧰 Getting Started (local)

> Minimal outline — adapt to your environment.

1. **Prereqs**: Docker & Docker Compose, Python 3.11+.
2. **Clone repo** & copy example env: `.env.example → .env` (LLM keys optional).
3. **Start services**: `docker compose up -d` (Neo4j/Memgraph, Meilisearch, Qdrant/Weaviate, MinIO, Redis, Langfuse).
4. **Backend**: `uvicorn backend.main:app --reload` (FastAPI).
5. **Frontend**: `streamlit run frontend/Chat.py` (agents chat UI; copilot/autopilot toggle).
	- Or use the one-command runner: `./run-dev.sh up` (brings up Neo4j, API, and Streamlit)
6. **Open**: Streamlit UI → select context → try **co-pilot** narration.

> Ingestion: upload a PDF/MD/HTML **or edit YAML**; the pipeline extracts/loads, chunks, embeds, and indexes to FTS & vectors with proper scoping.

### LLM configuration

- Default backend: mock (no API keys required)
- To use OpenAI-compatible chat:
	- `export MONITOR_LLM_BACKEND=openai`
	- `export OPENAI_API_KEY=sk-...`
	- Optional: `export MONITOR_OPENAI_MODEL=gpt-4o-mini` and `export MONITOR_OPENAI_BASE_URL=...`


---

## API: Modes Router (narration vs monitor)

The FastAPI backend exposes a simple router to switch between diegetic narration and operational monitor actions:

- POST `/api/langgraph/modes/chat` — stateful chat with router; supports `mode` (copilot/autopilot) and ContextToken.
- GET `/api/langgraph/modes/help` — brief help with available monitor commands (lists, show transcript, end scene, etc.).

See `core/interfaces/langgraph_modes_api.py` and `docs/agents_and_langgraph.md` for details.

### API Quickstart

Use these minimal examples to try the router and a stateful chat quickly.

Prereqs:
- Backend running (FastAPI). If you use the provided app, it exposes `/api`.
- Context token header as required by the middleware (replace with your token).

Examples:

1) Get router help (monitor commands)

```bash
curl -s \
	-H "X-Context-Token: <your-context-token>" \
	http://localhost:8000/api/langgraph/modes/help | jq
```

2) Chat (router will decide narration vs monitor)

```bash
curl -s -X POST \
	-H "Content-Type: application/json" \
	-H "X-Context-Token: <your-context-token>" \
	-d '{
				"turns": [{"content": "Introduce a rival in the alley", "scene_id": "scene:1"}],
				"mode": "copilot",
				"persist_each": false
			}' \
	http://localhost:8000/chat | jq
```

3) Single step (LangGraph single-turn flow)

```bash
curl -s -X POST \
	-H "Content-Type: application/json" \
	-H "X-Context-Token: <your-context-token>" \
	-d '{
				"intent": "Introduce a rival in the alley",
				"scene_id": "scene:1",
				"mode": "copilot",
				"record_fact": false
			}' \
	http://localhost:8000/step | jq
```

Tips:
- Set `mode` to `autopilot` to commit immediately (writes bypass staging).
- In copilot, use `/api/langgraph/modes/chat` with a monitor command like "end scene" to flush staged writes.

### Web UI (Streamlit)

A lightweight chat UI is available for interactive use:

```bash
streamlit run frontend/Chat.py
```

Or start everything at once (DB + API + UI):

```bash
./run-dev.sh up
```

Then:
- Pick LLM backend (mock/OpenAI/Groq) and model (optional).
- Toggle `copilot` vs `autopilot` in the sidebar.
- Set a `scene_id` (optional) and type your intent; the app calls `run_once` behind the scenes.
- Use the persist checkbox to stage/commit Facts from drafts.

### Agents overview

Core LLM-backed agents used by the LangGraph flow:

- Director → Librarian → Steward → Narrator → Critic → Archivist → Recorder

See `docs/agents_and_langgraph.md` for prompts, flow diagrams, and policies.

---

## 🔒 Governance & Ops (lightweight, opt-in)

See **Design Extensions & Integration Addendum (EN)** for:

* Minimal **ACL** (universe meta YAML),
* **Annotations** (non-canonical notes),
* **Agent run** logs (framework-agnostic),
* **Search map** contract (FTS/vector),
* **Schema/taxonomy versioning** and migrations,
* **Workflow states**: draft/review/approved/locked.

---

## 🧭 Roadmap (Sprints Summary)

1. **Foundations**: containers, ContextToken, API stubs.
2. **Graph model**: entities, relations, scenes, **Facts**, temporal rules (Steward v1).
3. **Docs & notes**: ingestion → FTS + vectors; citations; note editor with backlinks.
4. **Multi-agent orchestration**: co-pilot/auto-pilot flows with guardrails.
5. **What-if branches**: isolation, diffs, promotion to canon.
6. **AgentOps**: Langfuse traces + Streamlit dashboards (latency, coherence, citations).

1. **Foundations**: containers, ContextToken, API stubs.
2. **Graph model**: entities, relations, scenes, Facts, temporal rules (Steward v1).
3. **Docs & notes**: ingestion → FTS + vectors; citations; note editor with backlinks.
4. **Multi-agent orchestration**: co-pilot/auto-pilot flows with guardrails.
5. **What-if branches**: isolation, diffs, promotion to canon (DERIVES_FROM, branch diffs).
6. **AgentOps**: Langfuse traces + Streamlit dashboards (latency, coherence, citations).

---

## 📄 License

**PolyForm Noncommercial 1.0.0** — free for personal and non-commercial use; commercial use requires a separate license.
(Include the full license text in `LICENSE`.)

---

## 🙌 Who is this for?

* **Worldbuilders / GMs** who want canonical, searchable universes and story assistance.
* **AI practitioners** exploring **state-of-the-art RAG + multi-agent** architectures with graph memory and provenance.
* **Writers** interested in consistent, evidence-backed narrative generation and safe “what-if” ideation.

---

## 📎 References (internal)

* **Ontology**: *Ontology Model — Updated With Facts (v2)*
* **Design addendum**: *M.O.N.I.T.O.R. — Design Extensions & Integration Addendum (EN)*
* **Narrative Engine**: `docs/narrative_engine.md` (consolidated design)

See the “System overview (how it works today)” section in `docs/narrative_engine.md` for the current implementation status, including RecorderService, ToolContext, caching/staging (in-memory and Redis), and the end-to-end flow.

> Tip: Start small. Create one Universe, one Story with a few Scenes, edit YAML or ingest two documents, and let the co-pilot draft a scene. Then add a what-if branch and compare diffs.

For a detailed explanation of agents, prompts, LangGraph/LangChain orchestration, and policies, see `docs/agents_and_langgraph.md`.

---

## Branch API quickstart

Endpoints are exposed under `/api/branches` (see `core/interfaces/branches_api.py`). Examples assume the backend is running and the required `X-Context-Token` header is set.

- Branch from a scene:
	- POST `/api/branches/branch-at-scene` with `{ "source_universe": "u:canon", "scene_id": "scene:42", "target_universe": "u:whatif" }`
- Clone a full universe or subset:
	- POST `/api/branches/clone` with filters like `stories`, `entities`, `facts_since`.
- Diff universes (counts):
	- GET `/api/branches/{source}/diff/{target}` → counts of stories/scenes/entities/facts.
- Typed diff (detailed lists + provenance counts):
	- GET `/api/branches/{source}/diff/{target}/typed` → per-type presence lists and `provenance_counts`.
- Promote changes into target:
	- POST `/api/branches/promote` with `{ "source": "u:whatif", "target": "u:canon", "strategy": "append_missing" }` to idempotently merge stories/scenes/entities/facts/sheets that exist in source but are missing in target.

Notes:
- `append_missing` is safe to re-run (MERGE semantics); `overwrite` will replace conflicting nodes/edges.
- Diffs help review before promotion; typed diff includes IDs for precise review.

## Optional Redis backend

Redis is used for cache/staging when available. Docker Compose includes a Redis service; ensure the client lib is installed (already listed in `requirements.txt`). To enable via env:

- `export MONITOR_USE_REDIS=true`
- Optional: `export MONITOR_REDIS_URL=redis://localhost:6379/0`

The system will fall back to in-memory staging if Redis is not configured.

## Minimal rules tool

The `rules` tool now supports a small, test-backed set of actions:

- `forbid_relation(type, a, b)` → returns violation if relation would be created.
- `require_role_in_scene(role, scene_id)` → checks scene participants/roles.
- `max_participants(scene_id, limit)` → enforces a cap.

These are invoked by agents internally; you can extend them in `core/engine/tools.py`. Steward integration is planned to run selected checks before persistence.
