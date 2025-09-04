# Core Domain Models

## Overview

The `core/domain/` folder contains the foundational data models that represent the core narrative and world-building concepts in the MONITOR system. These models use Pydantic for type safety and validation, forming the backbone of the multi-dimensional storytelling framework.

## Architecture Role

The domain models define the semantic structure of the narrative universe hierarchy:
- **Omniverse** → **Multiverse** → **Universe** → **Story** → **Scene**
- **Entities** (characters, places, concepts) that exist within these contexts
- **Facts** and **Events** that drive narrative progression
- **Systems** that define game mechanics and rules

## Base Model

### BaseModel (`base_model.py`)

**Purpose**: Custom Pydantic base class with project-specific configuration.

**Configuration**:
- `arbitrary_types_allowed=True` - Allows complex Python objects as field types

---

## Hierarchy Models

### Omniverse (`omniverse.py`)

**Purpose**: Top-level container for all multiverses in the system.

**Fields**:
- `id: str` - Unique identifier
- `name: str` - Human-readable name
- `description: str | None` - Optional description
- `multiverses: list[Multiverse]` - Child multiverses

### Multiverse (`multiverse.py`)

**Purpose**: Container for related universes sharing common axioms and archetypes.

**Fields**:
- `id: str` - Unique identifier (auto-generated UUID)
- `name: str` - Human-readable name
- `description: str | None` - Optional description
- `universes: list[Universe]` - Child universes
- `omniverse_id: str | None` - Parent omniverse reference
- `axioms: list[Axiom]` - Shared fundamental rules
- `archetypes: list[ArchetypeEntity]` - Shared entity templates

### Universe (`universe.py`)

**Purpose**: Specific world/reality instance containing stories and entities.

**Key Methods**:
- Entity management (add/remove entities)
- Story lifecycle management
- System integration for game mechanics

### Story (`story.py`)

**Purpose**: Narrative arc within a universe containing scenes and character development.

**Key Methods**:
- Scene sequencing and management
- Character arc tracking
- Plot thread maintenance

### Scene (`scene.py`)

**Purpose**: Individual narrative moment or interaction within a story.

**Key Methods**:
- Entity interaction recording
- Event capture and processing
- Context state management

---

## Entity Models

### ArchetypeEntity (`entity.py`)

**Purpose**: Template/prototype for entities that can be instantiated across universes.

**Fields**:
- `id: str` - Unique identifier
- `name: str` - Human-readable name
- `description: str | None` - Optional description
- `type: str` - Entity category (default: "concept")
- `attributes: dict[str, str]` - Key-value properties
- `relations: dict[str, str]` - Relationships to other archetypes

**Use Cases**:
- Character archetypes (Hero, Villain, Mentor)
- Location templates (Tavern, Castle, Forest)
- Concept definitions (Magic, Technology, Politics)

### ConcreteEntity (`entity.py`)

**Purpose**: Actual instance of an entity within a specific universe.

**Fields**:
- `id: str` - Unique identifier
- `name: str` - Human-readable name
- `universe_id: str` - Parent universe reference
- `archetype_id: str | None` - Source archetype reference
- `type: str` - Entity category (default: "manifestation")
- `attributes: dict[str, str]` - Instance-specific properties
- `story: list[str]` - Event/observation history
- `relations: dict[str, str]` - Relationships to other concrete entities
- `system_id: str | None` - Associated game system
- `sheets: list[Sheet]` - Character/stat sheets

**Configuration**:
- `arbitrary_types_allowed=True` - Allows complex Sheet objects

---

## Narrative Content Models

### NarrativeContent (`narrative_content.py`)

**Purpose**: Rich narrative content for enhanced storytelling and AI context.

**Models Include**:
- `EntityDescription` - Detailed character/location descriptions
- `ChatLog` - Conversation and dialogue history
- `SceneAbstract` - Scene summaries and mood
- `GMNote` - Game master annotations and secrets
- `NarrativeState` - Current story state and momentum
- `CharacterMemory` - Character-specific memories and perspectives

---

## Event and Fact Models

### Event (`event.py`)

**Purpose**: Represents actions or occurrences within the narrative.

**Key Features**:
- Timestamp tracking
- Entity involvement
- Consequence modeling
- System integration

### Fact (`fact.py`)

**Purpose**: Immutable truth statements about the narrative world.

**Key Features**:
- Truth validation
- Source attribution
- Importance weighting
- Cross-reference capability

---

## System Models

### System (`system.py`)

**Purpose**: Game system definitions and rule frameworks.

**Key Features**:
- Rule set definitions
- Dice mechanics
- Attribute frameworks
- Integration hooks

### Sheet (`sheet.py`)

**Purpose**: Character or entity stat sheets within a system.

**Key Features**:
- Attribute tracking
- Skill management
- System-specific calculations
- Historical state preservation

---

## Supporting Models

### Axiom (`axiom.py`)

**Purpose**: Fundamental rules and constraints that govern a multiverse.

**Key Features**:
- Rule definitions
- Constraint enforcement
- Logic validation
- Inheritance patterns

### Arc (`arc.py`)

**Purpose**: Character or plot development arcs spanning multiple scenes.

**Key Features**:
- Progress tracking
- Milestone definitions
- Character growth
- Plot advancement

### Deltas (`deltas.py`)

**Purpose**: Change tracking and state transitions between narrative states.

**Key Features**:
- State difference calculation
- Change attribution
- Rollback capability
- Audit trail maintenance

---

## Design Principles

1. **Immutability**: Events and facts are immutable once created
2. **Hierarchy**: Clear parent-child relationships maintain narrative context
3. **Flexibility**: Attributes and relations use dictionaries for extensibility
4. **Type Safety**: Pydantic ensures runtime validation and IDE support
5. **Modularity**: Each model has a single, clear responsibility
6. **Integration**: Models support both graph (Neo4j) and document (MongoDB) persistence

## Usage Patterns

- **Creation**: Use factory methods or direct instantiation with validation
- **Persistence**: Models serialize/deserialize automatically for database storage
- **Relationships**: Use ID references for loose coupling between models
- **Evolution**: Attributes dict allows adding new properties without schema changes
- **Validation**: Pydantic automatically validates types and constraints
