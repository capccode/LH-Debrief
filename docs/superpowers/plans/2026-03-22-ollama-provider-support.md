# Ollama Provider Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to choose between Anthropic Claude and a local Ollama model (recommended: Qwen3 8B) for meeting transcript analysis, so a therapist can run the tool fully offline without API costs.

**Architecture:** Add a `--provider` CLI flag that routes analysis through either the existing Anthropic path or a new Ollama path. Both providers share the same prompt and output parsing. The `ollama` Python package handles Ollama communication with structured JSON output via its `format` parameter.

**Tech Stack:** `ollama` Python package, Qwen3 8B (default local model)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `pyproject.toml` | Modify | Add `ollama` dependency + pytest path config |
| `src/analyze.py` | Modify | Add provider abstraction, Ollama call function, route by provider |
| `src/diarize.py` | Modify | Add `--provider` and `--llm-model` CLI flags, update help text to be provider-agnostic, pass to analyze |
| `src/README.md` | Modify | Document new flags, Ollama setup instructions |
| `.env.example` | Modify | Add optional `OLLAMA_HOST` |
| `tests/test_analyze.py` | Create | Test provider routing, JSON parsing, prompt construction |

---

### Task 1: Add ollama dependency and pytest config

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `ollama` to dependencies and pytest pythonpath to pyproject.toml**

Add `"ollama"` to the `dependencies` list in `pyproject.toml`. Also add pytest config so tests can import from `src/`:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

- [ ] **Step 2: Install the new ollama dependency**

Run: `pip install ollama`
Expected: Successful installation

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add ollama dependency and pytest path config"
```

---

### Task 2: Refactor analyze.py — extract Anthropic call into helper

**Files:**
- Modify: `src/analyze.py:106-131` (the try/except block with Anthropic call)
- Create: `tests/test_analyze.py`

Extract the Anthropic API call into a private function so the main `analyze_transcript` can route between providers.

- [ ] **Step 1: Write the failing test for provider routing**

Create `tests/test_analyze.py`:

```python
"""Tests for analyze module provider routing and JSON parsing."""

import json
from unittest.mock import patch

import pytest


def _make_segments():
    """Minimal valid segments for testing."""
    return [
        {"start": 0.0, "end": 5.0, "speaker": "Speaker 0", "text": "Hello world"},
        {"start": 5.0, "end": 10.0, "speaker": "Speaker 1", "text": "Hi there"},
    ]


VALID_ANALYSIS_JSON = json.dumps({
    "executive_summary": "Test summary",
    "decisions": ["Decision 1"],
    "action_items": [{"owner": "Alice", "action": "Do thing", "due": "TBD"}],
    "key_concepts": [{"term": "Term", "explanation": "Meaning"}],
    "open_questions": ["Question?"],
    "follow_ups": ["Follow up"],
})


class TestProviderRouting:
    """Test that analyze_transcript routes to the correct provider."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("analyze._call_anthropic")
    def test_defaults_to_anthropic(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = VALID_ANALYSIS_JSON
        result = analyze_transcript(_make_segments(), "test")
        mock_call.assert_called_once()
        assert result is not None
        assert result["executive_summary"] == "Test summary"

    @patch("analyze._call_ollama")
    def test_routes_to_ollama(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = VALID_ANALYSIS_JSON
        result = analyze_transcript(
            _make_segments(), "test", provider="ollama"
        )
        mock_call.assert_called_once()
        assert result is not None
        assert result["executive_summary"] == "Test summary"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("analyze._call_anthropic")
    def test_model_override_passed_to_anthropic(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = VALID_ANALYSIS_JSON
        analyze_transcript(
            _make_segments(), "test", provider="anthropic", model="claude-sonnet-4-20250514"
        )
        args, kwargs = mock_call.call_args
        assert args[1] == "claude-sonnet-4-20250514"

    @patch("analyze._call_ollama")
    def test_model_override_passed_to_ollama(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = VALID_ANALYSIS_JSON
        analyze_transcript(
            _make_segments(), "test", provider="ollama", model="phi4:14b"
        )
        args, kwargs = mock_call.call_args
        assert args[1] == "phi4:14b"


class TestJsonParsing:
    """Test that response JSON is parsed correctly regardless of provider."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("analyze._call_anthropic")
    def test_parses_clean_json(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = VALID_ANALYSIS_JSON
        result = analyze_transcript(_make_segments(), "test")
        assert result["decisions"] == ["Decision 1"]

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("analyze._call_anthropic")
    def test_parses_json_wrapped_in_code_block(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = f"```json\n{VALID_ANALYSIS_JSON}\n```"
        result = analyze_transcript(_make_segments(), "test")
        assert result is not None
        assert result["executive_summary"] == "Test summary"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("analyze._call_anthropic")
    def test_returns_none_on_invalid_json(self, mock_call):
        from analyze import analyze_transcript

        mock_call.return_value = "not json at all"
        result = analyze_transcript(_make_segments(), "test")
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python -m pytest tests/test_analyze.py -v`
Expected: FAIL — `_call_anthropic` and `_call_ollama` don't exist yet

- [ ] **Step 3: Extract `_call_anthropic()` from analyze_transcript**

In `src/analyze.py`, add this function before `analyze_transcript`:

```python
def _call_anthropic(prompt: str, model: str) -> str:
    """Call Anthropic Claude API and return raw response text."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text  # type: ignore
```

- [ ] **Step 4: Refactor `analyze_transcript` to accept provider/model params and route**

Replace the current `analyze_transcript` function signature and body. New signature:

```python
def analyze_transcript(
    segments: list[dict],
    audio_name: str,
    domain_context: str | None = None,
    provider: str = "anthropic",
    model: str | None = None,
) -> MeetingAnalysis | None:
```

New body (replacing everything from the api_key check through the try/except):

```python
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[yellow]Warning: ANTHROPIC_API_KEY not set, skipping analysis[/yellow]")
            return None

    console.print(f"[cyan]Analyzing transcript with {provider}...[/cyan]")

    # Build transcript text
    transcript_text = ""
    for seg in segments:
        text = seg.get("text", "")
        if text:
            transcript_text += f"[{seg['start']:.1f}s] {seg['speaker']}: {text}\n"

    if not transcript_text.strip():
        console.print("[yellow]Warning: No transcript text to analyze[/yellow]")
        return None

    # Domain context for better understanding
    domain_prompt = ""
    if domain_context:
        domain_prompt = f"\n<domain_context>\n{domain_context}\n</domain_context>\n"

    prompt = f"""Analyze this meeting transcript and extract structured information.

{domain_prompt}
<transcript>
{transcript_text}
</transcript>

Provide your analysis as JSON with this exact structure:
{{
    "executive_summary": "2-3 sentence summary of the meeting's main points and outcomes",
    "decisions": ["Decision 1 that was made", "Decision 2 that was made"],
    "action_items": [
        {{"owner": "Person name or role", "action": "What they need to do", "due": "Due date if mentioned, otherwise 'TBD'"}}
    ],
    "key_concepts": [
        {{"term": "Technical term or acronym", "explanation": "What it means in context"}}
    ],
    "open_questions": ["Question that was raised but not answered"],
    "follow_ups": ["Topic that needs follow-up discussion"]
}}

Focus on:
- Being precise and accurate - only include what was actually discussed
- Capturing technical terms and acronyms specific to this domain
- Identifying action items with clear owners when possible
- Noting decisions vs. things still being discussed

Return ONLY the JSON, no other text."""

    try:
        if provider == "ollama":
            resolved_model = model or "qwen3:8b"
            response_text = _call_ollama(prompt, resolved_model)
        else:
            resolved_model = model or "claude-opus-4-5-20251101"
            response_text = _call_anthropic(prompt, resolved_model)

        # Clean up response if needed (remove markdown code blocks)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        analysis = json.loads(response_text.strip())
        console.print("[green]Analysis complete[/green]")
        return cast(MeetingAnalysis, analysis)

    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse LLM response: {e}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]LLM error ({provider}): {e}[/red]")
        return None
```

- [ ] **Step 5: Run tests to verify refactored Anthropic path passes**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python -m pytest tests/test_analyze.py::TestProviderRouting::test_defaults_to_anthropic tests/test_analyze.py::TestJsonParsing -v`
Expected: These tests PASS (Ollama tests still fail)

- [ ] **Step 6: Commit**

```bash
git add src/analyze.py tests/test_analyze.py
git commit -m "refactor: extract _call_anthropic, add provider routing to analyze_transcript"
```

---

### Task 3: Add Ollama provider

**Files:**
- Modify: `src/analyze.py` (add `_call_ollama` function and `import ollama`)

- [ ] **Step 1: Add `_call_ollama()` function to analyze.py**

Add import at top of file (alongside existing imports):

```python
try:
    import ollama as ollama_client
except ImportError:
    ollama_client = None  # type: ignore
```

Add function after `_call_anthropic`:

```python
def _call_ollama(prompt: str, model: str) -> str:
    """Call local Ollama model and return raw response text."""
    if ollama_client is None:
        raise RuntimeError("ollama package not installed. Run: pip install ollama")

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama_client.Client(host=host)
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    return response.message.content  # type: ignore
```

Note: Ollama's `format="json"` uses constrained decoding to guarantee valid JSON output, so the markdown code-block stripping in `analyze_transcript` is unnecessary for this path but harmless.

- [ ] **Step 2: Run all tests**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python -m pytest tests/test_analyze.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/analyze.py
git commit -m "feat: add Ollama provider for local LLM analysis"
```

---

### Task 4: Add CLI flags to diarize.py

**Files:**
- Modify: `src/diarize.py:309-342` (argparse section — add before `args = parser.parse_args()` on line 343)
- Modify: `src/diarize.py` (where `analyze_transcript` is called)
- Modify: `src/diarize.py:323-324` (update `--no-analyze` help text)
- Modify: `src/diarize.py:305` (update argparse description)

- [ ] **Step 1: Find the analyze_transcript call site in diarize.py**

Run: `grep -n "analyze_transcript" src/diarize.py`

- [ ] **Step 2: Update argparse description and `--no-analyze` help text to be provider-agnostic**

Change the argparse description (line 305) from any Claude-specific wording to generic:
```python
    parser = argparse.ArgumentParser(description="Diarize, transcribe, and analyze audio")
```

Change `--no-analyze` help text (line 324) from `"Skip Claude AI analysis"` to:
```python
        help="Skip AI analysis (default: analyze is ON)",
```

- [ ] **Step 3: Add `--provider` and `--llm-model` arguments**

Add before `args = parser.parse_args()` (line 343):

```python
    parser.add_argument(
        "--provider",
        choices=["anthropic", "ollama"],
        default="anthropic",
        help="LLM provider for analysis (default: anthropic)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="Override LLM model name (default: claude-opus-4-5-20251101 for anthropic, qwen3:8b for ollama)",
    )
```

- [ ] **Step 4: Pass provider and model to analyze_transcript call**

At the call site found in Step 1, update the `analyze_transcript` call to pass the new args:

```python
    analysis = analyze_transcript(
        segments,
        audio_name,
        domain_context=args.context,
        provider=args.provider,
        model=args.llm_model,
    )
```

- [ ] **Step 5: Verify CLI help shows new flags**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python src/diarize.py --help`
Expected: Output includes `--provider` and `--llm-model` flags, `--no-analyze` says "Skip AI analysis"

- [ ] **Step 6: Commit**

```bash
git add src/diarize.py
git commit -m "feat: add --provider and --llm-model CLI flags"
```

---

### Task 5: Update documentation

**Files:**
- Modify: `src/README.md`
- Modify: `.env.example`

- [ ] **Step 1: Add OLLAMA_HOST to .env.example**

Add to `.env.example`:

```
# Optional: Ollama host (defaults to http://localhost:11434)
# OLLAMA_HOST=http://localhost:11434
```

- [ ] **Step 2: Update README options table**

Add two rows to the Options table in `src/README.md`:

```markdown
| `--provider` | LLM provider: `anthropic` or `ollama` (default: anthropic) |
| `--llm-model` | Override LLM model (e.g., `phi4:14b`, `claude-sonnet-4-20250514`) |
```

- [ ] **Step 3: Add Ollama setup section to README**

Add after the Requirements section:

```markdown
## Local Mode (Ollama)

To run analysis without an API key, use a local model via [Ollama](https://ollama.com):

1. Install Ollama: `brew install ollama`
2. Pull the recommended model: `ollama pull qwen3:8b`
3. Run with `--provider ollama`:

```bash
python src/diarize.py meeting.mp4 -o output/ -c "therapy session" --provider ollama
```

**Recommended models for 16GB RAM:**
| Model | Size | Context | Notes |
|-------|------|---------|-------|
| `qwen3:8b` | ~5GB | 32K | Best balance of quality and speed |
| `phi4:14b` | ~8.5GB | 16K | Higher quality, tighter RAM fit |
```

- [ ] **Step 4: Commit**

```bash
git add src/README.md .env.example
git commit -m "docs: add Ollama setup instructions and new CLI flags"
```

---

### Task 6: End-to-end smoke test

- [ ] **Step 1: Verify no import errors**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python -c "from analyze import analyze_transcript, _call_anthropic, _call_ollama; print('imports OK')"`
Expected: `imports OK`

- [ ] **Step 2: Verify CLI help is correct**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python src/diarize.py --help`
Expected: Shows all flags including `--provider` and `--llm-model`

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/loewcx/Documents/root/30-39_Software/LH-Debrief && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit (only if there are changes)**

```bash
git add tests/ src/
git commit -m "feat: complete Ollama provider support for offline meeting analysis"
```
