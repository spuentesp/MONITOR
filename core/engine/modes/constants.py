"""Constants and patterns for mode classification."""
import re

# Command patterns for intent classification
CMD_MONITOR = re.compile(r"^[\s]*[\/@]?(monitor)\b", re.IGNORECASE)
CMD_NARRATE = re.compile(r"^[\s]*[\/@]?(narrar|narrador|narrate|narrator)\b", re.IGNORECASE)
CMD_HELP = re.compile(r"^[\s]*[\/@]?help\b", re.IGNORECASE)

# Help text content
HELP_TEXT = """
**Monitor Help**

Available commands:
- `/monitor` - Switch to operational mode
- `/narrate` - Switch to narrative mode
- `/help` - Show this help

Monitor actions:
- Create universes, stories, and scenes
- Query narrative data
- Manage game state

Examples:
- `start story topics "fantasy, adventure" story "The Quest"`
- `create universe name "My World"`
- `setup universe multiverse mv:demo name "Test Universe"`
"""
