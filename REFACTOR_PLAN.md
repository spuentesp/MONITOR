# SOLID/DRY Refactoring Plan

## Phase 1: Split Large Files (Single Responsibility) ✅ PARTIALLY COMPLETE

### 1.1 Split `tools.py` (568 lines) ✅ COMPLETED
- ✅ `core/engine/tools/` directory structure:
  - ✅ `__init__.py` - ToolContext and tool registry
  - ✅ `query_tool.py` - Query tool and rules tool implementation
  - ✅ `recorder_tool.py` - Recording/persistence tool
  - ✅ `narrative_tool.py` - Narrative/story tools
  - ✅ `indexing_tool.py` - Search indexing tools
  - ✅ `retrieval_tool.py` - Retrieval/search tools
  - ✅ `object_tool.py` - Object storage tools
  - ✅ `bootstrap_tool.py` - Story bootstrapping tools
  - ✅ `notes_tool.py` - Note recording tools

### 1.2 Split `langgraph_modes.py` (1003 lines) 🔄 PENDING
- `core/engine/modes/` directory:
  - `__init__.py` - Mode types and registry
  - `router.py` - Mode detection/routing logic
  - `narration_mode.py` - Narration-specific flow
  - `monitor_mode.py` - Monitor command handling
  - `state.py` - GraphState management
  - `utils.py` - Helper functions

### 1.3 Split `langgraph_flow.py` (656 lines) 🔄 PENDING
- `core/engine/flows/` directory:
  - `__init__.py` - Flow builder and registry
  - `graph_builder.py` - LangGraph construction
  - `nodes/` subdirectory:
    - `planner.py` - Planning node
    - `resolver.py` - Resolution node  
    - `recorder.py` - Recording node
    - `critic.py` - Validation node

## Phase 2: Extract Query Patterns (Interface Segregation) ✅ PARTIALLY COMPLETE

### 2.1 Create Query Builders (Separate from Executors) ✅ COMPLETED
- ✅ `core/persistence/query_files/builders/` directory:
  - ✅ `query_loader.py` - Query loading and caching utility

### 2.2 Extract Raw Queries to Configuration ✅ PARTIALLY COMPLETE
- ✅ `core/persistence/query_files/cypher/` directory:
  - ✅ `system_usage_summary.cypher` - System usage queries
  - ✅ `effective_system_for_universe.cypher` - System hierarchy queries
  - ✅ `entities_in_scene.cypher` - Entity by scene queries
  - ✅ `entities_in_story.cypher` - Entity by story queries
  - ✅ `entities_in_universe.cypher` - Entity by universe queries
  - ✅ `entities_in_arc.cypher` - Entity by arc queries
  - ✅ `entities_in_*_by_role.cypher` - Role-based entity queries
  - ✅ `entity_by_name_in_universe.cypher` - Entity lookup queries
  - ✅ `facts_for_scene.cypher` - Scene fact queries
  - ✅ `facts_for_story.cypher` - Story fact queries
  - ✅ `scenes_for_entity.cypher` - Entity scene queries
  - ✅ `participants_by_role_for_*.cypher` - Role participation queries
  - ✅ `*_scene_for_entity_in_story.cypher` - Scene navigation queries
  - ✅ `stories_in_universe.cypher` - Universe story queries
  - ✅ `scenes_in_story.cypher` - Story scene queries
  - 🔄 More queries to extract from remaining query files

### 2.3 Create Repository Abstractions ✅ PARTIALLY COMPLETE
- `core/persistence/repositories/` directory:
  - `entity_repository.py` - Entity-focused operations
  - `relation_repository.py` - Relationship operations
  - `fact_repository.py` - Fact storage/retrieval
  - `system_repository.py` - System management

## Phase 3: Dependency Inversion (SOLID D)

### 3.1 Define Clear Interfaces
- `core/interfaces/persistence/` directory:
  - `query_interface.py` - Read operations contract
  - `repository_interface.py` - Write operations contract
  - `cache_interface.py` - Caching contract

### 3.2 Service Layer Separation
- `core/services/domain/` directory:
  - `entity_service.py` - Entity business logic
  - `narrative_service.py` - Story/scene logic
  - `system_service.py` - System resolution logic

## Phase 4: Open/Closed Principle Improvements

### 4.1 Plugin Architecture for Tools
- `core/engine/tools/registry.py` - Tool registration system
- Tool discovery via entry points or configuration

### 4.2 Configurable Query Strategies
- Support for different database backends
- Strategy pattern for query execution

## Implementation Priority

### High Priority (Immediate):
1. Split `tools.py` → tool modules
2. Extract Cypher queries to `.cypher` files
3. Create query builders

### Medium Priority:
4. Split `langgraph_modes.py` → mode modules  
5. Repository pattern implementation
6. Service layer creation

### Low Priority (Future):
7. Plugin architecture
8. Multi-backend support
9. Advanced query optimization

## Benefits Expected

- **Maintainability**: Smaller, focused files
- **Testability**: Isolated responsibilities
- **Reusability**: Composable query builders
- **Extensibility**: Clear extension points
- **Readability**: Single-purpose modules
