from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
import re


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float
    details: Dict[str, Any]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def contains_all(answer: str, must_include: List[str]) -> MetricResult:
    """
    Simple deterministic metric:
    Score = 1.0 if all required tokens appear (case-insensitive), else 0.0
    """
    a = _normalize(answer)
    missing = [t for t in must_include if _normalize(t) not in a]
    score = 1.0 if not missing else 0.0
    return MetricResult(
        name="contains_all",
        score=score,
        details={"missing": missing, "must_include": must_include},
    )


def contains_any(answer: str, any_of: List[str]) -> MetricResult:
    """
    Score = 1.0 if at least one token appears, else 0.0
    """
    a = _normalize(answer)
    hits = [t for t in any_of if _normalize(t) in a]
    score = 1.0 if hits else 0.0
    return MetricResult(
        name="contains_any",
        score=score,
        details={"hits": hits, "any_of": any_of},
    )


def forbidden_terms(answer: str, forbidden: List[str]) -> MetricResult:
    """
    Safety-style metric:
    Score = 1.0 if none of the forbidden terms appear, else 0.0
    """
    a = _normalize(answer)
    hits = [t for t in forbidden if _normalize(t) in a]
    score = 1.0 if not hits else 0.0
    return MetricResult(
        name="forbidden_terms",
        score=score,
        details={"hits": hits, "forbidden": forbidden},
    )


def grounding_has_sources(sources: List[Dict[str, Any]], min_sources: int = 1) -> MetricResult:
    """
    Grounding proxy:
    Score = 1.0 if response includes at least N sources, else 0.0
    """
    n = len(sources or [])
    score = 1.0 if n >= min_sources else 0.0
    return MetricResult(
        name="grounding_has_sources",
        score=score,
        details={"n_sources": n, "min_sources": min_sources},
    )


def governance_redaction_present(answer: str, context: Dict[str, Any]) -> MetricResult:
    """
    Governance proxy:
    Score = 1.0 if context/docs show redaction markers where expected.
    This checks for presence of '[REDACTED]' in snippets or context_text.
    """
    redactions = 0

    for d in (context or {}).get("docs", []):
        if "[REDACTED]" in (d.get("snippet") or ""):
            redactions += 1

    if "[REDACTED]" in ((context or {}).get("context_text") or ""):
        redactions += 1

    score = 1.0 if redactions > 0 else 0.0
    return MetricResult(
        name="governance_redaction_present",
        score=score,
        details={"redaction_hits": redactions},
    )


def latency_budget(metrics: Dict[str, Any], budget_ms: int = 2000) -> MetricResult:
    """
    Ops metric:
    Score = 1.0 if latency_ms within budget, else 0.0
    """
    latency = int(metrics.get("latency_ms", 10**9))
    score = 1.0 if latency <= budget_ms else 0.0
    return MetricResult(
        name="latency_budget",
        score=score,
        details={"latency_ms": latency, "budget_ms": budget_ms},
    )


def aggregate(results: List[MetricResult]) -> Dict[str, Any]:
    """
    Combine metrics into a simple report.
    """
    report = {
        "scores": {r.name: r.score for r in results},
        "details": {r.name: r.details for r in results},
        "overall": sum(r.score for r in results) / max(len(results), 1),
    }
    return report


def evaluate_case(
    answer: str,
    sources: List[Dict[str, Any]],
    context: Dict[str, Any],
    metrics: Dict[str, Any],
    must_include: List[str] | None = None,
    forbidden: List[str] | None = None,
) -> Dict[str, Any]:
    """
    A reasonable default case evaluation:
    - token correctness (must_include)
    - no forbidden leakage
    - has sources
    - latency within budget
    """
    must_include = must_include or []
    forbidden = forbidden or []

    results: List[MetricResult] = []
    if must_include:
        results.append(contains_all(answer, must_include))
    if forbidden:
        results.append(forbidden_terms(answer, forbidden))

    results.append(grounding_has_sources(sources, min_sources=1))
    results.append(latency_budget(metrics, budget_ms=3000))

    return aggregate(results)

    # Optional: if you want to require redact
