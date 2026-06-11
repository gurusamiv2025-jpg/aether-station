# Contributing to Aether Station

Thanks for poking around. This is a hackathon submission for **Agents
League @ AISF 2026**, but contributions and forks are welcome.

## Quick setup

```bash
git clone <fork>
cd aether-station
make install        # or: pip install -r requirements.txt
make test           # 88 tests in ~2.5s
make run            # launches Streamlit on http://localhost:8501
```

If anything looks broken, run `python cli.py doctor` — it prints OK/FAIL
for every subsystem so you can localize the issue fast.

## Adding a character

Two ways:

1. **YAML (no code):** drop a `.yaml` file in `characters_extra/`. See
   `characters_extra/garcia.yaml` for a template.
2. **Python (for full flexibility):** add an entry to `CHARACTERS` in
   `characters.py`, write a dossier under `lore/crew/<key>.md`, and add
   a voice profile in `llm.py::_VOICE_PROFILES` for the offline mock.
   If your character has a refusal voice, add entries to
   `safety.py::_REFUSALS`.

Both paths are covered by tests — see `tests/test_characters.py` and
`tests/test_character_loader.py`.

## Adding lore

1. Drop a markdown file under `lore/world/`, `lore/crew/`, or
   `lore/incidents/`.
2. Start with an H1 (`# ...`) so the CLI's `lore list` picks it up
   cleanly.
3. Add a row to `tests/test_retrieval_quality.py` so the retriever's
   ability to find it is pinned by CI.

That last step is the one people forget. Without a golden row, a future
edit to retrieval scoring could silently make your lore unfindable.

## Adding a scenario

Edit `scenarios.py`. Every scenario must:

- Have a unique `key`
- Target a real character (`active_character`)
- Have a starter prompt that actually exercises something interesting

`tests/test_scenarios.py` will catch a typo'd character key on the next
`pytest` run.

## Tests

```bash
make test              # full suite
pytest tests/test_X.py # single file
pytest -k name         # filter by name
```

Anything that flakes is a real bug. The mock LLM is deterministic.

## Style

- Black-compatible (no enforced formatter, but match the surrounding
  code).
- Imports at the top of files, per PEP 8.
- No emojis in code comments unless the user asked for them.
- Reach for the standard library before adding a dep.

## What we won't merge

- Real personal data in tests or lore.
- Anything that puts secrets in the repo (`.env` is gitignored for a
  reason).
- Vendored copies of dependencies.

## Reporting a security issue

See `JUDGES_GUIDE.md` for the rubric map. For security concerns, please
open a private GitHub Security Advisory rather than a public issue.
