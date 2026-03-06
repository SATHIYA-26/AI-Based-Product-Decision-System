import os
from typing import List

# To keep dependencies light we try to import OpenAI only when needed.
try:
    import openai
except ImportError:
    openai = None


class LLMService:
    """Wrapper around a Large Language Model for summaries/labels.

    This service assumes an OpenAI-compatible API key is available in the
    environment variable `OPENAI_API_KEY`. If the library is not installed or
    the key is absent, the methods will raise an informative exception so the
    caller can fallback gracefully.
    """

    @staticmethod
    def _ensure_client():
        if openai is None:
            raise RuntimeError("`openai` package is not installed")
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        openai.api_key = key

    @staticmethod
    def generate_issue_summary(reviews: List[str]) -> str:
        """Produce a concise explanation of the underlying issue in the cluster."""
        LLMService._ensure_client()
        prompt = (
            "You are a helpful assistant that reads user feedback and writes a "
            "brief description of the common problem. Here are some examples:\n\n"
            + "\n".join(f"- {r}" for r in reviews[:10])
            + "\n\nProvide a one-sentence summary."
        )
        resp = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50,
            temperature=0.3,
        )
        return resp.choices[0].text.strip()

    @staticmethod
    def generate_label(reviews: List[str]) -> str:
        """Generate a short title appropriate for the cluster (3–5 words)."""
        LLMService._ensure_client()
        prompt = (
            "Read the following customer comments and suggest a short issue title "
            "(3-5 words) that summarizes them. Example comments:\n\n"
            + "\n".join(f"* {r}" for r in reviews[:10])
            + "\n\nTitle:"
        )
        resp = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=10,
            temperature=0.0,
        )
        label = resp.choices[0].text.strip()
        # remove any trailing punctuation
        return label.strip(".\n ")
