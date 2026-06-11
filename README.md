# Aether Station — Multi-Character Chatbot

[![CI](https://github.com/USERNAME/aether-station/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/aether-station/actions/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-301_passing-brightgreen)](tests/)
[![python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> A Creative Apps submission for **Agents League @ AISF 2026**.
> Track: 🎨 Creative Apps · IQ: 🧠 Foundry IQ

> **🌐 Live demo:** _set the URL here after deploying — see [`DEPLOY.md`](DEPLOY.md) for four hosting paths (Streamlit Community Cloud, Hugging Face Spaces, Render, Azure Container Apps)._

Talk to the crew of an orbital research station. Each character has their own
voice, expertise, and relationships — and every answer is **grounded in the
station's lore bible** through Foundry IQ, so the cast never contradicts the
world or invents facts about it.

## Why this is interesting

Most character chatbots drift: the longer you talk, the more the character
contradicts their own backstory. Aether Station fixes this by treating the
**world bible as a retrieval source**. When you ask Cmdr. Park about the
Halberd incident, she pulls from `lore/incidents/halberd.md` instead of
hallucinating. When the engineer complains about reactor coolant, he's citing
the actual maintenance log. The result is a cast that stays coherent across
sessions, and citations you can click to verify.

## The cast

| Character | Role | Voice |
|---|---|---|
| **Cmdr. Yuna Park** | Station commander, ex-Orbital Guard | Pragmatic, dry, decisive |
| **Dr. Idris Okafor** | Xenobiologist | Curious, verbose, optimistic |
| **Mira-7** | Station AI | Formal, precise, faintly amused |
| **Kostya Volkov** | Chief engineer | Gruff, blunt, allergic to jargon |
| **Lin Hua** | Junior medic | Anxious, observant, dryly funny |

Pick one in the sidebar, or use **Round Table** mode to have two characters
respond to the same prompt and watch them disagree.

## What makes the cast feel like a crew

- **Shared station log.** A short rolling memory of recent turns gets
  injected into every character's prompt. If Volkov just complained about
  Mira-7's coolant-leak delay, Park can reference it when you talk to her
  thirty seconds later.
- **Multi-step reasoning trace.** Every reply ships with a collapsible
  panel showing the agent's chain: *Intent → Foundry IQ query → retrieved
  passages → salient facts → character synthesis.* You can see exactly
  how the answer was built — no black box.
- **Director agent.** An invisible 6th agent watches the station log
  and injects ambient events when the conversation lingers on a topic
  (Mira-7 broadcasts an HB-441 amplitude update; an audit log lands when
  the safety layer fires). Makes the station feel alive.
- **Per-reply citations.** Click the grounding panel to see which lore
  files informed each line, with retrieval scores.
- **Persona memory.** Say *"for the record, the relief ship arrives
  Thursday"* to a character and they will remember it for the rest of
  the session. *"Forget the relief-ship note"* drops it again.
- **Conversation summarizer.** Long sessions don't bloat the prompt:
  past N turns the oldest are compressed into an "earlier in this
  session" rollup that the cast can still read.
- **Inter-character dialogue.** Pick two characters and a topic;
  watch them debate back and forth without you in the middle. Each
  reply is grounded; each character addresses the other by their
  preferred form (Park says *Kostya*, Mira says *Commander Park*).
- **Per-character mood.** Topics, refusals, and time shift each
  character's energy/focus/openness vector. The offline mock LLM
  picks shorter openers when a character is stressed, warmer ones
  when they're chatty.
- **Per-character retrieval bias.** Same question, different priorities:
  Okafor surfaces HB-441 1.6× harder than the baseline; Volkov pulls
  the coolant-leak report to the top; Park reaches for the Halberd
  incident first. The cast doesn't just *speak* differently — they
  *retrieve* differently. The reply is grounded in passages each
  character would actually pay attention to.
- **Live station-systems simulation.** Reactor output, coolant
  pressure, oxygen, water, comms link, and HB-441 EM peak are *actual
  numbers* that drift each turn. Ask Park "what's Reactor A at?" and
  she answers with the live value. Crew positions tracked, too.
- **Personality drift detector.** Each reply is scored against the
  character's voice signature; the sidebar shows a live drift label.
  If the LLM stops sounding like Park, the UI notices.
- **Compliance audit log.** Every safety verdict, refusal, and
  persona-memory edit is timestamp-logged. Exportable as CSV from the
  sidebar — proper accountability instead of "trust us."
- **i18n.** Mira-7's welcome and key UI labels available in English,
  Spanish, and Hindi. Picker at the top of the sidebar.
- **Browser voice.** Every reply has a 🔊 Speak button that runs the
  text through your browser's Web Speech API with a per-character voice
  profile — Park lower and slower, Hua higher and faster, Volkov
  deepest with Russian voice hints.
- **Per-character tools.** Mira reads telemetry; Volkov can ACK a
  reading (resets the simulation toward nominal); Hua does vitals
  spot-checks (Okafor's elevated heart rate shows up); Okafor pulls
  HB-441 trend data. Tool results are threaded into the reply and
  shown as 🔧 chips.
- **System-prompt inspector.** A sidebar expander shows the *exact*
  system prompt the next reply will use — dossier + mood + persona
  memory + telemetry. No hidden state.
- **Auto-detected crises.** If a station system drifts out of nominal,
  a `CrisisEvent` fires with severity (`watch` / `alarm`) and routes
  to the right owner (Volkov for reactor, Mira for life support,
  Okafor for HB-441). Main pane shows an active-alarms banner; the
  prompt absorbs the crisis context so replies reflect station state.
- **Character handover.** Ask Park about reactor coolant and she
  suggests you follow up with Volkov. Ask Volkov about HB-441 biology
  and he defers to Okafor. Each character answers briefly from their
  own perspective but knows who's really qualified.
- **Voice loop.** Combined with the per-character TTS, the mic
  button (Web Speech Recognition) gives you a full voice
  conversation with the crew.
- **Slash commands.** Type `/help`, `/sitrep`, `/vitals`, `/reactor`,
  `/lore <query>`, `/note <text>`, `/forget <text>`, `/clear`, or
  `/handover <key>` for instant power-user actions that bypass the
  LLM.
- **Session memos.** First reply, first refusal, first crisis, first
  dialogue, first character switch — all captured as a timestamped
  sidebar timeline so a returning user gets a "here's what happened"
  view at a glance.
- **Full-state persistence.** Sidebar Save / Load writes world sim
  + persona memory + mood + audit + memos to a single JSON file.
  Survives a browser refresh, a container restart, or a copy to
  another machine. Schema-versioned.
- **Interactive terminal REPL.** `python cli.py chat park` opens a
  colored, stateful prompt that runs the full pipeline. Slash commands
  work; `/handover volkov` switches the active character live.
- **Live cost estimate.** Sidebar shows running token + USD estimate
  against Azure OpenAI list pricing. Offline mock = $0. Override the
  pricing constants for your own model.
- **HTTP API.** `python cli.py serve` starts a FastAPI server with
  `/crew`, `/ask`, `/dialogue`, `/sitrep`, `/lore/search`, `/doctor`,
  `/healthz` endpoints — programmatic access without spinning up
  Streamlit.
- **Performance metrics.** Sidebar shows live count/min/avg/p95/max
  timings for retrieval and LLM calls. Capped at 200 samples per
  operation.

## Crew relationships

```mermaid
graph LR
  park -- "calls him Kostya" --> volkov
  park -- '"Doctor"' --> okafor
  park -- "calls her Mira" --> mira
  volkov -- "complains about her" --> mira
  volkov -- "mentors at chess" --> hua
  okafor -- "asks her to speculate" --> mira
  hua -- "quietly worried" --> okafor
  hua -- "shares concerns" --> mira
```

## Adding a character (YAML)

Drop a `.yaml` file into `characters_extra/`:

```yaml
key: garcia
name: Diego Garcia
role: Hydroponics Officer
avatar: "🌱"
tagline: "Soft-spoken botanist."
voice:
  openers: ["Hm.", "Sure."]
  closers: ["Anyway."]
system_prompt: |
  You are Diego Garcia, hydroponics officer on Aether Station...
```

The cast auto-discovers it at startup. Malformed files are skipped, not
crashed on. See `characters_extra/garcia.yaml` for a working example.

## GitHub Copilot integration (MCP server)

`mcp_server.py` exposes the cast as an MCP server you can plug into
GitHub Copilot in VS Code:

| Tool | What it does |
|---|---|
| `list_crew()` | List every available character |
| `ask_crew(character, question)` | Talk to a crew member from the IDE |
| `lore_search(query, top_k)` | Search the Foundry IQ knowledge layer |
| `station_log()` | Read recent in-world chatter |

Add to your VS Code `mcp.json`:

```json
{
  "servers": {
    "aether-station": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/absolute/path/to/aether-station"
    }
  }
}
```

You can also use the tools without MCP for quick demos:
```bash
python mcp_server.py cli list_crew
python mcp_server.py cli ask_crew park "What's your view of the Halberd Mining Cooperative?"
python mcp_server.py cli lore_search "coolant leak"
```

## HTTP API quick start

Start the API:

```bash
make api          # or: python cli.py serve --port 8000
```

Then call it:

```bash
# list the crew
curl -s http://localhost:8000/crew | jq

# ask Park about the Halberd incident
curl -sX POST http://localhost:8000/ask \
  -H 'content-type: application/json' \
  -d '{"character": "park", "question": "Tell me about the Halberd incident"}' | jq

# park ↔ volkov dialogue, 2 rounds (4 turns)
curl -sX POST http://localhost:8000/dialogue \
  -H 'content-type: application/json' \
  -d '{"a": "park", "b": "volkov", "topic": "the eleven-second delay", "rounds": 2}' | jq

# live station telemetry + active alarms
curl -s http://localhost:8000/sitrep | jq

# search the lore corpus
curl -s 'http://localhost:8000/lore/search?q=coolant+leak&top=4' | jq

# self-diagnostic
curl -s http://localhost:8000/doctor | jq '.return_code'
```

Auto-generated OpenAPI docs live at <http://localhost:8000/docs>.

`/ask` and `/dialogue` are protected by a per-IP token-bucket
(default: 30 burst, 0.5 tokens/sec sustained); over the limit returns
HTTP 429.

## How Foundry IQ is used

`foundry_iq.py` exposes a `retrieve(query, top_k)` function used before every
character response. It has two backends:

1. **Azure AI Foundry agent** (`FOUNDRY_PROJECT_ENDPOINT` set) — calls a
   knowledge-grounded agent configured against the `lore/` corpus. Returns
   passages with source citations and permission-aware filtering.
2. **Local TF-IDF fallback** (no key set) — TF-IDF retrieval over the
   same markdown files so the demo runs out of the box.
3. **Local BM25** — set `RETRIEVER_BACKEND=bm25` for Okapi BM25
   retrieval over the same corpus. Better recall on multi-term queries.
   Pure Python, no extra deps.

Either way, the chat UI shows which lore documents informed the reply, so
judges can verify the grounding without setup.

## Quick start (Docker)

```bash
docker build -t aether-station .
docker run --rm -p 8501:8501 aether-station
# Then open http://localhost:8501
```

## Headless quick start (CLI)

```bash
python cli.py list
python cli.py ask park "What happened with the Halberd tug?"
python cli.py round park volkov "Should we pull the plug on HB-441?"
python cli.py lore search "coolant leak"
python cli.py lore stats
python cli.py lore validate       # lint the corpus
python cli.py dialogue park volkov "HB-441 anomaly" --rounds 2
python cli.py status              # print current backends + env
python cli.py scenarios           # list all turnkey demos
python cli.py replay session.json # re-render an exported session
python cli.py bench               # benchmark each character on a fixed query set
python cli.py crisis lif_a_psi --value 200  # simulate a station crisis
python cli.py snapshot            # one-page project snapshot for submission forms
python cli.py chat park           # interactive terminal REPL with Park
python cli.py inspect park        # full character dossier (system prompt + voice + tools)
python cli.py serve --port 8000   # start the FastAPI HTTP server
python cli.py bench --json        # machine-readable benchmark output
python cli.py smoke               # end-to-end demo path PASS/FAIL
python cli.py doctor              # self-diagnostic — 43 checks
```

## Quick start

```bash
git clone <your-fork>
cd aether-station
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # (optional) add Azure AI Foundry creds for real IQ
streamlit run app.py
```

The app launches at `http://localhost:8501`.

## Configuration

| Env var | Purpose |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint for chat completions |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (e.g. `gpt-4o-mini`) |
| `FOUNDRY_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint (optional — falls back to local retrieval) |
| `FOUNDRY_AGENT_ID` | ID of the Foundry agent configured for lore retrieval |
| `RETRIEVER_BACKEND` | `tfidf` (default) or `bm25` — only consulted when Foundry IQ env vars are empty |

If none are set, the app runs in **offline demo mode** using local retrieval
plus a deterministic mock LLM, so reviewers can still try the cast.

## How GitHub Copilot helped

This project was built with GitHub Copilot in VS Code. Notable assists:

- **Scaffolding**: Copilot Chat drafted the Streamlit layout and character
  picker from a one-line prompt.
- **Retrieval fallback**: Copilot suggested the TF-IDF + cosine-similarity
  pattern for the offline path and autocompleted the scoring loop.
- **Persona prompts**: Iterated character system prompts using Copilot as a
  sparring partner ("make Mira-7 sound less HAL, more Jeeves").
- **Edge cases**: Copilot inline suggestions caught empty-history and
  no-results branches that would have crashed the chat loop.

## Project layout

```
aether-station/
├── app.py                 # Streamlit chat UI (the main entry point)
├── cli.py                 # Headless CLI: list, ask, round, dialogue, lore, doctor, etc.
├── mcp_server.py          # MCP server exposing the cast to GitHub Copilot / VS Code
│
│   # Cast & persona
├── characters.py          # Built-in 5-character cast (system prompts + identity)
├── character_loader.py    # Discovers extra characters in characters_extra/ (YAML)
├── llm.py                 # Azure OpenAI client + per-character mock + voice profiles
├── persona_memory.py      # Per-session learned facts ("for the record" notes)
├── mood.py                # 3-axis mood vector (energy / focus / openness)
├── mira_welcome.py        # First-visit Mira-7 welcome monologue
│
│   # Knowledge / retrieval
├── foundry_iq.py          # Azure AI Foundry agent + TF-IDF + BM25 backends
├── retrieval_bias.py      # Per-character lore weighting (Park ops, Okafor science...)
├── reasoning.py           # 5-step reasoning trace builder
│
│   # Live world
├── world_sim.py           # Live station-systems simulation (reactor, O2, comms, HB-441)
├── world_state.py         # Shared station log (cross-character memory + summarizer)
├── director.py            # Ambient-event director (Mira-7 broadcasts, audit logs)
├── crisis.py              # Detects out-of-nominal readings + routes to owner
├── character_tools.py     # Mira reads telemetry, Volkov ACKs, Hua does vitals, etc.
├── handover.py            # Suggests the right specialist when off-topic
│
│   # Interaction
├── dialogue.py            # Inter-character back-and-forth dialogue chains
├── slash.py               # /help, /sitrep, /vitals, /reactor, /lore, /note, ...
├── scenarios.py           # 10 turnkey one-click demo scenarios
├── tts.py                 # Browser Web Speech voice profile per character
├── voice_input.py         # Browser Web Speech Recognition mic button
├── i18n.py                # English / Spanish / Hindi UI strings
│
│   # Safety, observability, persistence
├── safety.py              # Input safety filter (jailbreak / harm / politics / PII)
├── audit.py               # Compliance audit log (CSV export)
├── drift.py               # Personality-drift detector
├── analytics.py           # Per-session metrics
├── memo.py                # Session milestone tracker
├── relationships.py       # Static crew-relationship graph (Mermaid + UI)
├── transcript.py          # Markdown + JSON export, JSON re-import
├── persistence.py         # Full-state save/load (world sim + memory + mood + audit + memos)
├── cost.py                # Approximate token + USD cost estimator (gpt-4o-mini)
├── api.py                 # FastAPI HTTP wrapper (/crew, /ask, /dialogue, /sitrep, ...)
├── rate_limit.py          # Per-IP token-bucket limiter for the HTTP API
├── perf.py                # Per-operation timing metrics (retrieval, LLM)
│
│   # Data
├── lore/                  # Markdown knowledge base — 18 files
│   ├── world/             # Station, factions, timeline, JOSC charter, ...
│   ├── crew/              # Dossiers (incl. Park's coffee ritual + service record)
│   └── incidents/         # Logged events characters reference
├── characters_extra/      # Drop YAML files here to add cast members
│
│   # Tests, deploy, docs
├── tests/                 # Pytest suite — 301 tests (`pytest -q` to run)
├── .github/               # Issue + PR templates, CI workflow, Dependabot
├── .streamlit/            # Theme + secrets template
├── deploy/                # Azure Container Apps Bicep template
├── Dockerfile             # One-command container build
├── render.yaml            # Render blueprint (one-click Docker deploy)
├── HUGGINGFACE_README.md  # Pre-baked HF Spaces metadata header
├── pyproject.toml         # Modern packaging + optional extras
├── requirements.txt
├── Makefile               # `make test`, `make run`, `make docker-run`, etc.
├── .env.example
├── README.md
├── CHANGELOG.md           # Iteration history (20 rounds)
├── SAMPLE_TRANSCRIPT.md   # Pre-recorded session (read without running)
├── JUDGES_GUIDE.md        # Rubric map + 60-sec / 5-min tours
├── SUBMISSION.md          # One-page submission packet (v1.0.0)
├── HOW_IT_WORKS.md        # One-page architecture (data flow + invariants)
├── DEMO_SCRIPT.md         # Walkthrough script for the demo video
├── FOUNDRY_IQ_SETUP.md    # Live Foundry IQ wiring instructions
├── DEPLOY.md              # Four ways to host publicly
├── PUBLISH.md             # Git + GitHub publishing steps
├── CONTRIBUTING.md        # Fork onboarding + how to add lore/characters
├── CODE_OF_CONDUCT.md     # Contributor Covenant v2.1
└── LICENSE
```

## Running the tests

```bash
pytest -q
```

The suite covers retrieval relevance, reasoning trace shape, safety
refusals (jailbreak / harm / real-world deflection), shared-log behavior,
scenario integrity, and per-character mock-LLM voicing.

## Track requi