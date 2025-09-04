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

Agents operate with comprehensive narrative and world context:

- **Graph Integration**: Full access to universe ontology, entities, relationships, and temporal facts
- **Narrative Grounding**: Agents receive complete story context including timelines, character development, and established facts
- **Context Enrichment**: Multi-layered context combining graph relationships with narrative content memories
- **Memory Recording**: Agent outputs captured as structured content linked to graph entities and events
- **Character Awareness**: Consistent character voices maintained through relationship tracking and development history
- **World Consistency**: All narrative generation grounded in established world state and continuity
- **Relationship Tracking**: Dynamic relationship state monitoring across graph and narrative content
- **Consequence Awareness**: Decision-making informed by established facts and potential story implications

## LangGraph Flow Architecture

### **Enhanced Multi-Phase Processing**

**Phase 1: Context Enrichment**
- Retrieve comprehensive context from both Neo4j graph and MongoDB narrative content
- Gather character memories, relationship states, and story timeline
- Load universe context, entities, facts, and established world state
- Build complete narrative grounding for agent decision-making

**Phase 2: Multi-Agent Council**
- **Narrator**: Analyzes dramatic potential with full world context
- **Steward**: Validates continuity against established facts and relationships
- **Character Analyst**: Evaluates character development with relationship awareness
- **Plot Analyst**: Assesses story momentum and consequence implications
- **Synthesis**: Combines perspectives for optimal narrative approach with comprehensive grounding

**Phase 3: Intelligent Generation**
- Context-aware content generation grounded in established world state
- Character consistency maintained through relationship and memory tracking
- Plot thread integration with consequence awareness from graph data
- Adaptive tone and pacing based on comprehensive narrative state

**Phase 4: Memory Integration**
- Update character memories with new experiences and relationship changes
- Track relationship developments across graph and narrative content
- Record plot thread progression and consequence realization
- Maintain comprehensive narrative state for future sessions

### **Flow Implementations**

- **Standard Flow** (`core/engine/flows/graph_builder.py`): Base multi-agent coordination
- **Enhanced Flow** (`core/engine/flows/enhanced_narrative_flow.py`): Advanced narrative intelligence
- **Modular Nodes** (`core/engine/flows/nodes/`): Reusable flow components

## Current Implementation Status

### **Type Safety & Code Quality** ✅
- **MyPy Compliance**: All type checking issues resolved
- **Composition Architecture**: Replaced problematic mixin inheritance with clean service composition
- **Test Coverage**: 104/104 tests passing
- **Dependency Management**: All required packages properly installed and configured

### **Service Layer** ✅
- **Branching Services**: Complete refactor using composition pattern
- **Projection Services**: Full domain-to-persistence mapping with type safety
- **Narrative Content**: Comprehensive MongoDB integration with rich content models
- **Agent Tools**: Context providers and content recorders for agent integration

### **Data Models** ✅
- **Core Ontology**: Omniverse → Multiverse → Universe → Story → Scene hierarchy
- **Narrative Content**: EntityDescription, ChatLog, SceneAbstract, GMNote, NarrativeState, CharacterMemory
- **Type Safety**: All models use Pydantic with strict type validation
- **Backward Compatibility**: Legacy interfaces maintained during transition

### **Multi-Agent System** ✅
- **Agent Specialization**: Director, Librarian, Steward, Narrator, Planner, Critic, Archivist
- **Context Integration**: Agents receive rich narrative context from MongoDB
- **Memory Management**: Persistent character and relationship tracking
- **Adaptive Behavior**: Context-aware content generation and decision making

### **LangGraph Integration** ✅
- **Modular Flow Architecture**: Clean separation of concerns with reusable nodes
- **Enhanced Narrative Flow**: Advanced multi-phase processing with memory integration
- **Fallback Execution**: Robust error handling with graceful degradation
- **Session Management**: Persistent state across multi-turn interactions

## System Capabilities

### **For Players** 🎮
- **Rich Narratives**: Context-aware storytelling with character consistency
- **Character Development**: Persistent memory and relationship tracking
- **Adaptive Campaigns**: AI that learns player preferences and adjusts accordingly
- **Multi-System Support**: D&D 3.5, PBtA, City of Mist, and extensible to others

### **For Game Masters** 🎲
- **Campaign Management**: Automated plot thread and consequence tracking
- **Continuity Support**: AI-assisted fact checking and consistency maintenance
- **Character Intelligence**: NPCs with persistent personalities and relationships
- **Session Preparation**: Context-aware content generation and campaign tools

### **Technical Features** ⚙️
- **Scalable Architecture**: Handles complex, long-running campaigns
- **Multi-Database Strategy**: Optimized storage for different data types
- **Type Safety**: Comprehensive static analysis and runtime validation
- **Extensible Design**: Easy addition of new agents, systems, and capabilities

## Configuration & Deployment

### **Environment Configuration**
```bash
# Core Database Configuration
NEO4J_URI=bolt://localhost:7687
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Agent Behavior Control
MONITOR_PERSONA=guardian
MONITOR_VERBOSE_TASKS=true
MONITOR_AGENTIC_STRICT=false

# Flow Control
MONITOR_ENGINE_BACKEND=langgraph
MONITOR_COPILOT_PAUSE=false
MONITOR_LC_TOOLS=false
```

### **Development Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure Python environment  
python -m venv venv
source venv/bin/activate

# Run type checking
python -m mypy core/ --ignore-missing-imports

# Execute tests
python -m pytest tests/

# Start development server
./run-dev.sh
```

## Architectural Principles

### **1. Composition Over Inheritance**
Services use composition patterns for flexibility and type safety, avoiding complex mixin hierarchies.

### **2. Domain-Driven Design** 
Pure domain models with clear boundaries between business logic and infrastructure concerns.

### **3. Multi-Agent Coordination**
Specialized agents with clear responsibilities collaborate through structured workflows.

### **4. Persistent Memory**
Rich narrative context persists across sessions, enabling consistent character development and plot continuity.

### **5. Type Safety**
Comprehensive static typing with Pydantic models and MyPy validation throughout the codebase.

### **6. Extensibility**
Modular architecture supports easy addition of new RPG systems, agents, and capabilities.

## Data Persistence Strategy

### **Write Flow**
1. **Domain Validation**: Pydantic models validate all incoming data
2. **Agent Processing**: Multi-agent workflow enriches and validates content  
3. **Projection**: Domain models projected to appropriate storage systems
4. **Memory Update**: Narrative content and character memories updated
5. **Indexing**: Content indexed for semantic search and retrieval

### **Read Flow**
1. **Context Query**: Retrieve relevant context from multiple storage systems
2. **Memory Integration**: Combine graph relationships with narrative content
3. **Agent Enrichment**: Provide rich context to agent workflows
4. **Adaptive Response**: Generate context-aware content with memory persistence

### **Data Guardrails**
- **Validation**: Multi-layer validation with Pydantic and Steward agent
- **Consistency**: Cross-system consistency checks and continuity validation
- **Versioning**: Timeline branching for "what-if" scenarios and rollback capability
- **Backup**: Automated backup strategies for long-running campaigns

## API & Interface Layer

### **LangGraph Modes Router**
- **Endpoint**: `/api/langgraph/modes/*`
- **Implementation**: `core/interfaces/langgraph_modes_api.py`
- **Features**: Chat and help endpoints with stateful session management
- **Modes**: Copilot (assisted) and autopilot (autonomous) operation

### **Session Management**
- **Stateful Sessions**: Persistent context across multi-turn interactions
- **ToolContext Injection**: Per-request mode configuration and state management
- **Error Handling**: Graceful degradation and fallback execution paths

## Implementation Notes

### **Ports & Service Boundaries**
- Ports define clean interfaces between layers (LLMPort, RepoPort, QueryReadPort, RecorderWritePort, CachePort, StagingPort)
- Service facades provide clean abstractions over persistence implementations
- LangGraph orchestration composes agents and tools through structured workflows

### **Persistence Policy**
- **Pydantic-First**: Domain models are the source of truth for all data operations
- **Validation Flow**: LangGraph nodes extract → validate (Pydantic + Steward) → persist via Recorder/Projector
- **Configuration**: YAML used for prompts/config and developer fixtures only

### **Quality Assurance**
- **Import Linter**: Configured via importlinter.ini to enforce allowed dependency graph
- **Type Safety**: Comprehensive MyPy checking with strict type validation
- **Testing**: Comprehensive test suite with 104/104 tests passing
- **Documentation**: Living architecture documentation reflecting current system state

## Data Model Reference

See `docs/data_spine_and_satellites.md` for the authoritative "Graph spine + satellites" persistence contract, including detailed write/read flows and data guardrails for the multi-database strategy (Neo4j spine, MongoDB satellites, Qdrant/OpenSearch indexes, MinIO binaries).
