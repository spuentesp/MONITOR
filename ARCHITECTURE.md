# Architecture and Module Boundaries

This project follows a layered architecture to keep responsibilities clear and enable swapping infrastructure without touching orchestration and domain logic.

- domain (pure): Pydantic models, small invariants. No I/O.
  - `core/domain/*`
- ports (interfaces): Protocols for external capabilities.
  - `core/ports/*`
  - LLMPort, RepoPort, QueryReadPort, RecorderWritePort, CachePort, StagingPort
- services (application): Business services orchestrating domain via ports.
  - `core/services/*`
  - Facades for Query/Recorder currently forward to persistence implementations
- infrastructure (adapters): Concrete tech and DB queries.
  - `core/persistence/*`, `core/engine/cache*`
  - Neo4j repo, projectors, query mixins, recorder Cypher, caches
- generation (models/providers): LLM providers and configs.
  - `core/generation/*`, `core/loaders/agent_prompts.py`
- agents: Behavior policies (Narrator, Archivist, Character).
  - `core/agents/*`
- orchestration: Flows and tool wiring (LangGraph default).
  - `core/engine/langgraph_flow.py` (single-turn nodes), `core/engine/langgraph_modes.py` (narration vs monitor router),
    `core/engine/orchestrator.py` (run_once, ToolContext helpers), `core/engine/tools.py`, `core/engine/lc_tools.py`
- interfaces (edges): API, CLI, UI.
  - `core/interfaces/*`, `frontend/*`

Allowed dependencies (top → bottom):

- domain ← none
- ports ← domain
- services ← domain, ports
- infrastructure ← domain, ports (implements ports)
- generation ← ports, domain
- agents ← generation, domain
- orchestration ← services, agents, generation (LLM port), ports (for ToolContext types)
- interfaces ← orchestration, services

Current status

- Ports added and used for ToolContext and service facades.
- LangGraph is the default orchestration. `run_once` composes agents and tools and invokes the flow.
- Librarian/Steward depend on QueryReadPort.

Interfaces exposure

- API exposes the LangGraph Modes Router under `/api/langgraph/modes/*`.
  - File: `core/interfaces/langgraph_modes_api.py` (chat/help endpoints). Builds a stateful session and injects `ToolContext` per request mode (copilot/autopilot).

Next steps

- Annotate remaining services with RepoPort and adopt ports at boundaries.
- Import Linter configured (importlinter.ini); wire into CI to enforce allowed import graph.
- Expand docs as modules evolve.
