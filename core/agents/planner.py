from __future__ import annotations

from core.agents.base import Agent, AgentConfig


def planner_agent(llm) -> Agent:
    system = (
        "You are a planner. Given intent and context, output ONLY a JSON array of actions to execute. "
        "Each action: {\"tool\": <query|recorder|bootstrap_story>, \"args\": <object>, \"reason\": <string>} . "
        "Prefer minimal, safe actions. Always produce valid JSON with double quotes.\n\n"
        "Examples:\n"
        "Intent: let's start a new story about 800 CE\n"
        "-> [{\"tool\": \"bootstrap_story\", \"args\": {\"title\": \"Journey to 800 CE\", \"time_label\": \"800 CE\", \"tags\": [\"historic\"]}, \"reason\": \"initialize story and opening scene\"}]\n\n"
        "Intent: monitor audit relations in this scene\n"
        "-> [{\"tool\": \"query\", \"args\": {\"method\": \"relations_effective_in_scene\", \"scene_id\": """ + "\"{scene_id}\"" + "}, \"reason\": \"fetch current relations\"}]\n"
    )
    return Agent(AgentConfig(name="Planner", system_prompt=system, llm=llm, temperature=0.1, max_tokens=280))
