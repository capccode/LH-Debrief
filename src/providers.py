"""LLM provider implementations for transcript analysis.

Supports Anthropic Claude (cloud) and Ollama (local) providers.
Provider selection is independent of analysis profile selection.
"""

import os

import anthropic
from rich.console import Console

try:
    import ollama as ollama_client
except ImportError:
    ollama_client = None  # type: ignore

console = Console()

# Default models per provider
DEFAULT_MODELS = {
    "anthropic": "claude-opus-4-5-20251101",
    "ollama": "qwen3:8b",
}


def call_llm(prompt: str, provider: str = "anthropic", model: str | None = None) -> str:
    """Route LLM call to the correct provider.

    Args:
        prompt: The full assembled prompt to send
        provider: "anthropic" or "ollama"
        model: Model name override (uses provider default if None)

    Returns:
        Raw response text from the LLM

    Raises:
        ValueError: If provider is unknown
        RuntimeError: If provider dependencies are missing or service unavailable
    """
    resolved_model = model or DEFAULT_MODELS.get(provider, "")

    if provider == "anthropic":
        return _call_anthropic(prompt, resolved_model)
    elif provider == "ollama":
        return _call_ollama(prompt, resolved_model)
    else:
        raise ValueError(f"Unknown provider: '{provider}'. Supported: anthropic, ollama")


def _call_anthropic(prompt: str, model: str) -> str:
    """Call Anthropic Claude API and return raw response text."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file or use --provider ollama for local analysis."
        )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text  # type: ignore


def _call_ollama(prompt: str, model: str) -> str:
    """Call local Ollama model and return raw response text.

    Uses Ollama's format="json" for constrained JSON output.
    """
    if ollama_client is None:
        raise RuntimeError("ollama package not installed. Run: uv add ollama")

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama_client.Client(host=host)

    try:
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
    except ollama_client.ResponseError as e:
        if "not found" in str(e).lower():
            raise RuntimeError(f"Model '{model}' not found. Run: ollama pull {model}") from e
        raise RuntimeError(f"Ollama error: {e}") from e
    except Exception as e:
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  brew install ollama\n"
                "  ollama serve"
            ) from e
        raise

    return response.message.content  # type: ignore
