"""
ChromaDB client wrapper.

Encapsulates all vector-database concerns: connecting to a persistent
ChromaDB store, embedding documents with Sentence-Transformers, upserting
the sports knowledge base, and querying by sport (with optional category
filtering) for the RAG pipeline.
"""

from __future__ import annotations

from typing import List, Optional

from config.telemetry_shim import patch_chromadb_grpc_telemetry

# Must run before the first `import chromadb` -- see telemetry_shim.py for why.
patch_chromadb_grpc_telemetry()

import chromadb  # noqa: E402
from chromadb.utils import embedding_functions  # noqa: E402

from config.settings import settings
from src.models.schema import RetrievedFact
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaDBManager:
    """Manages the lifecycle of the sports-facts vector collection."""

    def __init__(
        self,
        persist_dir: str = settings.CHROMA_PERSIST_DIR,
        collection_name: str = settings.CHROMA_COLLECTION_NAME,
        embedding_model_name: str = settings.EMBEDDING_MODEL,
    ) -> None:
        self._persist_dir = persist_dir
        self._collection_name = collection_name

        logger.info("Connecting to persistent ChromaDB store at '%s'.", persist_dir)
        self._client = chromadb.PersistentClient(path=persist_dir)

        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )

        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Collection '%s' ready with %d existing documents.",
            self._collection_name,
            self._collection.count(),
        )

    @property
    def collection(self):
        return self._collection

    def is_populated(self) -> bool:
        """Whether the collection already has documents."""
        return self._collection.count() > 0

    def upsert_facts(self, facts: List[dict]) -> int:
        """
        Insert or update a list of fact dicts into the collection.

        Each fact dict is expected to have: id, sport, category, text, tags.
        Returns the number of facts written.
        """
        if not facts:
            return 0

        ids = [f["id"] for f in facts]
        documents = [f["text"] for f in facts]
        metadatas = [
            {
                "sport": f["sport"],
                "category": f.get("category", "general"),
                "tags": ", ".join(f.get("tags", [])),
            }
            for f in facts
        ]

        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Upserted %d facts into ChromaDB collection.", len(ids))
        return len(ids)

    def query_by_sport(
        self,
        sport: str,
        query_text: Optional[str] = None,
        top_k: int = settings.RAG_TOP_K_HISTORICAL,
    ) -> List[RetrievedFact]:
        """
        Retrieve the most relevant historical facts for a given sport.

        If ``query_text`` is not provided, a generic query built from the
        sport name is used so that semantically related facts are still
        surfaced via the embedding space.
        """
        effective_query = query_text or (
            f"Interesting historical facts, records, records, tournaments, "
            f"players and milestones about {sport}"
        )

        try:
            results = self._collection.query(
                query_texts=[effective_query],
                n_results=top_k,
                where={"sport": sport},
            )
        except Exception:
            logger.exception("ChromaDB query failed for sport '%s'.", sport)
            return []

        return self._parse_query_results(results)

    @staticmethod
    def _parse_query_results(results: dict) -> List[RetrievedFact]:
        facts: List[RetrievedFact] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        for i, doc in enumerate(documents):
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else None
            facts.append(
                RetrievedFact(
                    text=doc,
                    sport=meta.get("sport", "unknown"),
                    category=meta.get("category"),
                    distance=dist,
                )
            )
        return facts

    def count_by_sport(self, sport: str) -> int:
        result = self._collection.get(where={"sport": sport})
        return len(result.get("ids", []))
