"""Foundry IQ integration layer.

Two backends with the same interface:

- :class:`FoundryAgentRetriever` — calls a Microsoft Foundry IQ knowledge
  agent (Azure AI Foundry Agent Service) configured against the ``lore/``
  corpus. Used when ``FOUNDRY_PROJECT_ENDPOINT`` and ``FOUNDRY_AGENT_ID``
  are set in the environment.

- :class:`LocalRetriever` — TF-IDF + cosine similarity over the local
  ``lore/`` markdown files. Used as a fallback so the demo runs without any
  Azure credentials.

The single public entry point is :func:`get_retriever`, which picks the
right backend based on environment configuration.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol

LORE_DIR = Path(__file__).parent / "lore"


@dataclass
class Passage:
    """A retrieved chunk of grounding context."""

    text: str
    source: str  # relative path from project root, e.g. "lore/crew/park.md"
    score: float

    @property
    def title(self) -> str:
        """Best-effort title — first markdown heading or the file stem."""
        match = re.search(r"^#\s+(.+)$", self.text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return Path(self.source).stem.replace("-", " ").title()


class Retriever(Protocol):
    name: str

    def retrieve(self, query: str, top_k: int = 4) -> List[Passage]: ...


# ---------------------------------------------------------------------------
# Local fallback: TF-IDF over the markdown corpus
# ---------------------------------------------------------------------------


def _load_corpus() -> List[Passage]:
    """Read every markdown file under ``lore/`` and chunk by section heading."""
    passages: list[Passage] = []
    if not LORE_DIR.exists():
        return passages

    for md_path in sorted(LORE_DIR.rglob("*.md")):
        rel = md_path.relative_to(LORE_DIR.parent).as_posix()
        text = md_path.read_text(encoding="utf-8")
        # Chunk on H2 headings; keep the H1 with each chunk for context.
        h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        h1 = h1_match.group(0) if h1_match else ""
        # Split by H2; if there are none, use the whole document as one chunk.
        sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
        # First element is the preamble (everything before the first ##).
        if len(sections) == 1:
            passages.append(Passage(text=text.strip(), source=rel, score=0.0))
            continue
        preamble = sections[0].strip()
        if preamble:
            passages.append(Passage(text=preamble, source=rel, score=0.0))
        for section in sections[1:]:
            chunk = f"{h1}\n\n## {section}".strip()
            passages.append(Passage(text=chunk, source=rel, score=0.0))
    return passages


class LocalRetriever:
    """TF-IDF retriever over the local lore corpus."""

    name = "local-tfidf"

    def __init__(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._corpus = _load_corpus()
        if not self._corpus:
            self._vectorizer = None
            self._matrix = None
            return
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_df=0.9,
        )
        self._matrix = self._vectorizer.fit_transform(
            [p.text for p in self._corpus]
        )

    def retrieve(self, query: str, top_k: int = 4) -> List[Passage]:
        if not self._corpus or self._vectorizer is None:
            return []
        from sklearn.metrics.pairwise import cosine_similarity

        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix).ravel()
        top_idx = sims.argsort()[::-1][:top_k]
        results: list[Passage] = []
        for i in top_idx:
            score = float(sims[i])
            if score <= 0:
                continue
            p = self._corpus[i]
            results.append(Passage(text=p.text, source=p.source, score=score))
        return results


# ---------------------------------------------------------------------------
# Foundry IQ: Azure AI Foundry agent backend
# ---------------------------------------------------------------------------


class FoundryAgentRetriever:
    """Calls a Microsoft Foundry IQ knowledge agent.

    Configured against the ``lore/`` corpus in the Foundry project, the agent
    returns cited passages with permission-aware filtering. We expose only
    the retrieval surface here; chat generation happens in ``llm.py`` so the
    grounding sources can be shown in the UI alongside the reply.
    """

    name = "foundry-iq"

    def __init__(self, project_endpoint: str, agent_id: str) -> None:
        self.project_endpoint = project_endpoint
        self.agent_id = agent_id
        self._client = None  # Lazy: only import azure-* when actually called.

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        self._client = AIProjectClient.from_endpoint(
            endpoint=self.project_endpoint,
            credential=DefaultAzureCredential(),
        )
        return self._client

    def retrieve(self, query: str, top_k: int = 4) -> List[Passage]:
        try:
            client = self._ensure_client()
            # Foundry IQ agents expose a knowledge/retrieve operation that
            # returns cited passages. The exact SDK shape varies by preview
            # version; we use a defensive call pattern and fall through to
            # local retrieval if anything is unexpected.
            agent = client.agents.get_agent(self.agent_id)
            response = client.agents.retrieve_knowledge(  # type: ignore[attr-defined]
                agent_id=agent.id,
                query=query,
                top_k=top_k,
            )
            passages: list[Passage] = []
            for item in getattr(response, "passages", []) or []:
                passages.append(
                    Passage(
                        text=getattr(item, "content", "") or "",
                        source=getattr(item, "source", "foundry-iq"),
                        score=float(getattr(item, "score", 0.0)),
                    )
                )
            return passages
        except Exception:
            # If the Foundry call fails for any reason (auth, network, SDK
            # version skew), fall back to local retrieval so the demo never
            # breaks mid-conversation.
            return LocalRetriever().retrieve(query, top_k=top_k)


# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BM25 fallback (pure Python, no extra deps)
# ---------------------------------------------------------------------------


import math


class BM25Retriever:
    """Okapi BM25 retriever over the local markdown corpus.

    BM25 generally beats TF-IDF on multi-term queries because it dampens
    saturating term frequencies and penalises very long passages. Opt
    into it by setting ``RETRIEVER_BACKEND=bm25`` in the environment.

    Implementation is bog-standard Okapi BM25 with k1=1.5, b=0.75. The
    corpus is the same set of chunks LocalRetriever uses, so golden
    retrieval tests don't have to change.
    """

    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        import re as _re

        self._corpus = _load_corpus()
        self._k1 = k1
        self._b = b
        self._tokenize_re = _re.compile(r"[A-Za-z][A-Za-z0-9\-]{1,}")
        self._docs_tokens = [self._tokenize(p.text) for p in self._corpus]
        self._doc_len = [len(d) for d in self._docs_tokens]
        self._avgdl = (sum(self._doc_len) / max(len(self._doc_len), 1)) or 1.0
        # IDF table
        from collections import Counter
        df: dict = {}
        for d in self._docs_tokens:
            for term in set(d):
                df[term] = df.get(term, 0) + 1
        N = len(self._docs_tokens) or 1
        self._idf = {
            term: math.log(1 + (N - n + 0.5) / (n + 0.5))
            for term, n in df.items()
        }
        # Per-doc term frequencies
        self._tf = [Counter(d) for d in self._docs_tokens]

    def _tokenize(self, text: str) -> list[str]:
        return [t.lower() for t in self._tokenize_re.findall(text)]

    def retrieve(self, query: str, top_k: int = 4):
        if not self._corpus:
            return []
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []
        scores = [0.0] * len(self._corpus)
        for i, tf in enumerate(self._tf):
            score = 0.0
            dl = self._doc_len[i] or 1
            for term in q_tokens:
                if term not in tf:
                    continue
                idf = self._idf.get(term, 0.0)
                f = tf[term]
                denom = f + self._k1 * (1 - self._b + self._b * dl / self._avgdl)
                score += idf * (f * (self._k1 + 1)) / denom
            scores[i] = score
        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]
        # Normalise top score to ~[0,1] range for UI consistency with TF-IDF.
        max_score = max(s for _, s in ranked) if ranked else 1.0
        norm = max_score if max_score > 0 else 1.0
        results = []
        for idx, sc in ranked:
            if sc <= 0:
                continue
            p = self._corpus[idx]
            results.append(Passage(text=p.text, source=p.source, score=sc / norm))
        return results


# Factory
# ---------------------------------------------------------------------------


def get_retriever() -> Retriever:
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    agent_id = os.getenv("FOUNDRY_AGENT_ID", "").strip()
    if endpoint and agent_id:
        return FoundryAgentRetriever(endpoint, agent_id)
    backend = os.getenv("RETRIEVER_BACKEND", "tfidf").lower()
    if backend == "bm25":
        return BM25Retriever()
    return LocalRetriever()
