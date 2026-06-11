# Submission packet — Aether Station

For: **Agents League @ AISF 2026**
Track: **🎨 Creative Apps**
IQ layer: **🧠 Foundry IQ** (with `azure-ai-projects` agent backend + a
TF-IDF / BM25 fallback that runs offline)

---

## What this is

A multi-character chatbot grounded in a custom 20-file lore corpus.
Five built-in crew members (Park, Okafor, Mira-7, Volkov, Hua) live on
a fictional orbital research station; every reply is retrieved from
the corpus and rendered in the speaker's voice. The cast knows about
each other, remembers things you tell them, runs tools on a live
station-systems simulation, escalates when readings go out of nominal,
and can be talked to via Streamlit, a terminal REPL, an HTTP API, or
the GitHub Copilot MCP server.

## How to run

```bash
# Web UI (the main demo)
make install
make run                   # → http://localhost:8501

# Or, with zero Python:
make docker-run            # → http://localhost:8501

# Terminal REPL (no browser)
python cli.py chat park

# HTTP API
python cli.py serve --port 8000
curl http://localhost:8000/sitrep | jq

# GitHub Copilot integration
python mcp_server.py       # then point VS Code mcp.json at it
```

Doctor / smoke / bench:

```bash
python cli.py doctor      # 43 subsystem invariants
python cli.py smoke       # canonical demo path
python cli.py bench       # per-character retrieval + voice quality
```

Sanity check after install: `python cli.py doctor` should print 43× OK.

## What's distinctive (top 5)

1. **Per-character retrieval bias.** The same query produces a different
   ranked source list per character (`retrieval_bias.py`). Okafor
   boosts HB-441 1.6×; Volkov pulls the coolant report to the top.
2. **Live world simulation.** Reactor output, coolant pressure, oxygen,
   HB-441 EM peak — actual numbers that drift each turn. Characters
   can read them, ACK them, and crisis-detect when they go red.
3. **Inter-character dialogue.** Two characters argue about a topic
   *without you typing between turns*. Each addresses the other by
   their preferred form (Park says "Kostya", Mira says "Commander Park").
4. **Full transparency.** Reasoning trace, drift detector,
   system-prompt inspector, audit log, performance metrics — every
   reply ships with proof of how it was built.
5. **Four interfaces from one core.** Streamlit UI, terminal REPL,
   HTTP API (rate-limited), MCP server for VS Code — same pipeline
   behind all of them.

## Test stats

- **301 pytest tests** in ~7 seconds
- **43 doctor checks**, all OK
- **GitHub Actions CI** across Python 3.10 / 3.11 / 3.12
- **10 golden retrieval rows** pinning lore quality
- **25 hackathon iteration rounds** captured in CHANGELOG

## Rubric mapping

See [`JUDGES_GUIDE.md`](JUDGES_GUIDE.md) for the per-criterion map
(Accuracy, Reasoning, Creativity, UX, Reliability & Safety) and 60-
second / 5-minute tours.

## How GitHub Copilot helped

Copilot Chat in VS Code drafted the initial Streamlit layout and
character-picker scaffolding from a one-line prompt; Copilot inline
suggestions caught empty-history and no-results edge cases that would
have crashed the chat loop; Copilot was used as a sparring partner
when iterating each character's voice ("make Mira less HAL, more
Jeeves"); and Copilot's autocompletion sped up the regex patterns in
`safety.py`, `handover.py`, and the slash-command parser.

## Deployment

See [`DEPLOY.md`](DEPLOY.md) for four hosting paths:

- Streamlit Community Cloud (free, recommended)
- Hugging Face Spaces (free)
- Render (free tier, Docker)
- Azure Container Apps (on-brand for the hackathon)

**Live demo URL:** https://aether-station-lttgtzagkyffhfgqzhyywx.streamlit.app/

## Repository hygiene

- ✅ MIT license, public repo
- ✅ No secrets committed (`.env` in `.gitignore`, `.env.example` is the template)
- ✅ Code of Conduct + Contributing guide
- ✅ Issue + PR templates + Dependabot
- ✅ Lore is original fiction; no real PII; no production data

## Where the code lives

```
36 Python modules · 20 lore files · 10 scenarios · 5 languages · 4 interfaces
```

Architecture diagram + file map in [`HOW_IT_WORKS.md`](HOW_IT_WORKS.md).
Iteration history in [`CHANGELOG.md`](CHANGELOG.md).

## Submitter

V GURUSAMI — `gurusamivelmurugan@gmail.com`
