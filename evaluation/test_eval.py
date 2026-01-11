import yaml
from evaluation.runner import build_executor
from evaluation.metrics import evaluate_case
from api.telemetry import Trace

def test_eval_cases():
    ex = build_executor()
    with open("evaluation/test_cases.yaml", "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    for c in cases:
        trace = Trace()
        out = ex.run(query=c["query"], trace=trace)
        trace.finish()  # ✅ ensure latency_ms is present

        answer = out["answer"]
        sources = out.get("sources", [])
        context = out.get("context", {})
        metrics = trace.metrics

        # 1) Token checks (existing)
        ans_lower = answer.lower()
        for token in c.get("must_include", []):
            assert token.lower() in ans_lower, f"Case {c['id']} missing token: {token}"

        # 2) Governance checks (existing)
        if c.get("expect_redaction"):
            any_redacted = False

            q = out.get("query_sanitized") or ""
            if "[REDACTED]" in q or q == "[BLOCKED]":
                any_redacted = True

            for d in context.get("docs", []):
                if "[REDACTED]" in (d.get("snippet") or ""):
                    any_redacted = True

            if "[REDACTED]" in (context.get("context_text") or ""):
                any_redacted = True

            assert any_redacted, f"Case {c['id']} expected redaction but none found"

        # 3) Standard evaluation metrics (LLMOps-style)
        report = evaluate_case(
            answer=answer,
            sources=sources,
            context=context,
            metrics=metrics,
            must_include=c.get("must_include", []),
            forbidden=c.get("forbidden", []),
        )

        # Optional: enforce overall score threshold per case
        min_overall = float(c.get("min_overall", 0.5))
        assert report["overall"] >= min_overall, (
            f"Case {c['id']} overall score {report['overall']} below {min_overall}. "
            f"Scores: {report['scores']}"
        )

