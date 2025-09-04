# Core Interfaces

## Overview

The `core/interfaces/` folder contains the external-facing APIs and user interfaces for the MONITOR system. These interfaces provide different ways to interact with the narrative system, from REST APIs to command-line tools.

## Architecture Role

Interfaces serve as the boundary layer between:
- **External Users**: Players, game masters, developers
- **Internal System**: Agents, services, and domain logic
- **Integration**: Other systems and tools
- **User Experience**: Different interaction modalities

---

## Core Interface Components

### API Interface (`api_interface.py`)

**Purpose**: REST API endpoints for programmatic access to the narrative system.

**Key Features**:
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Communication**: Structured request/response format
- **Authentication**: Secure access control
- **Validation**: Input validation and error handling

**Endpoint Categories**:
- **Universe Management**: Create, read, update universes
- **Story Operations**: Story creation and progression
- **Entity Management**: Character and location operations
- **Narrative Generation**: AI-powered content creation

### CLI Interface (`cli_interface.py`)

**Purpose**: Command-line interface for developers and administrators.

**Key Commands**:
- **Setup Commands**: Initialize new multiverses and universes
- **Development Tools**: Testing and debugging utilities
- **Administration**: System maintenance and monitoring
- **Import/Export**: Data migration and backup operations

**Features**:
- **Interactive Mode**: Step-by-step guidance for complex operations
- **Batch Mode**: Script-friendly automation support
- **Progress Indicators**: Visual feedback for long-running operations
- **Error Reporting**: Detailed error messages and suggestions

### Branches API (`branches_api.py`)

**Purpose**: Specialized API for universe branching and timeline management.

**Key Operations**:
- **Branch Creation**: Create parallel universe timelines
- **Branch Management**: List, compare, and merge branches
- **Decision Points**: Mark and track branching decisions
- **Timeline Analysis**: Analyze differences between branches

### LangGraph Modes API (`langgraph_modes_api.py`)

**Purpose**: API for different narrative generation modes and workflows.

**Features**:
- **Mode Selection**: Choose different agent coordination patterns
- **Workflow Customization**: Configure agent behavior and priorities
- **Performance Tuning**: Optimize for different use cases
- **Experimental Features**: Access to beta and experimental capabilities

---

## Persistence Interface (`persistence/`)

**Purpose**: Specialized interfaces for data import/export and persistence operations.

**Key Components**:
- **Data Import**: Bulk data import from external sources
- **Data Export**: Export narrative data for backup or migration
- **Format Conversion**: Convert between different data formats
- **Validation**: Ensure data integrity during operations

---

## Design Principles

1. **Consistency**: Uniform interface patterns across all endpoints
2. **Security**: Authentication and authorization throughout
3. **Performance**: Optimized for responsive user experience
4. **Documentation**: Comprehensive API documentation and examples
5. **Versioning**: Backward compatibility and graceful evolution
6. **Error Handling**: Clear error messages and recovery guidance

## Integration Patterns

### REST API Usage
```python
# Create a new universe
POST /api/v1/universes
{
    "name": "Fantasy Campaign",
    "description": "Epic fantasy adventure",
    "system_id": "dnd5e"
}

# Generate narrative content
POST /api/v1/universes/{id}/generate
{
    "intent": "describe tavern",
    "context": {"scene_id": "scene_001"}
}
```

### CLI Usage
```bash
# Initialize new campaign
monitor init --universe "Space Opera" --system "scifi"

# Import existing data
monitor import --file campaign_data.json --universe space_opera

# Generate content
monitor generate --intent "describe alien marketplace" --context space_station
```

## Security Considerations

- **Authentication**: Token-based authentication for API access
- **Authorization**: Role-based access control
- **Rate Limiting**: Prevent abuse and ensure fair usage
- **Input Validation**: Sanitize all inputs to prevent injection attacks
- **Audit Logging**: Track all interface interactions

## Performance Optimization

- **Caching**: Cache frequently accessed data
- **Pagination**: Handle large datasets efficiently  
- **Compression**: Compress responses to reduce bandwidth
- **Async Operations**: Non-blocking operations for better responsiveness
