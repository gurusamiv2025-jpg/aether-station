# How Aether Station works

A single page on the architecture, for anyone who wants to read code
fluently.

## High-level data flow

```
                ┌──────────────┐
   User types ──┤  app.py (UI) ├── prompt + character
                └──────┬───────┘
                       │
                       ▼
               ┌──────────────┐
               │  safety.py   │  rejects jailbreak / harm / politics / PII
               └──────┬───────┘
                allow │ refuse → in-voice refusal, short-circuit
                       ▼
               ┌──────────────┐
               │ foundry_iq   │  retrieve(query, top_k=4)
               │  Azure OR    │  ─── returns Passages with scores
               │ TF-IDF fallback
               └──────┬───────┘
                       ▼
       ┌─────────────────────────────┐
       │ _build_messages() in app.py │
       │  system =                   │
       │   character.system_prompt   │
       │   + station_log (shared)    │
       │   + GROUNDING passages      │
       └──────────────┬──────────────┘
                       ▼
               ┌──────────────┐
               │   llm.py     │  Azure OpenAI OR per-character mock
               └──────┬───────┘
                       ▼
               ┌──────────────┐
               │ reasoning.py │  builds 5-step trace (intent → synthesis)
               └──────┬───────┘
                       ▼
               ┌──────────────┐
               │ director.py  │  may emit ambient event (topic/quiet/refusal)
               └──────┬───────┘
                       ▼
                  Reply + trace
                       ▼
               ┌──────────────┐
               │ analytics +  │  recorded on every turn
               │ station_log  │  visible to next character's prompt
               └──────────────┘
```

## Key invariants

1. **Every reply is grounded.** The model never sees a question without
   the retrieved lore passages in its system prompt. If retrieval comes
   back empty, the system prompt says so explicitly and the character
   falls back to an in-voice "I'd need to check the logs" line.

2. **Safety runs before the LLM.** No banned input ever reaches the
   model. The refusal text is character-specific.

3. **Shared memory, isolated histories.** Each character has their own
   conversation history, but they all read from one rolling station log
   — so cross-character references work.

4. **Director is opinionated, not noisy.** Cooldowns (global + per-topic)
   keep ambient events from spamming.

5. **Two backends, one interface.** Both retrieval and LLM expose the
   same surface for Azure and local fallback — swap by setting env vars.

## File map

| File | Role |
|---|---|
| **Entry points** | |
| `app.py` | Streamlit UI, session state, orchestration |
| `cli.py` | Headless CLI mirror of the pipeline (16 verbs) |
| `mcp_server.py` | MCP wrapper so VS Code / Copilot can call the cast |
| **Cast & persona** | |
| `characters.py` | Built-in 5-character cast (persona system prompts) |
| `character_loader.py` | YAML extras in `characters_extra/` |
| `llm.py` | Azure OpenAI + per-character mock with voice profiles |
| `persona_memory.py` | Per-character session memory ("for the record" notes) |
| `mood.py` | 3-axis mood vector (energy / focus / openness) |
| `mira_welcome.py` | First-visit Mira-7 welcome monologue (i18n-aware) |
| **Knowledge / retrieval** | |
| `foundry_iq.py` | Retrieval — Azure agent + TF-IDF + BM25 |
| `retrieval_bias.py` | Per-character lore weighting |
| `reasoning.py` | 5-step reasoning trace |
| **Live world** | |
| `world_sim.py` | Live station-systems simulation |
| `world_state.py` | Shared station log + summarizer |
| `director.py` | Ambient-events agent (broadcasts, audit pings) |
| `crisis.py` | Out-of-nominal detection + owner routing |
| `character_tools.py` | Mira telemetry, Volkov ACK, Hua vitals, etc. |
| `handover.py` | Suggest the right specialist when off-topic |
| **Interaction** | |
| `dialogue.py` | Inter-character back-and-forth |
| `slash.py` | Slash commands (`/help`, `/sitrep`, `/vitals`, ...) |
| `scenarios.py` | One-click guided demos (10 scenarios) |
| `tts.py` | Browser Web Speech voice profile per character |
| `voice_input.py` | Browser Web Speech Recognition mic button |
| `i18n.py` | English / Spanish / Hindi UI strings |
| **Safety, observability** | |
| `safety.py` | Jailbreak / harm / politics / PII filter + refusals |
| `audit.py` | Compliance audit log (CSV export) |
| `drift.py` | Personality-drift detector |
| `analytics.py` | Per-session metrics |
| `memo.py` | Session milestone tracker |
| `relationships.py` | Static crew-relationship graph |
| `transcript.py` | Markdown + JSON export, JSON re-import |
| `persistence.py` | Full-state save/load (world sim + memory + mood + audit + memos) |
| `cost.py` | Approximate token + USD cost estimator |
| `api.py` | FastAPI HTTP wrapper (`/crew`, `/ask`, `/dialogue`, `/sitrep`, ...) |
| `rate_limit.py` | Per-IP token-bucket limiter |
| `perf.py` | Per-operation timing metrics |


## Tests live in `tests/`

`pytest -q` runs everything in ~3.7s. 239 tests as of Round 19. Every
public module has a test file. The integration test
(`tests/test_integration.py`) walks the full pipeline so contract drift
between modules surfaces immediately.
