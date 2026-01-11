from __future__ import annotations

from typing import List, Dict, Any, Tuple
import os
import re


STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is",
    "are", "was", "were", "be", "as", "at", "by", "from", "it", "this", "that",
    "we", "you", "i", "they", "them", "our", "your"
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9_]+", (text or "").lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _doc_text(d: Dict[str, Any]) -> str:
    return ((d.get("title") or "") + " " + (d.get("snippet") or "")).strip()


class SimpleReranker:
    """
    Deterministic reranker:
    - boosts docs that share more tokens with the query (Jaccard similarity)
    - optionally boosts by doc type priority (runbook > guide > procedure > policy)
    - combines rerank_score with original retrieval score for final ordering
    - optional MMR diversification to reduce near-duplicates
    """

    def __init__(
        self,
        type_weights: Dict[str, float] | None = None,
        alpha: float | None = None,
        mmr_lambda: float | None = None,
    ):
        # final = alpha * original + (1-alpha) * rerank
        self.alpha = alpha if alpha is not None else float(os.getenv("RERANK_ALPHA", "0.65"))

        self.type_weights = type_weights or {
            "runbook": 1.10,
            "guide": 1.05,
            "procedure": 1.03,
            "policy": 1.00,
        }

        # MMR: 1.0 = no diversification, lower = more diversity
        self.mmr_lambda = mmr_lambda if mmr_lambda is not None else float(os.getenv("RERANK_MMR_LAMBDA", "1.0"))

    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int | None = None) -> List[Dict[str, Any]]:
        if not docs:
            return []

        q_tokens = _tokenize(query)
        # If query tokenization fails (e.g., very short query), just keep base ordering
        if not q_tokens:
            return self._ensure_scores(docs, top_k=top_k)

        scored: List[Dict[str, Any]] = []
        for d in docs:
            title = d.get("title", "") or ""
            snippet = d.get("snippet", "") or ""
            meta = d.get("metadata", {}) or {}
            doc_type = (meta.get("type") or "").lower()

            d_tokens = _tokenize(title + " " + snippet)
            overlap = _jaccard(q_tokens, d_tokens)

            w = self.type_weights.get(doc_type, 1.0)
            rerank_score = overlap * w

            base = float(d.get("score", 0.0))
            final = self.alpha * base + (1.0 - self.alpha) * rerank_score

            nd = dict(d)
            nd["rerank_score"] = float(rerank_score)
            nd["final_score"] = float(final)
            scored.append(nd)

        # Sort deterministic: final_score desc, then doc_id asc as tie-breaker
        scored.sort(key=lambda x: (-float(x.get("final_score", 0.0)), str(x.get("doc_id", ""))))

        if top_k is not None:
            scored = scored[:top_k]

        # Optional diversification step
        if self.mmr_lambda < 1.0:
            scored = self._mmr_select(scored, top_k=top_k or len(scored))

        return scored

    def _ensure_scores(self, docs: List[Dict[str, Any]], top_k: int | None = None) -> List[Dict[str, Any]]:
        out = []
        for d in docs:
            nd = dict(d)
            base = float(nd.get("score", 0.0))
            nd.setdefault("rerank_score", 0.0)
            nd.setdefault("final_score", base)
            out.append(nd)

        # deterministic ordering by score then doc_id
        out.sort(key=lambda x: (-float(x.get("final_score", 0.0)), str(x.get("doc_id", ""))))
        if top_k is not None:
            out = out[:top_k]
        return out

    def _mmr_select(self, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Simple deterministic MMR using Jaccard similarity on doc text tokens.
        MMR score = λ * relevance - (1-λ) * max_similarity_to_selected
        """
        lam = self.mmr_lambda
        selected: List[Dict[str, Any]] = []
        remaining = docs[:]

        doc_tokens = {d.get("doc_id"): _tokenize(_doc_text(d)) for d in remaining}

        while remaining and len(selected) < top_k:
            best = None
            best_score = None

            for d in remaining:
                rel = float(d.get("final_score", 0.0))
                if not selected:
                    mmr = rel
                else:
                    sims = [_jaccard(doc_tokens[d.get("doc_id")], doc_tokens[s.get("doc_id")]) for s in selected]
                    max_sim = max(sims) if sims else 0.0
                    mmr = lam * rel - (1.0 - lam) * max_sim

                if best is None or mmr > best_score:
                    best = d
                    best_score = mmr

            selected.append(best)
            remaining = [x for x in remaining if x is not best]

        return selected


def maybe_rerank(query: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Feature-flag entry point:
    - Always ensures final_score exists (even when disabled)
    """
    enabled = os.getenv("RERANK_ENABLED", "true").lower() in ("1", "true", "yes", "y")
    reranker = SimpleReranker()
    if not enabled:
        # still ensure final_score so downstream can rely on it
        return reranker._ensure_scores(docs)
    return reranker.rerank(query=query, docs=docs)
