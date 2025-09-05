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
    class State(dict):
        """Enhanced state with narrative intelligence."""
        pass

    # Initialize narrative services
    content_service = NarrativeContentService(tools.get("mongo_store"))
    context_provider = NarrativeContextProvider(content_service, tools.get("query_service"))
    content_recorder = NarrativeContentRecorder(content_service)

    def enrich_narrative_context(state: dict[str, Any]) -> dict[str, Any]:
        """Enrich the state with comprehensive narrative and graph context."""
        universe_id = state.get("universe_id")
        scene_id = state.get("scene_id")
        
        if not universe_id:
            return state
        
        # Get comprehensive context including graph data
        comprehensive_context = context_provider.get_comprehensive_context(universe_id, scene_id)
        
        # Get story timeline for narrative grounding
        story_timeline = None
        story_id = state.get("story_id")
        if story_id:
            story_timeline = context_provider.get_story_timeline(universe_id, story_id)
        
        # Enrich character contexts for all participants
        participants = state.get("participants", [])
        character_contexts = {}
        for char_id in participants:
            char_context = context_provider.get_character_full_context(char_id, universe_id)
            character_contexts[char_id] = char_context
        
        return {
            **state,
            "comprehensive_context": comprehensive_context,
            "story_timeline": story_timeline,
            "character_contexts": character_contexts,
            "context_enriched": True
        }

    def narrative_council(state: dict[str, Any]) -> dict[str, Any]:
        """Multi-agent council using actual QueryService data."""
        intent = state.get("intent", "")
        comprehensive_context = state.get("comprehensive_context", {})
        story_timeline = state.get("story_timeline", {})
        
        # Build council input with real QueryService data
        council_input = {
            "intent": intent,
            "stories": comprehensive_context.get("stories", []),           # From stories_in_universe()
            "entities": comprehensive_context.get("entities", []),         # From entities_in_universe()  
            "scene_relationships": comprehensive_context.get("scene_relationships", []),  # From relations_effective_in_scene()
            "narrative_state": comprehensive_context.get("narrative_state"),  # From MongoDB
            "story_progression": story_timeline.get("story_progression", []),  # From scenes_in_story()
            "key_events": story_timeline.get("key_events", []),            # From facts_for_story()
            "character_contexts": state.get("character_contexts", {}),
        }
        
        # Narrator perspective with real data
        narrator_perspective = _safe_agent_call(
            tools, "narrator", 
            f"Analyze dramatic potential with established facts: {council_input}",
            default={"focus": "narrative", "approach": "standard"}
        )
        
        # Steward perspective with actual continuity data
        steward_perspective = _safe_agent_call(
            tools, "steward",
            f"Check continuity against established entities and facts: {council_input}",
            default={"risks": [], "recommendations": []}
        )
        
        # Character analysis with real relationship data
        character_perspective = _analyze_character_impact_with_real_data(council_input)
        
        # Plot analysis with actual story progression
        plot_perspective = _analyze_plot_with_real_data(council_input)
        
        # Synthesize council decision
        council_decision = {
            "narrator_focus": narrator_perspective,
            "steward_check": steward_perspective,
            "character_impact": character_perspective,
            "plot_implications": plot_perspective,
            "approach": _determine_narrative_approach_with_real_data(
                narrator_perspective, steward_perspective, character_perspective, plot_perspective
            ),
            "grounding_summary": _create_grounding_summary_real(comprehensive_context, story_timeline)
        }
        
        return {**state, "council_decision": council_decision}

    def character_aware_narrator(state: dict[str, Any]) -> dict[str, Any]:
        """Generate narrative content with comprehensive character and world awareness."""
        intent = state.get("intent", "")
        council_decision = state.get("council_decision", {})
        character_contexts = state.get("character_contexts", {})
        comprehensive_context = state.get("comprehensive_context", {})
        story_timeline = state.get("story_timeline", {})
        
        # Build grounding summary from comprehensive context
        grounding_summary = council_decision.get("grounding_summary", {})
        
        # Build character awareness notes
        character_notes = []
        for char_id, context in character_contexts.items():
            char_note_parts = []
            
            # Add entity data from graph
            entity_data = context.get("entity_data", {})
            if entity_data:
                char_note_parts.append(f"Entity: {entity_data.get('name', char_id)} ({entity_data.get('entity_type', 'unknown')})")
            
            # Add memory from narrative content
            memory = context.get("memory")
            if memory and hasattr(memory, 'personal_memories') and memory.personal_memories:
                char_note_parts.append(f"Memories: {memory.personal_memories[:100]}...")
            
            # Add relationship context
            relationships = context.get("relationships", [])
            if relationships:
                rel_count = len(relationships)
                char_note_parts.append(f"Relationships: {rel_count} known connections")
            
            if char_note_parts:
                character_notes.append(f"Character {char_id}: " + " | ".join(char_note_parts))
        
        # Build world context notes
        world_notes = []
        universe_context = comprehensive_context.get("universe", {})
        if universe_context:
            world_notes.append(f"Universe: {universe_context.get('name', 'Unknown')}")
            
        story_contexts = comprehensive_context.get("stories", [])
        active_stories = [s for s in story_contexts if s.get("status") == "active"]
        if active_stories:
            world_notes.append(f"Active Stories: {len(active_stories)}")
        
        # Recent events from timeline
        recent_events = []
        story_progression = story_timeline.get("story_progression", [])
        if story_progression:
            recent_scenes = story_progression[-2:]  # Last 2 scenes
            for scene in recent_scenes:
                if scene.get("summary"):
                    recent_events.append(f"Recent: {scene['summary'][:100]}...")
        
        # Build comprehensive narrative prompt
        narrative_prompt = f"""
Intent: {intent}

WORLD GROUNDING:
{chr(10).join(world_notes)}

NARRATIVE STATE:
- Tone: {grounding_summary.get('narrative_tone', 'neutral')}
- Active Plot Threads: {grounding_summary.get('active_plot_threads', [])}
- Story Momentum: {council_decision.get('plot_implications', {}).get('story_momentum', 'neutral')}

CHARACTER CONTEXT:
{chr(10).join(character_notes) if character_notes else 'No character context available'}

RECENT STORY EVENTS:
{chr(10).join(recent_events) if recent_events else 'No recent events recorded'}

ESTABLISHED FACTS (for continuity):
{chr(10).join(f"- {fact}" for fact in grounding_summary.get('important_facts', []))}

COUNCIL RECOMMENDATION: 
Approach: {council_decision.get('approach', 'balanced_narrative')}
Focus: {council_decision.get('narrator_focus', {}).get('focus', 'narrative')}

Generate narrative content that respects all established facts, maintains character consistency, 
and advances the story in a way that feels grounded in the established world and relationships.
"""
        
        # Generate narrative with comprehensive context
        draft = _safe_agent_call(
            tools, "narrator", narrative_prompt,
            default="The scene continues, drawing upon the rich history and relationships that define this world..."
        )
        
        return {**state, "enhanced_draft": draft, "grounding_applied": True}

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

    def _analyze_character_impact_with_real_data(council_input: dict[str, Any]) -> dict[str, Any]:
        """Analyze character impact using actual QueryService data."""
        character_contexts = council_input.get("character_contexts", {})
        entities = council_input.get("entities", [])  # From entities_in_universe()
        scene_relationships = council_input.get("scene_relationships", [])  # From relations_effective_in_scene()
        
        impact_analysis = {
            "characters_affected": list(character_contexts.keys()),
            "development_opportunities": [],
            "relationship_changes": [],
            "entities_in_scene": []
        }
        
        # Analyze based on real entity data
        for entity in entities:
            entity_id = entity.get("id")
            if entity_id in character_contexts:
                impact_analysis["development_opportunities"].append(
                    f"Character {entity.get('name', entity_id)} ({entity.get('entity_type', 'unknown')})"
                )
        
        # Analyze real relationship data from scene
        for rel in scene_relationships:
            from_entity = rel.get("from_entity_id") or rel.get("from_entity")
            to_entity = rel.get("to_entity_id") or rel.get("to_entity")
            
            if from_entity in character_contexts or to_entity in character_contexts:
                impact_analysis["relationship_changes"].append({
                    "relationship": f"{from_entity} -> {to_entity}",
                    "type": rel.get("relation_type"),
                    "current_strength": rel.get("strength", 0)
                })
        
        return impact_analysis

    def _analyze_plot_with_real_data(council_input: dict[str, Any]) -> dict[str, Any]:
        """Analyze plot using actual story progression and facts."""
        story_progression = council_input.get("story_progression", [])  # From scenes_in_story()
        key_events = council_input.get("key_events", [])  # From facts_for_story()
        narrative_state = council_input.get("narrative_state")  # From MongoDB
        
        plot_analysis = {
            "active_threads": [],
            "recent_events": [],
            "story_momentum": "neutral",
            "scene_count": len(story_progression)
        }
        
        # Analyze real story progression
        if len(story_progression) > 0:
            plot_analysis["story_momentum"] = "building" if len(story_progression) >= 3 else "starting"
            
            # Get recent scenes
            recent_scenes = story_progression[-2:] if len(story_progression) > 1 else story_progression
            plot_analysis["recent_events"] = [
                f"Scene: {scene.get('location', 'Unknown')} - {scene.get('summary', 'No summary')[:50]}..."
                for scene in recent_scenes
            ]
        
        # Analyze real facts
        if key_events:
            plot_analysis["recent_events"].extend([
                f"Fact: {event.get('content', '')[:50]}..."
                for event in key_events[:3]  # Last 3 facts
            ])
        
        # Use real narrative state
        if narrative_state:
            plot_analysis["active_threads"] = getattr(narrative_state, "active_plot_threads", [])
        
        return plot_analysis

    def _determine_narrative_approach_with_real_data(
        narrator_view: Any, steward_view: Any, character_view: Any, plot_view: Any
    ) -> str:
        """Determine approach based on real data analysis."""
        
        # Check steward warnings first
        if steward_view and steward_view.get("risks"):
            return "continuity_focused"
        
        # Check real story momentum
        momentum = plot_view.get("story_momentum", "neutral")
        if momentum == "building":
            return "momentum_building"
        elif momentum == "starting":
            return "establishment_focused"
        
        # Check character development opportunities
        dev_opportunities = character_view.get("development_opportunities", [])
        if len(dev_opportunities) > 0:
            return "character_development"
        
        # Check relationship complexity
        rel_changes = character_view.get("relationship_changes", [])
        if len(rel_changes) > 2:
            return "relationship_focused"
        
        return "balanced_narrative"

    def _create_grounding_summary_real(comprehensive_context: dict[str, Any], story_timeline: dict[str, Any]) -> dict[str, Any]:
        """Create grounding summary from real QueryService and MongoDB data."""
        stories = comprehensive_context.get("stories", [])
        entities = comprehensive_context.get("entities", [])
        story_progression = story_timeline.get("story_progression", [])
        key_events = story_timeline.get("key_events", [])
        narrative_state = comprehensive_context.get("narrative_state")
        
        summary = {
            "total_stories": len(stories),
            "total_entities": len(entities),
            "recent_scenes": len(story_progression),
            "key_facts": len(key_events),
            "active_stories": [story.get("title", story.get("id", "Unknown")) for story in stories[:3]],
            "main_characters": [
                entity.get("name", entity.get("id", "Unknown")) 
                for entity in entities 
                if entity.get("entity_type") == "character"
            ][:5],
            "recent_locations": list(set(
                scene.get("location") 
                for scene in story_progression[-3:] 
                if scene.get("location")
            )),
            "narrative_tone": None,
            "active_plot_threads": []
        }
        
        # Add real narrative state
        if narrative_state:
            summary["narrative_tone"] = getattr(narrative_state, "current_tone", None)
            summary["active_plot_threads"] = getattr(narrative_state, "active_plot_threads", [])
        
        return summary

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
    workflow = StateGraph(State)  # type: ignore[type-var]
    
    # Add enhanced nodes
    workflow.add_node("enrich_context", enrich_narrative_context)  # type: ignore[type-var]
    workflow.add_node("narrative_council", narrative_council)  # type: ignore[type-var]
    workflow.add_node("character_narrator", character_aware_narrator)  # type: ignore[type-var]
    workflow.add_node("update_memories", update_narrative_memories)  # type: ignore[type-var]
    workflow.add_node("track_relationships", relationship_tracker)  # type: ignore[type-var]
    
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
