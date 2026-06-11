"""Browser-side text-to-speech per character.

Each crew member maps to a Web Speech API voice configuration (rate,
pitch, voice-name hints). Streamlit renders a small JavaScript-driven
"🔊 Speak" button on every assistant reply that, when clicked, runs the
text through ``window.speechSynthesis`` in the user's browser.

No server-side audio is generated; this is a pure client-side feature.
Browsers ship different voices, so we provide *hints* and fall back to
the default voice if none of the hints match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class VoiceProfile:
    rate: float = 1.0      # 0.1 - 10.0
    pitch: float = 1.0     # 0.0 - 2.0
    voice_hints: tuple = () # Substring matches against window.speechSynthesis.getVoices()


# Per-character voice profiles. Tuned to match the dossiers:
#  - Park: lower pitch, slightly slower, an English/American "deliberate" voice
#  - Okafor: average rate, warmer pitch, prefers a UK/Nigerian English voice
#  - Mira-7: very steady, mid-pitch, prefers a UK female voice (alto corpus)
#  - Volkov: low pitch, slow, prefers any Russian / deep voice
#  - Hua: slightly higher pitch, faster (anxious), prefers a Chinese English voice
PROFILES: Dict[str, VoiceProfile] = {
    "park": VoiceProfile(rate=0.95, pitch=0.85,
                         voice_hints=("English", "United States", "Female")),
    "okafor": VoiceProfile(rate=1.05, pitch=1.05,
                          voice_hints=("English", "United Kingdom", "Male", "Nigerian")),
    "mira": VoiceProfile(rate=0.90, pitch=1.00,
                          voice_hints=("UK English Female", "English", "United Kingdom", "Female")),
    "volkov": VoiceProfile(rate=0.85, pitch=0.75,
                          voice_hints=("Russian", "Male", "ru-RU")),
    "hua": VoiceProfile(rate=1.10, pitch=1.15,
                          voice_hints=("Chinese", "Female", "zh-CN")),
    "garcia": VoiceProfile(rate=0.95, pitch=1.0,
                          voice_hints=("Spanish", "Male", "es-ES")),
}


def speak_button_html(character_key: str, text: str, button_id: str) -> str:
    """Return raw HTML for a "🔊 Speak" button that triggers Web Speech."""
    profile = PROFILES.get(character_key, VoiceProfile())
    # Escape for embedding inside a JS string literal.
    safe = (
        text.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("$", "\\$")
            .replace("</", "<\\/")
    )
    hints_js = "[" + ", ".join(f'"{h}"' for h in profile.voice_hints) + "]"
    return f"""
<button id="{button_id}" style="
    font-family: ui-monospace, monospace;
    font-size: 11px;
    background: rgba(88, 166, 255, 0.10);
    color: #58a6ff;
    border: 1px solid rgba(88, 166, 255, 0.4);
    border-radius: 4px;
    padding: 2px 8px;
    cursor: pointer;
    margin: 4px 0;
">🔊 Speak</button>
<script>
(function() {{
  const btn = document.getElementById("{button_id}");
  if (!btn || btn.dataset.bound) return;
  btn.dataset.bound = "1";
  btn.addEventListener("click", function() {{
    if (typeof speechSynthesis === "undefined") {{
      alert("Speech synthesis not available in this browser.");
      return;
    }}
    const text = `{safe}`;
    const u = new SpeechSynthesisUtterance(text);
    u.rate = {profile.rate};
    u.pitch = {profile.pitch};
    const hints = {hints_js};
    const voices = speechSynthesis.getVoices();
    let chosen = null;
    for (const h of hints) {{
      chosen = voices.find(v => (v.name && v.name.includes(h)) || (v.lang && v.lang.includes(h)));
      if (chosen) break;
    }}
    if (chosen) u.voice = chosen;
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  }});
}})();
</script>
""".strip()
