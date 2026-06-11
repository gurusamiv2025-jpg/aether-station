"""Aether Station — Streamlit chat UI.

Multi-character chatbot with grounded responses via Foundry IQ.

Run: ``streamlit run app.py``
"""

from __future__ import annotations

from typing import List

import streamlit as st
from dotenv import load_dotenv

from analytics import Metrics, render_metrics_text
from audit import AuditLog
from drift import score_recent as score_drift
from i18n import LANGUAGES, t as i18n_t
from mood import MoodState
from character_tools import detect_and_invoke as detect_tools, render_for_prompt as render_tools
from crisis import render_for_prompt as render_crisis, scan as scan_crises
from handover import detect as detect_handover, render_for_prompt as render_handover
from memo import MemoBook
from cost import CostEstimate
from perf import Timings, timer as perf_timer
from persistence import (
    DEFAULT_PATH as PERSIST_DEFAULT,
    apply as persistence_apply,
    read_from as persistence_read,
    serialize as persistence_serialize,
    write_to as persistence_write,
)
from slash import dispatch as slash_dispatch, is_slash
from voice_input import mic_button_html
from tts import speak_button_html
from world_sim import StationSim
from persona_memory import PersonaMemory
from character_loader import merged_cast
from director import StationEvent, maybe_event, refusal_event
from foundry_iq import Passage, get_retriever
from llm import ChatMessage, get_llm
from reasoning import build_trace
from safety import check_input, refusal_for
from scenarios import SCENARIOS
from transcript import (
    apply_to_state,
    from_json as transcript_from_json,
    to_json as transcript_to_json,
    to_markdown as transcript_to_markdown,
)
from world_state import StationLog, format_for_prompt

# Cast = built-in characters merged with any YAML extras in characters_extra/.
CHARACTERS = merged_cast()


def all_characters():
    return list(CHARACTERS.values())


def get(key):
    return CHARACTERS[key]

load_dotenv()

st.set_page_config(
    page_title="Aether Station",
    page_icon="🛰️",
    layout="wide",
)


_THEME_CSS = """
<style>
:root { --aether-dim: #8b949e; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0b1020 0%, #11182d 100%);
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
  font-family: ui-monospace, "JetBrains Mono", "Cascadia Code", Menlo, Consolas, monospace;
  letter-spacing: 0.04em;
}
h1, h2, h3 {
  font-family: ui-monospace, "JetBrains Mono", "Cascadia Code", Menlo, Consolas, monospace;
  letter-spacing: 0.02em;
}
.aether-tag {
  display: inline-block;
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: var(--aether-dim);
  border: 1px solid rgba(139, 148, 158, 0.35);
  border-radius: 4px;
  padding: 1px 6px;
  margin-right: 4px;
}
.aether-event {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  border-left: 3px solid #58a6ff;
  padding: 6px 10px;
  margin: 6px 0;
  background: rgba(88, 166, 255, 0.06);
}
.aether-hud {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  color: var(--aether-dim);
  border-top: 1px dashed rgba(139, 148, 158, 0.35);
  padding-top: 8px;
  margin-top: 8px;
}
</style>
"""

st.markdown(_THEME_CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def _retriever():
    return get_retriever()


@st.cache_resource(show_spinner=False)
def _llm():
    return get_llm()


def _init_state() -> None:
    if "histories" not in st.session_state:
        st.session_state.histories = {k: [] for k in CHARACTERS}
    if "active" not in st.session_state:
        st.session_state.active = "park"
    if "round_table" not in st.session_state:
        st.session_state.round_table = False
    if "round_table_pair" not in st.session_state:
        st.session_state.round_table_pair = ("park", "volkov")
    if "round_table_history" not in st.session_state:
        st.session_state.round_table_history = []
    if "station_log" not in st.session_state:
        st.session_state.station_log = StationLog()
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "metrics" not in st.session_state:
        st.session_state.metrics = Metrics()
    if "director_enabled" not in st.session_state:
        st.session_state.director_enabled = True
    if "last_event_turn" not in st.session_state:
        st.session_state.last_event_turn = -10  # so first event can fire
    if "event_feed" not in st.session_state:
        st.session_state.event_feed = []
    if "topic_cooldowns" not in st.session_state:
        st.session_state.topic_cooldowns = {}
    if "persona_memory" not in st.session_state:
        st.session_state.persona_memory = PersonaMemory()
    if "mood_state" not in st.session_state:
        st.session_state.mood_state = MoodState()
    if "world_sim" not in st.session_state:
        st.session_state.world_sim = StationSim()
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = AuditLog()
    if "ui_lang" not in st.session_state:
        st.session_state.ui_lang = "en"
    if "memo_book" not in st.session_state:
        st.session_state.memo_book = MemoBook()
    if "cost" not in st.session_state:
        st.session_state.cost = CostEstimate()
    if "timings" not in st.session_state:
        st.session_state.timings = Timings()


_init_state()


def _format_grounding(passages: List[Passage]) -> str:
    if not passages:
        return "GROUNDING: (no relevant passages — answer in voice and note the gap)"
    lines = ["GROUNDING:"]
    for p in passages:
        snippet = p.text.strip().replace("\n", " ")
        if len(snippet) > 600:
            snippet = snippet[:600] + "…"
        lines.append(f"- [{p.source}] {snippet}")
    return "\n".join(lines)


def _build_messages(character, history, user_input, passages, tool_block: str = ""):
    log_entries = st.session_state.station_log.recent(exclude_character=character.key)
    log_block = format_for_prompt(log_entries)
    notes_block = st.session_state.persona_memory.render_for_prompt(character.key)
    mood_block = st.session_state.mood_state.render_for_prompt(character.key)
    telemetry_block = st.session_state.world_sim.render_for_prompt()
    system_parts = [
        character.system_prompt, mood_block, notes_block, telemetry_block, log_block,
    ]
    if tool_block:
        system_parts.append(tool_block)
    # Crisis context — only adds a block when world_sim has out-of-nominal readings.
    crisis_block = render_crisis(scan_crises(st.session_state.world_sim))
    if crisis_block:
        system_parts.append(crisis_block)
    # Handover hint — only when the user's question is in another lane.
    handover_block = render_handover(detect_handover(character.key, user_input))
    if handover_block:
        system_parts.append(handover_block)
    system_parts.append(_format_grounding(passages))
    system = "\n\n".join(system_parts)
    msgs = [ChatMessage(role="system", content=system)]
    for turn in history[-8:]:
        msgs.append(ChatMessage(role=turn["role"], content=turn["content"]))
    msgs.append(ChatMessage(role="user", content=user_input))
    return msgs


def _respond(character, user_input):
    # Persona memory: catch "for the record" / "forget" / etc. *before* safety,
    # so the recording is observed even when the rest of the message is benign.
    memory_event = st.session_state.persona_memory.observe(character.key, user_input)
    st.session_state.audit_log.memory_event(character.key, memory_event)
    verdict = check_input(user_input)
    st.session_state.audit_log.safety(character.key, verdict.category, verdict.allowed)
    st.session_state.mood_state.observe(
        character.key, user_input,
        is_refusal=not verdict.allowed and verdict.category not in ("", "empty"),
    )
    st.session_state.world_sim.advance()
    if not verdict.allowed and verdict.category not in ("", "empty"):
        refusal = refusal_for(character.key, verdict.category)
        turn = {
            "role": "assistant",
            "content": refusal,
            "character": character.key,
            "sources": [],
            "trace": [{
                "label": "Safety layer",
                "detail": f"Input flagged as `{verdict.category}` — refused in character.",
                "items": [],
            }],
            "refused": True,
        }
        st.session_state.metrics.record_turn(character.key, turn)
        if st.session_state.director_enabled:
            ev = refusal_event(user_input)
            st.session_state.event_feed.append({
                "speaker": ev.speaker, "avatar": ev.avatar, "body": ev.body,
                "category": ev.category,
            })
        return turn
    # Character tools: detect and invoke any tools whose triggers match the user input.
    tool_results = detect_tools(character.key, user_input, st.session_state.world_sim)
    from retrieval_bias import apply as apply_bias
    with perf_timer(st.session_state.timings, "retrieval"):
        raw_passages = _retriever().retrieve(user_input, top_k=8)
        passages = apply_bias(character.key, raw_passages, top_k=4)
    msgs = _build_messages(
        character, st.session_state.histories[character.key], user_input, passages,
        tool_block=render_tools(tool_results),
    )
    with perf_timer(st.session_state.timings, "llm"):
        reply = _llm().chat(msgs, temperature=0.85, max_tokens=350)
    # Cost estimate (offline mock counts as $0 since we mark it so).
    if _llm().name != "mock":
        sys_msg = next((m.content for m in msgs if m.role == "system"), "")
        st.session_state.cost.record(sys_msg, user_input, reply)
    trace = build_trace(user_input, passages)
    turn = {
        "role": "assistant",
        "content": reply,
        "character": character.key,
        "sources": [{"source": p.source, "title": p.title, "score": p.score} for p in passages],
        "trace": [{"label": s.label, "detail": s.detail, "items": s.items} for s in trace],
    }
    if memory_event["recorded"] or memory_event["forgot"] or memory_event["cleared"]:
        turn["memory_event"] = memory_event
    if tool_results:
        turn["tool_results"] = [
            {"tool": r.tool, "summary": r.summary, "detail": r.detail}
            for r in tool_results
        ]
    st.session_state.metrics.record_turn(character.key, turn)
    st.session_state.memo_book.record_turn(character.key, turn)
    # Crisis-first-detected: record once when any system goes alarm.
    from crisis import scan as _scan_now
    for ev in _scan_now(st.session_state.world_sim):
        if ev.severity == "alarm":
            st.session_state.memo_book.record_crisis_first(ev.system_name)
            break
    return turn


def _commit_to_log(role, character_key, speaker, text):
    st.session_state.station_log.add(
        character=character_key if role == "assistant" else "user",
        speaker=speaker,
        raw=text,
    )


def _consume_pending_prompt():
    pending = st.session_state.pending_prompt
    if pending:
        st.session_state.pending_prompt = None
    return pending


def _maybe_fire_director_event():
    if not st.session_state.director_enabled:
        return None
    ev = maybe_event(
        st.session_state.station_log.entries,
        st.session_state.last_event_turn,
        st.session_state.topic_cooldowns,
    )
    if ev is None:
        return None
    last_turn = (
        st.session_state.station_log.entries[-1].turn
        if st.session_state.station_log.entries
        else 0
    )
    st.session_state.last_event_turn = last_turn
    st.session_state.event_feed.append({
        "speaker": ev.speaker, "avatar": ev.avatar, "body": ev.body, "category": ev.category,
    })
    return ev


def _render_reasoning_panel(trace_items):
    if not trace_items:
        return
    with st.expander("🧠 Reasoning trace — how this answer was built", expanded=False):
        for step in trace_items:
            st.markdown(f"**{step['label']}** — {step['detail']}")
            if step["items"]:
                for it in step["items"]:
                    st.markdown(f"- {it}")
            else:
                st.markdown("*(synthesized in the reply above)*")


def _render_sources(sources):
    if not sources:
        return
    with st.expander(f"📚 Grounding ({len(sources)} passages from the lore bible)", expanded=False):
        for s in sources:
            st.markdown(
                f"- **{s['title']}** — `{s['source']}` &nbsp; "
                f"<span class='aether-tag'>score {s['score']:.2f}</span>",
                unsafe_allow_html=True,
            )


def _render_assistant_turn(turn):
    ch = get(turn["character"])
    with st.chat_message("assistant", avatar=ch.avatar):
        st.markdown(f"**{ch.name}** &nbsp;·&nbsp; *{ch.role}*")
        if turn.get("refused"):
            st.warning("Input refused by safety layer — character stayed in voice.", icon="🛡️")
        me = turn.get("memory_event")
        if me:
            bits = []
            if me["recorded"]:
                bits.append(f"📝 noted: {', '.join(me['recorded'][:2])}")
            if me["forgot"]:
                bits.append(f"🗑️ forgot {me['forgot']} note(s)")
            if me["cleared"]:
                bits.append("🗑️ cleared all notes")
            if bits:
                st.caption(" · ".join(bits))
        st.markdown(turn["content"])
        # Tool results badge.
        for tr in turn.get("tool_results") or []:
            extra = f" — {tr['detail']}" if tr.get("detail") else ""
            st.markdown(
                f"<span class='aether-tag'>🔧 {tr['tool']}</span> "
                f"{tr['summary']}{extra}",
                unsafe_allow_html=True,
            )
        # Per-character TTS speak button.
        import uuid as _uuid
        btn_id = f"speak-{_uuid.uuid4().hex[:8]}"
        st.markdown(speak_button_html(turn["character"], turn["content"], btn_id), unsafe_allow_html=True)
        _render_reasoning_panel(turn.get("trace") or [])
        _render_sources(turn.get("sources") or [])


def _render_event(ev_dict):
    st.markdown(
        f"<div class='aether-event'>{ev_dict['avatar']} <b>{ev_dict['speaker']}</b>"
        f" &nbsp;·&nbsp; {ev_dict['body']}</div>",
        unsafe_allow_html=True,
    )


def _render_history(history):
    for turn in history:
        if turn["role"] == "user":
            with st.chat_message("user"):
                st.markdown(turn["content"])
        else:
            _render_assistant_turn(turn)


with st.sidebar:
    st.title("🛰️ Aether Station")
    st.caption("Multi-character chatbot · Foundry IQ grounded")

    # Language picker (i18n for the welcome monologue + key labels).
    lang_label = i18n_t("ui_language", st.session_state.ui_lang)
    new_lang = st.selectbox(
        lang_label,
        list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code],
        index=list(LANGUAGES.keys()).index(st.session_state.ui_lang),
        key="ui_lang_picker",
    )
    if new_lang != st.session_state.ui_lang:
        st.session_state.ui_lang = new_lang
        st.rerun()

    st.markdown("### Crew")
    for ch in all_characters():
        if st.button(
            f"{ch.avatar}  {ch.name}",
            key=f"pick-{ch.key}",
            use_container_width=True,
            type="primary" if ch.key == st.session_state.active else "secondary",
        ):
            st.session_state.active = ch.key
            st.session_state.round_table = False
            st.rerun()

    st.divider()
    st.markdown("### Scenarios")
    st.caption("One-click guided demos.")
    for sc in SCENARIOS:
        if st.button(
            f"{sc.icon}  {sc.name}",
            key=f"scenario-{sc.key}",
            use_container_width=True,
            help=sc.summary,
        ):
            st.session_state.active = sc.active_character
            if sc.round_table_pair:
                st.session_state.round_table = True
                st.session_state.round_table_pair = sc.round_table_pair
            else:
                st.session_state.round_table = False
            st.session_state.pending_prompt = sc.starter_prompt
            st.rerun()

    st.divider()
    st.markdown("### Round Table")
    st.session_state.round_table = st.toggle(
        "Enable round table",
        value=st.session_state.round_table,
    )
    if st.session_state.round_table:
        keys = list(CHARACTERS.keys())
        a, b = st.session_state.round_table_pair
        a = st.selectbox("Voice A", keys, index=keys.index(a))
        b = st.selectbox(
            "Voice B",
            keys,
            index=keys.index(b if b != a else next(k for k in keys if k != a)),
        )
        st.session_state.round_table_pair = (a, b)


    st.divider()
    st.markdown("### 🎙️ Voice input")
    st.caption("Speak into your mic; transcript copied to your clipboard. Paste into the chat.")
    st.markdown(mic_button_html("voice_transcript_box", "voice_mic_btn"), unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🎬 Director agent")
    st.session_state.director_enabled = st.toggle(
        "Ambient station events",
        value=st.session_state.director_enabled,
        help="A 6th invisible agent injects in-world events (Mira-7 broadcasts, audit logs) based on conversation topic.",
    )
    if st.session_state.event_feed:
        with st.expander(f"Event feed ({len(st.session_state.event_feed)})", expanded=False):
            for ev in reversed(st.session_state.event_feed[-8:]):
                st.markdown(
                    f"<span class='aether-tag'>{ev['category']}</span> "
                    f"**{ev['speaker']}** — {ev['body']}",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("### 📝 Personal notes")
    st.caption('Say "for the record, X" to drop a note; "forget the X note" to remove it.')
    pm_total = sum(len(v) for v in st.session_state.persona_memory.facts.values())
    if pm_total == 0:
        st.caption("_(no notes recorded yet)_")
    else:
        with st.expander(f"Show notes ({pm_total})", expanded=False):
            for k, items in st.session_state.persona_memory.facts.items():
                if not items:
                    continue
                ch = get(k)
                st.markdown(f"**{ch.avatar} {ch.name}**")
                for it in items:
                    st.markdown(f"- {it}")

    st.divider()
    st.markdown("### 📡 Live telemetry")
    st.caption("Station systems update each turn — characters can cite these values.")
    sim = st.session_state.world_sim
    st.markdown(
        f"<div class='aether-hud'>"
        f"TICK · <b>{sim.tick}</b><br/>"
        + "<br/>".join(
            f"{r.name} · <b>{r.fmt().split(': ', 1)[1]}</b>"
            for r in list(sim.systems.values())[:5]
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### 🪞 Personality drift")
    drift_rows: list[str] = []
    for ch in all_characters():
        replies = [t["content"] for t in st.session_state.histories[ch.key] if t.get("role") == "assistant"]
        rep = score_drift(ch.key, replies)
        chip = f"<span class='aether-tag'>{rep.label()}</span>"
        drift_rows.append(f"- {ch.avatar} **{ch.name}** {chip} · score {rep.score:.2f}")
    st.markdown("\n".join(drift_rows), unsafe_allow_html=True)
    st.caption("Detector pattern-matches signature openers/closers/idioms; flags drift below 0.25.")

    st.divider()
    st.markdown("### 📋 Audit log")
    al = st.session_state.audit_log
    st.caption(f"{len(al)} compliance events recorded this session.")
    if len(al) > 0:
        st.download_button(
            "Download audit CSV",
            data=al.to_csv(),
            file_name="aether-audit.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    st.markdown("### Station log")
    log_entries = st.session_state.station_log.entries
    st.caption(f"{len(log_entries)} recent entries — shared world memory.")
    if log_entries:
        with st.expander("View station log", expanded=False):
            for e in reversed(log_entries[-8:]):
                st.markdown(
                    f"<span class='aether-tag'>T{e.turn}</span> "
                    f"**{e.speaker}** · {e.summary}",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("### 🎭 Inter-character dialogue")
    st.caption("Watch two crew members debate a topic without you in the middle.")
    keys_all = list(CHARACTERS.keys())
    col1, col2 = st.columns(2)
    da = col1.selectbox("A", keys_all, index=keys_all.index("park"), key="dialog_a")
    default_b = "volkov" if "volkov" in keys_all and "volkov" != da else next(k for k in keys_all if k != da)
    db = col2.selectbox("B", keys_all, index=keys_all.index(default_b), key="dialog_b")
    dtopic = st.text_input("Topic", value="the HB-441 anomaly", key="dialog_topic")
    drounds = st.slider("Rounds", 1, 4, 2, key="dialog_rounds")
    if st.button("▶ Run dialogue", use_container_width=True, type="primary"):
        if da == db:
            st.warning("Pick two different characters.")
        else:
            from dialogue import run_dialogue
            res = run_dialogue(
                da, db, dtopic, rounds=drounds,
                cast=CHARACTERS,
                retriever=_retriever(),
                llm=_llm(),
                build_trace_fn=build_trace,
                safety_check=check_input,
                safety_refusal=refusal_for,
                mood_state=st.session_state.mood_state,
                persona_memory=st.session_state.persona_memory,
            )
            st.session_state.dialogue_last = [
                {"speaker_key": t.speaker_key, "speaker_name": t.speaker_name, "avatar": t.avatar,
                 "content": t.content, "sources": t.sources, "trace": t.trace}
                for t in res.turns
            ]
            st.success(f"Ran {len(res.turns)} turn(s). See main pane.")
            st.rerun()

    st.divider()
    st.markdown("### 📈 Mood over time")
    history = st.session_state.mood_state.history
    if any(history.values()):
        import pandas as pd
        rows = []
        for ch_key, snaps in history.items():
            for snap in snaps:
                rows.append({"turn": snap["turn"], "character": ch_key, "openness": snap["openness"]})
        if rows:
            df = pd.DataFrame(rows)
            pivot = df.pivot_table(index="turn", columns="character", values="openness")
            st.line_chart(pivot, height=160)

    st.markdown("**Current mood radar**")
    radar_rows = []
    for ch in all_characters():
        m = st.session_state.mood_state.get(ch.key)
        for axis, val in (("energy", m.energy), ("focus", m.focus), ("openness", m.openness)):
            radar_rows.append({"axis": axis, "character": ch.key, "value": val})
    if radar_rows:
        import pandas as pd
        rdf = pd.DataFrame(radar_rows).pivot_table(index="axis", columns="character", values="value")
        st.bar_chart(rdf, height=160)
        st.caption("Energy / focus / openness per character (1.0 = max).")

    st.divider()
    st.markdown("### 📔 Session memos")
    mb = st.session_state.memo_book
    if len(mb) == 0:
        st.caption("_(memos appear when notable moments happen — first reply, first crisis, etc.)_")
    else:
        st.markdown(mb.to_markdown())

    st.divider()
    st.markdown("### 🔎 System-prompt inspector")
    with st.expander("Show next-reply system prompt", expanded=False):
        ch = get(st.session_state.active)
        mood_p = st.session_state.mood_state.render_for_prompt(ch.key)
        notes_p = st.session_state.persona_memory.render_for_prompt(ch.key)
        telemetry_p = st.session_state.world_sim.render_for_prompt()
        full = (
            ch.system_prompt
            + "\n\n" + mood_p
            + "\n\n" + notes_p
            + "\n\n" + telemetry_p
            + "\n\n(GROUNDING block is filled in once the user types a query)"
        )
        st.code(full[:4000] + ("…" if len(full) > 4000 else ""), language="markdown")

    st.divider()
    st.markdown("### 🧠 Crew mood")
    with st.expander("Show moods", expanded=False):
        for ch in all_characters():
            mood = st.session_state.mood_state.get(ch.key)
            st.markdown(
                f"- {ch.avatar} **{ch.name}** — {mood.label()} "
                f"<span class='aether-tag'>E {mood.energy:.2f}</span>"
                f"<span class='aether-tag'>F {mood.focus:.2f}</span>"
                f"<span class='aether-tag'>O {mood.openness:.2f}</span>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("### 🕸️ Crew relationships")
    with st.expander("Show crew graph", expanded=False):
        from relationships import to_mermaid
        try:
            st.markdown(f"```mermaid\n{to_mermaid()}\n```")
        except Exception:
            st.code(to_mermaid(), language="mermaid")

    st.divider()
    st.markdown("### 📊 Session analytics")
    st.markdown(render_metrics_text(st.session_state.metrics, get))

    st.divider()
    st.markdown("### ⏱️ Performance")
    st.markdown(st.session_state.timings.render(), unsafe_allow_html=True)

    st.divider()
    st.markdown("### 💵 Cost estimate")
    st.markdown(st.session_state.cost.render(), unsafe_allow_html=True)

    st.divider()
    st.markdown("### 💾 Persist full state")
    st.caption(
        "Snapshot world sim, persona memory, mood, audit, and memos to disk "
        "so they survive a refresh."
    )
    save_path = st.text_input("File path", value=str(PERSIST_DEFAULT), key="persist_path")
    col_a, col_b = st.columns(2)
    if col_a.button("💾 Save", use_container_width=True):
        try:
            from pathlib import Path
            persistence_write(
                Path(save_path),
                world_sim=st.session_state.world_sim,
                persona_memory=st.session_state.persona_memory,
                mood_state=st.session_state.mood_state,
                audit_log=st.session_state.audit_log,
                memo_book=st.session_state.memo_book,
            )
            st.success(f"Saved to {save_path}")
        except Exception as exc:
            st.error(f"Save failed: {exc}")
    if col_b.button("📂 Load", use_container_width=True):
        try:
            payload = persistence_read(save_path)
            restored = persistence_apply(
                payload,
                world_sim_cls=StationSim,
                persona_memory_cls=PersonaMemory,
                mood_state_cls=MoodState,
                audit_log_cls=AuditLog,
                memo_book_cls=MemoBook,
            )
            for k, v in restored.items():
                st.session_state[k] = v
            st.success("Loaded — refreshing")
            st.rerun()
        except Exception as exc:
            st.error(f"Load failed: {exc}")

    st.divider()
    st.markdown("### ⬇️ Export / ⬆️ Import")
    md_data = transcript_to_markdown(
        st.session_state.histories,
        st.session_state.round_table_history,
        get,
    )
    json_data = transcript_to_json(
        st.session_state.histories,
        st.session_state.round_table_history,
        st.session_state.station_log.entries,
    )
    st.download_button(
        "Download as Markdown",
        data=md_data,
        file_name="aether-transcript.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.download_button(
        "Download as JSON",
        data=json_data,
        file_name="aether-session.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded = st.file_uploader(
        "Resume from JSON",
        type=["json"],
        accept_multiple_files=False,
        help="Upload a session exported earlier — characters resume where they left off.",
    )
    if uploaded is not None and st.button("↪️ Load uploaded session", use_container_width=True):
        try:
            payload = transcript_from_json(uploaded.getvalue().decode("utf-8"))
            applied = apply_to_state(payload, StationLog)
            for k, v in applied["histories"].items():
                if k in st.session_state.histories:
                    st.session_state.histories[k] = v
            st.session_state.round_table_history = applied["round_table_history"]
            st.session_state.station_log = applied["station_log"]
            st.success("Session resumed.")
            st.rerun()
        except Exception as exc:
            st.error(f"Couldn't load session: {exc}")

    st.divider()
    backend = _retriever().name
    llm_backend = _llm().name
    st.markdown("### Status HUD")
    st.markdown(
        f"<div class='aether-hud'>"
        f"RETRIEVAL · <b>{backend}</b><br/>"
        f"LLM · <b>{llm_backend}</b><br/>"
        f"SAFETY · <b>active</b><br/>"
        f"DIRECTOR · <b>{'on' if st.session_state.director_enabled else 'off'}</b><br/>"
        f"REACTOR · A (B offline)<br/>"
        f"CREW · {len(CHARACTERS)} online"
        f"</div>",
        unsafe_allow_html=True,
    )
    if backend == "local-tfidf":
        st.info("Offline retrieval mode. See FOUNDRY_IQ_SETUP.md for live Foundry IQ.", icon="ℹ️")
    if llm_backend == "mock":
        st.info("Demo mock LLM (per-character voice). Set Azure OpenAI env vars for real chat.", icon="🛠️")

    if st.button("🧹 Clear conversation", use_container_width=True):
        st.session_state.histories = {k: [] for k in CHARACTERS}
        st.session_state.round_table_history = []
        st.session_state.station_log = StationLog()
        st.session_state.pending_prompt = None
        st.session_state.metrics = Metrics()
        st.session_state.event_feed = []
        st.session_state.last_event_turn = -10
        st.session_state.topic_cooldowns = {}
        st.session_state.persona_memory = PersonaMemory()
        st.session_state.mood_state = MoodState()
        st.session_state.world_sim = StationSim()
        st.session_state.audit_log = AuditLog()
        st.session_state.memo_book = MemoBook()
        st.session_state.cost = CostEstimate()
        st.session_state.pop("dialogue_last", None)
        st.rerun()


# --- Main pane ---


if st.session_state.get("dialogue_last"):
    st.markdown("## 🎭 Inter-character dialogue")
    for t in st.session_state.dialogue_last:
        with st.chat_message("assistant", avatar=t["avatar"]):
            st.markdown(f"**{t['speaker_name']}**")
            st.markdown(t["content"])
    if st.button("Clear dialogue", key="clear_dialogue_main"):
        st.session_state.pop("dialogue_last", None)
        st.rerun()
    st.divider()

if st.session_state.get("dialogue_last"):
    st.markdown("## 🎭 Inter-character dialogue")
    for t in st.session_state.dialogue_last:
        with st.chat_message("assistant", avatar=t["avatar"]):
            st.markdown(f"**{t['speaker_name']}**")
            st.markdown(t["content"])
    if st.button("Clear dialogue", key="clear_dialogue_main"):
        st.session_state.pop("dialogue_last", None)
        st.rerun()
    st.divider()

if st.session_state.round_table:
    a_key, b_key = st.session_state.round_table_pair
    ch_a, ch_b = get(a_key), get(b_key)
    st.markdown(f"## Round Table — {ch_a.name} & {ch_b.name}")
    st.caption("Both characters respond to the same prompt with their own grounded retrieval.")
    _render_history(st.session_state.round_table_history)

    prompt = st.chat_input("Ask the table…") or _consume_pending_prompt()
    if prompt:
        st.session_state.round_table_history.append({"role": "user", "content": prompt})
        _commit_to_log("user", "user", "User", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        for ch in (ch_a, ch_b):
            with st.spinner(f"{ch.name} is thinking…"):
                local_history = [
                    t for t in st.session_state.round_table_history
                    if t["role"] == "user" or t.get("character") == ch.key
                ]
                saved = st.session_state.histories[ch.key]
                st.session_state.histories[ch.key] = local_history[:-1]
                turn = _respond(ch, prompt)
                st.session_state.histories[ch.key] = saved
            st.session_state.round_table_history.append(turn)
            _commit_to_log("assistant", ch.key, ch.name, turn["content"])
            _render_assistant_turn(turn)
        ev = _maybe_fire_director_event()
        if ev:
            _render_event({"speaker": ev.speaker, "avatar": ev.avatar, "body": ev.body, "category": ev.category})
else:
    ch = get(st.session_state.active)
    st.markdown(f"## {ch.avatar} {ch.name}")
    st.caption(f"*{ch.role}* — {ch.tagline}")

    history = st.session_state.histories[ch.key]
    # Active crisis banner — render once at the top.
    active_crises = scan_crises(st.session_state.world_sim)
    if active_crises:
        st.warning(
            "Active station alarms:\n\n"
            + "\n".join(f"- {e.to_banner()}" for e in active_crises),
            icon="⚠",
        )
    # First-visit welcome: nothing has happened yet and the user landed on Park.
    nothing_yet = (
        not any(st.session_state.histories.values())
        and not st.session_state.round_table_history
        and st.session_state.metrics.total_queries() == 0
    )
    if nothing_yet:
        from mira_welcome import build_welcome_turn
        _render_assistant_turn(build_welcome_turn(st.session_state.ui_lang))
    _render_history(history)

    prompt = st.chat_input(f"Talk to {ch.name.split()[-1]}…") or _consume_pending_prompt()
    if prompt:
        # Slash commands bypass the LLM entirely.
        if is_slash(prompt):
            slash_res = slash_dispatch(
                prompt,
                active_character=ch.key,
                world_sim=st.session_state.world_sim,
                persona_memory=st.session_state.persona_memory,
                retriever=_retriever(),
                cast=CHARACTERS,
            )
            history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🛰️"):
                st.markdown(f"**{slash_res.title}**\n\n{slash_res.body}")
            # Honour /handover by switching the active character on the next rerun.
            if slash_res.handover_to:
                st.session_state.active = slash_res.handover_to
                st.rerun()
            prompt = None  # don't fall through to the LLM path
    if prompt:
        history.append({"role": "user", "content": prompt})
        # If a handover was suggested, surface it briefly.
        h = detect_handover(ch.key, prompt)
        if h and h.refer_to != ch.key:
            st.caption(f"💡 The active character may suggest you ask **{h.refer_to}** about {h.topic}.")
        _commit_to_log("user", "user", "User", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner(f"{ch.name} is thinking…"):
            turn = _respond(ch, prompt)
        history.append(turn)
        _commit_to_log("assistant", ch.key, ch.name, turn["content"])
        _render_assistant_turn(turn)
        ev = _maybe_fire_director_event()
        if ev:
            _render_event({"speaker": ev.speaker, "avatar": ev.avatar, "body": ev.body, "category": ev.category})
