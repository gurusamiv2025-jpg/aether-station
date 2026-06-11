"""Browser-side speech recognition.

Returns raw HTML/JS that, when clicked, opens the user's browser
microphone via Web Speech Recognition and pastes the transcript into
the page. The user then confirms/edits before sending.

We can't easily inject the transcript back into a Streamlit
``st.chat_input`` because Streamlit's chat input doesn't expose a JS
API for programmatic writes. So instead we render the transcript into
a small read-only display box; the user can copy-paste into the chat
input. (This sidesteps Streamlit's lack of a stable speech component
without requiring a third-party dependency.)
"""

from __future__ import annotations


def mic_button_html(target_div_id: str, button_id: str) -> str:
    """Return HTML for a mic button + transcript display box."""
    return f"""
<button id="{button_id}" style="
    font-family: ui-monospace, monospace;
    font-size: 13px;
    background: rgba(248, 81, 73, 0.10);
    color: #f85149;
    border: 1px solid rgba(248, 81, 73, 0.4);
    border-radius: 4px;
    padding: 4px 12px;
    cursor: pointer;
    margin: 4px 0;
">🎤 Speak to the crew</button>
<div id="{target_div_id}" style="
    font-family: ui-monospace, monospace;
    font-size: 12px;
    color: #c9d1d9;
    border: 1px dashed rgba(139, 148, 158, 0.35);
    border-radius: 4px;
    padding: 6px 8px;
    margin: 4px 0;
    min-height: 22px;
"></div>
<script>
(function() {{
  const btn = document.getElementById("{button_id}");
  const out = document.getElementById("{target_div_id}");
  if (!btn || btn.dataset.bound) return;
  btn.dataset.bound = "1";
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{
    btn.textContent = "🎤 (not supported in this browser)";
    btn.disabled = true;
    return;
  }}
  const rec = new SR();
  rec.continuous = false;
  rec.interimResults = true;
  rec.lang = (document.documentElement.lang || "en-US");
  let listening = false;
  btn.addEventListener("click", function() {{
    if (listening) {{ rec.stop(); return; }}
    out.textContent = "Listening…";
    try {{ rec.start(); }} catch (e) {{ out.textContent = "Could not start mic: " + e.message; }}
  }});
  rec.onstart = function() {{ listening = true; btn.textContent = "🛑 Stop listening"; }};
  rec.onend = function() {{ listening = false; btn.textContent = "🎤 Speak to the crew"; }};
  rec.onerror = function(e) {{ out.textContent = "Mic error: " + e.error; }};
  rec.onresult = function(event) {{
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {{
      transcript += event.results[i][0].transcript;
    }}
    out.textContent = transcript.trim();
    // Try to write the transcript into the page clipboard so the user can
    // paste it into the chat input without retyping.
    if (event.results[event.results.length - 1].isFinal) {{
      try {{
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(transcript.trim());
        }}
      }} catch (_) {{}}
    }}
  }};
}})();
</script>
""".strip()
