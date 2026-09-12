import os
from functools import lru_cache

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_client() -> Anthropic:
    base_url = os.environ.get("AI_GATEWAY_BASE_URL", "").strip()
    token = os.environ.get("AI_GATEWAY_TOKEN", "").strip()
    if not base_url or not token:
        raise RuntimeError(
            "Set AI_GATEWAY_BASE_URL and AI_GATEWAY_TOKEN in a .env file "
            "(copy .env.example)."
        )
    return Anthropic(base_url=base_url, api_key=token)


def get_model_name() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4")


def extract_text(response) -> str:
    return next((b.text for b in response.content if b.type == "text"), "")


def complete(prompt: str, max_tokens: int = 700) -> dict:
    client = get_client()
    model = get_model_name()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    usage = getattr(response, "usage", None)
    return {
        "text": extract_text(response),
        "model": model,
        "input_tokens": getattr(usage, "input_tokens", 0) or 0,
        "output_tokens": getattr(usage, "output_tokens", 0) or 0,
    }
