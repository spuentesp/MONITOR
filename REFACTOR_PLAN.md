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

### 1.2 Split `langgraph_modes.py` (1003 lines) ✅ COMPLETED
- ✅ `core/engine/modes/` directory structure:
  - ✅ `state.py` - GraphState management and utilities
  - ✅ `router.py` - Intent classification and routing logic  
  - ✅ `narration_mode.py` - Simple narration mode handler
  - ✅ `monitor/` subdirectory with specialized handlers:
    - ✅ `__init__.py` - Package exports
    - ✅ `main_handler.py` - Central coordinator for all monitor operations
    - ✅ `crud_handlers.py` - Basic CRUD operations (create, list entities/facts/etc)
    - ✅ `entity_handlers.py` - Entity queries (show info, list enemies, last seen)
    - ✅ `scene_handlers.py` - Scene management (end/add/modify scenes, conversations)
    - ✅ `entity_management_handlers.py` - Entity creation, retcon, wizard flows
    - ✅ `setup_handlers.py` - Story/universe setup workflows
    - ✅ `utils.py` - Helper functions for commits, wizard state, auto-flush
- ✅ Created `langgraph_modes_modular.py` with legacy compatibility adapters
- ✅ **All tests passing (71/71)** after major refactoring

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

### 2.2 Extract Raw Queries to Configuration ✅ COMPLETED
- ✅ `core/persistence/query_files/cypher/` directory:
  - ✅ **30 query files extracted** from inline strings to separate .cypher files
  - ✅ Entity queries: `entities_in_*.cypher` (8 files)
  - ✅ Fact queries: `facts_for_*.cypher` (2 files)  
  - ✅ Scene queries: `scenes_*.cypher`, `participants_by_role_*.cypher` (6 files)
  - ✅ Relation queries: `relation_*.cypher`, `relations_*.cypher` (3 files)
  - ✅ System queries: `system_usage_summary.cypher`, `effective_system_for_*.cypher` (6 files)
  - ✅ Axiom queries: `axioms_*.cypher` (2 files)
  - ✅ Catalog queries: `list_*.cypher` (2 files)
  - ✅ Navigation queries: `*_scene_for_entity_in_story.cypher` (2 files)
- ✅ **7 query classes updated** to use QueryLoader:
  - ✅ `EntitiesQueries`, `FactsQueries`, `ScenesQueries`
  - ✅ `RelationsQueries`, `SystemsQueries`, `AxiomsQueries`, `CatalogQueries`

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
