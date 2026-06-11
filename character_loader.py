"""Optional YAML extra-character loader.

Drop a ``.yaml`` file in ``characters_extra/`` and the cast gains a new
member at app start. Lets non-Python users contribute characters.

Schema (see ``characters_extra/garcia.yaml`` for a working example):

    key: str           # unique slug, e.g. "garcia"
    name: str          # display name
    role: str          # role line shown under the name
    avatar: str        # single emoji
    tagline: str       # short one-liner
    system_prompt: str # free-form persona prompt (GROUND TRUTH appended)
    voice:             # optional — used by the offline mock LLM
      openers: [...]
      closers: [...]
      fact_lead: str
      no_fact: str

Returns an empty list if the directory is missing or PyYAML isn't
available — never raises in the import path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from characters import Character

EXTRA_DIR = Path(__file__).parent / "characters_extra"

# Same _BASE_RULES the built-in cast uses, kept in sync by reading
# characters.py at import time so YAML characters get identical grounding.
def _base_rules() -> str:
    from characters import _BASE_RULES  # type: ignore[attr-defined]

    return _BASE_RULES


@dataclass
class ExtraCharacter:
    character: Character
    voice_profile: dict[str, Any] | None  # consumed by llm._MockClient


def _validate(payload: dict) -> None:
    required = ("key", "name", "role", "avatar", "tagline", "system_prompt")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    if not isinstance(payload["key"], str) or not payload["key"].isidentifier():
        raise ValueError(f"invalid key (must be a Python identifier): {payload['key']!r}")


def load_extras() -> list[ExtraCharacter]:
    if not EXTRA_DIR.exists():
        return []
    try:
        import yaml  # PyYAML
    except ImportError:
        return []

    extras: list[ExtraCharacter] = []
    base = _base_rules()
    for yml_path in sorted(EXTRA_DIR.glob("*.yaml")):
        try:
            payload = yaml.safe_load(yml_path.read_text(encoding="utf-8")) or {}
            _validate(payload)
        except Exception:
            # Skip malformed files rather than crashing the whole app.
            continue
        ch = Character(
            key=payload["key"],
            name=payload["name"],
            role=payload["role"],
            avatar=payload["avatar"],
            tagline=payload["tagline"],
            system_prompt=payload["system_prompt"].strip() + "\n" + base,
        )
        extras.append(ExtraCharacter(character=ch, voice_profile=payload.get("voice")))
    return extras


def merged_cast() -> dict[str, Character]:
    """Return built-in CHARACTERS merged with any YAML extras."""
    from characters import CHARACTERS

    out: dict[str, Character] = dict(CHARACTERS)
    for e in load_extras():
        out[e.character.key] = e.character
    return out


def merged_voice_profiles() -> dict[str, dict[str, Any]]:
    """Voice profiles contributed by YAML extras, keyed by character key."""
    return {e.character.key: e.voice_profile for e in load_extras() if e.voice_profile}
