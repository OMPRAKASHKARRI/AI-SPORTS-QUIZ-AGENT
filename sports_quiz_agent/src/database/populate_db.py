"""
Populate ChromaDB with the sports knowledge base.

Can be run standalone (``python -m src.database.populate_db``) or imported
and called from the Streamlit app on first startup so the vector store is
always ready before a quiz is requested.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from config.settings import settings
from src.database.chroma_client import ChromaDBManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_facts_from_disk(path: Path = settings.SPORTS_FACTS_FILE) -> List[dict]:
    """Load and lightly validate the sports_facts.json knowledge base."""
    if not path.exists():
        raise FileNotFoundError(
            f"Sports facts file not found at {path}. "
            "Ensure data/sports_facts.json exists."
        )

    with open(path, "r", encoding="utf-8") as f:
        facts = json.load(f)

    required_fields = {"id", "sport", "category", "text"}
    for fact in facts:
        missing = required_fields - fact.keys()
        if missing:
            raise ValueError(f"Fact '{fact.get('id', '?')}' missing fields: {missing}")

    logger.info("Loaded %d facts from %s.", len(facts), path)
    return facts


def populate_database(force: bool = False) -> ChromaDBManager:
    """
    Ensure ChromaDB is populated with the sports knowledge base.

    If the collection already has documents and ``force`` is False, this
    is a no-op (fast path for repeated Streamlit reruns). Set ``force=True``
    to re-upsert all facts (e.g. after editing sports_facts.json).
    """
    manager = ChromaDBManager()

    if manager.is_populated() and not force:
        logger.info("ChromaDB already populated; skipping re-ingestion.")
        return manager

    facts = load_facts_from_disk()
    manager.upsert_facts(facts)
    logger.info("ChromaDB population complete: %d documents.", manager.collection.count())
    return manager


if __name__ == "__main__":
    populate_database(force=True)
    print("ChromaDB has been populated with the sports knowledge base.")
