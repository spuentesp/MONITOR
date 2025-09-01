# Narrative Engine — Consolidated Design (v1)

Purpose
- Capture how agents generate/assist narratives with continuity and provenance.
- Keep framework-agnostic now; adopt LangChain/LangGraph orchestration in Sprint 4.

---

## Components

- LLM interface
  - Contract: `core/generation/interfaces/llm.py`
  - Mock for tests: `core/generation/mock_llm.py`
- Agents (MVP)
  - Narrador (GM): `core/agents/narrador.py`
  - Personificador (Character): `core/agents/personificador.py`
  - Archivista (Librarian): `core/agents/archivista.py`
  - Base + Session: `core/agents/base.py`
- Engine facade
  - `core/engine/__init__.py` → `default_narrative_session(llm)`
- Graph access (read): `core/persistence/queries.py` (QueryService)
- Persistence (write): YAML-first via projector; Facts + RelationState deltas (planned tools)

---

## Orchestration

- Current (MVP): in-memory `Session` (single primary agent; conversation history)
- Planned (Sprint 4): LangChain/LangGraph
  - Proposed nodes: Director → Librarian → Steward → Narrator → Critic → Archivist → Persist
  - Tools:
    - query_tool: wraps `QueryService` (entities/scenes/facts/relations/axioms/systems)
    - rules_tool: dice/system helpers (from `systems/*.yaml`)
    - persist_tool: write Facts and RelationState changes (guarded by Steward)
    - notes_tool: write annotations/non-canonical notes
  - Modes:
    - Co‑pilot vs Auto‑pilot (user approval gates persistence in co‑pilot)
  - Guardrails: tone/rating checks; refusal if policy violated

---

## Prompts (guidelines)

- Narrador: short, evocative, scene‑focused; end with 1 guiding question
- Personificador: first‑person, concise reactions; maintain voice
- Archivista: bullet points (summary, threads, inconsistencies)
- Safety default: PG‑13; configurable per Story (planned)

---

## Continuity & Provenance

- Reads via QueryService:
  - `relation_state_history(a, b)`
  - `relations_effective_in_scene(scene_id)`
  - Effective system resolution for universe/story/scene/entity
  - Entities/stories/scenes/facts retrieval helpers
- Writes (planned):
  - Facts: `Fact(id, description, occurs_in, participants, when|time_span, derived_from)`
  - RelationState deltas: set/changed/ended per Scene
  - All writes produce an `ops/agent_runs.yaml` record with context and trace

---

## Persistence Policy

- Canonical writes go to YAML (validated by Steward)
- DBs are projections; avoid direct writes to Neo4j in prod paths
- Dev mode may write to DB for smoke tests; mark as non‑canonical

---

## API (planned minimal)

- POST `/ops/agent-runs`: register run metadata (idempotent by `run_id`)
- POST `/sessions`: create session (mode: co‑pilot|auto‑pilot, story_id, ruleset)
- POST `/sessions/{id}/step`: advance LangGraph one step (co‑pilot)

---

## Testing

- Unit
  - Agents produce text with MockLLM (`tests/test_agents_engine.py`)
  - QueryService shapes (`tests/test_queries_service.py`)
- Integration
  - Live Neo4j queries (`tests/test_queries_integration.py`)
  - Indexes existence (`tests/test_indexes_integration.py`)
- Acceptance (planned)
  - LangGraph e2e: plan → retrieve → validate → draft → critique → persist (dry‑run)

---

## Roadmap

- Sprint 2: continuity queries, indexes (done)
- Sprint 3: documents & notes pipeline
- Sprint 4: replace Session with LangGraph; add tools; log `ops/agent_runs.yaml`
- Sprint 5: branching integrated into agent flows
- Sprint 6: Langfuse traces, metrics, dashboards

---

## Contracts (summary)

- LLM.complete(system_prompt, messages[], temperature, max_tokens, extra?) → str
- Agent.act(messages[]) → str
- Session.user(text) → None; Session.step() → str; history: [Message]

---

## Open Questions

- Tool auth and rate control per ContextToken
- Story/Scene selection heuristics for Librarian retrieval
- Dice/system execution layer shape (pure function vs stateful service)
