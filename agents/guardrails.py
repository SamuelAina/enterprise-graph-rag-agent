from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import re


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern
    action: str = "redact"  # "redact" | "block"


# Practical starter rules (extend over time)
RULES: List[Rule] = [
    # Generic secrets in key=value or JSON-ish formats
    Rule(
        name="api_key_assignment",
        pattern=re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*([^\s\"']+|\"[^\"]+\"|'[^']+')"),
        action="redact",
    ),
    # Authorization header bearer tokens
    Rule(
        name="bearer_token",
        pattern=re.compile(r"(?i)\bauthorization\b\s*:\s*bearer\s+[A-Za-z0-9\-\._~\+\/]+=*"),
        action="redact",
    ),
    # UK NI number (rough pattern), can be "block" if you prefer
    Rule(
        name="uk_nino",
        pattern=re.compile(r"(?i)\b(?!BG)(?!GB)(?!NK)(?!KN)(?!TN)(?!NT)(?!ZZ)[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b"),
        action="redact",
    ),
    # Credit card numbers (very rough; consider Luhn check if you add complexity)
    Rule(
        name="credit_card_like",
        pattern=re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
        action="redact",
    ),
    # US SSN
    Rule(
        name="us_ssn",
        pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        action="redact",
    ),
]


def _apply_rules(text: str) -> Tuple[str, Dict[str, int], bool]:
    """
    Returns:
      redacted_text, hits_by_rule, should_block
    """
    hits: Dict[str, int] = {}
    should_block = False
    out = text

    for rule in RULES:
        # count matches first (without logging values)
        matches = list(rule.pattern.finditer(out))
        if not matches:
            continue

        hits[rule.name] = hits.get(rule.name, 0) + len(matches)

        if rule.action == "block":
            should_block = True
            continue

        # Redaction strategy:
        # - If pattern has groups with values, redact only the value part when possible.
        # - Otherwise redact the full match.
        def repl(m: re.Match) -> str:
            # If we have at least 2 groups, assume group(2) is the sensitive value
            if m.lastindex and m.lastindex >= 2:
                whole = m.group(0)
                val = m.group(2)
                return whole.replace(val, "[REDACTED]")
            return "[REDACTED]"

        out = rule.pattern.sub(repl, out)

    return out, hits, should_block


def apply_guardrails(query: str, context: Dict[str, Any], trace) -> Dict[str, Any]:
    """
    Governance hook:
    - Redacts sensitive info in retrieved snippets
    - Redacts sensitive info in query (for logging + LLM)
    - Emits structured audit info (rule hits), without leaking secrets
    - Optionally blocks if high-risk content detected
    """
    # 1) Sanitize query (do NOT log raw query)
    redacted_query, q_hits, q_block = _apply_rules(query)

    docs = []
    total_hits = 0
    hits_by_rule: Dict[str, int] = {}
    blocked = bool(q_block)

    # accumulate query hits
    for k, v in q_hits.items():
        hits_by_rule[k] = hits_by_rule.get(k, 0) + v
        total_hits += v

    # 2) Sanitize retrieved docs/snippets
    for d in context.get("docs", []):
        d = dict(d)
        snippet = d.get("snippet", "") or ""

        redacted, hits, should_block = _apply_rules(snippet)
        d["snippet"] = redacted

        for k, v in hits.items():
            hits_by_rule[k] = hits_by_rule.get(k, 0) + v
            total_hits += v

        blocked = blocked or should_block
        docs.append(d)

    out_ctx = dict(context)
    out_ctx["docs"] = docs

    # Optional: also sanitize context_text if you use it downstream
    if "context_text" in out_ctx and isinstance(out_ctx["context_text"], str):
        out_ctx["context_text"], c_hits, c_block = _apply_rules(out_ctx["context_text"])
        for k, v in c_hits.items():
            hits_by_rule[k] = hits_by_rule.get(k, 0) + v
            total_hits += v
        blocked = blocked or c_block

    trace.event(
        "guardrails_applied",
        redactions=total_hits,
        hits_by_rule=hits_by_rule,
        blocked=blocked,
    )
    trace.set_metric("redactions", total_hits)
    trace.set_metric("blocked", int(blocked))

    # If blocking, prevent downstream leakage
    if blocked:
        out_ctx["context_text"] = "[BLOCKED: sensitive content detected]"
        return {
            "query": "[BLOCKED]",
            "context": out_ctx,
        }

    # Normal path: return sanitized query + sanitized context
    return {
        "query": redacted_query,
        "context": out_ctx,
    }
