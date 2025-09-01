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
  - Narrator (GM): `core/agents/narrator.py`
  - Character (Character): `core/agents/character.py`
  - Archivist (Librarian): `core/agents/archivist.py`
  - Base + Session: `core/agents/base.py`
- Engine facade
  - `core/engine/__init__.py` → `default_narrative_session(llm)`
- Graph access (read): `core/persistence/queries.py` (QueryService)
- Persistence (write): YAML-first via projector; Facts + RelationState deltas (planned tools)

---

## Orchestration

- Current (MVP): in-memory `Session` (single primary agent; conversation history)
- Planned (Sprint 4): LangChain/LangGraph
  - Proposed nodes: Director → Librarian → Steward → Narrator → Critic → Archivist → Recorder
  - Tools:
    - query_tool: wraps `QueryService` (entities/scenes/facts/relations/axioms/systems)
    - rules_tool: dice/system helpers (from `systems/*.yaml`)
    - persist_tool: write Facts and RelationState changes (guarded by Steward)
    - notes_tool: write annotations/non-canonical notes
  - Modes:
    - Co‑pilot vs Auto‑pilot (user approval gates persistence in co‑pilot)
  - Guardrails: tone/rating checks; refusal if policy violated
  - Integration: a minimal LangGraph flow (`core/engine/langgraph_flow.py`) mirrors the orchestrator; install `langgraph` to enable. Tests will skip if not installed.

---

## Narrative Engine — Functions (contracts)

1) Rule Interpretation
- Function: Translate declarative rules (e.g., YAML) into executable operations.
- Inputs: game system definition, narrative/scene context, requested actions.
- Outputs: resolutions (success/failure/partial), derived effects, state changes.
- Constraints: deterministic given same inputs; full traceability (which rule applied and why).
- Metrics: rule coverage, resolution latency, ambiguity rate.

2) Narrative State Management
- Function: Maintain the state of story, scene, and active entities.
- Inputs: resolutions, confirmed events, user/agent decisions.
- Outputs: updated consistent state (timeline, flags, conditions).
- Invariants: no loss of causality; no duplicate events; consistency between attributes and conditions.
- Metrics: number of inconsistencies detected, commit time.

3) Narrative Generation
- Function: Produce diegetic text (prose, dialogue, descriptions) from state + resolutions.
- Inputs: current state, scene goals, style/tone.
- Outputs: narrative passages with continuity markers (which facts it supports).
- Quality: coherence, tone, pacing, variety; no explicit contradictions.
- Metrics: clarity/coherence score (Critic), controlled length, revision rate.

4) Continuity & Validation
- Function: Check temporality, roles, identities, canon.
- Inputs: new/modified facts; proposed relationships.
- Outputs: ok / warnings / veto with reasons and correction suggestions.
- Typical rules: no same entity in two places at the same time; role conflicts; paradox detection.
- Metrics: false positives/negatives, validation time.

5) Scene Planning
- Function: Transform high-level goals into beats (micro-narrative objectives).
- Inputs: high-level goal (e.g., “introduce rival”, “reveal clue”).
- Outputs: ordered list of beats with completion criteria and risks.
- Metrics: beat completion rate, deviation from plan.

6) Traceability & Explainability
- Function: Record why outcomes happened (rule X + evidence Y ⇒ decision Z).
- Inputs: all actions/checks/selections.
- Outputs: queryable trace (who decided, based on what).
- Metrics: trace completeness, auditability.

---

## Agents — Functions

- Director
  - Goal: Turn a request into a scene/beat plan.
  - Inputs: user intent, current context.
  - Outputs: list of beats, dependencies, conditions of success, risks.
  - Failure: if insufficient data, return alternative plans with clear assumptions.

- Librarian
  - Goal: Answer “what do we already know” and “what supports X.”
  - Inputs: query or hypothesis.
  - Outputs: relevant excerpts/summaries, ranking, justification.
  - Failure: when no evidence exists, return null with identified gaps.

- Steward (Continuity Guardian)
  - Goal: Detect and arbitrate contradictions.
  - Inputs: new/modified facts; proposed relationships.
  - Outputs: validation, warnings, or veto with fix recommendations.
  - Failure: if ambiguity, request disambiguation (time, identity, source).

- Narrator
  - Goal: Write diegetic output consistent with plan + rules + continuity.
  - Inputs: validated beats, engine resolutions, style/tone.
  - Outputs: final text, markers of which facts are referenced/changed.
  - Failure: if constraints can’t be met, return degraded version + notes.

- Character (Personifier)
  - Goal: Simulate voices/behaviors of entities/characters.
  - Inputs: characterization (traits, goals, limits), scene context.
  - Outputs: dialogue/action turns consistent with character sheet/entity.
  - Failure: if characterization is insufficient, request minimal traits.

- Critic
  - Goal: Evaluate and suggest improvements.
  - Inputs: narrator’s draft + quality criteria (coherence, tone, pacing).
  - Outputs: scores, comments, suggested actions (cut, reorder, rewrite).
  - Thresholds: if below threshold, return for rewrite with clear directions.

- Recorder
  - Goal: Formalize and consolidate accepted outcomes.
  - Inputs: final text, canonical facts, state changes.
  - Outputs: commit confirmation and reference keys (for future queries).
  - Failure: if commit violates invariants, reject and return diff/diagnosis.

- Chat Host / Orchestrator
  - Goal: Manage turns, modes (copilot/autopilot), and agent handoffs.
  - Inputs: user intent, flow state, guardrail policies.
  - Outputs: next step, which agent acts, what is needed, when to stop.
  - Failure: in loops or conflicts, escalate to human review.

---

## Cross‑Cutting Policies (Guardrails)

- Separation of powers: narrator doesn’t persist; recorder doesn’t generate; steward validates before commit.
- Mandatory explainability: every decision logs “rule + evidence + responsible.”
- Copilot vs autopilot modes: copilot requires checkpoints; autopilot follows thresholds/policies.
- Idempotence & retry safety: every step can be retried without duplicating effects.
- Quality control: critic is mandatory with thresholds; subpar results trigger rewrite loop.

---

## Acceptance Criteria by Function (high‑level)

- Planning: produces actionable beats.
- Validation (Steward): catches obvious contradictions; FP/FN within tolerance.
- Narration: respects beats, rules, and style; coherence ≥ threshold.
- Personification: consistent behavior with declared traits in ≥ X turns.
- Retrieval (Librarian): clear relevance + justification.
- Recording: commits consistent, full trace included.
- Orchestration: flow without deadlocks; recoverable on failure.

> Next step: formalize these into interfaces (inputs, outputs, pre/post‑conditions, error signals) so we can write smoke tests and enforce compliance before diving into implementations.

---

## Prompts (guidelines)

- Narrator: short, evocative, scene‑focused; end with 1 guiding question
- Character: first‑person, concise reactions; maintain voice
- Archivist: bullet points (summary, threads, inconsistencies)
- Safety default: PG‑13; configurable per Story (planned)

---

## Continuity & Provenance

- Reads via QueryService:
  - `relation_state_history(a, b)`
  - `relations_effective_in_scene(scene_id)`
  - Effective system resolution for universe/story/scene/entity
  - Entities/stories/scenes/facts retrieval helpers
- Writes (dev/autopilot via RecorderService):
  - Multiverse/Universe/Arc/Story/Scene/Entity upserts with ownership links
  - Facts: `Fact(id, description, occurs_in, participants, when|time_span, derived_from)`
  - RelationState deltas: set/changed/ended per Scene
  - Simple Relations: `Entity-[:REL {type, weight, temporal?}]->Entity`
  - APPEARS_IN and PARTICIPATES_AS edges wired by participants where provided
  - All writes should produce an `ops/agent_runs.yaml` record with context and trace (planned)

Delta schema (recorder_tool → commit_deltas):
- ids/context
  - `scene_id?`, `universe_id?`
- creation
  - `new_multiverse: {id?, name?, description?, omniverse_id?}`
  - `new_universe: {id?, name?, description?, multiverse_id?}`
  - `new_arc: {id?, title, tags?, ordering_mode?, universe_id?}`
  - `new_story: {id?, title, summary?, universe_id?, arc_id?, sequence_index?}`
  - `new_scene: {id?, story_id?, sequence_index?, when?, time_span?, recorded_at?, location?, participants?: [entity_id]}`
  - `new_entities: [{id?, name, type?, universe_id?, attributes?}]`
- facts & relations
  - `facts: [{id?, description, occurs_in?, when?, time_span?, participants?: [{entity_id, role}], confidence?, derived_from?}]`
  - `relation_states: [{id?, type, entity_a, entity_b, set_in_scene?|changed_in_scene?|ended_in_scene?, started_at?, ended_at?}]`
  - `relations: [{from|a, to|b, type, weight?, temporal?}]`  # timeless/interval

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
