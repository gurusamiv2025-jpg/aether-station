"""Power-user slash commands.

When a chat input starts with ``/``, we treat it as a command and
bypass the LLM. Commands return a ``SlashResult`` the UI can render as
a system message — fast, deterministic, no token spend.

Supported commands:

  /help              — list every command
  /sitrep            — full station status (telemetry + crisis + crew positions)
  /vitals [person]   — vital signs for the named crew member (defaults to Okafor)
  /reactor           — focused reactor / coolant readout
  /lore <query>      — search the lore corpus (no character, just raw results)
  /note <text>       — record a persona note for the active character
  /forget <text>     — drop a persona note matching ``text``
  /clear             — clear notes for the active character only
  /handover <key>    — explicit hand-off to another character
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SlashResult:
    command: str            # original command name (e.g. "/sitrep")
    title: str              # short heading
    body: str               # markdown body
    handover_to: Optional[str] = None  # set by /handover
    is_help: bool = False


HELP_BODY = """
**Slash commands**

| Command | Purpose |
|---|---|
| `/help` | Show this list |
| `/sitrep` | Full station status — telemetry + crisis + crew positions |
| `/vitals [person]` | Vital-signs spot-check (person key, e.g. `/vitals okafor`) |
| `/reactor` | Reactor + coolant readout |
| `/lore <query>` | Search the lore corpus directly |
| `/note <text>` | Add a persona note for the active character |
| `/forget <text>` | Drop a persona note matching `<text>` |
| `/clear` | Clear notes for the active character |
| `/handover <key>` | Hand off to another character (`/handover volkov`) |
| `/summary` | Session recap — persona notes, world state |
| `/system-prompt` | Show the active character's pure system prompt |

Slash commands don't burn LLM tokens — they're handled locally.
""".strip()


def is_slash(text: str) -> bool:
    return bool(text) and text.lstrip().startswith("/")


def parse(text: str) -> tuple[str, str]:
    """Split a slash input into (command_name, args_text)."""
    body = text.lstrip()
    if not body.startswith("/"):
        return ("", "")
    first_space = body.find(" ")
    if first_space == -1:
        return (body.lower(), "")
    return (body[:first_space].lower(), body[first_space + 1:].strip())


def dispatch(text: str, *, active_character: str, world_sim, persona_memory, retriever, cast) -> Optional[SlashResult]:
    """Run a slash command. Returns ``None`` if ``text`` isn't a slash."""
    if not is_slash(text):
        return None
    cmd, args = parse(text)

    if cmd in ("/help", "/?"):
        return SlashResult(command=cmd, title="Help", body=HELP_BODY, is_help=True)

    if cmd == "/sitrep":
        # Telemetry + crisis overview.
        from crisis import scan
        events = scan(world_sim) if world_sim else []
        lines = []
        if world_sim:
            for r in world_sim.systems.values():
                lines.append(f"- {r.fmt()}")
        body = "**Telemetry**\n" + ("\n".join(lines) if lines else "(no telemetry)")
        if events:
            body += "\n\n**Active alarms**\n"
            for e in events:
                body += f"- {e.to_banner()}\n"
        if world_sim and world_sim.crew_positions:
            body += "\n\n**Crew positions**\n"
            for k, where in world_sim.crew_positions.items():
                body += f"- `{k}`: {where}\n"
        return SlashResult(command=cmd, title="Station SITREP", body=body)

    if cmd == "/vitals":
        from character_tools import detect_and_invoke
        target = args.strip() or "okafor"
        results = detect_and_invoke("hua", f"vital signs check on {target}", world_sim)
        if not results:
            return SlashResult(command=cmd, title="Vitals", body=f"_(no vitals found for {target!r})_")
        body = "\n".join(f"- {r.summary} — {r.detail}" for r in results)
        return SlashResult(command=cmd, title=f"Vitals — {target}", body=body)

    if cmd == "/reactor":
        if not world_sim:
            return SlashResult(command=cmd, title="Reactor", body="_(no telemetry available)_")
        keys = ("reactor_a_mw", "reactor_b_mw", "lif_a_psi")
        body = "\n".join(
            f"- {world_sim.systems[k].fmt()}"
            for k in keys if k in world_sim.systems
        )
        return SlashResult(command=cmd, title="Reactor readout", body=body)

    if cmd == "/lore":
        if not args:
            return SlashResult(command=cmd, title="/lore", body="_(provide a search query)_")
        if retriever is None:
            return SlashResult(command=cmd, title="/lore", body="_(retriever unavailable)_")
        results = retriever.retrieve(args, top_k=4)
        body = "\n".join(
            f"- [{p.score:.2f}] `{p.source}` — {p.title}"
            for p in results
        ) if results else "_(no matches)_"
        return SlashResult(command=cmd, title=f"Lore search · {args!r}", body=body)

    if cmd == "/note":
        if not args:
            return SlashResult(command=cmd, title="/note", body="_(provide note text)_")
        ev = persona_memory.observe(active_character, f"For the record, {args}.")
        body = f"📝 Recorded for `{active_character}`: {args}" if ev["recorded"] else "_(nothing recorded)_"
        return SlashResult(command=cmd, title="/note", body=body)

    if cmd == "/forget":
        if not args:
            return SlashResult(command=cmd, title="/forget", body="_(provide a note to forget)_")
        ev = persona_memory.observe(active_character, f"Forget the {args} note.")
        body = f"🗑 Forgot {ev['forgot']} matching note(s) for `{active_character}`." if ev["forgot"] else "_(no match found)_"
        return SlashResult(command=cmd, title="/forget", body=body)

    if cmd == "/clear":
        # Clear notes for the active character only.
        ev = persona_memory.observe(active_character, "Clear your notes")
        body = "🧹 Cleared notes for `{}`.".format(active_character) if ev["cleared"] else "_(nothing to clear)_"
        return SlashResult(command=cmd, title="/clear", body=body)

    if cmd == "/summary":
        # Generate a quick recap from the audit log, persona memory, and (if a
        # station log was provided) recent chatter.
        from collections import Counter
        sections = []
        # Persona notes per character
        any_notes = False
        note_lines = []
        for k, items in persona_memory.facts.items():
            if not items:
                continue
            any_notes = True
            note_lines.append(f"- **{k}** ({len(items)} note(s)): " + "; ".join(items[:3]))
        if any_notes:
            sections.append("**Persona notes recorded:**\n" + "\n".join(note_lines))
        # World sim headline
        if world_sim is not None:
            sections.append(f"**Station state:** tick {world_sim.tick}, {world_sim.headline()}")
        if sections:
            return SlashResult(
                command=cmd, title="Session summary",
                body="\n\n".join(sections),
            )
        return SlashResult(
            command=cmd, title="Session summary",
            body="_(no session activity yet — try a few exchanges first)_",
        )

    if cmd == "/system-prompt":
        # Show the active character's pure (un-augmented) system prompt.
        ch = (cast or {}).get(active_character)
        if ch is None:
            return SlashResult(command=cmd, title="/system-prompt",
                               body=f"_(no active character: {active_character!r})_")
        body = ch.system_prompt
        if len(body) > 4000:
            body = body[:4000] + "…"
        return SlashResult(command=cmd, title=f"System prompt — {ch.name}",
                           body="```\n" + body + "\n```")

    if cmd == "/handover":
        target = args.strip()
        if target not in (cast or {}):
            avail = ", ".join((cast or {}).keys())
            return SlashResult(command=cmd, title="/handover", body=f"_(unknown character: {target!r}; available: {avail})_")
        return SlashResult(
            command=cmd, title="/handover",
            body=f"🔁 Handed off to `{target}`.",
            handover_to=target,
        )

    return SlashResult(command=cmd, title="Unknown command",
                       body=f"_(no such command: `{cmd}` — try `/help`)_")
