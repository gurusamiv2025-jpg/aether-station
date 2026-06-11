"""MCP server exposing the Aether Station crew to GitHub Copilot.

Once configured in VS Code (see README), GitHub Copilot Chat can call:

- ``ask_crew(character, question)`` — talk to any crew member from the IDE
- ``list_crew()`` — list available characters
- ``station_log()`` — read recent in-world chatter
- ``lore_search(query, top_k)`` — query the Foundry IQ-backed knowledge layer

This makes the Aether Station cast available to developers right inside
their editor — see the Creative Apps track brief, which explicitly calls
out building MCP servers for Copilot as a creative bonus.

Run standalone:
    python mcp_server.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from characters import CHARACTERS, all_characters, get
from foundry_iq import get_retriever
from llm import ChatMessage, get_llm
from world_state import StationLog


# A single in-memory log for the lifetime of the server process.
_LOG = StationLog()
_RETRIEVER = None
_LLM = None


def _retriever():
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = get_retriever()
    return _RETRIEVER


def _llm():
    global _LLM
    if _LLM is None:
        _LLM = get_llm()
    return _LLM


# ---------------------------------------------------------------------------
# Tool implementations (pure Python; usable from both MCP and CLI)
# ---------------------------------------------------------------------------


def tool_list_crew() -> list[dict[str, str]]:
    return [
        {
            "key": c.key,
            "name": c.name,
            "role": c.role,
            "tagline": c.tagline,
        }
        for c in all_characters()
    ]


def tool_lore_search(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    passages = _retriever().retrieve(query, top_k=top_k)
    return [
        {
            "source": p.source,
            "title": p.title,
            "score": round(p.score, 3),
            "text": p.text[:1200],
        }
        for p in passages
    ]


def tool_station_log() -> list[dict[str, Any]]:
    return _LOG.to_dict()


def tool_ask_crew(character: str, question: str) -> dict[str, Any]:
    if character not in CHARACTERS:
        return {
            "error": f"unknown character: {character!r}",
            "available": list(CHARACTERS.keys()),
        }
    ch = get(character)
    passages = _retriever().retrieve(question, top_k=4)
    grounding = "GROUNDING:\n" + "\n".join(
        f"- [{p.source}] {p.text[:300].replace(chr(10), ' ')}" for p in passages
    )
    recent = _LOG.recent(exclude_character=ch.key)
    from world_state import format_for_prompt

    log_block = format_for_prompt(recent)
    system = f"{ch.system_prompt}\n\n{log_block}\n\n{grounding}"
    reply = _llm().chat(
        [ChatMessage("system", system), ChatMessage("user", question)],
        temperature=0.85,
        max_tokens=350,
    )
    _LOG.add("user", "User", question)
    _LOG.add(ch.key, ch.name, reply)
    return {
        "character": ch.key,
        "name": ch.name,
        "role": ch.role,
        "reply": reply,
        "sources": [
            {"source": p.source, "title": p.title, "score": round(p.score, 3)}
            for p in passages
        ],
    }


# ---------------------------------------------------------------------------
# MCP server wiring
# ---------------------------------------------------------------------------


def _build_mcp_server():
    """Wire the tools above into the official `mcp` server. Lazy-imported so
    the rest of the module is usable as a plain Python library even when the
    `mcp` package isn't installed."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("aether-station")

    @server.tool()
    def list_crew() -> list[dict[str, str]]:
        """List every available Aether Station character."""
        return tool_list_crew()

    @server.tool()
    def ask_crew(character: str, question: str) -> dict[str, Any]:
        """Ask a specific Aether Station character a question.

        Args:
            character: One of the keys from list_crew (e.g. 'park', 'volkov').
            question: The question to ask, in natural language.
        """
        return tool_ask_crew(character, question)

    @server.tool()
    def lore_search(query: str, top_k: int = 4) -> list[dict[str, Any]]:
        """Search the Aether Station lore corpus via Foundry IQ."""
        return tool_lore_search(query, top_k)

    @server.tool()
    def station_log() -> list[dict[str, Any]]:
        """Get recent in-world conversation history (user + characters)."""
        return tool_station_log()

    return server


# ---------------------------------------------------------------------------
# CLI fallback (so you can demo the tools without an MCP client)
# ---------------------------------------------------------------------------


def _cli() -> int:
    """Quick manual driver: ``python mcp_server.py cli ask_crew park "..."``."""
    args = sys.argv[2:]
    if not args:
        print("usage: python mcp_server.py cli <tool> [args...]")
        print("tools: list_crew, ask_crew, lore_search, station_log")
        return 1
    name, *rest = args
    if name == "list_crew":
        print(json.dumps(tool_list_crew(), indent=2))
    elif name == "ask_crew" and len(rest) >= 2:
        print(json.dumps(tool_ask_crew(rest[0], " ".join(rest[1:])), indent=2))
    elif name == "lore_search" and rest:
        top_k = int(rest[1]) if len(rest) > 1 else 4
        print(json.dumps(tool_lore_search(rest[0], top_k), indent=2))
    elif name == "station_log":
        print(json.dumps(tool_station_log(), indent=2))
    else:
        print(f"unknown tool or bad args: {name} {rest}")
        return 1
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        return _cli()
    try:
        server = _build_mcp_server()
    except ImportError:
        print(
            "The `mcp` package isn't installed. Install with `pip install mcp` "
            "or run `python mcp_server.py cli <tool>` to use the tools "
            "directly without an MCP client.",
            file=sys.stderr,
        )
        return 2
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
