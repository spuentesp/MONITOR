# MONITOR: Intelligent DM/Assistant System Architecture

MONITOR is a LangGraph-based intelligent dungeon master and assistant system for tabletop RPGs. It combines multi-agent coordination, persistent narrative memory, and adaptive storytelling to create rich, consistent campaign experiences.

## Core Architecture

### **Multi-Agent DM System**
The system operates as a collaborative AI dungeon master with specialized agents:

- **Director**: High-level coordination and narrative direction
- **Librarian**: Evidence gathering and context retrieval  
- **Steward**: Validation, continuity, and consistency enforcement
- **Narrator**: Context-aware narrative content generation
- **Planner**: Action planning and execution coordination
- **Critic**: Quality assessment and refinement
- **Archivist**: Content indexing and memory management

### **Layered Architecture**

- **domain** (pure): Pydantic models, business invariants. No I/O.
  - `core/domain/*` - Core ontology (Multiverse → Universe → Story → Scene)
  - `core/domain/narrative_content.py` - Rich narrative content models
- **ports** (interfaces): Protocols for external capabilities.
  - `core/ports/*` - LLMPort, RepoPort, QueryReadPort, RecorderWritePort, CachePort, StagingPort
- **services** (application): Composition-based business services.
  - `core/services/branching/*` - Universe cloning and branching operations
  - `core/services/projection/*` - Domain-to-persistence projection services
  - `core/services/narrative_content_service.py` - MongoDB narrative content management
  - `core/services/narrative_agent_tools.py` - Agent integration with narrative content
- **infrastructure** (adapters): Database implementations and concrete technology.
  - `core/persistence/*` - Neo4j graph operations, MongoDB document storage
  - `core/engine/cache*` - Redis and in-memory caching
- **generation** (models/providers): LLM providers and model configurations.
  - `core/generation/*`, `core/loaders/agent_prompts.py`
- **agents**: Specialized AI behavior policies with narrative intelligence.
  - `core/agents/*` - Individual agent implementations
- **orchestration**: Multi-phase LangGraph flows with narrative memory.
  - `core/engine/flows/*` - Modular flow construction and node implementations
  - `core/engine/flows/enhanced_narrative_flow.py` - Advanced narrative intelligence flow
  - `core/engine/orchestrator.py`, `core/engine/tools.py`
- **interfaces** (edges): API, CLI, and user interfaces.
  - `core/interfaces/*`, `frontend/*`

### **Dependency Flow** (top → bottom)

- **domain** ← none (pure business models)
- **ports** ← domain (interface definitions)
- **services** ← domain, ports (composition-based business logic)
- **infrastructure** ← domain, ports (concrete implementations)
- **generation** ← ports, domain (LLM integration)
- **agents** ← generation, domain (AI behavior policies)
- **orchestration** ← services, agents, generation, ports (flow coordination)
- **interfaces** ← orchestration, services (external APIs)

## Data Architecture

### **Multi-Database Strategy**

**Neo4j Graph Database** (Primary Ontology)
- **Spine**: Omniverse → Multiverse → Universe → Story → Scene hierarchy
- **Entities**: Characters, locations, objects with relationships
- **Facts**: Temporal facts and relation states
- **Query Operations**: Complex graph traversals and relationship analysis

**MongoDB Document Database** (Narrative Content)
- **EntityDescription**: Rich character and location descriptions
- **ChatLog**: Dialogue and conversation history
- **SceneAbstract**: Scene summaries and key events
- **GMNote**: Game master notes and campaign tracking
- **NarrativeState**: Current narrative tone, tension, and plot threads
- **CharacterMemory**: Character development, relationships, and growth

**Supporting Systems**
- **Qdrant/OpenSearch**: Semantic search and content indexing
- **MinIO**: Binary asset storage (images, documents)
- **Redis**: Session caching and temporary state

### **Domain Model Hierarchy**

```
Omniverse (Meta-container)
├── Multiverse (Setting/Campaign)
│   ├── Universe (Game Instance)
│   │   ├── Story (Narrative Arc)
│   │   │   ├── Scene (Play Session)
│   │   │   └── Sheet (Character/Entity Data)
│   │   ├── Entity (Characters, NPCs, Objects)
│   │   ├── Fact (Temporal Information)
│   │   └── RelationState (Entity Relationships)
│   └── System (RPG Rule System)
└── ArchetypeEntity (Templates/Patterns)
```

## Service Architecture

### **Composition-Based Services**

**Branching Services** (`core/services/branching/`)
- **UniverseCloner**: Creates deep copies of universe states
- **UniverseBrancher**: Manages timeline branching and "what-if" scenarios  
- **BrancherService**: Unified interface for branching operations

**Projection Services** (`core/services/projection/`)
- **SystemProjector**: Maps game systems to persistence
- **UniverseProjector**: Projects universe models to Neo4j
- **StoryProjector**: Handles story and scene persistence
- **EntityProjector**: Manages entity and relationship storage
- **FactProjector**: Temporal fact management
- **ProjectionService**: Coordinated projection operations

**Narrative Intelligence Services**
- **NarrativeContentService**: MongoDB content management with search and indexing
- **NarrativeContextProvider**: Rich context retrieval for agents
- **NarrativeContentRecorder**: Structured content recording and memory updates

### **Agent Integration**

Agents now operate with rich narrative context:

- **Context Enrichment**: Agents receive relevant memories, relationships, and plot threads
- **Memory Recording**: Agent outputs are captured as structured narrative content  
- **Character Awareness**: Agents maintain consistent character voices and development
- **Relationship Tracking**: Dynamic relationship state monitoring and updates

## LangGraph Flow Architecture

### **Enhanced Multi-Phase Processing**

**Phase 1: Context Enrichment**
- Retrieve relevant narrative context from MongoDB
- Gather character memories and relationship states
- Load scene history and current narrative state

**Phase 2: Multi-Agent Council**
- **Narrator**: Analyzes dramatic potential and story flow
- **Steward**: Validates continuity and consistency
- **Character Analyst**: Evaluates character development impact
- **Synthesis**: Combines perspectives for optimal narrative approach

**Phase 3: Intelligent Generation**
- Context-aware content generation with character consistency
- Plot thread integration and consequence management
- Adaptive tone and pacing based on narrative state

**Phase 4: Memory Integration**
- Update character memories with new experiences
- Track relationship changes and developments
- Record plot thread progression and consequences
- Maintain narrative state for future sessions

### **Flow Implementations**

- **Standard Flow** (`core/engine/flows/graph_builder.py`): Base multi-agent coordination
- **Enhanced Flow** (`core/engine/flows/enhanced_narrative_flow.py`): Advanced narrative intelligence
- **Modular Nodes** (`core/engine/flows/nodes/`): Reusable flow components

Current status

- Ports added and used for ToolContext and service facades.
- LangGraph is the default orchestration. `run_once` composes agents and tools and invokes the flow.
- Librarian/Steward depend on QueryReadPort.

Persistence policy

- Pydantic-first: domain models are the source of truth. LangGraph nodes extract → validate (Pydantic + Steward) → persist via Recorder/Projector. YAML is used for prompts/config and developer fixtures only.

Data model reference

- See docs/data_spine_and_satellites.md for the authoritative “Graph spine + satellites” persistence contract (Neo4j spine, Mongo satellites, Qdrant/OpenSearch indexes, MinIO binaries), including write/read flows and guardrails.

Interfaces exposure

- API exposes the LangGraph Modes Router under `/api/langgraph/modes/*`.
  - File: `core/interfaces/langgraph_modes_api.py` (chat/help endpoints). Builds a stateful session and injects `ToolContext` per request mode (copilot/autopilot).

Next steps

- Annotate remaining services with RepoPort and adopt ports at boundaries.
- Import Linter configured (importlinter.ini); wire into CI to enforce allowed import graph.
- Expand docs as modules evolve.
