"""
Centralized application configuration.

All environment variables are loaded exactly once here and exposed as a
single, typed, importable ``settings`` object. No other module should call
``os.getenv`` directly -- this keeps configuration consistent, testable,
and easy to audit.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env from the project root before anything else reads env vars.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


class Settings:
    """Typed, read-only application settings loaded from environment variables."""

    # --- Paths ---
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    SPORTS_FACTS_FILE: Path = DATA_DIR / "sports_facts.json"
    STATIC_DIR: Path = PROJECT_ROOT / "static"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # --- LLM Provider ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").strip().lower()

    # --- Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    # --- Generation ---
    LLM_TEMPERATURE: float = _get_float("LLM_TEMPERATURE", 0.9)
    LLM_MAX_TOKENS: int = _get_int("LLM_MAX_TOKENS", 2500)

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "sports_facts")

    # --- Embeddings ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # --- Retrieval ---
    RAG_TOP_K_HISTORICAL: int = _get_int("RAG_TOP_K_HISTORICAL", 8)
    RAG_TOP_K_WEB: int = _get_int("RAG_TOP_K_WEB", 5)

    # --- Web Search ---
    WEB_SEARCH_MAX_RESULTS: int = _get_int("WEB_SEARCH_MAX_RESULTS", 5)
    WEB_SEARCH_REGION: str = os.getenv("WEB_SEARCH_REGION", "wt-wt")

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")

    # --- Domain constants ---
    SUPPORTED_SPORTS: List[str] = [
        "Cricket",
        "Football",
        "Basketball",
        "Tennis",
        "Badminton",
        "Hockey",
        "Kabaddi",
        "Formula 1",
        "Olympics",
    ]
    DIFFICULTY_LEVELS: List[str] = ["Easy", "Medium", "Hard"]
    QUESTIONS_PER_QUIZ_MIN: int = 4
    QUESTIONS_PER_QUIZ_MAX: int = 5

    def validate(self) -> List[str]:
        """Return a list of human-readable configuration problems, if any."""
        problems: List[str] = []
        if self.LLM_PROVIDER not in {"groq", "gemini"}:
            problems.append(
                f"LLM_PROVIDER must be 'groq' or 'gemini', got '{self.LLM_PROVIDER}'."
            )
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            problems.append("GROQ_API_KEY is missing. Set it in your .env file.")
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            problems.append("GEMINI_API_KEY is missing. Set it in your .env file.")
        return problems


settings = Settings()