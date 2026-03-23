"""Tests for profile and block loading."""

import pytest

from profiles import list_blocks, list_profiles, load_block, load_profile, resolve_blocks


class TestLoadBlock:
    def test_valid_block_has_required_keys(self):
        block = load_block("session_summary")
        assert isinstance(block, dict)
        for key in ("name", "display_name", "description", "prompt", "json_example"):
            assert key in block

    def test_nonexistent_block_raises(self):
        with pytest.raises(FileNotFoundError, match="Block 'nonexistent' not found"):
            load_block("nonexistent")


class TestLoadProfile:
    def test_valid_profile_has_required_keys(self):
        profile = load_profile("business")
        assert isinstance(profile, dict)
        for key in ("name", "description", "context", "blocks"):
            assert key in profile

    def test_nonexistent_profile_raises(self):
        with pytest.raises(FileNotFoundError, match="Profile 'nonexistent' not found"):
            load_profile("nonexistent")


class TestListFunctions:
    def test_list_blocks_returns_all(self):
        blocks = list_blocks()
        assert len(blocks) == 13
        assert "session_summary" in blocks
        assert "action_items" in blocks
        assert "decisions" in blocks

    def test_list_profiles_returns_all(self):
        assert list_profiles() == ["business", "therapy"]


class TestResolveBlocks:
    def test_with_profile(self):
        profile = load_profile("business")
        blocks = resolve_blocks(profile)
        assert len(blocks) == len(profile["blocks"])
        assert all(isinstance(b, dict) for b in blocks)

    def test_with_profile_and_add_blocks(self):
        profile = load_profile("business")
        base_count = len(profile["blocks"])
        blocks = resolve_blocks(profile, add_blocks=["emotional_patterns"])
        assert len(blocks) == base_count + 1

    def test_with_block_names(self):
        blocks = resolve_blocks(block_names=["session_summary", "decisions"])
        assert len(blocks) == 2
        assert blocks[0]["name"] == "session_summary"
        assert blocks[1]["name"] == "decisions"

    def test_no_args_returns_empty(self):
        assert resolve_blocks() == []
