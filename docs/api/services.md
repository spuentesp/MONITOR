# Core Services

## Overview

The `core/services/` folder contains high-level business logic services that coordinate between domain models, persistence layers, and agents. These services implement complex operations, data transformations, and cross-cutting concerns for the narrative system.

## Architecture Role

Services provide the application layer that:
- **Orchestrates** complex business operations across multiple domain objects
- **Abstracts** persistence details from agents and domain logic
- **Coordinates** between different subsystems (graph, document, cache)
- **Implements** cross-cutting concerns like indexing, caching, and validation
- **Provides** high-level APIs for narrative manipulation and query

---

## Core Services

### Query Service (`query_service.py`)

**Purpose**: Primary facade for reading narrative data across all persistence layers.

**Key Methods**:
- `stories_in_universe(universe_id)` - Get all stories in a universe
- `entities_in_universe(universe_id)` - Get all entities in a universe
- `scenes_in_story(story_id)` - Get scene progression for a story
- `facts_for_story(story_id)` - Get key facts relevant to a story
- `relations_effective_in_scene(scene_id)` - Get active relationships in a scene

**Responsibilities**:
- Unify access to Neo4j graph and MongoDB document data
- Optimize queries across multiple data sources
- Provide consistent data formats for agents
- Handle caching and performance optimization

### Object Service (`object_service.py`)

**Purpose**: Domain object lifecycle management and persistence coordination.

**Responsibilities**:
- Create, update, and delete domain objects
- Coordinate persistence across multiple storage systems
- Handle object validation and business rule enforcement
- Manage object relationships and dependencies

### Recorder Service (`recorder_service.py`)

**Purpose**: Event recording and state change tracking.

**Key Features**:
- Record narrative events and state transitions
- Maintain audit trails for story changes
- Support rollback and replay capabilities
- Integrate with monitoring and analytics

---

## Specialized Services

### Narrative Content Service (`narrative_content_service.py`)

**Purpose**: MongoDB-based service for rich narrative content management.

**Key Operations**:
- **Entity Descriptions**: Store and retrieve detailed character/location descriptions
- **Chat Logs**: Manage conversation history and dialogue
- **Scene Abstracts**: Handle scene summaries and atmospheric details
- **GM Notes**: Store game master annotations and secrets
- **Character Memory**: Track character-specific memories and perspectives

**Methods**:
- `save_entity_description(entity_id, description)` - Store rich entity details
- `get_chat_logs(scene_id, limit=50)` - Retrieve conversation history
- `save_scene_abstract(scene_id, abstract)` - Store scene summary
- `search_content(query, content_types=None)` - Full-text content search
- `get_character_memories(character_id)` - Retrieve character perspective

### Narrative Agent Tools (`narrative_agent_tools.py`)

**Purpose**: Integration layer providing agents with comprehensive narrative context.

**Key Components**:

#### NarrativeContextProvider
**Purpose**: Aggregate narrative context from multiple sources for agent use.

**Methods**:
- `get_comprehensive_context(universe_id, story_id=None)` - Full narrative context
- `get_story_timeline(story_id)` - Story progression and event timeline
- `get_character_context(entity_id)` - Character-specific context and memory

**Data Sources**:
- QueryService for structural data (entities, relationships, facts)
- NarrativeContentService for rich content (descriptions, memories)
- Scene and story progression tracking
- Relationship and interaction history

#### NarrativeContentRecorder
**Purpose**: Record agent-generated content back to persistent storage.

**Methods**:
- `record_scene_content(scene_id, content)` - Save scene descriptions
- `record_character_interaction(char_id, interaction)` - Log character actions
- `record_gm_note(scene_id, note)` - Save private GM annotations

### Indexing Service (`indexing_service.py`)

**Purpose**: Search indexing and full-text search capabilities.

**Features**:
- Build and maintain search indices for narrative content
- Support complex queries across multiple content types
- Provide relevance scoring and ranking
- Handle incremental index updates

### Retrieval Service (`retrieval_service.py`)

**Purpose**: Intelligent information retrieval and context assembly.

**Capabilities**:
- Retrieve relevant context based on semantic similarity
- Assemble multi-source context for agent consumption
- Optimize retrieval performance and caching
- Support context-aware search and filtering

---

## Composition Services

### Branching Services (`branching/`)

**Purpose**: Universe branching and parallel timeline management using composition pattern.

#### Universe Cloner (`branching/universe_cloner.py`)
**Purpose**: Clone universe state for branching scenarios.

**Key Methods**:
- `clone_universe(source_id, target_id)` - Deep copy universe state
- `clone_entities(universe_id, entity_map)` - Clone entity state and relationships
- `clone_stories(universe_id, story_map)` - Clone story progression

#### Universe Brancher (`branching/universe_brancher.py`)
**Purpose**: Create branched universes from decision points.

**Key Methods**:
- `create_branch(universe_id, decision_point)` - Branch from specific point
- `merge_branches(source_id, target_id)` - Merge parallel timelines
- `compare_branches(branch_a, branch_b)` - Analyze differences

#### Brancher Service (`branching/brancher_service.py`)
**Purpose**: High-level branching operations coordinator.

**Features**:
- Coordinate complex branching workflows
- Handle branch validation and consistency
- Manage branch lifecycle and cleanup
- Provide unified branching API

### Projection Services (`projection/`)

**Purpose**: Transform domain models to persistence layer formats using composition pattern.

#### System Projector (`projection/system_projector.py`)
**Purpose**: Project game system definitions to database formats.

#### Universe Projector (`projection/universe_projector.py`)
**Purpose**: Project universe models to graph and document representations.

#### Story Projector (`projection/story_projector.py`)
**Purpose**: Project story models to appropriate persistence formats.

#### Entity Projector (`projection/entity_projector.py`)
**Purpose**: Project entity models to graph nodes and document collections.

#### Fact Projector (`projection/fact_projector.py`)
**Purpose**: Project fact models to graph relationships and document stores.

#### Projection Service (`projection/projection_service.py`)
**Purpose**: Coordinate all projection operations and maintain consistency.

**Key Features**:
- Unified projection API across all domain models
- Consistency validation between projections
- Batch projection operations for performance
- Error handling and rollback capabilities

---

## Service Architecture Patterns

### Composition over Inheritance
All services use composition pattern instead of complex inheritance hierarchies:
- **Single Responsibility**: Each service has one clear purpose
- **Loose Coupling**: Services interact through well-defined interfaces
- **Easy Testing**: Services can be tested in isolation
- **Flexible Composition**: Services can be combined in different ways

### Facade Pattern
Services provide simplified interfaces to complex subsystems:
- **QueryService**: Unifies access to multiple databases
- **NarrativeContentService**: Simplifies MongoDB operations
- **ProjectionService**: Coordinates multiple projection operations

### Repository Pattern
Services abstract data access patterns:
- **Consistent APIs**: Same interface regardless of underlying storage
- **Caching Integration**: Transparent caching layer
- **Error Handling**: Consistent error handling across services

## Design Principles

1. **Single Responsibility**: Each service has one clear business purpose
2. **Composition**: Prefer composition over inheritance for flexibility
3. **Abstraction**: Hide persistence and infrastructure details
4. **Performance**: Integrated caching and optimization
5. **Consistency**: Unified interfaces and error handling patterns
6. **Testability**: Services designed for isolated testing

## Integration Patterns

### Agent Integration
```python
# Agents use services through dependency injection
context_provider = NarrativeContextProvider(query_service, content_service)
context = context_provider.get_comprehensive_context(universe_id, story_id)
```

### Service Composition
```python
# Services compose together for complex operations
brancher = BrancherService(cloner, brancher, validator)
new_universe = brancher.create_branch(universe_id, decision_point)
```

### Cross-Cutting Concerns
```python
# Services handle cross-cutting concerns transparently
query_service.stories_in_universe(uuid)  # Automatic caching
content_service.search_content(query)    # Automatic indexing
```

## Performance Considerations

- **Caching**: Multi-level caching strategy across all services
- **Batch Operations**: Optimize database operations through batching
- **Lazy Loading**: Load data on-demand to minimize memory usage
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Optimize database queries and indices

## Error Handling

- **Graceful Degradation**: Services continue operating with reduced functionality
- **Consistent Error Types**: Standardized exception hierarchy
- **Recovery Mechanisms**: Automatic retry and fallback strategies
- **Logging and Monitoring**: Comprehensive error tracking and alerting
