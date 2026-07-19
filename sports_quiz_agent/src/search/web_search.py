"""
Live web search via DuckDuckGo.

Provides current/recent sporting information (latest winners, records,
tournament results) to complement the static ChromaDB knowledge base, so
generated quizzes can reflect up-to-date events rather than only
historical facts.
"""

from __future__ import annotations

from typing import List

from duckduckgo_search import DDGS

from config.settings import settings
from src.models.schema import WebResult
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Query templates that bias DuckDuckGo toward recent, quiz-worthy content.
_QUERY_TEMPLATES = [
    "{sport} latest news winner champion",
    "{sport} recent tournament results record",
]


class WebSearchClient:
    """Thin wrapper around duckduckgo_search with cleaning/summarization."""

    def __init__(
        self,
        max_results: int = settings.WEB_SEARCH_MAX_RESULTS,
        region: str = settings.WEB_SEARCH_REGION,
    ) -> None:
        self._max_results = max_results
        self._region = region

    def search_sport(self, sport: str) -> List[WebResult]:
        """
        Run one or more live searches for a sport and return cleaned results.

        Any network / rate-limit failure is caught and logged; the RAG
        pipeline is designed to degrade gracefully to ChromaDB-only context
        if live search is unavailable, rather than crashing the app.
        """
        collected: List[WebResult] = []

        for template in _QUERY_TEMPLATES:
            query = template.format(sport=sport)
            try:
                collected.extend(self._run_query(query))
            except Exception:
                logger.exception("DuckDuckGo search failed for query '%s'.", query)
                continue

            if len(collected) >= self._max_results:
                break

        deduped = self._dedupe(collected)
        return deduped[: self._max_results]

    def _run_query(self, query: str) -> List[WebResult]:
        results: List[WebResult] = []
        with DDGS() as ddgs:
            for hit in ddgs.text(
                query, region=self._region, safesearch="moderate", max_results=self._max_results
            ):
                title = (hit.get("title") or "").strip()
                body = (hit.get("body") or "").strip()
                url = hit.get("href")
                if not title or not body:
                    continue
                results.append(
                    WebResult(
                        title=title,
                        snippet=self._clean_snippet(body),
                        url=url,
                    )
                )
        return results

    @staticmethod
    def _clean_snippet(text: str, max_len: int = 280) -> str:
        """Trim and normalize whitespace in a search snippet."""
        cleaned = " ".join(text.split())
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len].rsplit(" ", 1)[0] + "..."
        return cleaned

    @staticmethod
    def _dedupe(results: List[WebResult]) -> List[WebResult]:
        seen_titles = set()
        unique: List[WebResult] = []
        for r in results:
            key = r.title.strip().lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            unique.append(r)
        return unique
