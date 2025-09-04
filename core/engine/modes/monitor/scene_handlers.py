"""Scene management handlers for monitor mode."""

from __future__ import annotations

from core.engine.monitor_parser import MonitorIntent
from core.engine.tools import query_tool

from ..state import GraphState, append_message, gen_id
from .utils import auto_flush_if_needed, commit_deltas


def handle_end_scene(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle ending current scene and starting the next one."""
    # Auto-persist policy: at scene boundaries, commit staged work in copilot
    flush_res = auto_flush_if_needed(ctx, "end_scene")
    persisted_msg = ""
    if isinstance(flush_res, dict) and flush_res.get("ok"):
        persisted_msg = "Staged changes persisted. "
    elif isinstance(flush_res, dict):
        persisted_msg = "Could not persist staged changes now. "
    else:
        persisted_msg = ""

    # Start next scene in the same story
    story_id = state.get("story_id")
    if not story_id:
        append_message(
            state,
            "assistant",
            persisted_msg + "Scene ended. No active story to start the next scene.",
        )
        state["last_mode"] = "monitor"
        return state

    next_seq = None
    try:
        if ctx:
            scenes = query_tool(ctx, "scenes_in_story", story_id=story_id) or []
            # compute next sequence index; fallback: count + 1
            seqs = [s.get("sequence_index") for s in scenes if s.get("sequence_index") is not None]
            if seqs:
                next_seq = (max(seqs) or 0) + 1
            else:
                next_seq = len(scenes) + 1
    except Exception:
        next_seq = None

    new_sc_id = gen_id("scene")
    deltas = {
        "new_scene": {
            "id": new_sc_id,
            "title": f"Scene {next_seq}" if next_seq else None,
            "story_id": story_id,
            "sequence_index": next_seq,
        },
        "_draft": f"Start Scene {next_seq or ''}".strip(),
    }
    res = commit_deltas(ctx, deltas)
    state["scene_id"] = new_sc_id
    msg = (
        f"Scene ended. {persisted_msg}Started next scene (mode={res.get('mode')}). id={new_sc_id}"
        + (f", seq={next_seq}. " if next_seq else ". ")
        + "Handing off to the narrator to decide the intro and cast."
    )
    append_message(state, "assistant", msg)
    # Nudge the router to go to narration on the next turn
    state["override_mode"] = "narration"
    state["last_mode"] = "monitor"
    return state


def handle_add_scene(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle adding a new scene to a story."""
    uid = state.get("universe_id")
    story_id = intent.story_id or state.get("story_id")
    if not story_id:
        action_reply = "Please specify a story id (e.g., story st:...)."
    else:
        sc_id = gen_id("scene")
        participants_ids: list[str] = []
        if ctx and intent.participants and uid:
            for name in intent.participants:
                try:
                    ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                    if ent:
                        participants_ids.append(ent["id"])  # type: ignore[index]
                except Exception:
                    pass
        deltas = {
            "new_scene": {
                "id": sc_id,
                "title": intent.name or None,
                "story_id": story_id,
                "participants": participants_ids or None,
            },
            "facts": (
                [{"description": intent.description, "occurs_in": sc_id}]
                if intent.description
                else None
            ),
            "_draft": f"Add scene {intent.name or sc_id}",
        }
        res = commit_deltas(ctx, deltas)
        # remember last created ids for session continuity
        state["scene_id"] = sc_id
        state["story_id"] = story_id
        action_reply = f"Scene created (mode={res.get('mode')}). id={sc_id}"

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_modify_last_scene(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle modifying the last scene in the session."""
    sc_id = state.get("scene_id")
    if not sc_id:
        action_reply = "No last scene in session. Provide scene_id or create a scene first."
    else:
        uid = state.get("universe_id")
        participants_ids: list[str] = []
        if ctx and intent.participants and uid:
            for name in intent.participants:
                try:
                    ent = query_tool(ctx, "entity_by_name_in_universe", universe_id=uid, name=name)
                    if ent:
                        participants_ids.append(ent["id"])  # type: ignore[index]
                except Exception:
                    pass
        facts = []
        if intent.description:
            facts.append({"description": intent.description, "occurs_in": sc_id})
        deltas = {
            "scene_id": sc_id,
            "facts": (facts or None),
            # Note: adding participants to an existing scene requires updating APPEARS_IN via new_scene participants delta; reuse new_scene path
            "new_scene": (
                {"id": sc_id, "participants": participants_ids} if participants_ids else None
            ),
            "_draft": (intent.description or "Append to scene"),
        }
        res = commit_deltas(ctx, deltas)
        action_reply = f"Scene updated (mode={res.get('mode')})."

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_save_conversation(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle saving current conversation as a transcript."""
    uid = state.get("universe_id")
    sc_id = state.get("scene_id")
    msgs = state.get("messages") or []
    # Build a compact transcript (last ~30 turns)
    lines = []
    for m in msgs[-60:]:
        r = m.get("role")
        if r in ("user", "assistant"):
            lines.append(f"{r}: {m.get('content', '')}")
    transcript = "\n".join(lines)
    if not transcript.strip():
        action_reply = "No conversation to save."
    else:
        res = commit_deltas(
            ctx,
            {
                "facts": [
                    {
                        "description": f"TRANSCRIPT\n{transcript}",
                        "universe_id": uid,
                        "occurs_in": sc_id,
                    }
                ],
                "_draft": "Save transcript",
            },
        )
        action_reply = f"Conversation saved (mode={res.get('mode')})."

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state


def handle_show_conversation(state: GraphState, intent: MonitorIntent, ctx) -> GraphState:
    """Handle showing saved conversation transcript."""
    # MVP: retrieve transcript fact(s) for current scene; if none, try universe-level
    sc_id = state.get("scene_id")
    try:
        facts = []
        if ctx and sc_id:
            facts = query_tool(ctx, "facts_for_scene", scene_id=sc_id) or []
        if not facts and ctx and state.get("story_id"):
            facts = query_tool(ctx, "facts_for_story", story_id=state.get("story_id")) or []
        # filter transcript facts
        transcripts = [
            f
            for f in (facts or [])
            if isinstance(f.get("description"), str)
            and f.get("description", "").startswith("TRANSCRIPT\n")
        ]
        if transcripts:
            latest = transcripts[-1]
            content = latest.get("description", "")[len("TRANSCRIPT\n") :]
            action_reply = content or "(empty transcript)"
        else:
            action_reply = "No transcript found for the current scene/story."
    except Exception as e:
        action_reply = f"Error fetching transcript: {e}"

    append_message(state, "assistant", action_reply)
    state["last_mode"] = "monitor"
    return state
