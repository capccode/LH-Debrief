"""Entity extraction for knowledge graph preparation.

Runs a post-analysis LLM pass to extract typed entities,
relationships, and per-block entity mappings from analysis results.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from providers import call_llm
from rich.console import Console

console = Console()


def extract_entities(
    analysis: dict,
    blocks: list[dict],
    provider: str = "anthropic",
    model: str | None = None,
) -> dict | None:
    """Extract typed entities and relationships from analysis results.

    Args:
        analysis: Parsed analysis dict from analyze_transcript()
        blocks: List of block dicts used in analysis
        provider: LLM provider for extraction
        model: Model override

    Returns:
        Entity extraction dict or None on failure
    """
    prompt = _build_extraction_prompt(analysis, blocks)

    console.print("[cyan]Extracting entities...[/cyan]")

    try:
        response_text = call_llm(prompt, provider, model)

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result = json.loads(response_text.strip())

        extraction = {
            "extraction_model": model or "default",
            "extraction_provider": provider,
            "extraction_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "entities": result.get("entities", []),
            "relationships": result.get("relationships", []),
            "block_entities": result.get("block_entities", {}),
        }

        console.print(
            f"[green]Extracted {len(extraction['entities'])} entities, "
            f"{len(extraction['relationships'])} relationships[/green]"
        )
        return extraction

    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse entity extraction response: {e}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Entity extraction error: {e}[/red]")
        return None


def save_entities(output_dir: Path, entities: dict) -> None:
    """Save entities.json to the output directory."""
    entities_file = output_dir / "entities.json"
    with open(entities_file, "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    console.print(f"[green]Saved entities: {entities_file}[/green]")


def _build_extraction_prompt(analysis: dict, blocks: list[dict]) -> str:
    """Build the entity extraction prompt from analysis results."""
    analysis_text = json.dumps(analysis, indent=2)
    block_names = [b["name"] for b in blocks if b["name"] in analysis]

    prompt = f"""Extract entities and relationships from this analysis output.

<analysis>
{analysis_text}
</analysis>

Extract the following:

1. **Entities**: Every notable entity mentioned. For each entity provide:
   - "text": the entity text as it appears
   - "type": one of: person, organization, concept, technology, finding, hypothesis, decision, action_item, question, project, domain, dataset, temporal_reference
   - "confidence": 0.0-1.0

2. **Relationships**: Connections between entities. For each:
   - "source": source entity text
   - "target": target entity text
   - "type": one of: OWNS, DECIDED, MENTIONS, PROPOSES, USES, RELATES_TO, RESOLVES, BELONGS_TO, PART_OF, PARTICIPATED_IN, REFERENCES
   - "context": brief explanation of the relationship

3. **Block entities**: For each analysis block that has content, list which entities appear in it. Use this structure:
   {{"block_name": [{{"text": "entity text", "type": "entity type"}}]}}

   The blocks in this analysis are: {json.dumps(block_names)}

Provide your response as JSON with this exact structure:
{{
    "entities": [
        {{"text": "Entity name", "type": "person|concept|technology|...", "confidence": 0.95}}
    ],
    "relationships": [
        {{"source": "Entity A", "target": "Entity B", "type": "RELATIONSHIP_TYPE", "context": "brief explanation"}}
    ],
    "block_entities": {{
        "block_name": [{{"text": "entity", "type": "type"}}]
    }}
}}

Return ONLY the JSON, no other text."""

    return prompt
