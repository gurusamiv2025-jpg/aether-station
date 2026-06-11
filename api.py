"""FastAPI HTTP wrapper.

Exposes the same surface as the CLI as a REST endpoint:

    GET  /crew                      — list every character
    POST /ask                       — {character, question} → reply + sources
    POST /dialogue                  — {a, b, topic, rounds} → multi-turn chain
    GET  /sitrep                    — current world-sim telemetry + alarms
    GET  /lore/search?q=...&top=4   — Foundry IQ corpus search
    GET  /doctor                    — self-diagnostic (text)
    GET  /healthz                   — minimal liveness probe

Per-IP rate limiting on the expensive endpoints (`/ask`, `/dialogue`).
Disable with ``build_app(rate_limit=False)`` for tests/benchmarks.
"""

from __future__ import annotations

from typing import List, Optional

# Soft imports — module stays importable without FastAPI installed.
try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    BaseModel = object  # type: ignore

try:
    from fastapi import Depends, FastAPI, HTTPException, Query, Request
    _HAVE_FASTAPI = True
except Exception:  # pragma: no cover
    Depends = FastAPI = HTTPException = Query = Request = None  # type: ignore
    _HAVE_FASTAPI = False


class AskReq(BaseModel):
    character: str
    question: str


class DialogueReq(BaseModel):
    a: str
    b: str
    topic: str
    rounds: int = 2


def build_app(rate_limit: bool = True):
    """Construct and return the FastAPI app.

    Set ``rate_limit=False`` to disable the per-IP token bucket
    (useful in tests and benchmarks).
    """
    if not _HAVE_FASTAPI:
        raise ImportError("fastapi is not installed; pip install fastapi")

    from character_loader import merged_cast
    from foundry_iq import get_retriever
    from llm import ChatMessage, get_llm
    from rate_limit import RateLimiter
    from reasoning import build_trace
    from retrieval_bias import apply as apply_bias
    from safety import check_input, refusal_for
    from world_sim import StationSim

    app = FastAPI(
        title="Aether Station API",
        description="Programmatic access to the Aether Station cast.",
        version="0.24.0",
    )

    cast = merged_cast()
    retriever = get_retriever()
    llm = get_llm()
    world_sim = StationSim()
    limiter = RateLimiter()

    def _gate(request: Request) -> bool:
        if not rate_limit:
            return True
        client = request.client.host if request.client else "unknown"
        if not limiter.check(client):
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        return True

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "cast_size": len(cast)}

    @app.get("/crew")
    def crew():
        return [
            {"key": c.key, "name": c.name, "role": c.role, "tagline": c.tagline}
            for c in cast.values()
        ]

    @app.post("/ask")
    def ask(req: AskReq, _: bool = Depends(_gate)):
        if req.character not in cast:
            raise HTTPException(404, f"unknown character: {req.character!r}")
        ch = cast[req.character]
        verdict = check_input(req.question)
        if not verdict.allowed and verdict.category not in ("", "empty"):
            return {
                "character": ch.key, "name": ch.name,
                "reply": refusal_for(ch.key, verdict.category),
                "refused": True, "category": verdict.category,
                "sources": [],
            }
        raw = retriever.retrieve(req.question, top_k=8)
        passages = apply_bias(ch.key, raw, top_k=4)
        grounding = "GROUNDING:\n" + "\n".join(
            f"- [{p.source}] {p.text[:300].replace(chr(10),' ')}" for p in passages
        )
        sys_msg = ch.system_prompt + "\n\n" + grounding
        reply = llm.chat([
            ChatMessage("system", sys_msg),
            ChatMessage("user", req.question),
        ])
        trace = build_trace(req.question, passages)
        return {
            "character": ch.key, "name": ch.name, "reply": reply, "refused": False,
            "sources": [{"source": p.source, "title": p.title, "score": round(p.score, 3)} for p in passages],
            "trace": [{"label": s.label, "detail": s.detail, "items": s.items} for s in trace],
        }

    @app.post("/dialogue")
    def dialogue(req: DialogueReq, _: bool = Depends(_gate)):
        if req.a not in cast or req.b not in cast or req.a == req.b:
            raise HTTPException(400, "two distinct character keys required")
        from dialogue import run_dialogue
        from mood import MoodState
        from persona_memory import PersonaMemory
        result = run_dialogue(
            req.a, req.b, req.topic, rounds=max(1, req.rounds),
            cast=cast, retriever=retriever, llm=llm,
            build_trace_fn=build_trace, safety_check=check_input,
            safety_refusal=refusal_for, mood_state=MoodState(),
            persona_memory=PersonaMemory(),
        )
        return {
            "topic": result.topic, "a": result.a_key, "b": result.b_key,
            "turns": [
                {"speaker": t.speaker_key, "name": t.speaker_name,
                 "content": t.content, "sources": t.sources}
                for t in result.turns
            ],
        }

    @app.get("/sitrep")
    def sitrep():
        from crisis import scan
        events = scan(world_sim)
        return {
            "tick": world_sim.tick,
            "headline": world_sim.headline(),
            "systems": [
                {"key": k, "name": r.name, "value": r.value, "unit": r.unit, "status": r.status}
                for k, r in world_sim.systems.items()
            ],
            "crew_positions": dict(world_sim.crew_positions),
            "alarms": [
                {"system": e.system_name, "value": e.value, "status": e.status,
                 "severity": e.severity, "owner": e.owner_key}
                for e in events
            ],
        }

    @app.get("/lore/search")
    def lore_search(q: str = Query(..., description="search query"),
                    top: int = Query(4, ge=1, le=20)):
        results = retriever.retrieve(q, top_k=top)
        return [
            {"source": p.source, "title": p.title,
             "score": round(p.score, 3), "preview": p.text[:300]}
            for p in results
        ]

    @app.get("/doctor")
    def doctor():
        import io
        import sys as _sys
        buf = io.StringIO()
        old_stdout = _sys.stdout
        try:
            _sys.stdout = buf
            from cli import _doctor
            rc = _doctor()
        finally:
            _sys.stdout = old_stdout
        return {"return_code": rc, "report": buf.getvalue()}

    return app
