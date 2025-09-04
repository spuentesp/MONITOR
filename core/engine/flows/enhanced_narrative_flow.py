"""
Enhanced LangGraph flow with narrative intelligence and rich context.

This flow demonstrates the advanced DM/assistant architecture with:
- Rich narrative context enrichment
- Multi-agent council deliberation
- Character-aware content generation
- Persistent memory management
"""

from __future__ import annotations

from typing import Any

from core.domain.narrative_content import NarrativeState, CharacterMemory
from core.services.narrative_agent_tools import NarrativeContextProvider, NarrativeContentRecorder
from core.services.narrative_content_service import NarrativeContentService


def build_enhanced_narrative_flow(tools: Any, config: dict | None = None):
    """Build an enhanced LangGraph flow with narrative intelligence."""
    try:
        from langgraph.graph import END, StateGraph
    except Exception as e:
        raise RuntimeError("LangGraph is not installed. Please install langgraph.") from e

    # Enhanced state model
    class EnhancedNarrativeState(dict):
        """Enhanced state with narrative intelligence."""
        pass

    # Initialize narrative services
    content_service = NarrativeContentService(tools.get("mongo_store"))
    context_provider = NarrativeContextProvider(content_service)
    content_recorder = NarrativeContentRecorder(content_service)

    def enrich_narrative_context(state: dict[str, Any]) -> dict[str, Any]:
        """Enrich the state with comprehensive narrative context."""
        universe_id = state.get("universe_id")
        scene_id = state.get("scene_id")
        
        if not universe_id:
            return state
        
        # Get rich narrative context
        narrative_context = {}
        
        if scene_id:
            narrative_context.update(context_provider.get_scene_context(scene_id, universe_id))
        
        narrator_context = context_provider.get_narrator_context(universe_id, scene_id)
        narrative_context.update(narrator_context)
        
        # Enrich character contexts for all participants
        participants = state.get("participants", [])
        character_contexts = {}
        for char_id in participants:
            char_context = context_provider.get_character_context(char_id, universe_id)
            character_contexts[char_id] = char_context
        
        return {
            **state,
            "narrative_context": narrative_context,
            "character_contexts": character_contexts,
            "context_enriched": True
        }

    def narrative_council(state: dict[str, Any]) -> dict[str, Any]:
        """Multi-agent council for complex narrative decisions."""
        intent = state.get("intent", "")
        narrative_context = state.get("narrative_context", {})
        
        # Get perspectives from different agents
        council_input = {
            "intent": intent,
            "narrative_state": narrative_context.get("narrative_state"),
            "scene_context": narrative_context.get("chat_logs", [])[-5:],  # Recent context
            "character_contexts": state.get("character_contexts", {}),
        }
        
        # Narrator perspective: dramatic potential and story flow
        narrator_perspective = _safe_agent_call(
            tools, "narrator", 
            f"Analyze dramatic potential: {council_input}",
            default={"focus": "narrative", "approach": "standard"}
        )
        
        # Steward perspective: continuity and consistency
        steward_perspective = _safe_agent_call(
            tools, "steward",
            f"Check continuity risks: {council_input}",
            default={"risks": [], "recommendations": []}
        )
        
        # Character analysis: relationship and development impact
        character_perspective = _analyze_character_impact(council_input)
        
        # Synthesize council decision
        council_decision = {
            "narrator_focus": narrator_perspective,
            "steward_check": steward_perspective,
            "character_impact": character_perspective,
            "approach": _determine_narrative_approach(
                narrator_perspective, steward_perspective, character_perspective
            )
        }
        
        return {**state, "council_decision": council_decision}

    def character_aware_narrator(state: dict[str, Any]) -> dict[str, Any]:
        """Generate narrative content with character awareness."""
        intent = state.get("intent", "")
        council_decision = state.get("council_decision", {})
        character_contexts = state.get("character_contexts", {})
        narrative_context = state.get("narrative_context", {})
        
        # Build character-aware prompt
        character_notes = []
        for char_id, context in character_contexts.items():
            if context.get("memory"):
                memory = context["memory"]
                char_note = f"Character {char_id}: {memory.get('personal_memories', '')[:100]}"
                character_notes.append(char_note)
        
        # Build narrative prompt with rich context
        narrative_prompt = f"""
Intent: {intent}

Current Narrative State:
- Tone: {narrative_context.get('narrative_state', {}).get('current_tone', 'neutral')}
- Tension: {narrative_context.get('narrative_state', {}).get('tension_level', 5)}/10
- Active Threads: {narrative_context.get('narrative_state', {}).get('active_plot_threads', [])}

Character Context:
{chr(10).join(character_notes)}

Council Recommendation: {council_decision.get('approach', 'standard')}

Recent Scene Activity:
{narrative_context.get('chat_logs', [])[-3:] if narrative_context.get('chat_logs') else 'No recent activity'}
"""
        
        # Generate narrative with enhanced context
        draft = _safe_agent_call(
            tools, "narrator", narrative_prompt,
            default="The scene continues with quiet tension..."
        )
        
        return {**state, "enhanced_draft": draft}

    def update_narrative_memories(state: dict[str, Any]) -> dict[str, Any]:
        """Update character memories and narrative state based on generated content."""
        universe_id = state.get("universe_id")
        scene_id = state.get("scene_id")
        draft = state.get("enhanced_draft", state.get("draft", ""))
        
        if not universe_id or not draft:
            return state
        
        # Record the narrative content
        if scene_id:
            content_recorder.record_chat_message(
                scene_id=scene_id,
                universe_id=universe_id,
                speaker_id=None,
                speaker_name="Narrator",
                message=draft,
                message_type="narration",
                created_by="enhanced_narrator"
            )
        
        # Update narrative state based on content
        narrative_updates = _analyze_narrative_for_updates(draft)
        if narrative_updates:
            content_recorder.update_narrative_state(
                universe_id=universe_id,
                current_tone=narrative_updates.get("tone"),
                tension_level=narrative_updates.get("tension_level"),
                pacing=narrative_updates.get("pacing"),
                created_by="enhanced_flow"
            )
        
        # Update character memories if relevant
        participants = state.get("participants", [])
        for char_id in participants:
            character_updates = _analyze_content_for_character(draft, char_id)
            if character_updates:
                content_recorder.update_character_memory(
                    character_id=char_id,
                    universe_id=universe_id,
                    personal_memories=character_updates.get("new_memories"),
                    last_updated_scene=scene_id,
                    created_by="enhanced_flow"
                )
        
        return {**state, "memories_updated": True}

    def relationship_tracker(state: dict[str, Any]) -> dict[str, Any]:
        """Track and update character relationships based on scene content."""
        draft = state.get("enhanced_draft", state.get("draft", ""))
        participants = state.get("participants", [])
        universe_id = state.get("universe_id")
        
        if len(participants) < 2 or not draft or not universe_id:
            return state
        
        # Analyze relationships mentioned in content
        relationship_updates = _analyze_relationships_in_content(draft, participants)
        
        # Record relationship notes if significant interactions occurred
        for relationship in relationship_updates:
            content_recorder.record_gm_note(
                universe_id=universe_id,
                content=f"Relationship update: {relationship['description']}",
                note_type="relationship",
                tags=[f"character:{char_id}" for char_id in relationship["characters"]],
                created_by="relationship_tracker"
            )
        
        return {**state, "relationships_tracked": relationship_updates}

    # Helper functions
    def _safe_agent_call(tools: Any, agent_name: str, content: str, default: Any = None) -> Any:
        """Safely call an agent with fallback."""
        try:
            agent = tools.get(agent_name)
            if agent and callable(agent):
                return agent([{"role": "user", "content": content}])
        except Exception:
            pass
        return default

    def _analyze_character_impact(council_input: dict[str, Any]) -> dict[str, Any]:
        """Analyze potential character development impact."""
        character_contexts = council_input.get("character_contexts", {})
        
        impact_analysis = {
            "characters_affected": list(character_contexts.keys()),
            "development_opportunities": [],
            "relationship_changes": []
        }
        
        # Simple analysis - in production this would be more sophisticated
        for char_id, context in character_contexts.items():
            if context.get("memory"):
                impact_analysis["development_opportunities"].append(f"Character {char_id} growth potential")
        
        return impact_analysis

    def _determine_narrative_approach(narrator_view: Any, steward_view: Any, character_view: Any) -> str:
        """Synthesize agent perspectives into narrative approach."""
        # Simple synthesis - in production this would be more sophisticated
        if steward_view and steward_view.get("risks"):
            return "cautious"
        elif character_view and character_view.get("development_opportunities"):
            return "character_focused"
        else:
            return "standard"

    def _analyze_narrative_for_updates(content: str) -> dict[str, Any]:
        """Analyze narrative content for state updates."""
        updates = {}
        
        # Simple keyword analysis - in production this would use NLP
        if any(word in content.lower() for word in ["tense", "danger", "threat"]):
            updates["tension_level"] = 7
            updates["tone"] = "tense"
        elif any(word in content.lower() for word in ["peaceful", "calm", "rest"]):
            updates["tension_level"] = 3
            updates["tone"] = "peaceful"
        
        return updates

    def _analyze_content_for_character(content: str, char_id: str) -> dict[str, Any]:
        """Analyze content for character-specific updates."""
        updates = {}
        
        # Simple analysis - in production this would be more sophisticated
        if char_id.lower() in content.lower():
            updates["new_memories"] = f"Recent scene involvement: {content[:100]}..."
        
        return updates

    def _analyze_relationships_in_content(content: str, participants: list[str]) -> list[dict[str, Any]]:
        """Analyze content for relationship dynamics."""
        relationships = []
        
        # Simple analysis - in production this would use NLP
        for i, char1 in enumerate(participants):
            for char2 in participants[i+1:]:
                if char1.lower() in content.lower() and char2.lower() in content.lower():
                    relationships.append({
                        "characters": [char1, char2],
                        "description": f"Interaction between {char1} and {char2} in scene"
                    })
        
        return relationships

    # Build the enhanced workflow
    workflow = StateGraph(EnhancedNarrativeState)
    
    # Add enhanced nodes
    workflow.add_node("enrich_context", enrich_narrative_context)
    workflow.add_node("narrative_council", narrative_council)
    workflow.add_node("character_narrator", character_aware_narrator)
    workflow.add_node("update_memories", update_narrative_memories)
    workflow.add_node("track_relationships", relationship_tracker)
    
    # Set entry point
    workflow.set_entry_point("enrich_context")
    
    # Add edges
    workflow.add_edge("enrich_context", "narrative_council")
    workflow.add_edge("narrative_council", "character_narrator")
    workflow.add_edge("character_narrator", "update_memories")
    workflow.add_edge("update_memories", "track_relationships")
    workflow.add_edge("track_relationships", END)
    
    # Compile and return
    compiled = workflow.compile()
    
    class EnhancedFlowAdapter:
        """Adapter for the enhanced narrative flow."""
        
        def __init__(self, compiled_graph):
            self._compiled = compiled_graph
        
        def invoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
            try:
                return self._compiled.invoke(inputs)
            except Exception:
                # Fallback to basic execution
                return {
                    **inputs,
                    "enhanced_draft": "Enhanced narrative generation failed, using fallback.",
                    "context_enriched": False,
                    "memories_updated": False,
                    "_fallback": True
                }
    
    return EnhancedFlowAdapter(compiled)
