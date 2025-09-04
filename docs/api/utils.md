# Core Utilities

## Overview

The `core/utils/` folder contains shared utility functions and helper modules used throughout the MONITOR system. These utilities provide common functionality for environment management, data persistence, and object merging.

## Architecture Role

Utilities provide:
- **Cross-Cutting Concerns**: Functionality needed across multiple modules
- **Environment Management**: Configuration and environment variable handling
- **Data Operations**: Common data manipulation and persistence helpers
- **Code Reuse**: Prevent duplication of common functionality

---

## Core Utility Modules

### Environment Utils (`env.py`)

**Purpose**: Environment variable management and configuration utilities.

**Key Functions**:
- `env_str(name, default=None, lower=False)` - Get string environment variable
- `env_bool(name, default=False)` - Get boolean environment variable with flexible parsing
- `env_int(name, default=0)` - Get integer environment variable
- `env_list(name, separator=",", default=None)` - Parse list from environment variable

**Features**:
- **Type Conversion**: Automatic type conversion with validation
- **Default Values**: Sensible defaults for all configuration
- **Boolean Parsing**: Flexible boolean parsing ("true", "1", "yes", etc.)
- **Case Handling**: Optional case conversion for strings

**Usage Examples**:
```python
# String configuration
database_url = env_str("DATABASE_URL", "mongodb://localhost:27017")

# Boolean flags
debug_mode = env_bool("DEBUG", False)  # Accepts "true", "1", "yes"
verbose_logging = env_bool("VERBOSE", True)

# Integer configuration
max_retries = env_int("MAX_RETRIES", 3)

# List configuration
allowed_origins = env_list("CORS_ORIGINS", default=["localhost"])
```

### Merge Utils (`merge.py`)

**Purpose**: Deep merging and data combination utilities.

**Key Functions**:
- `deep_merge(dict_a, dict_b)` - Deep merge two dictionaries
- `merge_lists(list_a, list_b, unique=True)` - Combine lists with deduplication
- `merge_objects(obj_a, obj_b)` - Merge domain objects intelligently

**Features**:
- **Deep Merging**: Recursive merging of nested structures
- **Conflict Resolution**: Configurable strategies for handling conflicts
- **Type Preservation**: Maintain original types during merging
- **Validation**: Ensure merged results are valid

**Use Cases**:
- Configuration merging from multiple sources
- Combining partial domain objects
- Merging user preferences with defaults
- Aggregating data from multiple services

### Persistence Utils (`persist.py`)

**Purpose**: Common persistence operations and data handling utilities.

**Key Functions**:
- `serialize_object(obj)` - Convert objects to serializable format
- `deserialize_object(data, target_type)` - Reconstruct objects from data
- `validate_data(data, schema)` - Validate data against schema
- `normalize_ids(obj)` - Ensure consistent ID formatting

**Features**:
- **Object Serialization**: Handle complex objects and relationships
- **Type Safety**: Maintain type information during serialization
- **Validation**: Ensure data integrity before persistence
- **ID Normalization**: Consistent identifier formatting

**Integration Points**:
- Domain model serialization
- Database operation helpers
- API request/response handling
- Cache serialization

---

## Design Principles

1. **Reusability**: Functions designed for use across multiple modules
2. **Type Safety**: Strong typing and validation throughout
3. **Performance**: Optimized for common operations
4. **Flexibility**: Configurable behavior for different use cases
5. **Error Handling**: Graceful handling of edge cases
6. **Documentation**: Clear documentation with examples

## Common Patterns

### Configuration Management
```python
# Environment-based configuration with defaults
class ServiceConfig:
    def __init__(self):
        self.host = env_str("SERVICE_HOST", "localhost")
        self.port = env_int("SERVICE_PORT", 8080)
        self.debug = env_bool("DEBUG", False)
        self.features = env_list("ENABLED_FEATURES", ["auth", "logging"])
```

### Data Merging
```python
# Merge user preferences with system defaults
user_prefs = load_user_preferences(user_id)
system_defaults = load_system_defaults()
final_config = deep_merge(system_defaults, user_prefs)
```

### Object Persistence
```python
# Serialize domain objects for storage
universe_data = serialize_object(universe)
store_data(universe_data)

# Deserialize from storage
stored_data = load_data(universe_id)
universe = deserialize_object(stored_data, Universe)
```

## Error Handling

### Environment Variables
- Validation of required variables
- Type conversion error handling
- Default value fallbacks
- Clear error messages for configuration issues

### Data Operations
- Schema validation before processing
- Type checking during merging
- Graceful handling of malformed data
- Detailed error reporting for debugging

## Performance Considerations

- **Caching**: Cache expensive operations like environment variable parsing
- **Lazy Evaluation**: Load configuration only when needed
- **Memory Efficiency**: Optimize for large data structures
- **Validation Costs**: Balance validation thoroughness with performance

## Testing Support

- **Mock Environment**: Easy environment variable mocking for tests
- **Test Data**: Utilities for generating test data
- **Validation Testing**: Test data validation scenarios
- **Performance Testing**: Benchmark utility functions
