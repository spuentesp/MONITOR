# Test Architecture Restructure Plan

## Proposed Test Structure (Aligned with SOLID Architecture)

```
tests/
├── conftest.py                    # Global fixtures and configuration
├── fixtures/                     # Shared test data and builders
│   ├── __init__.py
│   ├── domain_fixtures.py        # Pydantic model builders
│   ├── context_fixtures.py       # ToolContext and component builders
│   ├── mock_services.py          # Service layer mocks
│   └── test_data.py              # Static test data
├── unit/                         # Fast, isolated tests
│   ├── domain/                   # Pure business logic tests
│   │   ├── test_base_model.py
│   │   ├── test_deltas.py
│   │   └── test_validators.py
│   ├── ports/                    # Interface contract tests
│   │   ├── test_repository_interface.py
│   │   ├── test_segregated_interfaces.py
│   │   └── test_service_interfaces.py
│   ├── services/                 # Service layer tests
│   │   ├── test_narrative_service.py
│   │   ├── test_embedding_service.py
│   │   └── test_indexing_service.py
│   ├── persistence/              # Data access layer tests
│   │   ├── test_base_repository.py
│   │   ├── test_entity_repository.py
│   │   ├── test_fact_repository.py
│   │   ├── test_segregated_adapters.py
│   │   └── test_query_builders.py
│   ├── agents/                   # Agent behavior tests
│   │   ├── test_agent_registry.py
│   │   ├── test_narrator_agent.py
│   │   ├── test_director_agent.py
│   │   └── test_steward_agent.py
│   ├── engine/                   # Orchestration engine tests
│   │   ├── context/
│   │   │   ├── test_tool_context.py
│   │   │   ├── test_context_builder.py
│   │   │   ├── test_database_context.py
│   │   │   ├── test_cache_context.py
│   │   │   └── test_service_context.py
│   │   ├── modes/
│   │   │   ├── test_graph_state.py
│   │   │   ├── test_router.py
│   │   │   ├── test_monitor_node.py
│   │   │   └── test_narrator_node.py
│   │   └── flows/
│   │       ├── test_graph_builder.py
│   │       └── test_flow_execution.py
│   ├── generation/               # LLM provider tests
│   │   ├── test_mock_llm.py
│   │   ├── test_openai_provider.py
│   │   └── test_provider_selection.py
│   └── config/                   # Configuration tests
│       ├── test_service_config.py
│       └── test_tool_context_builder.py
├── integration/                  # Cross-layer integration tests
│   ├── persistence/
│   │   ├── test_repository_integration.py
│   │   └── test_query_integration.py
│   ├── engine/
│   │   ├── test_langgraph_flow.py
│   │   └── test_agent_orchestration.py
│   ├── api/
│   │   ├── test_endpoints.py
│   │   └── test_api_integration.py
│   └── cli/
│       └── test_cli_commands.py
├── e2e/                          # End-to-end scenario tests
│   ├── test_story_creation.py
│   ├── test_narrative_flow.py
│   └── test_multiverse_branching.py
└── performance/                  # Performance and load tests
    ├── test_agent_performance.py
    └── test_repository_performance.py
```

## Test Categories

### Unit Tests (Fast, Isolated)
- **Domain**: Pure business logic, no I/O dependencies
- **Ports**: Interface contracts and protocols
- **Services**: Business logic with mocked dependencies
- **Persistence**: Repository patterns with mocked databases
- **Agents**: Agent behavior with mocked LLMs
- **Engine**: Orchestration logic with mocked contexts
- **Generation**: LLM providers with API mocks
- **Config**: Configuration building and validation

### Integration Tests (Cross-Layer)
- **Persistence**: Real database interactions
- **Engine**: Multi-agent coordination
- **API**: HTTP endpoint testing
- **CLI**: Command-line interface testing

### E2E Tests (Full System)
- **Story Creation**: Complete narrative workflows
- **Multiverse Branching**: Complex scenario testing

### Performance Tests
- **Load Testing**: System under stress
- **Performance Profiling**: Resource usage analysis

## Key Design Principles

1. **Layer Alignment**: Tests mirror architectural boundaries
2. **Dependency Injection**: All tests use proper mocking/fixtures
3. **Fast Feedback**: Unit tests run in <100ms each
4. **Clear Scope**: Each test file has single responsibility
5. **Reusable Fixtures**: Shared builders for common objects
6. **Mock Strategies**: Interface-based mocking aligned with DIP

## Migration Strategy

1. **Phase 1**: Create new structure and fixtures
2. **Phase 2**: Migrate unit tests by architectural layer
3. **Phase 3**: Update integration tests for new components
4. **Phase 4**: Add missing coverage for SOLID components
5. **Phase 5**: Validate and optimize test performance