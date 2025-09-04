# Core Generation

## Overview

The `core/generation/` folder contains the language model integration layer that provides AI text generation capabilities for the narrative system. This includes LLM abstractions, provider implementations, and testing utilities.

## Architecture Role

The generation layer provides:
- **LLM Abstraction**: Unified interface for different language model providers
- **Provider Management**: Support for multiple AI service providers
- **Testing Support**: Mock implementations for testing and development
- **Configuration Management**: Flexible model selection and tuning

---

## Core Interfaces

### LLM Interface (`interfaces/llm.py`)

**Purpose**: Define standard interface for all language model interactions.

**Key Components**:

#### Message Protocol
**Purpose**: Standardized message format for conversations.

```python
Message = dict[str, str]  # {"role": "user|system|assistant", "content": "..."}
```

#### LLM Protocol
**Purpose**: Abstract interface that all LLM providers must implement.

**Required Methods**:
- `complete(system_prompt, messages, temperature, max_tokens) -> str`
  - Generate text completion from conversation history
  - Parameters for creativity control and length limits
  - Consistent interface across providers

**Benefits**:
- **Provider Agnostic**: Switch between different LLM providers easily
- **Type Safety**: Static type checking for LLM interactions
- **Testing**: Easy mocking with consistent interface
- **Configuration**: Unified parameter handling

---

## Provider Implementations

### Providers (`providers.py`)

**Purpose**: Concrete implementations of LLM providers for production use.

**Supported Providers**:
- **OpenAI**: GPT-3.5, GPT-4, and newer models
- **Anthropic**: Claude models
- **Local Models**: Ollama, llama.cpp integration
- **Azure OpenAI**: Enterprise OpenAI deployments

**Key Features**:
- **Automatic Provider Detection**: Based on configuration or environment
- **Error Handling**: Retry logic and fallback strategies
- **Rate Limiting**: Respect provider rate limits
- **Cost Tracking**: Monitor token usage and costs

**Provider Configuration**:
```python
# Environment-based provider selection
provider = get_llm_provider()  # Auto-detects from environment

# Explicit provider configuration
provider = OpenAIProvider(
    model="gpt-4",
    api_key="...",
    temperature=0.7,
    max_tokens=1000
)
```

### Mock LLM (`mock_llm.py`)

**Purpose**: Testing and development implementation that doesn't require real AI services.

**Features**:
- **Deterministic Responses**: Predictable outputs for testing
- **Response Templates**: Pre-configured responses for different scenarios
- **Latency Simulation**: Simulate real provider response times
- **Error Simulation**: Test error handling scenarios

**Key Classes**:

#### MockLLM
**Purpose**: Simple mock that returns configurable responses.

**Methods**:
- `complete(...)` - Returns pre-configured or template-based responses
- `set_response(response)` - Configure next response
- `set_template(template)` - Use response template

#### TemplateMockLLM
**Purpose**: Advanced mock using templates for realistic responses.

**Features**:
- Template-based response generation
- Variable substitution in templates
- Different templates for different agent types
- Realistic response formatting

**Usage Examples**:
```python
# Simple mock for testing
mock = MockLLM()
mock.set_response("A simple test response")

# Template-based mock for realistic testing
template_mock = TemplateMockLLM()
template_mock.set_template("narrator", "You see {location}. {question}")
```

---

## Integration Patterns

### Agent Integration

**Purpose**: How agents use the generation layer.

```python
# Agent configuration with LLM
config = AgentConfig(
    name="Narrator",
    system_prompt="You are a creative storyteller...",
    llm=provider,  # Any LLM implementation
    temperature=0.8,
    max_tokens=350
)

agent = Agent(config)
response = agent.act(messages)
```

### Service Integration

**Purpose**: How services access generation capabilities.

```python
# Service with injected LLM dependency
class NarrativeService:
    def __init__(self, llm: LLM):
        self.llm = llm
    
    def generate_description(self, context):
        return self.llm.complete(
            system_prompt="Generate vivid descriptions...",
            messages=[{"role": "user", "content": context}],
            temperature=0.9,
            max_tokens=200
        )
```

---

## Configuration Management

### Environment Configuration

**Purpose**: Configure LLM providers through environment variables.

**Key Variables**:
- `LLM_PROVIDER` - Which provider to use (openai, anthropic, local)
- `OPENAI_API_KEY` - OpenAI authentication
- `ANTHROPIC_API_KEY` - Anthropic authentication
- `LLM_MODEL` - Specific model selection
- `LLM_TEMPERATURE` - Default creativity setting
- `LLM_MAX_TOKENS` - Default response length

### Dynamic Provider Selection

**Purpose**: Runtime provider switching based on requirements.

```python
# Provider selection based on task requirements
def get_provider_for_task(task_type: str) -> LLM:
    if task_type == "creative_writing":
        return get_creative_provider()  # Higher temperature
    elif task_type == "analysis":
        return get_analytical_provider()  # Lower temperature
    else:
        return get_default_provider()
```

---

## Testing Support

### Test Utilities

**Purpose**: Utilities for testing LLM-dependent code.

**Key Features**:
- **Response Mocking**: Control exactly what the LLM returns
- **Interaction Tracking**: Record all LLM calls for verification
- **Performance Testing**: Simulate different response times
- **Error Testing**: Test error handling without real failures

### Test Patterns

```python
# Unit testing with mocked LLM
def test_agent_response():
    mock = MockLLM()
    mock.set_response("Expected agent response")
    
    agent = Agent(AgentConfig(name="Test", llm=mock, ...))
    result = agent.act([{"role": "user", "content": "test input"}])
    
    assert result == "Expected agent response"

# Integration testing with template mock
def test_narrative_flow():
    template_mock = TemplateMockLLM()
    template_mock.load_templates("test_templates.yaml")
    
    flow = build_narrative_flow(llm=template_mock)
    result = flow.invoke({"intent": "describe scene"})
    
    assert "scene description" in result["narrative_result"]
```

---

## Performance Considerations

### Caching
- **Response Caching**: Cache identical requests to reduce API calls
- **Template Caching**: Cache processed templates for reuse
- **Model Caching**: Cache model configurations

### Rate Limiting
- **Provider Limits**: Respect API rate limits
- **Cost Management**: Track and limit token usage
- **Queue Management**: Handle high-volume requests efficiently

### Error Handling
- **Retry Logic**: Automatic retry for transient failures
- **Fallback Providers**: Switch providers on failure
- **Circuit Breakers**: Prevent cascade failures

---

## Design Principles

1. **Provider Agnostic**: Code should work with any LLM provider
2. **Type Safety**: Strong typing for all LLM interactions
3. **Testability**: Easy mocking and testing without real APIs
4. **Performance**: Caching and optimization for production use
5. **Flexibility**: Support different models for different tasks
6. **Monitoring**: Track usage, performance, and costs

## Future Considerations

### Model Selection
- **Task-Specific Models**: Different models for different narrative tasks
- **Cost Optimization**: Choose models based on complexity requirements
- **Quality Metrics**: Track and optimize model performance

### Advanced Features
- **Fine-tuning**: Custom models for specific narrative styles
- **Prompt Engineering**: Optimize prompts for better results
- **Multi-modal**: Support for image and audio generation
- **Streaming**: Real-time response streaming for better UX

## Error Handling Strategies

### Provider Failures
```python
# Graceful fallback between providers
try:
    response = primary_provider.complete(...)
except ProviderError:
    response = fallback_provider.complete(...)
```

### Rate Limiting
```python
# Automatic rate limit handling
@retry_with_backoff
def safe_complete(llm, *args, **kwargs):
    return llm.complete(*args, **kwargs)
```

### Cost Management
```python
# Token usage tracking
class TokenTracker:
    def track_usage(self, prompt_tokens, completion_tokens):
        self.total_cost += calculate_cost(prompt_tokens, completion_tokens)
        if self.total_cost > self.budget_limit:
            raise BudgetExceededError()
```
