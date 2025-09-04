"""
Narrative domain service.

This module contains business logic for narrative operations,
including story management, scene orchestration, and continuity validation.
"""

from typing import Any, Dict, List, Optional
from core.interfaces.persistence import SceneRepositoryInterface, QueryInterface


class NarrativeService:
    """Domain service for narrative business logic."""
    
    def __init__(self, scene_repository: SceneRepositoryInterface, query_interface: QueryInterface):
        self.scene_repository = scene_repository
        self.query_interface = query_interface
    
    async def create_scene_with_context(self, scene_data: Dict[str, Any], story_id: str) -> Dict[str, Any]:
        """Create a scene with proper story context and validation."""
        # Validate scene data
        validation_result = await self._validate_scene_data(scene_data, story_id)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}
        
        # Add story context
        scene_data["story_id"] = story_id
        scene_data["sequence_number"] = await self._get_next_sequence_number(story_id)
        
        # Create the scene
        try:
            scene_id = await self.scene_repository.create_scene(scene_data)
            return {"success": True, "scene_id": scene_id}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}
    
    async def add_scene_participant(self, scene_id: str, entity_id: str, role: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a participant to a scene with role validation."""
        # Validate participant addition
        validation_result = await self._validate_participant_addition(scene_id, entity_id, role)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}
        
        # Add participant
        try:
            success = await self.scene_repository.add_participant(scene_id, entity_id, role)
            if success and context:
                # Store additional context about the participation
                await self._store_participation_context(scene_id, entity_id, context)
            return {"success": success}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}
    
    async def transition_scene_status(self, scene_id: str, new_status: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Transition a scene status with business rule validation."""
        # Get current scene
        scene = await self._get_scene_details(scene_id)
        if not scene:
            return {"success": False, "errors": ["Scene not found"]}
        
        # Validate status transition
        validation_result = await self._validate_status_transition(scene, new_status)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}
        
        # Update status
        try:
            success = await self.scene_repository.update_scene_status(scene_id, new_status)
            if success and reason:
                # Log transition reason
                await self._log_status_transition(scene_id, scene.get("status"), new_status, reason)
            return {"success": success}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}
    
    async def validate_scene_continuity(self, scene_id: str, narrative_content: str) -> Dict[str, Any]:
        """Validate narrative continuity for a scene."""
        try:
            # Get scene context
            scene = await self._get_scene_details(scene_id)
            if not scene:
                return {"valid": False, "errors": ["Scene not found"]}
            
            # Get story context
            story_context = await self._get_story_context(scene.get("story_id"))
            
            # Validate continuity
            continuity_issues = await self._check_continuity_issues(scene, story_context, narrative_content)
            
            return {
                "valid": len(continuity_issues) == 0,
                "issues": continuity_issues,
                "suggestions": await self._generate_continuity_suggestions(continuity_issues)
            }
        except Exception as e:
            return {"valid": False, "errors": [str(e)]}
    
    async def get_scene_narrative_context(self, scene_id: str) -> Dict[str, Any]:
        """Get comprehensive narrative context for a scene."""
        try:
            scene = await self._get_scene_details(scene_id)
            if not scene:
                return {"success": False, "errors": ["Scene not found"]}
            
            # Get participants and their context
            participants = await self._get_scene_participants_with_context(scene_id)
            
            # Get relevant facts
            relevant_facts = await self._get_scene_relevant_facts(scene_id)
            
            # Get previous scenes context
            previous_scenes = await self._get_previous_scenes_context(scene.get("story_id"), scene.get("sequence_number"))
            
            return {
                "success": True,
                "scene": scene,
                "participants": participants,
                "relevant_facts": relevant_facts,
                "previous_context": previous_scenes,
                "narrative_constraints": await self._get_narrative_constraints(scene_id)
            }
        except Exception as e:
            return {"success": False, "errors": [str(e)]}
    
    async def _validate_scene_data(self, scene_data: Dict[str, Any], story_id: str) -> Dict[str, Any]:
        """Validate scene data against business rules."""
        errors = []
        
        # Required fields
        if not scene_data.get("title"):
            errors.append("Scene title is required")
        
        # Story existence
        if story_id:
            # In a real implementation, verify story exists
            pass
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _validate_participant_addition(self, scene_id: str, entity_id: str, role: str) -> Dict[str, Any]:
        """Validate adding a participant to a scene."""
        errors = []
        
        # Valid roles
        valid_roles = ["protagonist", "antagonist", "supporting", "narrator", "observer"]
        if role not in valid_roles:
            errors.append(f"Invalid role: {role}")
        
        # Check if entity exists
        entity = await self.query_interface.get_entity_by_id(entity_id)
        if not entity:
            errors.append("Entity not found")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _validate_status_transition(self, scene: Dict[str, Any], new_status: str) -> Dict[str, Any]:
        """Validate scene status transitions."""
        errors = []
        current_status = scene.get("status", "draft")
        
        # Valid status transitions
        valid_transitions = {
            "draft": ["active", "cancelled"],
            "active": ["completed", "paused"],
            "paused": ["active", "cancelled"],
            "completed": [],  # Terminal state
            "cancelled": []   # Terminal state
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            errors.append(f"Invalid transition from {current_status} to {new_status}")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _get_next_sequence_number(self, story_id: str) -> int:
        """Get the next sequence number for a scene in a story."""
        try:
            # In a real implementation, query for max sequence number
            return 1  # Placeholder
        except Exception:
            return 1
    
    async def _get_scene_details(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed scene information."""
        # In a real implementation, this would use the query interface
        return {"id": scene_id, "status": "draft"}  # Placeholder
    
    async def _get_story_context(self, story_id: str) -> Dict[str, Any]:
        """Get story-level context for continuity checking."""
        return {}  # Placeholder
    
    async def _check_continuity_issues(self, scene: Dict[str, Any], story_context: Dict[str, Any], content: str) -> List[str]:
        """Check for continuity issues in narrative content."""
        issues = []
        # Placeholder for continuity validation logic
        return issues
    
    async def _generate_continuity_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions to fix continuity issues."""
        return [f"Suggestion for: {issue}" for issue in issues]
    
    async def _get_scene_participants_with_context(self, scene_id: str) -> List[Dict[str, Any]]:
        """Get scene participants with their context."""
        return []  # Placeholder
    
    async def _get_scene_relevant_facts(self, scene_id: str) -> List[Dict[str, Any]]:
        """Get facts relevant to the scene."""
        return []  # Placeholder
    
    async def _get_previous_scenes_context(self, story_id: str, current_sequence: int) -> List[Dict[str, Any]]:
        """Get context from previous scenes."""
        return []  # Placeholder
    
    async def _get_narrative_constraints(self, scene_id: str) -> Dict[str, Any]:
        """Get narrative constraints for the scene."""
        return {}  # Placeholder
    
    async def _store_participation_context(self, scene_id: str, entity_id: str, context: Dict[str, Any]) -> None:
        """Store additional context about entity participation."""
        pass  # Placeholder
    
    async def _log_status_transition(self, scene_id: str, old_status: str, new_status: str, reason: str) -> None:
        """Log status transition with reason."""
        pass  # Placeholder
