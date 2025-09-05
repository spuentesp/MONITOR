# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing & Quality
```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=core --cov-report=term-missing

# Run specific test markers
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests only
python -m pytest -m e2e           # End-to-end tests only

# Type checking
python -m mypy core/ --ignore-missing-imports

# Code formatting and linting
ruff check core/
ruff format core/

# Import linting (enforces layered architecture)
import-linter --config importlinter.ini
```

### Development Server
```bash
# Start all services (Neo4j, API, Streamlit UI)
./run-dev.sh up

# Check service status
./run-dev.sh status

# View logs
./run-dev.sh logs

# Stop all services
./run-dev.sh down
```

### Individual Services
```bash
# Start Docker services only
docker compose up -d

# API server (FastAPI)
uvicorn core.interfaces.api_interface:app --host 0.0.0.0 --port 8000 --reload

# Frontend UI (Streamlit)  
streamlit run frontend/Chat.py --server.address=0.0.0.0 --server.port=8501
```

## Architecture Overview

### Layered Architecture (Enforced by Import Linter)
- **domain** - Pure business models (Pydantic), no I/O dependencies
- **ports** - Interface definitions for external capabilities  
- **services** - Composition-based business logic layer
- **persistence** - Database adapters (Neo4j, MongoDB, Redis, etc.)
- **generation** - LLM providers and model configurations
- **agents** - Specialized AI behavior policies
- **engine** - Multi-agent orchestration (LangGraph flows)
- **interfaces** - API endpoints and user interfaces

### Core Ontology
```
Omniverse → Multiverse → Universe → Story → Scene → Facts
```

### Multi-Database Strategy
- **Neo4j**: Graph spine (entities, relations, temporal facts, story hierarchy)
- **MongoDB**: Narrative content (descriptions, dialogue, notes, character memory)
- **Qdrant/OpenSearch**: Semantic search and content indexing
- **MinIO**: Binary asset storage (PDFs, images, documents)
- **Redis**: Caching and session state

### Multi-Agent System
- **Director**: High-level narrative coordination
- **Librarian**: Evidence gathering and context retrieval
- **Steward**: Validation, continuity, and consistency enforcement  
- **Narrator**: Context-aware narrative content generation
- **Planner**: Action planning and execution coordination
- **Critic**: Quality assessment and content refinement
- **Archivist**: Content indexing and memory management

## Key Patterns

### Service Composition
The codebase uses composition over inheritance for service architecture:
- Services are composed from injected dependencies via ports
- Avoid complex mixin hierarchies - use clear service boundaries
- Repository patterns for data access, service facades for business logic

### Pydantic-First Data Flow
- **Canonical**: Pydantic models are the source of truth
- **Validation**: LangGraph nodes extract → validate → persist via Recorder/Projector
- **YAML**: Used only for config/prompts/fixtures, not canonical data

### Type Safety Requirements
- All code must pass `mypy` type checking
- Use Pydantic models for data validation
- Follow strict typing patterns throughout

### Persistence Policy
- **Write Flow**: Domain validation → Agent processing → Projection → Memory update → Indexing
- **Read Flow**: Context query → Memory integration → Agent enrichment → Adaptive response
- **Staging**: In-memory + Redis staging for uncommitted changes

## Configuration

### Environment Variables
```bash
# Database connections
NEO4J_URI=bolt://localhost:7687
MONGODB_URI=mongodb://localhost:27017  
REDIS_URL=redis://localhost:6379

# Agent behavior
MONITOR_PERSONA=guardian
MONITOR_VERBOSE_TASKS=true
MONITOR_AGENTIC_STRICT=false

# Engine configuration
MONITOR_ENGINE_BACKEND=langgraph
MONITOR_COPILOT_PAUSE=false
MONITOR_LC_TOOLS=false

# LLM backends
MONITOR_LLM_BACKEND=openai  # or groq, mock
OPENAI_API_KEY=sk-...
MONITOR_OPENAI_MODEL=gpt-4o-mini
```

### Docker Services
Standard stack includes Neo4j, MongoDB, Qdrant, OpenSearch, MinIO, Redis. All configured in `docker-compose.yml` with sensible defaults for local development.

## API Architecture

### LangGraph Modes Router
- **Endpoints**: `/api/langgraph/modes/{chat,help}`
- **Modes**: `copilot` (assisted) vs `autopilot` (autonomous)
- **Sessions**: Stateful context across multi-turn interactions

### Branch Management
- **Branching**: `/api/branches/branch-at-scene` for timeline splits
- **Cloning**: `/api/branches/clone` for universe duplication
- **Diffing**: `/api/branches/{source}/diff/{target}` for change analysis
- **Promotion**: `/api/branches/promote` for merging changes back

## Testing Guidelines

### Test Organization
- **Unit tests**: Fast, isolated business logic tests
- **Integration tests**: Cross-component interaction tests  
- **E2E tests**: Full system workflow tests with external dependencies

### Test Markers
Use pytest markers for selective test execution:
```python
@pytest.mark.unit
@pytest.mark.integration  
@pytest.mark.e2e
```

## Performance Considerations

### Caching Strategy
- Redis for session state and frequently accessed data
- In-memory staging for uncommitted narrative changes
- Lazy loading for large graph traversals

### Search Optimization
- Hybrid search: Full-text (OpenSearch) + semantic (Qdrant)
- Scoped metadata for universe/story/scene filtering
- Efficient embedding pipelines for document ingestion

## Development Workflows

### Adding New Agents
1. Implement in `core/agents/` following existing patterns
2. Register in orchestration flows (`core/engine/`)
3. Add appropriate tests with mocked dependencies
4. Update agent documentation

### Extending Ontology
1. Add/modify Pydantic models in `core/domain/`
2. Update projection services in `core/services/projection/`
3. Migrate existing data if needed
4. Update validation logic in Steward agent

### Database Schema Changes
1. Neo4j: Update projection services and Cypher queries
2. MongoDB: Modify document models and content services
3. Test migrations with sample data
4. Update API documentation