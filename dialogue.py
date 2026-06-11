"""Inter-character dialogue chains.

Two crew members have a multi-turn back-and-forth on a user-supplied
topic. Each turn:

  1. Fetch grounding passages for the running conversation context.
  2. Inject the *other* character's last reply into this character's
     prompt as a quoted observation.
  3. Apply persona memory + station log + mood as usual.
  4. Generate the next line in character.

The result is a small in-world dialogue the user can watch — two
characters arguing or agreeing without the user typing between turns.
This is the "two bots talking to each other" mode the brief calls for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DialogueTurn:
    speaker_key: str       # character key
    speaker_name: str      # display name
    avatar: str            # emoji
    content: str           # the reply text
    sources: list = field(default_factory=list)
    trace: list = field(default_factory=list)


@dataclass
class DialogueResult:
    topic: str
    a_key: str
    b_key: str
    turns: List[DialogueTurn] = field(default_factory=list)


def _other(a_key: str, b_key: str, current_key: str) -> str:
    return b_key if current_key == a_key else a_key


def run_dialogue(
    a_key: str,
    b_key: str,
    topic: str,
    rounds: int,
    *,
    cast: dict,
    retriever,
    llm,
    build_trace_fn,
    safety_check,
    safety_refusal,
    station_log_cls=None,
    persona_memory=None,
    mood_state=None,
) -> DialogueResult:
    """Run a 2N-turn back-and-forth between two characters.

    The dependencies are passed in so this module is the same whether it's
    called from cli.py, app.py, or a test. Returns a DialogueResult with
    all turns in order.
    """
    from world_state import StationLog, format_for_prompt
    if station_log_cls is None:
        station_log_cls = StationLog

    log = station_log_cls()
    result = DialogueResult(topic=topic, a_key=a_key, b_key=b_key)

    # Each round = one reply from A, one from B.
    current_key = a_key
    previous_reply: Optional[str] = None

    for round_idx in range(rounds * 2):
        character = cast[current_key]
        other_key = _other(a_key, b_key, current_key)
        other = cast[other_key]

        # Frame the prompt: first turn opens the topic; later turns react.
        if previous_reply is None:
            prompt_text = (
                f"You are in a brief inter-crew exchange with {other.name}. "
                f"Topic: {topic}. Open with your view in 1-2 sentences."
            )
        else:
            prompt_text = (
                f"{other.name} just said:\n  \"{previous_reply}\"\n\n"
                "Respond to them in your own voice in 1-2 sentences. "
                "Agree, push back, or build on it — stay in character."
            )

        # Safety pass on the *constructed* prompt — the user's topic is the
        # untrusted input. Refusal is in voice, dialogue stops on refusal.
        verdict = safety_check(topic)
        if not verdict.allowed and verdict.category not in ("", "empty"):
            refusal = safety_refusal(current_key, verdict.category)
            result.turns.append(DialogueTurn(
                speaker_key=current_key,
                speaker_name=character.name,
                avatar=character.avatar,
                content=refusal,
                sources=[],
                trace=[],
            ))
            break

        from retrieval_bias import apply as apply_bias
        raw = retriever.retrieve(topic + " " + (previous_reply or ""), top_k=8)
        passages = apply_bias(current_key, raw, top_k=4)

        log_block = format_for_prompt(log.recent(exclude_character=current_key))
        notes_block = (
            persona_memory.render_for_prompt(current_key)
            if persona_memory else "PERSONAL NOTES: (none)"
        )
        mood_block = (
            mood_state.render_for_prompt(current_key)
            if mood_state else ""
        )
        grounding = "GROUNDING:\n" + "\n".join(
            f"- [{p.source}] {p.text[:300].replace(chr(10), ' ')}"
            for p in passages
        ) if passages else "GROUNDING: (no relevant passages)"

        system = (
            character.system_prompt
            + ("\n\n" + mood_block if mood_block else "")
            + "\n\n" + notes_block
            + "\n\n" + log_block
            + "\n\n" + grounding
        )

        from llm import ChatMessage
        reply = llm.chat(
            [ChatMessage("system", system), ChatMessage("user", prompt_text)],
            temperature=0.9,
            max_tokens=220,
        )

        log.add(current_key, character.name, reply)
        trace = build_trace_fn(topic + " " + (previous_reply or ""), passages)
        result.turns.append(DialogueTurn(
            speaker_key=current_key,
            speaker_name=character.name,
            avatar=character.avatar,
            content=reply,
            sources=[{"source": p.source, "title": p.title, "score": p.score} for p in passages],
            trace=[{"label": s.label, "detail": s.detail, "items": s.items} for s in trace],
        ))

        previous_reply = reply
        current_key = other_key

    return result
