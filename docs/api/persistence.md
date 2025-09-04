# Core Persistence

## Overview

The `core/persistence/` folder contains the data access layer that manages all interactions with storage systems. This includes Neo4j graph database operations, MongoDB document storage, Qdrant vector search, and caching mechanisms.

## Architecture Role

The persistence layer provides:
- **Data Access Abstraction**: Unified interfaces for different storage systems
- **Repository Pattern Implementation**: Consistent data access patterns
- **Query Optimization**: Efficient database operations and caching
- **Transaction Management**: ACID compliance and data consistency
- **Search Integration**: Vector and full-text search capabilities

---

## Core Storage Interfaces

### Protocols (`protocols.py`)

**Purpose**: Define standard interfaces for all persistence operations.

**Key Protocols**:
- `Repository` - Standard CRUD operations interface
- `GraphRepository` - Graph-specific operations (nodes, relationships)
- `DocumentRepository` - Document store operations
- `SearchRepository` - Search and indexing operations

**Benefits**:
- Type safety through protocol typing
- Consistent interface across storage types
- Easy mocking and testing
- Clear contract definitions

### Object Store (`object_store.py`)

**Purpose**: High-level object persistence coordinator.

**Responsibilities**:
- Coordinate persistence across multiple storage systems
- Handle object serialization and deserialization
- Manage object lifecycle and validation
- Provide unified CRUD operations

**Key Methods**:
- `save(obj)` - Persist object to appropriate storage
- `load(id, type)` - Retrieve object by ID and type
- `delete(id, type)` - Remove object from all storage systems
- `query(criteria)` - Search across storage systems

---

## Graph Database Layer

### Neo4j Repository (`neo4j_repo.py`)

**Purpose**: Neo4j-specific graph database operations.

**Key Operations**:
- **Node Management**: Create, update, delete graph nodes
- **Relationship Management**: Manage edges and connections
- **Graph Traversal**: Complex path queries and graph analysis
- **Transaction Support**: ACID transactions for consistency

**Key Methods**:
- `create_node(labels, properties)` - Create graph node
- `create_relationship(from_node, to_node, type, properties)` - Link nodes
- `cypher_query(query, parameters)` - Execute raw Cypher queries
- `get_neighbors(node_id, relationship_type)` - Find connected nodes

**Query Optimization**:
- Index management for fast lookups
- Query plan optimization
- Connection pooling
- Result caching

---

## Document Database Layer

### MongoDB Store (`mongo_store.py`)

**Purpose**: MongoDB document database operations.

**Key Features**:
- **Collection Management**: Dynamic collection creation and management
- **Document Operations**: CRUD operations for document data
- **Aggregation Pipelines**: Complex data transformation queries
- **Index Management**: Automatic index creation and optimization

**Key Methods**:
- `insert_one(collection, document)` - Insert single document
- `find(collection, query, projection)` - Query documents
- `update_one(collection, filter, update)` - Update single document
- `aggregate(collection, pipeline)` - Execute aggregation pipeline

### MongoDB Repositories (`mongo_repos.py`)

**Purpose**: Specialized MongoDB repositories for different domain models.

**Repository Types**:
- `UniverseRepository` - Universe document operations
- `StoryRepository` - Story progression tracking
- `EntityRepository` - Entity description and attributes
- `EventRepository` - Event logging and history

**Features**:
- Domain-specific query methods
- Optimized indexing strategies
- Data validation and transformation
- Performance monitoring

---

## Search and Indexing

### Search Index (`search_index.py`)

**Purpose**: Full-text search indexing and query capabilities.

**Features**:
- **Text Indexing**: Index narrative content for search
- **Query Processing**: Parse and execute search queries
- **Relevance Scoring**: Rank results by relevance
- **Faceted Search**: Filter by multiple criteria

### Qdrant Index (`qdrant_index.py`)

**Purpose**: Vector database operations for semantic search.

**Capabilities**:
- **Vector Storage**: Store embeddings for semantic similarity
- **Similarity Search**: Find similar content using vector similarity
- **Clustering**: Group similar content automatically
- **Hybrid Search**: Combine vector and text search

**Key Methods**:
- `add_vectors(points)` - Add vector embeddings
- `search(vector, limit)` - Find similar vectors
- `delete_vectors(ids)` - Remove vector data
- `create_collection(name, config)` - Set up vector collection

---

## Query Management

### Queries (`queries.py`)

**Purpose**: Centralized query definitions and execution.

**Query Categories**:
- **Structural Queries**: Navigate narrative hierarchy
- **Content Queries**: Search narrative content
- **Relationship Queries**: Analyze entity connections
- **Timeline Queries**: Track story progression

### Query Files (`query_files/`)

**Purpose**: Externalized query definitions for maintainability.

**Organization**:
- Cypher queries for Neo4j operations
- MongoDB aggregation pipelines
- Search query templates
- Query optimization hints

### Queries Library (`queries_lib/`)

**Purpose**: Query building utilities and helpers.

**Features**:
- Dynamic query construction
- Parameter binding and validation
- Query optimization suggestions
- Performance monitoring

---

## Specialized Components

### Recorder (`recorder.py`)

**Purpose**: Event recording and audit trail management.

**Responsibilities**:
- Record all narrative events and state changes
- Maintain immutable event logs
- Support event replay and analysis
- Integrate with monitoring systems

**Key Features**:
- Event serialization and storage
- Temporal querying capabilities
- Event aggregation and statistics
- Integration with analytics

### Brancher (`brancher.py`)

**Purpose**: Universe branching and timeline management at persistence layer.

**Note**: This is legacy code replaced by composition-based services in `core/services/branching/`.

### Projector (`projector.py`)

**Purpose**: Model-to-storage projection at persistence layer.

**Note**: This is legacy code replaced by composition-based services in `core/services/projection/`.

---

## Repository Pattern Implementation

### Repositories (`repositories/`)

**Purpose**: Implement repository pattern for each domain model.

**Repository Structure**:
- **Base Repository**: Common CRUD operations
- **Graph Repository**: Graph-specific operations
- **Document Repository**: Document-specific operations
- **Search Repository**: Search-specific operations

**Benefits**:
- Consistent data access patterns
- Easy testing with mock repositories
- Clear separation of concerns
- Pluggable storage implementations

---

## Legacy Libraries

### Brancher Library (`brancher_lib/`)

**Purpose**: Legacy branching operations library.

**Status**: Deprecated - Use `core/services/branching/` instead

### Projector Library (`projector_lib/`)

**Purpose**: Legacy projection operations library.

**Status**: Deprecated - Use `core/services/projection/` instead

---

## Design Principles

1. **Repository Pattern**: Consistent data access abstraction
2. **Protocol-Based Design**: Type-safe interfaces
3. **Storage Agnostic**: Abstract storage implementation details
4. **Performance First**: Caching and optimization throughout
5. **Transaction Safety**: ACID compliance where needed
6. **Monitoring**: Comprehensive query and performance tracking

## Transaction Management

### ACID Compliance
- **Atomicity**: Operations complete fully or not at all
- **Consistency**: Data integrity maintained across storage systems
- **Isolation**: Concurrent operations don't interfere
- **Durability**: Committed changes persist through failures

### Cross-Storage Consistency
- Two-phase commit for multi-storage transactions
- Compensation patterns for rollback scenarios
- Event sourcing for audit trails
- Eventual consistency where appropriate

## Performance Optimization

### Caching Strategy
- **Multi-level Caching**: Memory, Redis, and application-level caches
- **Cache Invalidation**: Smart invalidation based on data dependencies
- **Cache Warming**: Preload frequently accessed data
- **Performance Monitoring**: Track cache hit rates and query performance

### Query Optimization
- **Index Management**: Automatic index creation and optimization
- **Query Planning**: Analyze and optimize query execution
- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Group operations for better performance

## Integration Points

- **Services Layer**: Repositories accessed through service facades
- **Domain Models**: Direct mapping between models and storage
- **Caching**: Transparent caching integration
- **Monitoring**: Performance tracking and alerting
- **Search**: Integration with full-text and vector search

## Error Handling

- **Graceful Degradation**: Continue operating with reduced functionality
- **Retry Logic**: Automatic retry for transient failures
- **Circuit Breakers**: Prevent cascade failures
- **Comprehensive Logging**: Track all errors and performance issues
