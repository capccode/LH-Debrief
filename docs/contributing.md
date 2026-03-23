# Contributing

## Review Criteria

All contributions to LH-Debrief are evaluated based on the following criteria:

**Completeness**

Your contribution should be production-ready and complete. This includes:

- Comprehensive test cases with synthetic data
- Complete documentation following our style guide
- Proper integration with existing modules
- Working examples demonstrating usage
- Clear docstrings for all public methods and classes

**Relevance to the Project**

LH-Debrief is an audio analysis and intelligence extraction tool. Contributions should enhance its utility for the broader community. Consider:

- Does this add meaningful functionality that others will use?
- Does it integrate well with existing components (blocks, profiles, providers)?
- Does it follow established patterns and conventions?
- Will it create confusion or maintenance burden?

The goal is to grow LH-Debrief thoughtfully, not just add features for the sake of features.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Git and a GitHub account
- FFmpeg: `brew install ffmpeg` (or equivalent)

### Setting Up Your Development Environment

1. Fork the LH-Debrief repository on GitHub

2. Clone your forked repository:
    ```bash
    git clone https://github.com/your_username/LH-Debrief.git
    cd LH-Debrief
    ```

3. Install dependencies:
    ```bash
    pip install -e ".[dev]"
    ```

4. Implement your code with proper test cases

5. Push changes to your forked repository

6. Create a pull request to the main LH-Debrief repository:
    - Target the `main` branch
    - Enable edits by maintainers
    - Rebase with the remote `main` branch before creating the PR

---

## Implementation Requirements

### Code File Headers

For new contributors, include the following at the top of new code files:

```python
"""
Module description.

Author: your-github-username
Reference: Paper/article title (if applicable)
Link: https://link-to-reference (if applicable)
Description: Brief description of what this implements
"""
```

### Code Style and Documentation

**General Guidelines:**

- Use object-oriented programming with well-defined and typed functions
- Follow `snake_case` naming for variables and functions (e.g., `this_variable`)
- Use `PascalCase` for class names (e.g., `ThisClass`)
- Follow PEP8 style with 100 character line length (per project `ruff` config)
- Use Google style for docstrings
- Type hints on all function signatures

**Function Documentation Requirements:**

Each function must document:

- Input arguments: variable types and descriptions
- Output arguments: variable types and descriptions
- High-level description of what the function does
- Example use case or where it will be called

**Example:**

```python
def load_block(name: str, blocks_dir: Path | None = None) -> dict:
    """Load a block definition from its TOML file.

    Reads the block TOML from the blocks directory and validates
    that all required fields are present. Called by `resolve_blocks()`
    during profile assembly.

    Args:
        name: Block identifier matching the TOML filename (e.g., "action_items").
        blocks_dir: Override path to blocks directory. Defaults to src/blocks/.

    Returns:
        Dict with keys: name, display_name, description, prompt, json_example.

    Raises:
        FileNotFoundError: If no TOML file exists for the given block name.
        ValueError: If required fields are missing from the TOML file.
    """
```

---

## Contribution Types

### Contributing a New Block

Blocks are the simplest contribution — no Python code required.

**Files:**

| File | Purpose |
|------|---------|
| `src/blocks/<name>.toml` | Block definition |
| `tests/test_blocks.py` | Add test case for your block |
| `docs/blocks.md` | Update the blocks table |

**Block file format:**

```toml
# src/blocks/methodology_notes.toml
name = "methodology_notes"
display_name = "Methodology Notes"
description = "Research methodology discussed or proposed"

prompt = """
Identify any research methodology discussed, proposed, or critiqued.
Note the approach, its strengths, and any concerns raised.
"""

json_example = """
"methodology_notes": [
    {"approach": "Method name", "details": "How it was discussed", "concerns": "Any issues raised"}
]"""
```

**Requirements:**

- `name` must match the filename (without `.toml`)
- `display_name` is the human-readable heading in briefings
- `prompt` should be clear enough that any LLM can follow it
- `json_example` is a literal JSON snippet showing expected output structure
- Add a test that verifies your block loads and has all required fields

### Contributing a New Profile

**Files:**

| File | Purpose |
|------|---------|
| `src/profiles/<name>.toml` | Profile definition |
| `tests/test_profiles.py` | Add test case for your profile |
| `docs/profiles.md` | Update the profiles table |

**Profile file format:**

```toml
# src/profiles/research.toml
name = "Research Discussion"
description = "Academic research meeting analysis"

context = """
Analyze as an academic research discussion. Focus on methodology,
findings, literature references, and open research questions.
"""

blocks = [
    "session_summary",
    "key_concepts",
    "action_items",
    "open_questions",
    "methodology_notes",
]
```

**Requirements:**

- All referenced blocks must exist in `src/blocks/`
- `context` should clearly frame the analysis lens
- Add a test that verifies all referenced blocks resolve correctly

### Contributing a New Provider

Adding a new LLM provider (e.g., OpenAI, local llama.cpp) requires Python code.

**Files:**

| File | Purpose |
|------|---------|
| `src/providers.py` | Add provider function |
| `tests/test_providers.py` | Add test cases with mocked API calls |
| `docs/providers.md` | Document setup instructions |
| `pyproject.toml` | Add dependency (if needed) |

**Requirements:**

- Provider function signature: `_call_<name>(prompt: str, model: str) -> str`
- Must return raw response text (JSON string)
- Use lazy imports (`try/except ImportError`) so the dependency is optional
- Support a host/endpoint override via environment variable
- Include clear error messages for common failures (not running, model not found, auth issues)

### Contributing a Feature or Bug Fix

For changes to core Python modules (`diarize.py`, `analyze.py`, `profiles.py`, `render.py`, etc.):

**Files:**

| File | Purpose |
|------|---------|
| `src/<module>.py` | Implementation |
| `tests/test_<module>.py` | Test cases |
| `docs/*.md` | Update relevant docs |

---

## Test Requirements

Every contribution must include tests. Tests must be fast, deterministic, and self-contained.

### Guidelines

- Place tests in `tests/` following existing structure
- Name files `test_*.py`
- Each test should complete in milliseconds; entire suite in seconds
- Use synthetic/mock data — never real audio files or API calls
- Set random seeds for deterministic output (`torch.manual_seed(42)`)
- Mock LLM calls, file I/O, and any external services
- Use `tempfile.mkdtemp()` for temporary files, clean up after tests

### What to test

| Contribution | Test coverage |
|--------------|---------------|
| Block | Loads from TOML, has all required fields, json_example is valid JSON fragment |
| Profile | Loads from TOML, all referenced blocks resolve, context is non-empty |
| Provider | API call is made with correct parameters (mocked), response text returned, errors handled |
| Feature | Core logic works with synthetic input, edge cases handled, output format correct |

### Example: Testing a block

```python
import tomllib
from pathlib import Path

def test_methodology_notes_block():
    block_path = Path("src/blocks/methodology_notes.toml")
    assert block_path.exists(), "Block file not found"

    with open(block_path, "rb") as f:
        block = tomllib.load(f)

    # Required fields
    assert block["name"] == "methodology_notes"
    assert "display_name" in block
    assert "description" in block
    assert "prompt" in block
    assert "json_example" in block

    # json_example should be a parseable JSON fragment
    import json
    json.loads("{" + block["json_example"] + "}")
```

### Example: Testing a provider (mocked)

```python
from unittest.mock import patch, MagicMock

@patch("providers.ollama_client")
def test_call_ollama(mock_client):
    from providers import _call_ollama

    mock_response = MagicMock()
    mock_response.message.content = '{"session_summary": "Test"}'
    mock_client.Client.return_value.chat.return_value = mock_response

    result = _call_ollama("test prompt", "qwen3:8b")
    assert result == '{"session_summary": "Test"}'
```

### What NOT to do in tests

- Do not load real audio files
- Do not make real API calls (Anthropic, Ollama, Hugging Face)
- Do not download models or data
- Do not run tests that take more than 1 second each
- Do not require credentials or external services
- Do not use large fixtures — keep synthetic data minimal

---

## Pull Request Guidelines

### Formatting Your PR

Every pull request must include:

- **Who you are** (GitHub username)
- **Type of contribution** (block, profile, provider, feature, bug fix)
- **High-level description** of what you've implemented
- **File guide** — which files to review

**Example PR description:**

```
**Contributor:** @janedoe

**Type:** New Block + Profile

**Description:** Added methodology_notes and literature_gaps blocks
for academic research use cases. Created a research profile that
assembles these with existing base blocks.

**Files to Review:**
- `src/blocks/methodology_notes.toml` — Block definition
- `src/blocks/literature_gaps.toml` — Block definition
- `src/profiles/research.toml` — Profile assembling research blocks
- `tests/test_blocks.py` — New test cases
```

### Review Process

1. Maintainers review for style, functionality, and completeness
2. Automated tests run to ensure compatibility
3. You may be asked to make revisions based on feedback
4. Once approved, your contribution is merged into `main`

---

## Getting Help

- Check existing [issues](https://github.com/capccode/LH-Debrief/issues) and discussions on GitHub
- Review similar implementations in the codebase
- Reach out through GitHub issues
