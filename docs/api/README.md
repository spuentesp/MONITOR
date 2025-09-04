# MONITOR Core API Documentation

## Overview

This directory contains comprehensive API documentation for all modules in the MONITOR core system. Each document provides detailed information about classes, methods, responsibilities, and integration patterns for different parts of the codebase.

## Architecture Overview

MONITOR is a multi-agent narrative intelligence system built with a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACES LAYER                         │
│  APIs, CLI, Web UI - External access points                │
├─────────────────────────────────────────────────────────────┤
│                     AGENTS LAYER                           │
│  Narrator, Steward, Archivist - AI personalities          │
├─────────────────────────────────────────────────────────────┤
│                     ENGINE LAYER                           │
│  LangGraph flows, Tools, Orchestration                    │
├─────────────────────────────────────────────────────────────┤
│                    SERVICES LAYER                          │
│  Business logic, Cross-cutting concerns                   │
├─────────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                           │
│  Core models, Business rules, Entities                    │
├─────────────────────────────────────────────────────────────┤
│                  PERSISTENCE LAYER                         │
│  Repositories, Storage abstraction                        │
├─────────────────────────────────────────────────────────────┤
│                   GENERATION LAYER                         │
│  LLM integration, Providers, Mocking                      │
├─────────────────────────────────────────────────────────────┤
│                    UTILITIES LAYER                         │
│  Shared helpers, Environment, Data operations             │
└─────────────────────────────────────────────────────────────┘
```

## Documentation Structure

### 📚 [Domain Models](domain.md)
**Core narrative data structures and business entities**
- Hierarchy models (Omniverse → Multiverse → Universe → Story → Scene)
- Entity models (Characters, locations, concepts)
- Event and fact tracking
- System and character sheet integration
- Narrative content models for rich storytelling

### 🤖 [Agents](agents.md)
**Multi-agent AI system for collaborative storytelling**
- Base agent framework and configuration
- Specialized narrative agents (Narrator, Character, Director)
- Quality assurance agents (Steward, Continuity, Critic)
- Information management agents (Archivist, Librarian, Monitor)
- Workflow coordination agents (Conductor, Planner, Resolver)

### ⚙️ [Engine](engine.md)
**Runtime execution and workflow orchestration**
- LangGraph flow construction and management
- Tool integration and execution
- Context management and state tracking
- Event handling and processing
- Caching and performance optimization

### 🔧 [Services](services.md)
**High-level business logic and coordination**
- Query service for unified data access
- Narrative content service for rich MongoDB content
- Branching services for timeline management
- Projection services for data transformation
- Specialized services for indexing and retrieval

### 💾 [Persistence](persistence.md)
**Data storage and retrieval layer**
- Repository pattern implementation
- Neo4j graph database operations
- MongoDB document storage
- Vector search with Qdrant
- Query management and optimization

### 🎭 [Generation](generation.md)
**Language model integration and AI text generation**
- LLM provider abstraction
- Support for multiple AI services (OpenAI, Anthropic, local models)
- Mock implementations for testing
- Configuration and performance management

### 🌐 [Interfaces](interfaces.md)
**External APIs and user interfaces**
- REST API for programmatic access
- CLI for administration and development
- Specialized APIs for branching and workflow modes
- Security and performance considerations

### 🛠️ [Utils](utils.md)
**Shared utilities and cross-cutting concerns**
- Environment variable management
- Data merging and manipulation utilities
- Persistence helpers and serialization
- Common patterns and reusable components

## Key Design Principles

### 1. **Single Responsibility**
Each module has a clear, focused purpose without overlapping concerns.

### 2. **Composition over Inheritance**
Complex functionality built through composition of simple services rather than inheritance hierarchies.

### 3. **Protocol-Based Design**
Type-safe interfaces define contracts between components, enabling easy testing and swapping of implementations.

### 4. **Domain-Driven Design**
Rich domain models capture business logic, with services orchestrating complex operations.

### 5. **Hexagonal Architecture**
Core business logic isolated from external concerns through well-defined ports and adapters.

### 6. **Multi-Agent Intelligence**
Specialized AI agents collaborate through structured workflows to create coherent narratives.

## Integration Patterns

### Agent Integration
```python
# Agents coordinate through LangGraph workflows
narrator = narrator_agent(llm)
steward = steward_agent(llm)

flow = build_langgraph_flow({"narrator": narrator, "steward": steward})
result = flow.invoke({"intent": "describe scene", "universe_id": "u1"})
```

### Service Composition
```python
# Services compose for complex operations
query_service = QueryService(neo4j_repo, mongo_store)
content_service = NarrativeContentService(mongo_store)
context_provider = NarrativeContextProvider(query_service, content_service)

context = context_provider.get_comprehensive_context(universe_id, story_id)
```

### Data Flow
```
User Request → Interface → Engine → Agents → Services → Domain → Persistence
           ← Response ← Results ← Output ← Data ← Models ← Storage
```

## Performance Characteristics

### Caching Strategy
- **Multi-level caching**: Memory, Redis, application-level
- **Smart invalidation**: Based on data dependencies
- **Cache warming**: Preload frequently accessed data

### Database Optimization
- **Connection pooling**: Efficient database connections
- **Query optimization**: Indexed queries and batch operations
- **Multi-storage coordination**: Consistent data across Neo4j and MongoDB

### Agent Coordination
- **Parallel execution**: Agents work concurrently where possible
- **Workflow optimization**: Efficient LangGraph flow construction
- **Context sharing**: Minimize redundant data loading

## Testing Strategy

### Unit Testing
- **Protocol mocking**: Easy mocking through protocol interfaces
- **Service isolation**: Test services independently
- **Domain validation**: Comprehensive domain model testing

### Integration Testing
- **End-to-end workflows**: Test complete narrative generation flows
- **Database integration**: Test with real database implementations
- **Agent coordination**: Verify multi-agent interactions

### Performance Testing
- **Load testing**: Verify system performance under load
- **Memory profiling**: Optimize memory usage patterns
- **Database performance**: Query optimization and indexing

## Development Workflow

### Adding New Features
1. **Domain modeling**: Define new domain entities if needed
2. **Service implementation**: Create services for business logic
3. **Agent integration**: Add or modify agents for AI functionality
4. **Interface exposure**: Expose through appropriate interfaces
5. **Testing**: Comprehensive testing at all layers

### Debugging
1. **Monitor integration**: Use Monitor agent for system health
2. **Comprehensive logging**: Detailed logging at service boundaries
3. **Error propagation**: Clear error handling and reporting
4. **Performance monitoring**: Track performance metrics

### Deployment
1. **Environment configuration**: Use environment utilities for config
2. **Database migration**: Handle schema changes gracefully
3. **Service coordination**: Ensure proper service startup order
4. **Health checks**: Implement comprehensive health monitoring

## Getting Started

### For New Developers
1. Start with [Domain Models](domain.md) to understand the core concepts
2. Review [Agents](agents.md) to understand the AI architecture
3. Explore [Services](services.md) for business logic patterns
4. Check [Engine](engine.md) for workflow understanding

### For API Users
1. Review [Interfaces](interfaces.md) for API usage patterns
2. Check [Generation](generation.md) for LLM integration
3. Understand [Persistence](persistence.md) for data considerations

### For System Administrators
1. Study [Utils](utils.md) for configuration management
2. Review [Engine](engine.md) for performance tuning
3. Check [Persistence](persistence.md) for database administration

## Contributing

When adding new functionality:
- Follow the established architectural patterns
- Add comprehensive documentation for new classes and methods
- Include examples in the appropriate API documentation
- Update integration patterns when introducing new components
- Maintain backward compatibility where possible

## Support

For questions about specific modules, refer to the detailed documentation in each file. For architectural questions or integration guidance, consult the main ARCHITECTURE.md file in the project root.
