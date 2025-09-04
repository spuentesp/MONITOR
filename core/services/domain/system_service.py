"""
System domain service.

This module contains business logic for system management,
including rule resolution, system application, and conflict detection.
"""

from typing import Any

from core.interfaces.persistence import QueryInterface, SystemRepositoryInterface


class SystemService:
    """Domain service for system business logic."""

    def __init__(
        self, system_repository: SystemRepositoryInterface, query_interface: QueryInterface
    ):
        self.system_repository = system_repository
        self.query_interface = query_interface

    async def create_system_with_validation(self, system_data: dict[str, Any]) -> dict[str, Any]:
        """Create a system with rule validation."""
        # Validate system data
        validation_result = await self._validate_system_data(system_data)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}

        # Validate rules consistency
        rules_validation = await self._validate_system_rules(system_data.get("rules", {}))
        if not rules_validation["valid"]:
            return {"success": False, "errors": rules_validation["errors"]}

        # Create the system
        try:
            system_id = await self.system_repository.create_system(system_data)
            return {"success": True, "system_id": system_id}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def apply_system_to_story_with_validation(
        self, system_id: str, story_id: str
    ) -> dict[str, Any]:
        """Apply a system to a story with conflict detection."""
        # Check if system exists
        system = await self._get_system_details(system_id)
        if not system:
            return {"success": False, "errors": ["System not found"]}

        # Get existing systems for the story
        existing_systems = await self._get_story_systems(story_id)

        # Check for conflicts
        conflicts = await self._detect_system_conflicts(system, existing_systems)
        if conflicts:
            return {
                "success": False,
                "errors": ["System conflicts detected"],
                "conflicts": conflicts,
            }

        # Apply the system
        try:
            success = await self.system_repository.apply_system_to_story(system_id, story_id)
            if success:
                # Initialize system state for the story
                await self._initialize_system_state(system_id, story_id)
            return {"success": success}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def resolve_system_rules(
        self, story_id: str, scene_id: str | None = None
    ) -> dict[str, Any]:
        """Resolve applicable system rules for a story/scene context."""
        try:
            # Get all systems for the story
            systems = await self._get_story_systems(story_id)

            # Get scene-specific context if provided
            scene_context = {}
            if scene_id:
                scene_context = await self._get_scene_context(scene_id)

            # Resolve rules in priority order
            resolved_rules = await self._resolve_rules_hierarchy(systems, scene_context)

            return {
                "success": True,
                "resolved_rules": resolved_rules,
                "applied_systems": [s["id"] for s in systems],
                "context": scene_context,
            }
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def validate_action_against_rules(
        self, action: dict[str, Any], story_id: str, scene_id: str | None = None
    ) -> dict[str, Any]:
        """Validate an action against system rules."""
        try:
            # Get resolved rules
            rules_result = await self.resolve_system_rules(story_id, scene_id)
            if not rules_result["success"]:
                return rules_result

            resolved_rules = rules_result["resolved_rules"]

            # Validate action
            violations = await self._check_rule_violations(action, resolved_rules)

            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "suggestions": await self._generate_rule_suggestions(violations, resolved_rules),
            }
        except Exception as e:
            return {"valid": False, "errors": [str(e)]}

    async def update_system_rules_with_validation(
        self, system_id: str, rule_updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update system rules with validation."""
        # Get current system
        system = await self._get_system_details(system_id)
        if not system:
            return {"success": False, "errors": ["System not found"]}

        # Merge and validate new rules
        current_rules = system.get("rules", {})
        merged_rules = {**current_rules, **rule_updates}

        validation_result = await self._validate_system_rules(merged_rules)
        if not validation_result["valid"]:
            return {"success": False, "errors": validation_result["errors"]}

        # Check for impacts on existing stories
        impact_analysis = await self._analyze_rule_change_impact(system_id, rule_updates)

        # Update rules
        try:
            success = await self.system_repository.update_system_rules(system_id, merged_rules)
            return {"success": success, "impact_analysis": impact_analysis}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _validate_system_data(self, system_data: dict[str, Any]) -> dict[str, Any]:
        """Validate system data."""
        errors = []

        # Required fields
        if not system_data.get("name"):
            errors.append("System name is required")

        if not system_data.get("type"):
            errors.append("System type is required")

        # Valid system types
        valid_types = ["rpg", "narrative", "simulation", "custom"]
        if system_data.get("type") and system_data["type"] not in valid_types:
            errors.append("Invalid system type")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _validate_system_rules(self, rules: dict[str, Any]) -> dict[str, Any]:
        """Validate system rules for consistency."""
        errors = []

        # Check for required rule categories
        required_categories = ["core_mechanics", "conflict_resolution"]
        for category in required_categories:
            if category not in rules:
                errors.append(f"Missing required rule category: {category}")

        # Validate rule values
        if "core_mechanics" in rules:
            mechanics = rules["core_mechanics"]
            if isinstance(mechanics, dict):
                # Validate dice system
                dice_system = mechanics.get("dice_system")
                if dice_system and dice_system not in ["d20", "d6", "d10", "percentile", "fudge"]:
                    errors.append("Invalid dice system")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _get_system_details(self, system_id: str) -> dict[str, Any] | None:
        """Get system details."""
        # In a real implementation, use query interface
        return {"id": system_id, "rules": {}}  # Placeholder

    async def _get_story_systems(self, story_id: str) -> list[dict[str, Any]]:
        """Get all systems applied to a story."""
        return []  # Placeholder

    async def _detect_system_conflicts(
        self, new_system: dict[str, Any], existing_systems: list[dict[str, Any]]
    ) -> list[str]:
        """Detect conflicts between systems."""
        conflicts = []

        # Check for rule conflicts
        new_rules = new_system.get("rules", {})
        for existing_system in existing_systems:
            existing_rules = existing_system.get("rules", {})

            # Simple conflict detection
            for rule_category in new_rules:
                if rule_category in existing_rules:
                    # Check for incompatible values
                    if new_rules[rule_category] != existing_rules[rule_category]:
                        conflicts.append(f"Rule conflict in {rule_category}")

        return conflicts

    async def _resolve_rules_hierarchy(
        self, systems: list[dict[str, Any]], scene_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve rules in priority order."""
        resolved = {}

        # Sort systems by priority (if available)
        sorted_systems = sorted(systems, key=lambda s: s.get("priority", 0), reverse=True)

        # Merge rules with priority override
        for system in sorted_systems:
            rules = system.get("rules", {})
            for category, rule_data in rules.items():
                if category not in resolved:
                    resolved[category] = rule_data

        return resolved

    async def _check_rule_violations(
        self, action: dict[str, Any], rules: dict[str, Any]
    ) -> list[str]:
        """Check if an action violates system rules."""
        violations = []

        # Example violation checks
        action_type = action.get("type")
        if action_type == "attack":
            # Check combat rules
            combat_rules = rules.get("combat", {})
            if combat_rules.get("require_initiative") and not action.get("initiative_roll"):
                violations.append("Combat action requires initiative roll")

        return violations

    async def _generate_rule_suggestions(
        self, violations: list[str], rules: dict[str, Any]
    ) -> list[str]:
        """Generate suggestions to fix rule violations."""
        return [f"To fix '{violation}', consider..." for violation in violations]

    async def _analyze_rule_change_impact(
        self, system_id: str, rule_updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze the impact of rule changes."""
        return {"affected_stories": [], "potential_issues": [], "recommendations": []}

    async def _get_scene_context(self, scene_id: str) -> dict[str, Any]:
        """Get scene context for rule resolution."""
        return {}  # Placeholder

    async def _initialize_system_state(self, system_id: str, story_id: str) -> None:
        """Initialize system state for a story."""
        pass  # Placeholder
