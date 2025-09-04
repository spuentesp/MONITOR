# Core Engine

## Overview

The `core/engine/` folder contains the runtime execution engine that orchestrates the multi-agent narrative system. It handles workflow management, tool integration, context management, and the coordination between agents to produce coherent narrative experiences.

## Architecture Role

The engine serves as the coordination layer between:
- **Agents**: Specialized AI personalities and roles
- **Domain Models**: Core narrative data structures  
- **Persistence**: Database storage and retrieval
- **Tools**: Narrative manipulation capabilities
- **Workflows**: LangGraph-based agent coordination

## Core Components

### Flow Management

#### Graph Builder (`flows/graph_builder.py`)

**Purpose**: Constructs and configures the main LangGraph workflow for narrative generation.

**Key Functions**:
- `build_langgraph_flow(tools, config=None)` - Main flow construction
- `_env_flag(name, default="0")` - Environment configuration parser

**Features**:
- Dynamic LangGraph workflow construction
- Optional LangChain tools integration
- Environment-based feature toggling
- Safe agent invocation with fallback handling

**Architecture**:
- Uses StateGraph for workflow definition
- Implements fallback mechanisms for missing agents
- Supports conditional tool loading based on environment
- Provides safe execution with error recovery

#### Flow State (`flows/state.py`)

**Purpose**: Defines the shared state structure passed between workflow nodes.

**Key Components**:
- Message history tracking
- Agent output accumulation
- Context preservation
- Error state management

#### Flow Nodes (`flows/nodes/`)

**Purpose**: Individual workflow steps implementing specific agent behaviors.

**Key Nodes**:
- `critic_node` - Quality evaluation and feedback
- `planner_node` - Strategic narrative planning
- `recorder_node` - Event and state recording
- `resolve_decider_node` - Conflict resolution and final decisions

---

### Tool Integration

#### Tools (`tools.py`)

**Purpose**: Core tool definitions for narrative manipulation and query operations.

**Responsibilities**:
- Provide standardized interfaces for narrative operations
- Handle database interactions and state changes
- Support agent tool usage patterns
- Ensure consistent data access patterns

#### LangChain Tools (`lc_tools.py`)

**Purpose**: Integration layer for LangChain-compatible tools.

**Features**:
- `build_langchain_tools(ctx)` - Convert internal tools to LangChain format
- Standardized tool interface adaptation
- Context-aware tool initialization
- Optional integration based on environment settings

#### Tool Resolution (`resolve_tool.py`)

**Purpose**: Advanced tool execution with context resolution and error handling.

**Capabilities**:
- Context-aware tool execution
- Error recovery and fallback strategies
- Tool result validation and post-processing
- Integration with agent decision-making

---

### Context Management

#### Context (`context.py`)

**Purpose**: Core context management for narrative state and agent coordination.

**Responsibilities**:
- Maintain narrative context across agent interactions
- Provide unified access to story state and history
- Handle context updates and state transitions
- Support context-aware agent operations

#### Context Utils (`context_utils.py`)

**Purpose**: Utility functions for context manipulation and analysis.

**Key Functions**:
- Context serialization and deserialization
- Context merging and conflict resolution  
- Context validation and integrity checking
- Performance optimization for context operations

---

### Workflow Orchestration

#### Orchestrator (`orchestrator.py`)

**Purpose**: High-level workflow coordination and execution management.

**Responsibilities**:
- Coordinate complex multi-agent workflows
- Manage workflow state and transitions
- Handle workflow error recovery and retries
- Provide workflow monitoring and diagnostics

#### Flow Utils (`flow_utils.py`)

**Purpose**: Utility functions for workflow construction and management.

**Key Features**:
- Workflow graph manipulation utilities
- Node and edge management helpers
- Flow optimization and analysis tools
- Debug and monitoring support

---

### Event and State Management

#### Event Handler (`event_handler.py`)

**Purpose**: Event processing and state transition management.

**Capabilities**:
- Process narrative events and trigger appropriate responses
- Manage state transitions and consistency
- Handle event validation and error recovery
- Support event-driven agent coordination

#### Autocommit (`autocommit.py`)

**Purpose**: Automatic state persistence and transaction management.

**Features**:
- Automatic state saving at key workflow points
- Transaction rollback and recovery
- Consistency validation and error handling
- Performance optimization for database operations

#### Commit (`commit.py`)

**Purpose**: Manual state persistence and checkpoint management.

**Responsibilities**:
- Explicit state saving and checkpoint creation
- State validation before persistence
- Error handling and recovery mechanisms
- Integration with transaction management

---

### Caching and Performance

#### Cache (`cache.py`)

**Purpose**: Core caching infrastructure for performance optimization.

**Features**:
- In-memory caching for frequently accessed data
- Cache invalidation and consistency management
- Performance monitoring and optimization
- Integration with database operations

#### Cache Operations (`cache_ops.py`)

**Purpose**: Specific caching operations and strategies.

**Capabilities**:
- Context-specific caching strategies
- Cache warming and preloading
- Cache statistics and monitoring
- Integration with workflow operations

#### Cache Redis (`cache_redis.py`)

**Purpose**: Redis-based distributed caching implementation.

**Features**:
- Distributed cache support for multi-instance deployments
- Redis-specific optimizations and configurations
- Failover and error recovery mechanisms
- Integration with core caching infrastructure

---

### Specialized Components

#### Attribute Extractor (`attribute_extractor.py`)

**Purpose**: Extract and analyze attributes from narrative content.

**Capabilities**:
- Extract character attributes from descriptions
- Analyze scene attributes and environmental factors
- Process entity relationships and connections
- Support AI-driven attribute inference

#### Monitor Parser (`monitor_parser.py`)

**Purpose**: Parse and analyze system monitoring data.

**Features**:
- Parse agent performance metrics
- Analyze workflow execution patterns
- Extract system health indicators
- Support debugging and optimization

#### Steward (`steward.py`)

**Purpose**: System stewardship and maintenance operations.

**Responsibilities**:
- System health monitoring and maintenance
- Resource cleanup and optimization
- Error recovery and system restoration
- Performance tuning and optimization

#### Librarian (`librarian.py`)

**Purpose**: Information organization and retrieval coordination.

**Features**:
- Coordinate information access across agents
- Optimize information retrieval patterns
- Maintain information organization and indexing
- Support cross-reference and relationship analysis

---

### Legacy and Compatibility

#### LangGraph Flow (`langgraph_flow.py`)

**Purpose**: Legacy compatibility wrapper for older flow implementations.

**Status**: Deprecated - use `flows/graph_builder.py` instead

#### LangGraph Modes (`langgraph_modes.py`, `langgraph_modes_modular.py`)

**Purpose**: Alternative workflow modes and configurations.

**Features**:
- Different agent coordination patterns
- Alternative workflow topologies
- Experimental features and configurations
- Backward compatibility support

---

## Design Principles

1. **Modularity**: Components can be combined and reconfigured
2. **Fault Tolerance**: Graceful degradation when components fail
3. **Performance**: Caching and optimization throughout
4. **Extensibility**: Easy to add new tools and agents
5. **Monitoring**: Comprehensive tracking and diagnostics
6. **Consistency**: Unified interfaces and patterns

## Key Patterns

### Tool Integration
```python
# Standard tool usage
tools = build_tools_package(ctx)
result = tools["narrative_tool"](action="describe", target="scene")

# LangChain integration (optional)
if use_lc_tools:
    lc_tools = build_langchain_tools(ctx)
```

### Flow Construction
```python
# Main flow building
graph = build_langgraph_flow(tools, config)
result = graph.invoke({"intent": "tell me something", "universe_id": "u1"})
```

### Context Management
```python
# Context operations
context = build_narrative_context(universe_id, story_id)
enhanced_context = merge_contexts(context, agent_context)
```

### Event Processing
```python
# Event handling
event = NarrativeEvent(action="character_speaks", data=speech_data)
result = process_event(event, current_context)
```

## Integration Points

- **LangGraph**: Workflow orchestration framework
- **LangChain**: Optional tool integration
- **Domain Models**: Direct access to narrative structures
- **Persistence**: Database operations and caching
- **Agents**: Agent coordination and execution
- **Tools**: Narrative manipulation capabilities

## Performance Considerations

- **Caching**: Multi-level caching strategy reduces database load
- **Lazy Loading**: Context loaded on-demand to optimize memory
- **Connection Pooling**: Database connections managed efficiently
- **Error Recovery**: Graceful degradation maintains system availability
- **Monitoring**: Performance tracking enables optimization
