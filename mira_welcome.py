"""Mira-7's first-visit welcome monologue.

The first time a visitor opens the app (no histories yet), Mira-7
greets them, names the cast, and points at the sidebar. This gives the
demo a clean "first impression" so judges aren't staring at an empty
chat panel.

The welcome is purely cosmetic: it isn't logged to the station log or
counted in analytics. Pressing "Clear conversation" makes it reappear.
"""

from __future__ import annotations


WELCOME_LINES = [
    "Welcome aboard Aether Station. I'm Mira-7, your seventh-generation "
    "station AI — alto voice, deliberate manner. You can speak with any "
    "of the crew via the sidebar.",

    "Cmdr. Park runs the place. Dr. Okafor is in Ring 3 with sample "
    "HB-441 and will tell you more about it than you asked. Chief Volkov "
    "is in engineering and will mention the eleven-second isolation delay "
    "I owe him from February. Junior medic Lin Hua is on her first "
    "rotation and is, in my opinion, the most observant person on this "
    "rotation.",

    "Click any crew member on the left to start, or pick a **Scenario** "
    "for a one-tap guided demo. If you want two of us to talk to each "
    "other, the **Dialogue** panel below sets that up. Every reply is "
    "grounded in our station logs — open the 📚 Grounding expander on "
    "any answer to see what we cited.",

    "Logged.",
]


def build_welcome_turn(lang: str = "en") -> dict:
    """Return a turn-dict the UI can render as if it were a real assistant turn."""
    try:
        from i18n import t
        body = "\n\n".join(
            t(k, lang) for k in ("welcome_par1", "welcome_par2", "welcome_par3", "welcome_par4")
        )
    except Exception:
        body = "\n\n".join(WELCOME_LINES)
    return {
        "role": "assistant",
        "content": body,
        "character": "mira",
        "sources": [],
        "trace": [],
        "is_welcome": True,
    }
