# Core Agents

## Overview

The `core/agents/` folder contains the multi-agent system that powers the narrative intelligence of MONITOR. Each agent has a specialized role in the collaborative storytelling process, working together through LangGraph workflows to create coherent, engaging narratives.

## Architecture Role

Agents form the cognitive layer of the system, each with distinct personalities and responsibilities:
- **Narrative Creation**: Generate story content and respond to player actions
- **Continuity Management**: Ensure consistency across the narrative
- **Quality Assurance**: Validate and improve generated content
- **Context Management**: Track and organize narrative information
- **Flow Control**: Route requests and coordinate agent interactions

## Base Infrastructure

### Agent (`base.py`)

**Purpose**: Core agent framework providing LLM integration and message handling.

**Classes**:

#### AgentConfig
**Purpose**: Configuration container for agent initialization.

**Fields**:
- `name: str` - Agent identifier
- `system_prompt: str` - Core personality and instruction prompt
- `llm: LLM` - Language model instance
- `temperature: float` - Response creativity (default: 0.7)
- `max_tokens: int` - Response length limit (default: 400)

#### Agent
**Purpose**: Base agent implementation with LLM interaction capabilities.

**Methods**:
- `__init__(config: AgentConfig)` - Initialize with configuration
- `name: str` (property) - Get agent name
- `act(messages: list[Message]) -> str` - Generate response to message sequence

#### Session
**Purpose**: In-memory multi-agent conversation session manager.

**Fields**:
- `primary: Agent` - Main agent for the session
- `history: list[Message]` - Conversation history

**Methods**:
- `user(content: str)` - Add user message to history
- `system(content: str)` - Add system message to history
- `step() -> str` - Execute one agent response cycle

---

## Narrative Agents

### Narrator (`narrator.py`)

**Purpose**: Primary storytelling agent responsible for scene description and player interaction.

**Functions**:
- `narrator_agent(llm) -> Agent` - Factory function for narrator initialization

**Characteristics**:
- Temperature: 0.8 (creative but coherent)
- Max tokens: 350 (concise responses)
- Focus: Sensory descriptions, scene continuity, guiding questions

**Responsibilities**:
- Generate scene descriptions and environmental details
- Respond to player actions with immediate consequences
- Ask guiding questions to drive narrative forward
- Maintain focus on current scene without unauthorized changes

### Character (`character.py`)

**Purpose**: Role-playing agent for non-player characters and entity representation.

**Responsibilities**:
- Embody specific characters within the narrative
- Maintain character consistency and personality
- Generate character dialogue and actions
- React authentically to story events

### Director (`director.py`)

**Purpose**: High-level narrative orchestration and pacing management.

**Responsibilities**:
- Oversee story arc development and progression
- Manage narrative pacing and dramatic tension
- Coordinate between different story elements
- Ensure overall narrative coherence and engagement

---

## Quality and Continuity Agents

### Steward (`steward.py`)

**Purpose**: Continuity guardian ensuring narrative consistency and world-building accuracy.

**Responsibilities**:
- Validate narrative consistency against established facts
- Prevent contradictions and continuity errors
- Maintain world-building integrity
- Flag potential consistency issues for review

### Continuity (`continuity.py`)

**Purpose**: Specialized continuity tracking for character and plot elements.

**Responsibilities**:
- Track character development and state changes
- Monitor plot thread progression and resolution
- Ensure character actions align with established personality
- Maintain relationship consistency between entities

### Critic (`critic.py`)

**Purpose**: Quality assurance agent for narrative content evaluation.

**Responsibilities**:
- Evaluate narrative quality and engagement
- Suggest improvements for story content
- Assess character development effectiveness
- Provide feedback on pacing and structure

### QA (`qa.py`)

**Purpose**: Quality assurance coordinator for multi-agent validation.

**Responsibilities**:
- Coordinate quality checks across multiple agents
- Aggregate feedback and validation results
- Ensure content meets quality standards
- Manage revision and improvement workflows

---

## Information Management Agents

### Archivist (`archivist.py`)

**Purpose**: Narrative history and information preservation specialist.

**Responsibilities**:
- Maintain comprehensive narrative archives
- Track important events and milestones
- Preserve character development history
- Manage story element documentation

### Librarian (`librarian.py`)

**Purpose**: Information retrieval and knowledge management agent.

**Responsibilities**:
- Retrieve relevant narrative context and history
- Search and organize story information
- Provide agents with necessary background context
- Maintain information organization and accessibility

### Monitor (`monitor.py`)

**Purpose**: System monitoring and performance tracking agent.

**Responsibilities**:
- Monitor agent performance and system health
- Track narrative flow effectiveness
- Identify bottlenecks and optimization opportunities
- Provide system diagnostics and reporting

---

## Workflow and Coordination Agents

### Conductor (`conductor.py`)

**Purpose**: Agent coordination and workflow orchestration.

**Responsibilities**:
- Coordinate multi-agent interactions
- Manage agent sequencing and handoffs
- Ensure proper workflow execution
- Handle agent communication and synchronization

### Intent Router (`intent_router.py`)

**Purpose**: Request analysis and agent routing specialist.

**Responsibilities**:
- Analyze user intents and requests
- Route requests to appropriate agents
- Determine required agent combinations
- Optimize workflow paths for efficiency

### Planner (`planner.py`)

**Purpose**: Strategic planning and goal-oriented agent coordination.

**Responsibilities**:
- Plan multi-step narrative operations
- Coordinate complex agent workflows
- Manage long-term narrative goals
- Optimize agent resource allocation

### Resolve (`resolve.py`)

**Purpose**: Conflict resolution and decision arbitration agent.

**Responsibilities**:
- Resolve conflicts between agent recommendations
- Make final decisions when agents disagree
- Ensure coherent final outputs
- Handle edge cases and exceptions

---

## Utility and Factory Components

### Factory (`factory.py`)

**Purpose**: Agent creation and configuration management.

**Responsibilities**:
- Provide standardized agent creation patterns
- Manage agent configuration templates
- Handle agent initialization and setup
- Support agent customization and specialization

## Design Principles

1. **Single Responsibility**: Each agent has a clear, focused role
2. **Collaborative Intelligence**: Agents work together rather than in isolation
3. **Modularity**: Agents can be combined and reconfigured for different workflows
4. **Consistency**: All agents follow the same base interface and patterns
5. **Specialization**: Agents are optimized for their specific narrative functions
6. **Extensibility**: New agents can be added without disrupting existing ones

## Usage Patterns

### Agent Creation
```python
# Standard agent creation
narrator = narrator_agent(llm_instance)

# Custom agent creation
config = AgentConfig(
    name="Custom",
    system_prompt="You are a specialized agent...",
    llm=llm_instance,
    temperature=0.6,
    max_tokens=500
)
custom_agent = Agent(config)
```

### Session Management
```python
# Create session with primary agent
session = Session(primary=narrator)

# Add messages and process
session.user("What do I see in the tavern?")
response = session.step()
```

### Multi-Agent Coordination
- Agents coordinate through LangGraph workflows
- Each agent contributes specialized expertise
- Final output represents collaborative intelligence
- Conflicts resolved through designated arbitration agents

## Integration Points

- **LLM Providers**: Configurable language model backends
- **LangGraph**: Workflow orchestration and coordination
- **Domain Models**: Direct access to narrative entities and state
- **Persistence**: Integration with MongoDB and Neo4j storage
- **Tools**: Access to narrative manipulation and query tools
