import os
import time
import httpx
import re

class BaseLLMClient:
    def chat(self, system: str, user: str, trace) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    Deterministic offline "LLM":
    - Extracts relevant lines from the prompt context
    - Ensures evaluation tokens can be asserted in CI
    """
    def chat(self, system: str, user: str, trace) -> str:
        # Pull out the CONTEXT section from the user prompt
        ctx_match = re.search(r"CONTEXT:\n(.*?)\n\nTASK:", user, flags=re.DOTALL)
        context = ctx_match.group(1) if ctx_match else ""

        # Collect document lines and graph lines deterministically
        doc_lines = []
        graph_lines = []

        for line in context.splitlines():
            line = line.strip()
            if line.startswith("- [DOC-"):
                doc_lines.append(line)
            elif line.startswith("- ") and "type=" in line and "owner=" in line:
                graph_lines.append(line)

        # Pick top lines to include (deterministic)
        picked_docs = doc_lines[:3]
        picked_graph = graph_lines[:5]

        # Build a concise answer that quotes key context terms
        parts = []
        parts.append("MOCK RESPONSE (offline mode). Using retrieved context:")
        if picked_graph:
            parts.append("\nDependency view:")
            parts.extend(picked_graph)

        if picked_docs:
            parts.append("\nKey retrieved guidance:")
            # Include snippets after the title so phrases like "least privilege" appear
            for d in picked_docs:
                # format: - [DOC-003] Title: snippet...
                parts.append(d)

        # Add a generic action section
        parts.append("\nAction plan:")
        parts.append("- Verify upstream/downstream dependencies and error rates.")
        parts.append("- Follow the most relevant runbook/policy from retrieved docs.")
        parts.append("- Capture trace_id and latency for observability.")

        return "\n".join(parts) + "\n"


class AzureOpenAIClient(BaseLLMClient):
    """
    Azure OpenAI Chat Completions (OpenAI-compatible shape but with deployment in URL).
    Uses environment variables:
      LLM_BASE_URL, LLM_API_KEY, LLM_DEPLOYMENT, LLM_API_VERSION
    """

    def __init__(self):
        self.base_url = os.environ["LLM_BASE_URL"].rstrip("/")
        self.api_key = os.environ["LLM_API_KEY"]
        self.deployment = os.environ["LLM_DEPLOYMENT"]
        self.api_version = os.getenv("LLM_API_VERSION", "2024-02-15-preview")

    def chat(self, system: str, user: str, trace) -> str:
        url = f"{self.base_url}/openai/deployments/{self.deployment}/chat/completions"
        params = {"api-version": self.api_version}
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }

        t0 = time.time()
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, params=params, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        trace.set_metric("llm_latency_ms", int((time.time() - t0) * 1000))

        return data["choices"][0]["message"]["content"]


class OpenAICompatibleClient(BaseLLMClient):
    """
    OpenAI-compatible chat completions endpoint:
      POST {LLM_BASE_URL}/chat/completions
    Env:
      LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
    """

    def __init__(self):
        self.base_url = os.environ["LLM_BASE_URL"].rstrip("/")
        self.api_key = os.environ["LLM_API_KEY"]
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def chat(self, system: str, user: str, trace) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }

        t0 = time.time()
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        trace.set_metric("llm_latency_ms", int((time.time() - t0) * 1000))

        return data["choices"][0]["message"]["content"]


def build_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    print(f"Building LLM client for provider: {provider}")
    if provider == "azure_openai":
        # if env not set, fall back to mock to keep the repo runnable
        try:
            return AzureOpenAIClient()
        except KeyError:
            return MockLLMClient()
    if provider == "openai_compatible":
        try:
            return OpenAICompatibleClient()
        except KeyError:
            return MockLLMClient()
    return MockLLMClient()
