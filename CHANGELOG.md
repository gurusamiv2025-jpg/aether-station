# Changelog

Iteration history for the Agents League @ AISF 2026 submission.

## Round 3 — Reliability, safety, scenarios

- **Per-character voice templates in the mock LLM.** Each crew member now
  speaks in their own verbal style even in offline demo mode — Park is
  terse, Volkov mutters, Mira logs everything. The mock now picks the
  question-relevant sentence from the grounding instead of a random
  bullet.
- **Input safety layer (`safety.py`).** Jailbreak attempts, real-world
  political baiting, and harmful requests are caught before the LLM is
  called and refused **in character**. Park says "save it"; Volkov says
  "nyet"; Hua deflects nervously.
- **Scenario mode (`scenarios.py`).** Five turnkey demo scenarios in the
  sidebar — one click loads a starter prompt and the right character (or
  round-table pair). Great for judges who want to see the cast immediately.
- **Pytest test suite (`tests/`).** 30+ tests across characters,
  retrieval, reasoning, safety, world_state, scenarios, and the mock LLM.
  Run with `pytest -q`.

## Round 2 — Reasoning, memory, MCP

- **Multi-step reasoning trace (`reasoning.py`).** Every reply now ships
  with a `Intent → Query → Retrieved → Salient facts → Synthesis` panel
  so judges can audit how each answer was built.
- **Shared crew memory (`world_state.py`).** A rolling station log
  injects recent turns from other crew into each character's prompt, so
  characters know what was just said. The cast feels like a crew.
- **GitHub Copilot MCP server (`mcp_server.py`).** Exposes `list_crew`,
  `ask_crew`, `lore_search`, and `station_log` as MCP tools — Copilot
  Chat in VS Code can now talk to the cast directly. Includes a CLI
  fallback for verification without an MCP client.
- **Themed UI.** Monospaced station-status HUD, sidebar log preview,
  reasoning panel above every reply.

## Round 1 — Initial submission

- 5-character cast (Park, Okafor, Mira-7, Volkov, Hua) with persona-driven
  system prompts.
- Foundry IQ integration layer (`foundry_iq.py`) with live Azure AI
  Foundry agent backend and TF-IDF local fallback over the lore corpus.
- Azure OpenAI client (`llm.py`) with deterministic mock fallback.
- 11-file lore bible covering station, crew, and three incidents.
- Streamlit chat UI with character picker and Round Table mode.
- README, LICENSE, demo-video script, Foundry IQ setup guide, publishing
  guide.

## Round 4 — Polish, analytics, exports, CI

- **Conversation export (`transcript.py`).** Two formats. Markdown for
  sharing in a PR or Discord (with collapsible reasoning traces). JSON
  for round-tripping a full session. Sidebar has download buttons.
- **Session analytics panel (`analytics.py`).** Queries per character,
  top-cited lore files with average retrieval score, safety refusals by
  category. Surfaces in the sidebar — judges see the project tracks its
  own behavior.
- **Sample transcript (`SAMPLE_TRANSCRIPT.md`).** A pre-recorded session
  showing the cast, citations, cross-character memory, and an in-voice
  safety refusal. Lets judges who don't run the app still see the value.
- **GitHub Actions CI (`.github/workflows/ci.yml`).** Pytest runs on
  Python 3.10 / 3.11 / 3.12 every push + PR. Badge-able.
- **More lore.** `lore/incidents/comms-blackout.md` (2095 antenna event)
  and `lore/crew/park-service.md` (Park's Orbital Guard service record).
  Deeper world = richer retrievals.
- **Test suite grew to 42 tests.** New coverage for transcript export
  (JSON round-trip, markdown rendering, schema validation), analytics
  (queries, citations, refusals, avg scores), and the lore additions.

## Round 5 — Director agent, replay, Docker

- **Director / Narrator agent (`director.py`).** A 6th invisible agent
  watches the station log. When topic mentions cross a threshold (HB-441,
  coolant, Halberd, comms), it injects an in-world Mira-7 broadcast.
  After a quiet stretch, it emits a status ping. Safety refusals get
  logged as audit events. Toggle in the sidebar.
- **Conversation replay (`transcript.apply_to_state`).** The Round-4
  JSON export now round-trips — upload a session and the cast resumes
  where you left off. Closes the export/import loop.
- **Dockerfile + .dockerignore.** `docker build -t aether-station . &&
  docker run -p 8501:8501 aether-station` gets judges to a running app
  with zero Python setup.
- **Tests grew to 49.** Director (topic triggers, cooldown, quiet ping,
  refusal events) and transcript replay (round trip, missing fields).

## Round 6 — Extensibility, relationships

- **YAML character extensibility (`character_loader.py` + `characters_extra/`).**
  Drop a `.yaml` file in `characters_extra/` and a new crew member shows
  up in the sidebar at app start. Includes a working `garcia.yaml`
  example (hydroponics officer). The mock LLM picks up YAML voice
  profiles too. Loader silently skips malformed files — never crashes
  the app.
- **Relationship map (`relationships.py`).** Static who-talks-to-whom
  graph compiled from the dossiers. Renders as Mermaid for the README
  and (next round) as a Streamlit panel. Every edge endpoint is
  unit-tested against the real cast.
- **Tests grew to 56.** Cover loader edge cases (missing dir, broken
  YAML, missing fields), voice-profile merging, and relationship
  integrity.

## Round 7 — Final polish

- **Integration test (`tests/test_integration.py`).** Exercises the full
  pipeline end-to-end (retrieval → safety → shared log → LLM →
  reasoning) for grounded turns, safety refusals, and YAML extras.
  Catches contract drift between modules.
- **Two new scenarios.** "Safety layer demo" (jailbreak → in-voice
  refusal) and "Director agent: HB-441 thread" (showcases the Round-5
  ambient-events agent). 7 scenarios total.
- **DEMO_SCRIPT extended.** Two new scenes for the Director agent and
  the session export feature; demo now runs ~2:05.
- **README badges.** CI status, test count, Python versions, license.
- **60 tests total**, all passing.

## Round 8 — Packaging, judge guide, headless CLI

- **`pyproject.toml`** with proper metadata, optional `azure` / `mcp` /
  `dev` extras, and a console-script entry for `aether-station`.
- **`JUDGES_GUIDE.md`** — maps every line of the official judging
  rubric to where the project meets it, plus a 60-second tour and a
  5-minute tour. Saves judges five minutes of hunting.
- **Headless CLI (`cli.py`).** `python cli.py list`, `ask`, and
  `round` run the full pipeline (retrieval → safety → LLM → reasoning)
  from a terminal, no Streamlit needed. JSON output for scripting.
- **Cleanup.** Imports in `app.py` now sit above any code per PEP 8;
  the cast definition lives just below the import block.
- **65 tests total** — added a CLI test module that exercises `list`,
  `ask`, `round`, unknown-character error paths, and the safety
  refusal flow.

## Round 9 — Richer prose, PII shield, smarter director

- **Two-sentence mock LLM responses.** The offline mock now chains a
  second salient sentence from a *different* lore passage when one is
  available. Offline demos feel less stubby; the prose actually flows.
- **PII detection in the safety layer.** Catches emails, US-style
  SSNs, and phone numbers before the LLM is called. Every character has
  an in-voice PII refusal too — Volkov: "Nyet. I do not need your phone
  number or your email."
- **Per-topic director cooldowns.** The Director agent now remembers
  which topic last fired and won't re-broadcast the same one for four
  turns. No more Mira-7 looping on HB-441 every time you mention it.
  Reset when the conversation is cleared.
- **73 tests total.** New coverage for PII (email / phone / SSN with a
  numbers-but-not-PII negative case), two-sentence prose chaining, and
  per-topic cooldown behavior.

## Round 10 — Alignment audit, lore CLI, Makefile, architecture doc

- **Alignment audit.** Verified every `.py` and `.md` referenced by the
  README + CHANGELOG exists on disk, every scenario points to a real
  character, every relationship-graph edge resolves to a real crew
  member. Zero drift between docs and code.
- **`cli.py lore` subcommand.** Three new verbs:
  - `lore list` — every file in the corpus with its top-level heading
  - `lore search <query>` — uses the same retriever the app uses
    (Foundry IQ or fallback), human or `--json` output
  - `lore stats` — file count, word count, breakdown by folder
- **`Makefile`.** Common dev tasks: `make test`, `make run`, `make demo`,
  `make docker-run`, `make compile`, `make clean`.
- **`HOW_IT_WORKS.md`.** Single-page architecture: ASCII data-flow
  diagram, key invariants, file map. The doc for someone who wants to
  read the code fluently.
- **More lore.** `lore/world/mira-commissioning.md` — Mira-7's 2094
  commissioning report. Explains her behavioral envelope, voice corpus,
  and the operator-preference note about Park's naming habit.
- **77 tests total.** Added coverage for the lore CLI verbs and a check
  that the new commissioning report is retrievable.

## Round 11 — Self-diagnostic, golden retrieval set, community docs

- **`cli.py doctor`** — self-diagnostic CLI verb. Walks ten critical
  subsystems (lore corpus, built-in cast, YAML loader, retriever, LLM
  backend, safety, reasoning, scenarios, relationships, transcript
  round-trip) and prints OK/FAIL per check. Returns non-zero if any fail.
  First thing a judge or contributor should run when something looks
  off.
- **Golden retrieval set (`tests/test_retrieval_quality.py`).** Ten
  pinned query → expected-source rows that lock in retrieval quality.
  If anyone edits lore in a way that hides a known doc from the
  retriever, the suite turns red. Includes a sanity score-threshold test.
- **`CONTRIBUTING.md`** — onboarding for forks: setup, how to add a
  character / lore / scenario, what we won't merge, where to report
  security issues. Highlights the golden-row rule so future lore PRs
  remember to pin retrieval.
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant v2.1 in spirit.
  Standard community polish.
- **90 tests total** (12 added this round: 10 golden retrieval rows + a
  score-threshold sanity test + 2 doctor smoke tests).

## Round 12 — BM25, summarizer, persona memory, lore validator, community templates

The biggest round so far. Five substantive additions:

- **BM25 retriever (`foundry_iq.BM25Retriever`).** Pure-Python Okapi BM25
  as a third backend. Selectable via `RETRIEVER_BACKEND=bm25`. Beats
  TF-IDF on multi-term queries (smoke-tested: top hit for "LiF-B
  coolant leak 11 second delay" is `lore/incidents/coolant-leak.md`).
  No new dependency.
- **Conversation summarizer (`world_state.summarize_if_long`).** When
  the station log grows past 10 non-summary turns, the oldest get
  compressed into a single "Earlier in this session" rollup that's
  merged with any prior summary — at most one rollup ever exists.
  Long sessions stay coherent without prompt bloat.
- **Persona memory (`persona_memory.py`).** Each character has a tiny
  per-session memory. Trigger phrases: *"for the record,"*, *"make a
  note,"*, *"remember that..."* record facts; *"forget the X note"* or
  *"clear your notes"* drop them. Facts inject into the system prompt
  under a `PERSONAL NOTES` block. Sidebar shows current notes per
  character; reply renders an emoji acknowledgement (`📝 noted: ...`)
  when a note was recorded.
- **`cli.py lore validate`.** Lints the corpus: every file has an H1,
  every internal `lore/...` link resolves, no duplicate H1s, no empty
  files. Returns non-zero with a punch list if anything's wrong.
- **Community templates in `.github/`.** Issue templates (bug report
  asks for `cli.py doctor` output), PR template (checklist enforces
  the golden-row rule), Dependabot weekly updates for pip and Actions.

Tests grew to **112**: BM25 (golden hits, score normalisation, factory
dispatch), summarizer (no-fire below trigger, single rollup invariant,
hard-cap respected), persona memory (record / forget / clear / cap /
scope-per-character / round-trip via dict), lore validate. `doctor`
expanded to 13 checks (added BM25, persona memory, summarizer).

## Round 13 — Inter-character dialogue, mood, richer voices

The "make the bots actually talk to each other" round.

- **Inter-character dialogue (`dialogue.py`).** Two characters carry a
  multi-turn back-and-forth on a user-supplied topic. Each turn the
  current speaker sees the other character's last reply as quoted
  context, plus the usual grounding / shared log / persona memory /
  mood. Available three ways:
  - **CLI:** `python cli.py dialogue park volkov "the HB-441 anomaly" --rounds 2`
  - **Streamlit:** new sidebar panel with character + topic + rounds
    pickers and a "Run dialogue" button; output renders in the main pane.
  - **Library:** `dialogue.run_dialogue(...)` for tests and integrations.
- **Per-character mood (`mood.py`).** Each crew member has a 3-axis
  mood vector (energy / focus / openness) that shifts with topic
  triggers (HB-441 stresses Okafor, coolant stresses Volkov, etc.),
  turn count, and safety refusals. Rendered into the system prompt as
  a one-line `CURRENT MOOD` hint and used by the offline mock LLM to
  bias opener choice (stressed → short openers, chatty → warm openers).
  Sidebar shows current moods with chips.
- **Enriched voice profiles.** Each character's `_VOICE_PROFILES` entry
  now has openers (~8), short_openers, warm_openers, idiom phrases,
  and more closers. The mock weaves idioms into the second sentence
  ~45% of the time.
- **Address forms (`llm.ADDRESS_FORMS` + `address_form`).** A
  who-calls-whom-what matrix so Park says "Kostya," Volkov says
  "Mira" not "Mira-7," Mira says "Commander Park," Okafor says
  "Doctor Hua." Mock auto-rewrites bare character keys in replies to
  the speaker's preferred form.
- **`doctor` expanded to 16 checks** (added mood, dialogue, address
  forms). All green.
- **Tests grew to 129.** New: `test_mood.py` (8), `test_dialogue.py` (5),
  `test_address_forms.py` (4), plus a regression fix for the voice-
  template tests now that profiles are richer.

## Round 14 — Deployment-ready (Streamlit Cloud + HF Spaces + Render + Azure)

- **`DEPLOY.md`** — one-page guide covering four public-hosting paths
  with a cost/setup/sleep comparison table and per-platform step-by-step.
- **`.streamlit/config.toml`** — production-friendly theme and server
  defaults (dark theme, headless, no usage stats, no file-watcher).
- **`.streamlit/secrets.toml.example`** — explicit secrets template
  ready to paste into Streamlit Cloud's "Secrets" box, HF Spaces
  variables, or Render env vars.
- **`render.yaml`** — Render blueprint for one-click Docker deployment
  with `healthCheckPath: /_stcore/health` and env-var slots for
  Azure/Foundry credentials.
- **`HUGGINGFACE_README.md`** — pre-baked YAML front-matter for HF
  Spaces (SDK: streamlit, sdk_version pinned, color theme set). Drop
  into a Space's README to skip the metadata setup.
- **`deploy/azure-container-app.bicep`** — declarative Azure Container
  Apps deployment: Log Analytics workspace, managed environment,
  container app with secret env vars, external ingress on port 8501.
  Single `az deployment group create` command brings it live.
- **README** now has a `🌐 Live demo` placeholder at the top pointing
  at `DEPLOY.md` until a real URL goes in.

## Round 15 — Per-character retrieval bias, Mira welcome, CLI status/replay/scenarios

The "make each character actually think differently" round.

- **Per-character retrieval bias (`retrieval_bias.py`).** Same query
  → different ranking depending on who's asking. Park boosts incidents
  (especially Halberd, her file). Okafor boosts HB-441 1.6x — his
  obsession. Volkov boosts the coolant-leak report and reactor docs.
  Hua weights crew dossiers higher, especially Okafor's (the colleague
  she quietly watches). Mira sees everything but tilts toward world
  state. Each character's reply is now grounded in passages they would
  actually pay attention to. Wired into app, CLI, and dialogue.
- **Mira-7 welcome monologue (`mira_welcome.py`).** First-visit users
  see Mira-7 greet them with a short orientation: the cast, the sidebar,
  the grounding panel. Clean first impression for judges instead of an
  empty chat panel.
- **Three new CLI verbs.**
  - `cli.py status` — prints current env vars, retriever/llm backends,
    cast size. No side effects.
  - `cli.py scenarios` — lists all 8 turnkey scenarios with summaries
    and starter prompts.
  - `cli.py replay <file.json>` — re-renders an exported session to
    stdout. Closes the loop with the existing Markdown/JSON export.
- **`doctor` expanded to 18 checks** (added retrieval bias + Mira
  welcome). All green.
- **150 tests total.** Added 14 new tests: retrieval bias (8 — every
  character's profile + folder/file boosts + immutability + top_k),
  Mira welcome (2), CLI new verbs (4).

## Round 16 — Live world sim, drift detector, audit log, i18n, more lore

The biggest round yet. Four new substantive systems, two new lore
documents, all five wired into the Streamlit UI.

- **Live station-systems simulation (`world_sim.py`).** Aether Station
  now has *current* numeric readings — not just lore. Reactor A output
  in MW, LiF-A loop pressure in psi, Ring 1/3 oxygen, water reserves,
  comms link margin, the HB-441 EM peak — all stochastically drifting
  each turn within nominal bands. Crew positions tracked separately
  (Park in command, Okafor in isolation suite B, Volkov in engineering,
  Hua in medbay, Mira *everywhere*). The values are injected into every
  character's prompt as `LIVE STATION TELEMETRY`. Ask Park "what's
  Reactor A at?" and she answers with a real, drifted number.
- **Personality drift detector (`drift.py`).** Each reply is scored
  against the character's voice signature — openers, closers, idioms,
  fact-leads, and address forms pulled live from `_VOICE_PROFILES`.
  Flag triggers below 0.25. Sidebar shows a live drift label
  (`in voice` / `weak voice` / `drift`) per character, refreshed every
  rerun. Pins a real safety guarantee: if the LLM stops sounding like
  the character, the UI notices.
- **Compliance audit log (`audit.py`).** Append-only, timestamped
  record of every safety verdict, refusal, persona-memory edit, and
  dialogue-chain launch. Exportable as CSV from the sidebar. For a
  hackathon this is theatre, but it's *real* theatre — judges
  reviewing under Reliability & Safety see proper accountability.
- **i18n stub (`i18n.py`).** Welcome monologue and key UI labels
  translated to English, Spanish, and Hindi. Sidebar language picker
  at the top of the sidebar. Mira-7 greets you in whichever language
  you pick.
- **More lore.** `lore/world/josc-charter.md` (the JOSC governance
  excerpts that justify Park overriding Mira's automated isolation +
  Okafor refusing sample transport + the Article 12 comms-blackout
  paperwork) and `lore/crew/volkov-tools.md` (Volkov's personal
  inventory including the pickle jar). Both retrievable, both pinned
  by golden-row tests.

`doctor` is now **22 checks** (added world sim, drift, audit, i18n).
**178 tests total** — 28 new across world_sim (7), drift (6), audit
(7), i18n (6), and the round-16 lore retrievability (2).

## Round 17 — Voice (TTS), character tools, mood-over-time, bench

Five substantive additions, all about turning the characters into more
active participants.

- **Browser TTS per character (`tts.py`).** Each character gets a Web
  Speech API voice profile (rate, pitch, voice-name hints) tuned to
  their dossier — Park lower & slower, Hua higher & faster, Volkov
  deepest with Russian voice hints, Mira a UK alto. Every assistant
  reply renders a "🔊 Speak" button that runs the text through the
  user's browser's speech synthesis. No server-side audio.
- **Per-character tools (`character_tools.py`).** Mira-7 can read the
  live telemetry; Volkov can ACK a reading (resets toward midpoint,
  *actually mutates the world sim*); Hua does vitals spot-checks
  (Okafor's elevated heart rate shows up here); Okafor pulls HB-441
  amplitude readings; Park gets station status. Triggers are regex
  patterns; results are threaded into the system prompt as
  `TOOL RESULTS` so the character weaves real numbers into their reply.
  Tool results are also surfaced as 🔧 chips under the reply.
- **Mood-over-time chart.** Each `MoodState.observe()` snapshots
  energy/focus/openness; the sidebar plots a per-character openness
  trajectory using Streamlit's line chart. Caps at 200 entries per
  character so long sessions don't bloat session state.
- **System-prompt inspector.** Sidebar expander shows the *exact*
  system prompt the next reply will use for the active character —
  dossier + mood + persona memory + telemetry — so judges can see
  there's no hidden state.
- **`cli.py bench` + two new tool scenarios.** `bench` runs every
  built-in character against a fixed 5-query set and reports retrieval
  coverage, average top score, and in-voice percentage. All five
  characters scored 100% retrieved / 100% in-voice on first run. New
  scenarios: "Mira-7: live station status" and "Hua: vitals spot-check
  on Okafor" — both exercise the tools system end-to-end.

`doctor` is now **25 checks** (added tts profiles, character tools,
mood history). **195 tests total** — 17 new across tts (6), character
tools (7), mood history (3), CLI bench (1).

## Round 18 — Crisis, handover, voice input

The "make the bots actually manage the station" round.

- **Crisis detector (`crisis.py`).** Scans the live world simulation
  every prompt build. When any monitored system drifts out of nominal,
  a `CrisisEvent` fires — with severity (`watch` if within half a band,
  `alarm` beyond), the system owner (Volkov for reactor/coolant, Mira
  for life support, Okafor for HB-441, Park for everything else), and
  a prompt block the cast incorporates only if relevant. Main pane
  surfaces an active-alarms banner above the chat.
- **Character handover (`handover.py`).** Five topic regexes route
  questions to the right specialist when the active character is out
  of their lane. Volkov defers HB-441 biology to Okafor, Park defers
  reactor-coolant questions to Volkov, Mira defers medical to Hua,
  and so on. The active character still answers briefly but also
  suggests who'd actually know.
- **Voice input (`voice_input.py`).** Mic button in the sidebar uses
  Web Speech Recognition to capture user input and copies the
  transcript to the clipboard (Streamlit's `st.chat_input` can't
  accept programmatic writes, so this is the cleanest path). Paired
  with the existing TTS "🔊 Speak" buttons, you can now have a full
  voice loop with the crew.
- **`cli.py crisis <system> [--value N]`.** Simulate a system going
  out of nominal and watch the owner + Park react in voice.
  Smoke-verified: `cli.py crisis lif_a_psi --value 200` correctly
  routes to Volkov and produces in-voice replies.
- **More lore.** `lore/world/emergency-procedures.md` — JOSC-charter-
  derived response procedures by casualty type (reactor, atmospheric,
  comms, medical, sample). Section 11 explicitly covers HB-441's
  0.030 Hz EM threshold.

`doctor` is now **29 checks** (added crisis scanner, handover, voice
input, emergency lore). **216 tests total** — 21 new across crisis (7),
handover (7), voice input (2), emergency lore (2), CLI crisis (3).

## Round 19 — Slash commands, milestone memos, mood radar

The "power user features" round.

- **Slash commands (`slash.py`).** Type `/` in the chat to bypass the
  LLM entirely. Supported: `/help` (lists everything), `/sitrep`
  (telemetry + crisis + crew positions), `/vitals [person]`,
  `/reactor`, `/lore <query>`, `/note <text>`, `/forget <text>`,
  `/clear`, `/handover <character>`. Deterministic, no token spend,
  rendered as a system reply.
- **Session memos (`memo.py`).** Auto-detect notable first-time moments
  — first reply, first refusal, first tool invocation, first crisis,
  first dialogue chain, first character switch. Surfaces in the
  sidebar as a timestamped timeline so a returning user sees what
  happened at a glance.
- **Mood radar in the sidebar.** Replaces the placeholder with a bar
  chart per character × axis (energy/focus/openness). Pairs with the
  existing line chart so you can see both per-turn drift and current
  state.
- **More lore.** `lore/crew/park-coffee.md` — the four-minute ritual,
  the chipped steel cup, the 412 separate brews Mira-7 has timed.
  Closes the loop on every other dossier's reference to Park's coffee
  habit.

`doctor` is now **32 checks** (added slash commands, memo book, coffee
lore). **239 tests total** — 23 new across slash (13), memo (7),
coffee lore (2). Live-verified slash flow: `/sitrep` returned full
telemetry, `/note bring extra coffee` recorded into Park's persona
memory, `/handover volkov` flipped the active character.

## Round 20 — Alignment audit, `cli.py snapshot`, extended analytics

The "make sure every cross-reference resolves" round.

- **Full alignment audit.** README project-layout block had drifted —
  was missing 15 of the 31 Python modules added since round 12. Rewrote
  it with categorized sections (Entry points / Cast & persona /
  Knowledge / Live world / Interaction / Safety, observability /
  Data / Tests, deploy, docs). HOW_IT_WORKS.md file map similarly
  rewritten with the same categorisation. Every `.py` on disk now
  appears in both.
- **`JUDGES_GUIDE.md` refreshed.** Rubric mapping updated to mention
  retrieval bias, crisis detection, handover, character tools, slash
  commands, audit log, drift detector, system-prompt inspector, i18n.
  Test count → 239, doctor → 32. Added a round-by-round highlights
  appendix.
- **Extended analytics (`analytics.py`).** New counters: slash
  commands by verb, tools invoked by name, scalar counters for crises
  observed / memos recorded / handovers suggested. Sidebar metrics
  block surfaces them when non-zero.
- **`cli.py snapshot`.** Single command that prints cast, lore stats,
  active backends, initial world-sim state, available scenarios, and
  the full `doctor` report. Perfect for pasting into a submission
  form. Smoke-verified live.

`doctor` stays at **32 checks**. **246 tests total** — 7 new across
extended analytics counters (6) and the snapshot smoke test (1).

## Round 21 — Full-state persistence

Audit-driven round. Confirmed alignment is clean: 31 modules on disk
all present in README and HOW_IT_WORKS; test count badge matches
reality (246 → now 250); doctor count claim matches (32 → now 33);
all 10 scenarios and 9 relationship edges resolve to real characters.

Then shipped one focused improvement:

- **Full-state persistence (`persistence.py`).** Saves the world sim,
  persona memory, mood state, audit log, and memo book to a single
  versioned JSON file. Sidebar Save / Load buttons restore the full
  session — survives a browser refresh, container restart, even a
  cross-machine copy. Schema-versioned (mismatches refuse cleanly).
  Round-trip verified live: a sim with tick=10, LiF-A=200 psi, two
  persona notes, one safety refusal, and one memo was written to disk
  (2459 bytes) and re-hydrated identically.

**250 tests total** — 4 new for persistence (serialize/apply round
trip, file-based write/read, schema mismatch rejection, memo dedup
preservation). **`doctor` is now 33 checks.**

## Round 22 — REPL chat, /summary, cost estimator, Mira's private log

Four substantive additions.

- **`cli.py chat <character>` — interactive REPL.** Stateful terminal
  chat that runs the full pipeline (retrieval → bias → safety → mood +
  memory + sim → LLM → reasoning). Slash commands work inside it
  (`/sitrep`, `/note`, `/handover` flips the active character live).
  Color output via ANSI (toggle with `--no-color`). Tool results
  surface as 🔧 lines, handover hints as 💡 lines. `/quit` exits.
  Smoke-verified: piped "What's reactor A at?\\n/sitrep\\n/quit\\n" runs
  end-to-end with Park's voice, tools fire, sitrep prints.
- **`/summary` slash command.** Generates an on-demand session recap
  from persona notes and world-sim state. Shows up in `/help`.
- **Cost estimator (`cost.py`).** Approximates input/output tokens
  (chars/4 heuristic) and projects Azure OpenAI gpt-4o-mini list-price
  cost. Sidebar shows running `LLM calls / tokens / estimated USD`.
  Offline mock LLM is excluded from billing. Pricing constructor
  overridable.
- **More lore.** `lore/world/mira-private-log.md` — Mira-7's private
  observation archive. Park untouched coffee 2096-03-04, Okafor's
  resting heart rate elevated 16 consecutive days, Volkov teaching Hua
  the Queen's Gambit at 22:14, Hua's first chess win not logged because
  she didn't log it — Mira logs it here. Adds the "she sees
  everything" quality without breaking her behavioral envelope.

`doctor` is now **36 checks** (added cost estimator, /summary, Mira
private log). **265 tests total** — 15 new across cost (5), /summary
(4), CLI chat REPL (4), Mira's private log lore (2).

## Round 23 — HTTP API, performance metrics, fr + de

Four substantive additions, all measurable wins.

- **FastAPI HTTP API (`api.py`).** REST endpoints mirroring the CLI:
  `GET /crew`, `POST /ask`, `POST /dialogue`, `GET /sitrep`,
  `GET /lore/search`, `GET /doctor`, `GET /healthz`. Lazy-imported so
  the rest of the project still works without FastAPI installed. All
  endpoints smoke-tested live via `TestClient`: `/ask park` returned
  Park's grounded reply with citations from `lore/incidents/halberd.md`,
  `/dialogue` produced 2 turns, `/doctor` returned `return_code=0`.
- **`cli.py serve`.** Starts the API on `0.0.0.0:8000` via uvicorn.
  Optional dep; prints a helpful error if uvicorn isn't installed.
- **Performance metrics (`perf.py`).** Context-manager timer plus
  per-operation `Timings` class tracking count/min/avg/p95/max. The
  Streamlit `_respond` now wraps retrieval and the LLM call in
  `perf_timer`, and the sidebar renders a live table:
  ```
  | operation | n | min | avg | p95 | max |
  | retrieval | 12 | 8.2ms | 11.5ms | 16.0ms | 18.4ms |
  | llm       | 12 | 0.7ms |  1.1ms |  1.8ms |  2.3ms |
  ```
- **i18n grew to 5 languages.** Added French + German for the Mira-7
  welcome monologue + UI labels. Sidebar picker shows en / es / hi /
  fr / de.

`doctor` is now **39 checks** (added HTTP api, perf timings, i18n
langs). **284 tests total** — 19 new across HTTP API (9), perf (5),
i18n more-languages (5).

## Round 24 — Inspect, /system-prompt, rate limiting, bench --json

Four polish items focused on transparency, API hardening, and tooling.

- **`cli.py inspect <character>`.** Dumps a character's full dossier —
  system prompt (with GROUND TRUTH rules), all voice profile fields
  (openers / short_openers / warm_openers / closers / idioms / fact_lead
  / no_fact), address forms for every other crew member, available
  tools, retrieval bias (folder weights + file boosts), and TTS voice
  profile (rate / pitch / voice_hints). Live-verified on Park.
- **`/system-prompt` slash command.** Inline alternative — type
  `/system-prompt` in chat to see the active character's pure
  (un-augmented) dossier. Pairs with the existing system-prompt
  inspector for sidebar parity.
- **API rate limiting (`rate_limit.py`).** Per-IP token-bucket
  limiter. Default 30-token burst, 0.5 tokens/sec refill. Wired into
  `/ask` and `/dialogue` via FastAPI `Depends`. Returns HTTP 429 over
  the limit. **Live verified: 50 requests → exactly 30 OK then 20 ×
  429**, matching the bucket size. `build_app(rate_limit=False)`
  disables it for tests and benchmarks.
- **`cli.py bench --json`.** Machine-readable output of the
  per-character benchmark — input queries + per-character
  retrieved_pct / avg_score / in_voice_pct. Useful for CI dashboards
  and regression tracking.
- **Makefile: `make api`, `make bench`, `make doctor`.** Common
  shortcuts for the new verbs.
- **README HTTP API quick-start.** Curl examples for every endpoint,
  pointer to auto-generated `/docs` OpenAPI page, rate-limit note.

Also rebuilt `api.py` cleanly: FastAPI imports were soft-failing
after an earlier patch sequence accumulated mess. The new version has
a proper `_HAVE_FASTAPI` flag, module-level model classes, and
dependency-injected gate that FastAPI introspects correctly.

`doctor` is now **41 checks** (added rate limiter, `/system-prompt`).
**298 tests total** — 14 new across CLI inspect (3), /system-prompt
(3), rate limiter (5), API rate-limit integration (2), bench --json
(1).

## Round 25 — Submission cut (v1.0.0)

The final round. Locks the submission state.

- **`SUBMISSION.md`** — single-page packet for the hackathon entry
  form: what this is, how to run (four interfaces), distinctive
  features, test stats, deployment options, repo hygiene checklist,
  submitter info. Mirrors the GitHub README opener but shorter and
  decision-oriented.
- **`cli.py smoke`** — end-to-end smoke that exercises the canonical
  demo path: safety refusal → grounded ask → character tool → handover
  → crisis routing → inter-character dialogue → /summary → persistence
  round-trip. Eight steps, all PASS on first run. Different from
  `doctor` (which checks invariants); this checks behavior.
- **Capstone lore.** `lore/crew/park-rotation-log.md` — Park's personal
  log, final entry of the seventh rotation. Brings the corpus to 20
  files and adds a small character note that closes the dossier
  collection symmetrically.
- **Doctor expanded to 43 checks** (added SUBMISSION packet
  verification, capstone lore retrievability). **301 tests total** —
  3 new across smoke (2) and capstone lore (1).
- **`pyproject.toml` → `1.0.0`.** Declaring the submission version.

After 25 rounds across one session, the project sits at:

- **36 Python modules** orchestrating retrieval, reasoning, safety,
  mood, persona memory, world simulation, crisis detection, character
  handover, dialogue chains, tools, TTS/STT voice loop, slash commands,
  session memos, persistence, audit log, cost estimation, performance
  metrics, HTTP API with rate limiting, MCP server, CLI with 22 verbs.
- **20 lore files** across world / crew / incidents.
- **10 turnkey scenarios** in the sidebar.
- **5 languages** for the welcome monologue.
- **301 tests** in ~7s.
- **43 doctor checks**, all green.
- **4 interfaces** (Streamlit / CLI REPL / HTTP API / MCP server).

Ready to submit.
