"""Profile and block loading for composable analysis configuration."""

import tomllib
from pathlib import Path

BLOCKS_DIR = Path(__file__).parent / "blocks"
PROFILES_DIR = Path(__file__).parent / "profiles"


def load_block(name: str) -> dict:
    """Read src/blocks/<name>.toml, return block dict.

    Raises FileNotFoundError with helpful message if block doesn't exist.
    """
    path = BLOCKS_DIR / f"{name}.toml"
    if not path.exists():
        available = ", ".join(sorted(list_blocks()))
        raise FileNotFoundError(f"Block '{name}' not found in {BLOCKS_DIR}. Available: {available}")
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_profile(name: str) -> dict:
    """Read src/profiles/<name>.toml, return profile dict.

    Raises FileNotFoundError with helpful message if profile doesn't exist.
    """
    path = PROFILES_DIR / f"{name}.toml"
    if not path.exists():
        available = ", ".join(sorted(list_profiles()))
        raise FileNotFoundError(
            f"Profile '{name}' not found in {PROFILES_DIR}. Available: {available}"
        )
    with open(path, "rb") as f:
        return tomllib.load(f)


def resolve_blocks(
    profile: dict | None = None,
    add_blocks: list[str] | None = None,
    block_names: list[str] | None = None,
) -> list[dict]:
    """Resolve and return ordered list of block dicts.

    Args:
        profile: Loaded profile dict (has 'blocks' key)
        add_blocks: Additional block names to append to profile's list
        block_names: Direct block names (used with --blocks, mutually exclusive with profile)

    Returns:
        Ordered list of loaded block dicts
    """
    if block_names:
        names = list(block_names)
    elif profile:
        names = list(profile["blocks"])
        if add_blocks:
            for b in add_blocks:
                if b not in names:
                    names.append(b)
    else:
        return []

    return [load_block(name) for name in names]


def list_profiles() -> list[str]:
    """Return available profile names (filenames without .toml)."""
    if not PROFILES_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILES_DIR.glob("*.toml"))


def list_blocks() -> list[str]:
    """Return available block names (filenames without .toml)."""
    if not BLOCKS_DIR.exists():
        return []
    return sorted(p.stem for p in BLOCKS_DIR.glob("*.toml"))
