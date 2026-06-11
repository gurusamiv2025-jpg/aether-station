"""Per-character retrieval bias.

Different characters care about different things, and a good chatbot
should reflect that. When Park asks the lore corpus about HB-441, she's
thinking about containment and the commander's responsibility; Okafor
is thinking about cell biology. Same query, different priorities.

This module lets us re-score generic retrieval results so that each
character's reply is grounded in passages weighted toward what *they*
would actually pay attention to.

The mechanism:

    final_score = base_score * folder_weight(character, source) * file_boost(character, source)

Weights default to 1.0 (no change). Negative scores are clamped to 0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class BiasProfile:
    # Folder weights — multiplied into the base score when the passage
    # source matches `lore/<folder>/...`.
    folder: dict
    # Per-file boosts — multiplied in for specific dossiers/incidents the
    # character has personal stakes in.
    file: dict


# Built-in character biases. Each captures something true from the dossiers.
PROFILES: dict[str, BiasProfile] = {
    "park": BiasProfile(
        # Park's brain: operations + incidents > crew chatter.
        folder={"world": 1.2, "incidents": 1.35, "crew": 0.95},
        file={
            "lore/crew/park.md": 1.4,
            "lore/crew/park-service.md": 1.3,
            "lore/incidents/halberd.md": 1.5,  # her personal file
            "lore/world/factions.md": 1.2,
        },
    ),
    "okafor": BiasProfile(
        # Okafor: science + his own work first.
        folder={"world": 1.0, "incidents": 1.25, "crew": 1.1},
        file={
            "lore/incidents/hb-441.md": 1.6,  # his obsession
            "lore/crew/okafor.md": 1.3,
            "lore/world/timeline.md": 1.15,  # discovery history
        },
    ),
    "mira": BiasProfile(
        # Mira sees everything but slightly favours world state + own file.
        folder={"world": 1.15, "incidents": 1.1, "crew": 1.05},
        file={
            "lore/crew/mira.md": 1.25,
            "lore/world/mira-commissioning.md": 1.35,
            "lore/world/station.md": 1.2,
        },
    ),
    "volkov": BiasProfile(
        # Volkov: reactor & engineering above all.
        folder={"world": 1.1, "incidents": 1.4, "crew": 0.9},
        file={
            "lore/incidents/coolant-leak.md": 1.6,  # the eleven seconds
            "lore/incidents/comms-blackout.md": 1.2,
            "lore/crew/volkov.md": 1.3,
            "lore/world/station.md": 1.15,
        },
    ),
    "hua": BiasProfile(
        # Hua: crew welfare + medical context.
        folder={"world": 1.0, "incidents": 1.15, "crew": 1.25},
        file={
            "lore/crew/hua.md": 1.3,
            "lore/crew/okafor.md": 1.4,  # the colleague she watches
            "lore/incidents/hb-441.md": 1.25,
        },
    ),
}


def _folder_of(source: str) -> str:
    # e.g. "lore/incidents/halberd.md" -> "incidents"
    parts = source.split("/")
    if len(parts) >= 2 and parts[0] == "lore":
        return parts[1]
    return ""


def apply(character_key: str, passages: List, *, top_k: int | None = None):
    """Re-score and re-sort passages for a character. Pure function.

    Each passage is expected to have ``score`` and ``source`` attributes
    (the :class:`foundry_iq.Passage` dataclass fits).
    """
    profile = PROFILES.get(character_key)
    if profile is None or not passages:
        return list(passages)[:top_k] if top_k else list(passages)

    rescored = []
    for p in passages:
        folder = _folder_of(p.source)
        f_weight = profile.folder.get(folder, 1.0)
        file_boost = profile.file.get(p.source, 1.0)
        new_score = max(0.0, p.score * f_weight * file_boost)
        # Don't mutate the input; create a new Passage if possible, else
        # fall back to a shallow copy.
        try:
            from foundry_iq import Passage
            rescored.append(Passage(text=p.text, source=p.source, score=new_score))
        except Exception:
            p_copy = type(p)(text=p.text, source=p.source, score=new_score)
            rescored.append(p_copy)
    rescored.sort(key=lambda x: x.score, reverse=True)
    return rescored[:top_k] if top_k else rescored
