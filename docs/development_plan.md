# Development Plan — Pydantic‑First, LangGraph‑Driven (Sep 2025)

This plan operationalizes the pivot to Pydantic‑first models with LangGraph extraction/save. YAML remains for prompts/config/fixtures and optional exports.

## Principles
- Pydantic is the source of truth for runtime models (entities, relations, facts, deltas, branches).
- LangGraph nodes do extract → validate → save. Recorder persists to the graph spine.
- Steward validations + service invariants enforce safety before commits.
- Copilot stages; Autopilot commits; resolve gate enables human review.

## Phase 1 — Structured extraction + Save in LangGraph
- Tasks
  - Define JSONSchema/tool schemas for core models needed in monitor flows.
  - Ensure monitor/narration nodes populate Pydantic models and call recorder_tool.
  - Add minimal DTOs for API I/O where missing.
- Acceptance
  - E2E: a monitor command creates a Scene + Fact via LangGraph, verified by a graph read.
  - Unit tests for extraction validators (happy + missing IDs).

## Phase 2 — Pydantic fixtures replace YAML in tests (where practical)
- Tasks
  - Introduce factory/builders for entities/relations/facts (test utilities).
  - Migrate key tests from YAML projection to model factories; keep YAML loader for seeds.
- Acceptance
  - Tests still pass; no reliance on YAML for core write-path tests.

## Phase 3 — Rules Tool (dice/system execution)
- Tasks
  - Implement rules_tool with Pydantic inputs/outputs; bind to Systems in `systems/*`.
  - Map outcomes to Facts and/or Sheet updates; persist via Recorder.
- Acceptance
  - Unit tests for 2–3 mechanics; an integration test showing a resolution produces a Fact.

## Phase 4 — Branching + Typed Diffs
- Tasks
  - Define Delta/ChangeSet and Branch models; add diff/merge on Pydantic models.
  - Add API endpoints for branch create/promote with resolve gate.
- Acceptance
  - What‑if branch from a Scene; promote subset of changes back; diffs visible via API.

## Phase 5 — ACL + ContextToken enforcement
- Tasks
  - Middleware to require ContextToken; enforce writer ACL on Recorder/resolve paths.
  - Tests for allowed/denied writes and read scoping.
- Acceptance
  - Unauthorized mutations rejected; reads scoped by `universe_id`.

## Phase 6 — Minimal ingestion/search pipeline
- Tasks
  - Doc → chunk → embed → index (FTS + vectors) with existing clients.
  - Link search docs back to Facts/Entities via metadata.
- Acceptance
  - Search returns documents filtered by universe/story/scene; evidence used by Librarian.

## Phase 7 — Observability
- Tasks
  - Add Langfuse (or similar) spans to orchestrator and LangGraph nodes.
  - Basic dashboard: latency, cost, error rates, tokens.
- Acceptance
  - Traces visible per request; simple thresholds alert in logs.

## Nice‑to‑haves
- Notes/annotations endpoint (non‑canonical), export snapshots, prompt registry UI.

## References
- README, Architecture, Agents & LangGraph, Narrative Engine, Data spine & satellites.
