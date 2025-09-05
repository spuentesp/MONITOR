"""
Tests for AgentRegistry pattern.

Validates the agent registration system that follows Open/Closed principle
and provides extensible agent management.
"""

import pytest
from unittest.mock import Mock

from core.agents.registry import AgentRegistry
from core.generation.mock_llm import MockLLM


class TestAgentRegistry:
    """Test AgentRegistry functionality."""
    
    def setup_method(self):
        """Set up clean registry for each test."""
        # Clear the registry for isolated tests
        AgentRegistry._agents.clear()
    
    def teardown_method(self):
        """Clean up registry after each test."""
        AgentRegistry._agents.clear()
    
    def test_register_decorator_adds_agent_to_registry(self):
        """Test that @AgentRegistry.register adds agent to registry."""
        
        @AgentRegistry.register("TestAgent", temperature=0.7, max_tokens=100)
        def test_agent_prompt():
            return "You are a test agent."
        
        # Should be in registry (stored with lowercase key)
        assert "testagent" in AgentRegistry._agents
        
        # Should have correct metadata
        spec, prompt_func = AgentRegistry._agents["testagent"]
        agent_info = {"temperature": spec.temperature, "max_tokens": spec.max_tokens, "prompt_func": prompt_func}
        assert agent_info["temperature"] == 0.7
        assert agent_info["max_tokens"] == 100
        assert agent_info["prompt_func"] == test_agent_prompt
    
    def test_get_agent_info_returns_agent_details(self):
        """Test getting agent information."""
        
        @AgentRegistry.register("InfoAgent", temperature=0.8)
        def info_agent_prompt():
            return "Info agent prompt"
        
        info = AgentRegistry.get_agent_info("InfoAgent")
        
        assert info is not None
        assert info["temperature"] == 0.8
        assert info["prompt_func"] == info_agent_prompt
    
    def test_get_agent_info_returns_none_for_unknown_agent(self):
        """Test that unknown agents return None."""
        info = AgentRegistry.get_agent_info("UnknownAgent")
        assert info is None
    
    def test_build_all_agents_creates_agent_instances(self):
        """Test building all registered agents."""
        
        @AgentRegistry.register("Agent1", temperature=0.5)
        def agent1_prompt():
            return "Agent 1 prompt"
        
        @AgentRegistry.register("Agent2", temperature=0.9, max_tokens=200)  
        def agent2_prompt():
            return "Agent 2 prompt"
        
        llm = MockLLM()
        agents = AgentRegistry.build_all_agents(llm)
        
        # Should create both agents
        assert "Agent1" in agents
        assert "Agent2" in agents
        
        # Agents should be Agent instances
        from core.agents.base import Agent
        assert isinstance(agents["Agent1"], Agent)
        assert isinstance(agents["Agent2"], Agent)
    
    def test_register_with_default_parameters(self):
        """Test registration with minimal parameters."""
        
        @AgentRegistry.register("MinimalAgent")
        def minimal_agent_prompt():
            return "Minimal agent"
        
        info = AgentRegistry.get_agent_info("MinimalAgent")
        assert info is not None
        assert "temperature" in info  # Should have defaults
        assert info["prompt_func"] == minimal_agent_prompt
    
    def test_register_overwrites_existing_agent(self):
        """Test that re-registering an agent overwrites the previous version."""
        
        @AgentRegistry.register("OverwriteAgent", temperature=0.5)
        def original_prompt():
            return "Original prompt"
        
        @AgentRegistry.register("OverwriteAgent", temperature=0.8)
        def new_prompt():
            return "New prompt"
        
        info = AgentRegistry.get_agent_info("OverwriteAgent")
        assert info["temperature"] == 0.8
        assert info["prompt_func"] == new_prompt
    
    def test_build_agent_with_custom_llm_parameters(self):
        """Test that agents are built with proper LLM parameters."""
        
        @AgentRegistry.register("CustomAgent", temperature=0.7, max_tokens=150)
        def custom_agent_prompt():
            return "You are a custom agent with specific parameters."
        
        llm = MockLLM()
        agents = AgentRegistry.build_all_agents(llm)
        
        # Agent should be created and be an Agent instance
        custom_agent = agents["CustomAgent"]
        from core.agents.base import Agent
        assert isinstance(custom_agent, Agent)
        
        # Test that agent can be used with the registered prompt
        messages = [{"role": "user", "content": "Hello"}]
        response = custom_agent.act(messages)
        
        # Should get some response
        assert response is not None
        assert isinstance(response, str)
    
    def test_registry_is_singleton_across_imports(self):
        """Test that registry maintains state across different imports."""
        
        @AgentRegistry.register("SingletonAgent")
        def singleton_prompt():
            return "Singleton agent"
        
        # Agent should be accessible through direct registry access (lowercase key)
        assert "singletonagent" in AgentRegistry._agents
        
        # Count should be consistent
        count_before = len(AgentRegistry._agents)
        
        # Re-importing shouldn't create duplicates
        from core.agents.registry import AgentRegistry as ImportedRegistry
        assert len(ImportedRegistry._agents) == count_before
        assert "singletonagent" in ImportedRegistry._agents


@pytest.mark.unit
def test_agent_registry_follows_open_closed_principle():
    """Test that new agents can be added without modifying existing code."""
    
    # Clear registry
    AgentRegistry._agents.clear()
    
    # Original agents
    @AgentRegistry.register("OriginalAgent")
    def original_agent():
        return "Original"
    
    original_count = len(AgentRegistry._agents)
    
    # Add new agent (Open for extension)
    @AgentRegistry.register("NewAgent")
    def new_agent():
        return "New agent"
    
    # Should have both agents (using lowercase keys)
    assert len(AgentRegistry._agents) == original_count + 1
    assert "originalagent" in AgentRegistry._agents
    assert "newagent" in AgentRegistry._agents
    
    # Original agent should be unchanged (Closed for modification)
    original_info = AgentRegistry.get_agent_info("OriginalAgent")
    assert original_info["prompt_func"] == original_agent