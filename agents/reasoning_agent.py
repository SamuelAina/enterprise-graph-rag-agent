from typing import Tuple, List, Dict, Any
from llm.prompts import build_system_prompt, build_user_prompt


def generate_answer(query: str, context: Dict[str, Any], llm, trace) -> Tuple[str, List[Dict[str, Any]]]:
    sys_prompt = build_system_prompt()
    user_prompt = build_user_prompt(query=query, context=context)

    trace.event("llm_call_start")
    resp = llm.chat(system=sys_prompt, user=user_prompt, trace=trace)
    trace.event("llm_call_done")

    sources = context.get("docs", [])
    return resp, sources
