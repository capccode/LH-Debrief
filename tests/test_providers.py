"""Tests for LLM provider routing and error handling."""

from unittest.mock import patch

import pytest

from providers import DEFAULT_MODELS, _call_anthropic, _call_ollama, call_llm


class TestCallLlm:
    @patch("providers._call_anthropic", return_value="response")
    def test_routes_to_anthropic(self, mock_fn):
        result = call_llm("prompt", "anthropic", "model-x")
        mock_fn.assert_called_once_with("prompt", "model-x")
        assert result == "response"

    @patch("providers._call_ollama", return_value="response")
    def test_routes_to_ollama(self, mock_fn):
        result = call_llm("prompt", "ollama", "model-y")
        mock_fn.assert_called_once_with("prompt", "model-y")
        assert result == "response"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            call_llm("prompt", "unknown")


class TestCallAnthropic:
    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY not set"):
            _call_anthropic("prompt", "model")


class TestCallOllama:
    def test_missing_package_raises(self):
        with patch("providers.ollama_client", None):
            with pytest.raises(RuntimeError, match="ollama package not installed"):
                _call_ollama("prompt", "model")


class TestDefaultModels:
    def test_anthropic_default(self):
        assert DEFAULT_MODELS["anthropic"] == "claude-opus-4-5-20251101"

    def test_ollama_default(self):
        assert DEFAULT_MODELS["ollama"] == "qwen3:8b"
