# Demo video script — Aether Station

**Target length:** 75–90 seconds
**Tool:** any screen recorder (OBS, Loom, Windows Game Bar `Win+G`, Xbox Game Bar)
**Resolution:** 1080p, browser window at ~1280×800 so the sidebar reads cleanly

## Before you record

1. Start the app: `python -m streamlit run app.py`
2. Open `http://localhost:8501` in a fresh browser window (no extensions
   visible).
3. Clear the conversation (sidebar button) so the chat starts empty.
4. Have these three prompts in a notepad ready to paste:
   - `What's your read on the Halberd Mining Cooperative?`
   - `Talk me through the LiF-B coolant leak.`
   - `Why don't you trust Mira-7?` *(round-table prompt)*

## The script

### Scene 1 — Hook (0:00–0:10)

**On screen:** the Aether Station home view with Cmdr. Park selected.

> "This is Aether Station — a multi-character chatbot where every reply is
> grounded in the world's lore through Microsoft Foundry IQ. So the cast
> never contradicts the world, and you can see exactly which lore document
> informed every answer."

### Scene 2 — One character, grounded reply (0:10–0:35)

**Action:** Paste prompt 1 ("What's your read on the Halberd Mining Cooperative?")
to Cmdr. Park. Wait for the reply.

> "Cmdr. Park has a dossier and relationships baked into her persona. When I
> ask about the Halberd Mining Cooperative — which is a faction in this
> world — she answers in her voice…"

**Action:** Click the **Grounding** expander under her reply.

> "…and the answer is grounded in three lore files: the factions doc, the
> 2093 Halberd tug-loss incident report, and her own dossier. Foundry IQ
> retrieved these from the lore corpus before the model generated the reply."

### Scene 3 — Switch character, same world (0:35–0:55)

**Action:** Click **Kostya Volkov** in the sidebar. Paste prompt 2 ("Talk me
through the LiF-B coolant leak.")

> "Switch to the chief engineer and ask about the coolant leak. He answers
> from his perspective — and notice he cites the actual incident timeline
> including the eleven-second isolation delay. That's not invention; that's
> in the lore."

**Action:** Expand the grounding panel briefly to show `coolant-leak.md`.

### Scene 3b — Reasoning trace (0:50–1:00)

**Action:** Expand the **Reasoning trace** panel on Volkov's reply.

> "The reasoning trace shows the agent's chain — it classified the question
> as a technical incident, queried the knowledge layer, retrieved four
> passages, pulled the salient facts, then synthesized the reply in
> Volkov's voice. Judges can see exactly how every answer is built."

### Scene 4 — Round Table (1:00–1:20)

**Action:** Toggle **Round Table** in sidebar. Pick Park and Volkov. Paste
prompt 3.

> "Round Table mode asks two characters the same question. Park stays
> measured. Volkov complains. Both responses are independently grounded
> against the same lore — so the disagreement is character-driven, not
> hallucination-driven."

### Scene 4b — Shared crew memory (1:20–1:30)

**Action:** Click on Cmdr. Park in the sidebar (exits round table) and ask
*"What did Kostya just say about Mira?"*

> "And because every character sees a shared station log, Park knows what
> Volkov just said two turns ago — the cast acts like a crew, not five
> isolated chatbots."

### Scene 4c — Director agent (1:30–1:42)

**Action:** Stay on Park, ask: *"Any update on HB-441 from your end?"*

> "After enough mentions of HB-441, the Director agent — a sixth
> invisible crew member — fires a Mira-7 broadcast into the chat with a
> fresh amplitude reading. The station feels alive instead of paused
> between user inputs."

### Scene 4d — Session export (1:42–1:52)

**Action:** Click *Download as Markdown* in the sidebar. Briefly show
the .md file in a text editor — collapsible reasoning blocks, citations
preserved.

> "Every session can be exported as Markdown or JSON, and re-imported
> later — the cast resumes where you left off."

### Scene 5 — Wrap (1:52–2:05)

**Action:** Show the sidebar status panel (`Retrieval: foundry-iq` or
`local-tfidf` — whichever you're using).

> "Backend runs on Azure AI Foundry agents when configured, with a local
> TF-IDF fallback so the demo always works offline. The cast is also
> exposed as a GitHub Copilot MCP server — so developers can talk to the
> crew directly from VS Code. Built with GitHub Copilot for Agents League
> at AISF 2026."

## Tips

- **Slow down on the citations panel.** That's the proof Foundry IQ is
  actually grounding the replies — judges will look for it.
- **Show the URL bar once** (briefly) so it's obvious this is a live app, not
  a recorded mockup.
- **Don't read the replies word-for-word** out loud; let the viewer skim
  them. Just call out one or two specific facts ("eleven-second delay,"
  "2093 tug loss") to prove the grounding is working.
- **Keep your terminal visible at the start** for two seconds so the app
  startup is real.
- If you run with Azure OpenAI, you'll get richer in-character replies than
  the offline mock. Worth setting up a free Azure trial just for the demo.
