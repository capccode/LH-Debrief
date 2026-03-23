"""Tests for entity extraction for knowledge graph preparation."""

import json
from unittest.mock import patch

from entities import _build_extraction_prompt, extract_entities, save_entities

MOCK_BLOCKS = [
    {
        "name": "session_summary",
        "display_name": "Session Summary",
        "description": "Summary of the session",
        "prompt": "Summarize the session",
        "json_example": '"session_summary": "..."',
    },
    {
        "name": "decisions",
        "display_name": "Decisions Made",
        "description": "Key decisions",
        "prompt": "List decisions",
        "json_example": '"decisions": ["..."]',
    },
]

MOCK_ANALYSIS = {
    "session_summary": "Discussion about Q3 planning with Mike and Sarah",
    "decisions": ["Selected AWS for hosting", "Postponed vendor review"],
}

MOCK_ENTITY_RESPONSE = json.dumps(
    {
        "entities": [
            {"text": "Mike", "type": "person", "confidence": 0.95},
            {"text": "AWS", "type": "technology", "confidence": 0.98},
            {"text": "Q3", "type": "temporal_reference", "confidence": 0.99},
        ],
        "relationships": [
            {
                "source": "Mike",
                "target": "Q3 planning",
                "type": "PARTICIPATED_IN",
                "context": "discussed planning",
            },
        ],
        "block_entities": {
            "session_summary": [
                {"text": "Mike", "type": "person"},
                {"text": "Q3", "type": "temporal_reference"},
            ],
            "decisions": [{"text": "AWS", "type": "technology"}],
        },
    }
)


class TestBuildExtractionPrompt:
    def test_prompt_contains_analysis(self):
        prompt = _build_extraction_prompt(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert "Q3 planning" in prompt
        assert "Selected AWS for hosting" in prompt

    def test_prompt_contains_block_names(self):
        prompt = _build_extraction_prompt(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert "session_summary" in prompt
        assert "decisions" in prompt

    def test_prompt_requests_json(self):
        prompt = _build_extraction_prompt(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert "Return ONLY the JSON" in prompt

    def test_prompt_mentions_entity_types(self):
        prompt = _build_extraction_prompt(MOCK_ANALYSIS, MOCK_BLOCKS)
        for entity_type in ("person", "organization", "technology", "decision", "project"):
            assert entity_type in prompt

    def test_prompt_mentions_relationship_types(self):
        prompt = _build_extraction_prompt(MOCK_ANALYSIS, MOCK_BLOCKS)
        for rel_type in ("OWNS", "DECIDED", "MENTIONS", "PARTICIPATED_IN", "REFERENCES"):
            assert rel_type in prompt


@patch("entities.console")
class TestExtractEntities:
    @patch("entities.call_llm", return_value=MOCK_ENTITY_RESPONSE)
    def test_returns_extraction_dict(self, _mock_llm, _mock_console):
        result = extract_entities(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert result is not None
        for key in (
            "extraction_model",
            "extraction_provider",
            "extraction_date",
            "entities",
            "relationships",
            "block_entities",
        ):
            assert key in result
        assert len(result["entities"]) == 3
        assert len(result["relationships"]) == 1

    @patch("entities.call_llm", return_value="this is not json at all!!!")
    def test_returns_none_on_invalid_json(self, _mock_llm, _mock_console):
        result = extract_entities(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert result is None

    @patch("entities.call_llm", side_effect=Exception("LLM connection failed"))
    def test_returns_none_on_exception(self, _mock_llm, _mock_console):
        result = extract_entities(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert result is None

    @patch("entities.call_llm", return_value=f"```json\n{MOCK_ENTITY_RESPONSE}\n```")
    def test_strips_code_fences(self, _mock_llm, _mock_console):
        result = extract_entities(MOCK_ANALYSIS, MOCK_BLOCKS)
        assert result is not None
        assert len(result["entities"]) == 3


@patch("entities.console")
class TestSaveEntities:
    def test_creates_entities_file(self, _mock_console, tmp_path):
        entities = {"entities": [], "relationships": []}
        save_entities(tmp_path, entities)
        assert (tmp_path / "entities.json").exists()

    def test_file_contains_valid_json(self, _mock_console, tmp_path):
        entities = {"entities": [{"text": "Mike", "type": "person"}], "relationships": []}
        save_entities(tmp_path, entities)
        with open(tmp_path / "entities.json") as f:
            loaded = json.load(f)
        assert loaded == entities
