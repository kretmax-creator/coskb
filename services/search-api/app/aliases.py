import json
import logging
from pathlib import Path

logger = logging.getLogger("search-api")

_ALIASES_PATH = Path(__file__).resolve().parent.parent / "aliases.json"


def _load_aliases() -> dict[str, list[str]]:
    try:
        with open(_ALIASES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded %d alias entries from %s", len(data), _ALIASES_PATH.name)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load aliases: %s. Query expansion disabled.", exc)
        return {}


ALIASES: dict[str, list[str]] = _load_aliases()


def expand_query(q: str) -> tuple[str, str | None]:
    """Replace alias matches with first synonym.

    Returns (original, rewritten) or (original, None) if no match.
    """
    if not ALIASES:
        return q, None

    words = q.split()
    rewritten = []
    changed = False
    for word in words:
        key = word.lower()
        if key in ALIASES:
            rewritten.append(ALIASES[key][0])
            changed = True
        else:
            rewritten.append(word)
    return q, " ".join(rewritten) if changed else None
