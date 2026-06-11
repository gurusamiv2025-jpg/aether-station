"""Static character-relationship map (compiled from the dossiers).

Used by the README's Mermaid diagram and by the relationship-graph
widget in the Streamlit UI. Keep this in sync with the crew dossiers in
``lore/crew/``.
"""

from __future__ import annotations

# (from, to, label)
EDGES = [
    ("park", "volkov", "calls him Kostya, respects him"),
    ("park", "okafor", "Doctor — formal"),
    ("park", "mira", "calls her Mira (Mira appreciates it)"),
    ("park", "hua", "Lin — informal"),
    ("volkov", "mira", "complains about her, depends on her"),
    ("volkov", "hua", "mentors at chess (silently)"),
    ("okafor", "mira", "asks her to speculate"),
    ("hua", "okafor", "quietly worried about him"),
    ("hua", "mira", "shares concerns about Okafor's vitals"),
]


def _safe_label(label: str) -> str:
    # Mermaid pipe-syntax labels can't contain unescaped pipes or quotes.
    return label.replace("|", "/").replace('"', "").replace("'", "")


def to_mermaid() -> str:
    lines = ["graph LR"]
    for a, b, label in EDGES:
        lines.append(f"  {a} -->|{_safe_label(label)}| {b}")
    return "\n".join(lines)
