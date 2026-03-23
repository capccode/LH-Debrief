"""Tests for prompt assembly and transcript analysis."""

from unittest.mock import patch

from analyze import analyze_transcript, assemble_prompt

MOCK_BLOCK = {
    "name": "test_block",
    "display_name": "Test Block",
    "description": "A test dimension",
    "prompt": "Extract test information.",
    "json_example": '"test_block": ["item1", "item2"]',
}

MOCK_SEGMENTS = [
    {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00", "text": "Hello there"},
    {"start": 5.0, "end": 10.0, "speaker": "SPEAKER_01", "text": "Hi back"},
]


class TestAssemblePrompt:
    def test_includes_transcript(self):
        prompt = assemble_prompt(MOCK_SEGMENTS, [MOCK_BLOCK])
        assert "<transcript>" in prompt
        assert "SPEAKER_00: Hello there" in prompt
        assert "SPEAKER_01: Hi back" in prompt

    def test_includes_dimensions_and_json_example(self):
        prompt = assemble_prompt(MOCK_SEGMENTS, [MOCK_BLOCK])
        assert "1. Test Block" in prompt
        assert "Extract test information." in prompt
        assert '"test_block"' in prompt

    def test_with_context_includes_context_section(self):
        prompt = assemble_prompt(MOCK_SEGMENTS, [MOCK_BLOCK], context="Team standup")
        assert "<context>" in prompt
        assert "Team standup" in prompt

    def test_without_context_omits_context_section(self):
        prompt = assemble_prompt(MOCK_SEGMENTS, [MOCK_BLOCK])
        assert "<context>" not in prompt


class TestAnalyzeTranscript:
    @patch("analyze.call_llm")
    def test_returns_parsed_dict(self, mock_llm):
        mock_llm.return_value = '{"test_block": ["a", "b"]}'
        result = analyze_transcript(MOCK_SEGMENTS, [MOCK_BLOCK])
        assert result == {"test_block": ["a", "b"]}

    @patch("analyze.call_llm")
    def test_strips_code_fences(self, mock_llm):
        mock_llm.return_value = '```json\n{"key": "value"}\n```'
        result = analyze_transcript(MOCK_SEGMENTS, [MOCK_BLOCK])
        assert result == {"key": "value"}

    @patch("analyze.call_llm")
    def test_returns_none_on_invalid_json(self, mock_llm):
        mock_llm.return_value = "not valid json {{"
        result = analyze_transcript(MOCK_SEGMENTS, [MOCK_BLOCK])
        assert result is None

    def test_returns_none_when_no_text(self):
        empty_segments = [
            {"start": 0.0, "end": 5.0, "speaker": "A"},
            {"start": 5.0, "end": 10.0, "speaker": "B", "text": ""},
        ]
        result = analyze_transcript(empty_segments, [MOCK_BLOCK])
        assert result is None
