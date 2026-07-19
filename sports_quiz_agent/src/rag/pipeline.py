"""
Retrieval-Augmented Generation pipeline.

Orchestrates the full grounding flow described in the assignment:

    User Input
        -> Retrieve historical facts from ChromaDB
        -> Search latest info via DuckDuckGo
        -> Merge context
        -> (context handed to the LLM client for grounded generation)

Keeping this as its own module (independent of Streamlit and independent
of the LLM client) makes it unit-testable and reusable outside the UI.
"""

from __future__ import annotations

from config.settings import settings
from src.database.chroma_client import ChromaDBManager
from src.models.schema import Difficulty, RAGContext
from src.search.web_search import WebSearchClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    """Retrieves and merges historical + live context for a sport/difficulty."""

    def __init__(
        self,
        chroma_manager: ChromaDBManager,
        web_search_client: WebSearchClient | None = None,
    ) -> None:
        self._chroma = chroma_manager
        self._web = web_search_client or WebSearchClient()

    def build_context(
        self,
        sport: str,
        difficulty: Difficulty,
        include_web_search: bool = True,
    ) -> RAGContext:
        """
        Retrieve and merge historical + live context for the given inputs.

        Historical retrieval always runs. Live web search can be disabled
        (e.g. offline demo mode) via ``include_web_search=False`` and the
        pipeline still returns a valid, usable context.
        """
        logger.info("Building RAG context for sport='%s', difficulty='%s'.", sport, difficulty)

        historical_facts = self._chroma.query_by_sport(
            sport=sport, top_k=settings.RAG_TOP_K_HISTORICAL
        )
        logger.info("Retrieved %d historical facts from ChromaDB.", len(historical_facts))

        web_results = []
        if include_web_search:
            try:
                web_results = self._web.search_sport(sport)
                logger.info("Retrieved %d live web results.", len(web_results))
            except Exception:
                logger.exception(
                    "Live web search failed; continuing with ChromaDB-only context."
                )

        context = RAGContext(
            sport=sport,
            difficulty=difficulty,
            historical_facts=historical_facts,
            web_results=web_results,
        )

        if not context.has_any_context():
            logger.warning(
                "No context retrieved for sport='%s'. LLM will be instructed "
                "to avoid fabricating facts.",
                sport,
            )

        return context
