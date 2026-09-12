from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml
from rank_bm25 import BM25Okapi

from src.config import CORPUS_DIR

TOKEN = re.compile(r"[a-z0-9]+")


@dataclass
class Document:
    id: str
    title: str
    tags: list[str]
    body: str
    path: Path
    status: str = "current"

    def search_text(self) -> str:
        tag_str = " ".join(self.tags)
        return f"{self.id} {self.title} {tag_str} {self.body}"


@dataclass
class Hit:
    doc: Document
    score: float
    rank: int
    snippet: str = ""


def _parse_markdown(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    meta: dict = {}
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
    doc_id = str(meta.get("id") or path.stem)
    return Document(
        id=doc_id,
        title=str(meta.get("title") or path.stem),
        tags=list(meta.get("tags") or []),
        body=body,
        path=path,
        status=str(meta.get("status") or "current"),
    )


def _tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def _snippet(body: str, query: str, width: int = 220) -> str:
    tokens = [t for t in _tokenize(query) if len(t) > 2]
    lower = body.lower()
    idx = -1
    for t in tokens:
        idx = lower.find(t)
        if idx != -1:
            break
    if idx == -1:
        return body[:width].strip() + ("…" if len(body) > width else "")
    start = max(0, idx - 60)
    end = min(len(body), idx + width - 60)
    chunk = body[start:end].strip()
    if start > 0:
        chunk = "…" + chunk
    if end < len(body):
        chunk = chunk + "…"
    return chunk


@dataclass
class Retriever:
    docs: list[Document] = field(default_factory=list)
    _bm25: BM25Okapi | None = None

    @classmethod
    def from_corpus(cls, corpus_dir: Path | None = None) -> "Retriever":
        directory = corpus_dir or CORPUS_DIR
        docs = [_parse_markdown(p) for p in sorted(directory.glob("*.md"))]
        if not docs:
            raise FileNotFoundError(f"No markdown files in {directory}")
        tokenized = [_tokenize(d.search_text()) for d in docs]
        retriever = cls(docs=docs, _bm25=BM25Okapi(tokenized))
        return retriever

    def search(
        self,
        query: str,
        k: int = 5,
        outdated_score_penalty: float | None = None,
    ) -> list[Hit]:
        if not self._bm25:
            return []
        if outdated_score_penalty is None:
            from src.spec import load_pipeline_spec

            outdated_score_penalty = load_pipeline_spec().retriever.outdated_score_penalty
        k = max(1, min(k, len(self.docs)))
        scores = list(self._bm25.get_scores(_tokenize(query)))
        for i, doc in enumerate(self.docs):
            if doc.status != "current":
                scores[i] *= outdated_score_penalty
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        hits = []
        for rank, (idx, score) in enumerate(ranked, start=1):
            doc = self.docs[idx]
            hits.append(
                Hit(
                    doc=doc,
                    score=float(score),
                    rank=rank,
                    snippet=_snippet(doc.body, query),
                )
            )
        return hits


@lru_cache
def get_retriever() -> Retriever:
    return Retriever.from_corpus()
