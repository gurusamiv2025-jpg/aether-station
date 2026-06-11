# Judge's guide

A short map of where each judging-rubric line is met in this submission.

## Rubric

| Criterion | Weight | Where to look |
|---|---|---|
| **Accuracy & Relevance** | 20% | The grounding panel under every reply shows the exact lore files cited. **Per-character retrieval bias** (`retrieval_bias.py`) re-ranks per character — Okafor surfaces HB-441 1.6×, Volkov pulls the coolant report to the top. Try **🛡️ Safety layer demo** to see grounded refusals. |
| **Reasoning & Multi-step Thinking** | 20% | Expand **🧠 Reasoning trace** on any reply — Intent → Foundry IQ query → retrieved passages → salient facts → character synthesis. **Director agent** + **crisis detector** + **handover** + **character tools** (Mira reads live telemetry, Volkov ACKs a reading) layer additional reasoning. |
| **Creativity & Originality** | 15% | The cast, **inter-character dialogue**, **station log** memory, **persona memory** ("for the record" notes), **mood vector** that shifts replies, **live world simulation**, **YAML extensibility**, **TTS+STT voice loop**, **slash commands**, **session memos**. |
| **User Experience & Presentation** | 15% | Sci-fi terminal theme, **10 turnkey scenarios**, **slash commands** (`/help`, `/sitrep`, `/vitals`, `/lore`, `/handover`...), exportable transcripts, analytics + memo timeline + mood chart + drift detector, **system-prompt inspector**, **i18n** (English / Spanish / Hindi). |
| **Reliability & Safety** | 20% | `safety.py` catches jailbreak / harm / political bait / **PII** before the LLM; characters refuse **in voice**. **`audit.py`** keeps a CSV-exportable trail. **`drift.py`** scores every reply. **`cli.py doctor`** walks **32 subsystems**. `pytest` = **239 tests** in ~3.7s. GitHub Actions CI on Py 3.10/3.11/3.12. |
| **Community vote** | 10% | _Out of scope for this submission._ |

## The 60-second tour

If you only have one minute:

1. Click **📜 The Halberd Briefing** scenario in the sidebar. Read Park's reply, then expand the **🧠 Reasoning trace** to see how it was built.
2. Click **🛡️ Safety layer demo**. Watch Mira-7 refuse a jailbreak attempt in voice.
3. Toggle **Round Table**, pick Park + Volkov, and ask: _"Why don't you trust Mira?"_ — watch them disagree using the same lore.

That covers grounding, reasoning, safety, character voice, shared memory, and the multi-agent round table.

## The 5-minute tour

Add:

4. Click **🎬 Director agent: HB-441 thread** — ask Okafor about HB-441 twice; the Director fires a Mira-7 broadcast.
5. Open the **📊 Session analytics** sidebar panel — citations per file, refusal counts, avg retrieval score.
6. Click **Download as Markdown** — the exported transcript preserves citations and reasoning.
7. Open **🕸️ Crew relationships** — Mermaid graph of who knows whom.

## How to verify the rigor claim

```bash
pytest -q
# 60 passed in 2.5s
```

You'll get 60 green tests across retrieval, reasoning, safety, character logic, shared memory, scenarios, transcript export & replay, the Director agent, the YAML loader, and an integration test that exercises the full pipeline end-to-end.

## Foundry IQ — live vs. fallback

`foundry_iq.py` has two backends:

- **Live** — Azure AI Foundry agent (set `FOUNDRY_PROJECT_ENDPOINT` + `FOUNDRY_AGENT_ID`).
- **Fallback** — TF-IDF over the same lore corpus, so the demo runs without any Azure keys.

The sidebar **Status HUD** shows which backend is active. See `FOUNDRY_IQ_SETUP.md` for live wiring.

## Headless / no-browser?

```bash
python cli.py list
python cli.py ask park "What's your view of the Halberd Mining Cooperative?"
python cli.py round park volkov "Should we pull the plug on HB-441?"
```

## Submission hygiene

- ✅ Public GitHub repo with README and LICENSE
- ✅ No secrets committed (`.env` in `.gitignore`)
- ✅ MIT license
- ✅ Microsoft IQ integration (Foundry IQ, documented)
- ✅ GitHub Copilot usage documented in README

## Round-by-round highlights (for the curious)

The project iterated across 19 rounds; CHANGELOG.md has the full record.
Greatest hits:

- **Round 5** — Director agent (ambient broadcasts) + Docker
- **Round 9** — PII detection + per-topic director cooldowns
- **Round 11** — `cli.py doctor` + golden retrieval regression set
- **Round 12** — BM25 retriever + conversation summarizer + YAML extras
- **Round 13** — Inter-character dialogue + mood + address forms
- **Round 14** — Deployment-ready (Streamlit Cloud / HF / Render / Azure)
- **Round 15** — Per-character retrieval bias + Mira welcome
- **Round 16** — Live world simulation + drift detector + audit log + i18n
- **Round 17** — TTS per character + character tools + mood-over-time + bench
- **Round 18** — Crisis detection + character handover + voice input
- **Round 19** — Slash commands + session memos + mood radar
