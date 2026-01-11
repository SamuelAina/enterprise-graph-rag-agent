from __future__ import annotations

import os
import json
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import pandas as pd
import requests
import yaml


# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="Enterprise Graph-RAG Agent Demo",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Enterprise Graph-RAG Agent Platform")
st.caption("Graph-RAG + Hybrid retrieval + Governance + LLMOps (Streamlit showcase)")


# ----------------------------
# Helpers
# ----------------------------
def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name, str(default)).lower()
    return v in ("1", "true", "yes", "y")


def _set_env_from_ui(key: str, value: Any):
    # Keep simple: store in os.environ for local-mode execution
    os.environ[key] = str(value)


def _build_local_executor_cached():
    # Cached so reruns are fast; we rebuild when user presses "Rebuild executor"
    from evaluation.runner import build_executor
    return build_executor()


def _call_api(base_url: str, api_key: str, query: str) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    r = requests.post(
        f"{base_url.rstrip('/')}/ask",
        headers=headers,
        json={"query": query},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def _run_local(executor, query: str) -> Dict[str, Any]:
    from api.telemetry import Trace
    trace = Trace()
    out = executor.run(query=query, trace=trace)
    trace.finish()

    # Streamlit-friendly combined payload
    return {
        "answer": out.get("answer", ""),
        "route": out.get("route", ""),
        "sources": out.get("sources", []),
        "context": out.get("context", {}),
        "query_sanitized": out.get("query_sanitized", ""),
        "metrics": trace.metrics,
        "events": trace.events,
        "trace_id": trace.trace_id,
    }


def _sources_df(sources: List[Dict[str, Any]]) -> pd.DataFrame:
    if not sources:
        return pd.DataFrame(columns=["doc_id", "title", "score", "metadata", "snippet"])
    rows = []
    for s in sources:
        rows.append({
            "doc_id": s.get("doc_id"),
            "title": s.get("title"),
            "score": s.get("score"),
            "metadata": s.get("metadata", {}),
            "snippet": s.get("snippet", ""),
        })
    return pd.DataFrame(rows)


def _docs_df_from_context(ctx: Dict[str, Any]) -> pd.DataFrame:
    docs = ctx.get("docs", []) if isinstance(ctx, dict) else []
    if not docs:
        return pd.DataFrame(columns=["doc_id", "title", "score", "final_score", "rerank_score", "metadata", "snippet"])
    rows = []
    for d in docs:
        rows.append({
            "doc_id": d.get("doc_id"),
            "title": d.get("title"),
            "score": d.get("score"),
            "final_score": d.get("final_score"),
            "rerank_score": d.get("rerank_score"),
            "metadata": d.get("metadata", {}),
            "snippet": d.get("snippet", ""),
        })
    return pd.DataFrame(rows)


def _render_trace_events(events: List[Dict[str, Any]]):
    if not events:
        st.info("No trace events captured.")
        return
    df = pd.DataFrame(events)
    # Ensure ordering by ts if present
    if "ts" in df.columns:
        df = df.sort_values("ts")
    st.dataframe(df, use_container_width=True)


def _load_cases_from_text(text: str) -> List[Dict[str, Any]]:
    data = yaml.safe_load(text) if text.strip() else []
    return data or []


# ----------------------------
# Sidebar: Mode + Controls
# ----------------------------
with st.sidebar:
    st.header("⚙️ Demo Controls")

    mode = st.radio(
        "Run mode",
        ["Local (recommended)", "API (FastAPI endpoint)"],
        help="Local mode imports the executor directly and shows full trace/events/context. API mode calls /ask.",
    )

    st.subheader("Retrieval / Rerank knobs")

    top_k = st.slider("TOP_K_DOCS", 1, 12, int(os.getenv("TOP_K_DOCS", "6")))
    graph_hops = st.slider("GRAPH_HOPS", 0, 4, int(os.getenv("GRAPH_HOPS", "2")))
    max_ctx = st.slider("MAX_CONTEXT_CHARS", 2000, 20000, int(os.getenv("MAX_CONTEXT_CHARS", "8000")), step=500)
    per_doc = st.slider("PER_DOC_SNIPPET_CHARS", 80, 600, int(os.getenv("PER_DOC_SNIPPET_CHARS", "280")), step=20)

    rerank_enabled = st.toggle("RERANK_ENABLED", value=_env_bool("RERANK_ENABLED", True))
    include_scores = st.toggle("INCLUDE_SCORES_IN_CONTEXT", value=_env_bool("INCLUDE_SCORES_IN_CONTEXT", True))

    st.subheader("LLM provider")
    llm_provider = st.selectbox(
        "LLM_PROVIDER",
        ["mock", "azure_openai", "openai_compatible"],
        index=["mock", "azure_openai", "openai_compatible"].index(os.getenv("LLM_PROVIDER", "mock")),
    )

    st.subheader("Security / Auth (API mode)")
    api_base = st.text_input("API_BASE_URL", value=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    api_key = st.text_input("X-API-Key", value=os.getenv("API_KEY", "change-me"), type="password")

    apply_env = st.button("Apply settings to environment")
    if apply_env:
        _set_env_from_ui("TOP_K_DOCS", top_k)
        _set_env_from_ui("GRAPH_HOPS", graph_hops)
        _set_env_from_ui("MAX_CONTEXT_CHARS", max_ctx)
        _set_env_from_ui("PER_DOC_SNIPPET_CHARS", per_doc)
        _set_env_from_ui("RERANK_ENABLED", rerank_enabled)
        _set_env_from_ui("INCLUDE_SCORES_IN_CONTEXT", include_scores)
        _set_env_from_ui("LLM_PROVIDER", llm_provider)
        _set_env_from_ui("API_BASE_URL", api_base)
        # NOTE: do not force API_KEY into env automatically in case you prefer .env
        st.success("Environment updated for this Streamlit session.")

    st.divider()
    if mode == "Local (recommended)":
        st.caption("Local mode caches the executor. If you change env knobs, click rebuild.")
        rebuild = st.button("🔁 Rebuild local executor")
        if rebuild:
            # Clearing Streamlit cache for local executor build
            st.cache_resource.clear()
            st.success("Executor cache cleared. Next run rebuilds it.")


# Cache local executor build
@st.cache_resource
def get_executor():
    return _build_local_executor_cached()


# ----------------------------
# Main UI: Ask + Results
# ----------------------------
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("💬 Ask a question")
    default_q = "OrderService is slow. What dependencies should I check first?"
    query = st.text_area("Query", value=default_q, height=110)

    demo_col_a, demo_col_b, demo_col_c = st.columns(3)
    with demo_col_a:
        if st.button("🧪 Demo: Dependency (Graph-RAG)"):
            query = "What services are upstream and downstream of InventoryService?"
            st.rerun()
    with demo_col_b:
        if st.button("📘 Demo: Policy (Doc-RAG)"):
            query = "What is the data access policy for ProductDB?"
            st.rerun()
    with demo_col_c:
        if st.button("🛡️ Demo: Redaction"):
            query = "OrderService failing. api_key=sk_live_123 Authorization: Bearer abc.def.ghi"
            st.rerun()

    run_btn = st.button("▶️ Run", type="primary")

with col2:
    st.subheader("🧭 What this demo shows")
    st.markdown(
        """
- **Router agent** selects Graph-RAG / Doc-RAG / Hybrid  
- **Hybrid retrieval** combines dependency context + docs  
- **Reranker** improves doc ordering (offline deterministic)  
- **Guardrails** redact secrets/PII in query + context  
- **Trace** captures decisions + latency metrics (LLMOps)  
        """
    )


def render_result(payload: Dict[str, Any]):
    # Headline summary
    route = payload.get("route", "")
    trace_id = payload.get("trace_id", payload.get("trace_id", ""))
    metrics = payload.get("metrics", {}) or {}

    top = st.container()
    with top:
        cA, cB, cC = st.columns([1, 1, 1])
        cA.metric("Route", route if route else "—")
        cB.metric("Latency (ms)", metrics.get("latency_ms", "—"))
        cC.metric("Redactions", metrics.get("redactions", "—"))

    st.subheader("✅ Answer")
    st.write(payload.get("answer", ""))

    tabs = st.tabs(["Sources", "Governance (sanitized)", "Trace", "Raw JSON"])

    # Sources
    with tabs[0]:
        st.markdown("**Sources returned to user** (safe subset).")
        df = _sources_df(payload.get("sources", []))
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            with st.expander("Show source snippets"):
                for _, row in df.iterrows():
                    st.markdown(f"**{row['doc_id']} — {row['title']}**")
                    st.code(row["snippet"])

    # Governance
    with tabs[1]:
        st.markdown("**Sanitized query & sanitized retrieval context** (for governance inspection).")
        st.markdown("**Query (sanitized)**")
        st.code(payload.get("query_sanitized", ""), language="text")

        ctx = payload.get("context", {}) or {}
        docs_df = _docs_df_from_context(ctx)
        st.markdown("**Retrieved docs (post-guardrails & post-rerank)**")
        st.dataframe(docs_df, use_container_width=True)

        if "context_text" in ctx:
            st.markdown("**Context text (post-guardrails)**")
            st.code(ctx.get("context_text", ""), language="text")

    # Trace
    with tabs[2]:
        st.markdown("**Trace metrics**")
        st.json(metrics)
        st.markdown("**Trace events**")
        events = payload.get("events", [])
        _render_trace_events(events)

    # Raw JSON
    with tabs[3]:
        st.code(_safe_json(payload), language="json")


if run_btn:
    try:
        if mode == "API (FastAPI endpoint)":
            t0 = time.time()
            resp = _call_api(api_base, api_key, query)
            # API returns AskResponse: answer, trace_id, route, sources, metrics
            # It does NOT include full context/events unless you add a debug endpoint.
            payload = {
                **resp,
                "trace_id": resp.get("trace_id"),
            }
            # Still show response, but governance/trace tabs are limited in API mode
            st.info("API mode shows API response only. For full governance/trace/events, use Local mode.")
            render_result(payload)

        else:
            ex = get_executor()
            payload = _run_local(ex, query)
            render_result(payload)

    except requests.HTTPError as e:
        st.error(f"HTTP error: {e}")
        if hasattr(e, "response") and e.response is not None:
            st.code(e.response.text)
    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)


st.divider()


# ----------------------------
# Evaluation Runner UI
# ----------------------------
st.subheader("🧪 Evaluation Runner (LLMOps)")

left, right = st.columns([1.2, 1])

with left:
    st.markdown("Run YAML test cases (like `evaluation/test_cases.yaml`) and see pass/fail + scores.")
    # Load existing file if present
    default_yaml = ""
    try:
        with open("evaluation/test_cases.yaml", "r", encoding="utf-8") as f:
            default_yaml = f.read()
    except Exception:
        default_yaml = "- id: demo-1\n  query: \"OrderService is slow. What dependencies should I check first?\"\n  must_include:\n    - \"InventoryService\"\n"

    cases_text = st.text_area("Test cases YAML", value=default_yaml, height=220)

    run_eval = st.button("▶️ Run evaluation", key="run_eval")

with right:
    st.markdown("**Evaluation output**")
    if run_eval:
        try:
            cases = _load_cases_from_text(cases_text)
            if not cases:
                st.warning("No cases found in YAML.")
            else:
                if mode == "API (FastAPI endpoint)":
                    st.warning("Evaluation runner requires Local mode for full trace/context. Switch to Local mode.")
                else:
                    ex = get_executor()
                    from evaluation.metrics import evaluate_case
                    from api.telemetry import Trace

                    rows = []
                    for c in cases:
                        trace = Trace()
                        out = ex.run(query=c["query"], trace=trace)
                        trace.finish()

                        report = evaluate_case(
                            answer=out["answer"],
                            sources=out.get("sources", []),
                            context=out.get("context", {}),
                            metrics=trace.metrics,
                            must_include=c.get("must_include", []),
                            forbidden=c.get("forbidden", []),
                        )

                        # Optional governance expectation
                        expect_redaction = bool(c.get("expect_redaction", False))
                        ctx = out.get("context", {}) or {}
                        any_redacted = False
                        q_s = out.get("query_sanitized") or ""
                        if "[REDACTED]" in q_s or q_s == "[BLOCKED]":
                            any_redacted = True
                        if "[REDACTED]" in (ctx.get("context_text") or ""):
                            any_redacted = True
                        for d in ctx.get("docs", []):
                            if "[REDACTED]" in (d.get("snippet") or ""):
                                any_redacted = True

                        gov_ok = (any_redacted if expect_redaction else True)

                        min_overall = float(c.get("min_overall", 0.5))
                        passed = (report["overall"] >= min_overall) and gov_ok

                        rows.append({
                            "id": c.get("id"),
                            "route": out.get("route"),
                            "overall": round(report["overall"], 3),
                            "min_overall": min_overall,
                            "gov_expected": expect_redaction,
                            "gov_ok": gov_ok,
                            "passed": passed,
                            "latency_ms": trace.metrics.get("latency_ms"),
                            "redactions": trace.metrics.get("redactions"),
                        })

                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)

                    fails = df[df["passed"] == False]
                    if not fails.empty:
                        st.error(f"{len(fails)} case(s) failed. Click a case in the table and re-run locally for details.")
                    else:
                        st.success("All cases passed ✅")

        except Exception as e:
            st.error(f"Evaluation error: {e}")
            st.exception(e)


st.caption("Tip: For the richest demo (router + rerank + guardrails + trace events), run in Local mode.")
