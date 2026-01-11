def build_system_prompt() -> str:
    return (
        "You are a senior enterprise GenAI assistant.\n"
        "Rules:\n"
        "1) Be accurate and operationally useful.\n"
        "2) If info is missing, state assumptions and propose safe next checks.\n"
        "3) Use retrieved context; do not invent systems or policies.\n"
        "4) Provide a short, actionable answer with bullets.\n"
    )


def build_user_prompt(query: str, context: dict) -> str:
    ctx = context.get("context_text", "")
    return (
        f"USER QUESTION:\n{query}\n\n"
        f"CONTEXT:\n{ctx}\n\n"
        "TASK:\n"
        "Answer using the context. Include a brief dependency-aware troubleshooting path if applicable.\n"
        "Return a concise, actionable response.\n"
    )
