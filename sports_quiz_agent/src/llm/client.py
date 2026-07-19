"""
LLM client abstraction.

Supports Groq (Llama 3.3 70B Versatile, etc.) and Google Gemini behind a
single interface, so the rest of the application (RAG pipeline, Streamlit
UI) never needs to know which provider is active. Handles:
  - Provider selection via config
  - Robust JSON extraction (LLMs sometimes wrap JSON in markdown fences)
  - Pydantic validation of the parsed quiz
  - Automatic retries with exponential backoff on transient failures
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.settings import settings
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.models.schema import Difficulty, Quiz, RAGContext
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QuizGenerationError(Exception):
    """Raised when the LLM fails to produce a valid, schema-compliant quiz."""


class LLMClient:
    """Unified client for generating grounded quizzes via Groq or Gemini."""

    def __init__(self, provider: str = settings.LLM_PROVIDER) -> None:
        self._provider = provider.lower()
        if self._provider == "groq":
            self._init_groq()
        elif self._provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    # ------------------------------------------------------------------ #
    # Provider initialization
    # ------------------------------------------------------------------ #

    def _init_groq(self) -> None:
        from groq import Groq

        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    def _init_gemini(self) -> None:
        import google.generativeai as genai

        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._genai = genai
        self._model = settings.GEMINI_MODEL

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def generate_quiz(
        self,
        context: RAGContext,
        sport: str,
        difficulty: Difficulty,
        num_questions: int = 5,
        previous_question_topics: Optional[List[str]] = None,
    ) -> Quiz:
        """
        Generate a validated, grounded Quiz object.

        Raises ``QuizGenerationError`` if the LLM cannot be coaxed into a
        schema-valid response after retries -- callers should surface this
        to the user rather than displaying a broken quiz.
        """
        user_prompt = build_user_prompt(
            context=context,
            sport=sport,
            difficulty=difficulty,
            num_questions=num_questions,
            previous_question_topics=previous_question_topics,
        )

        raw_text = self._call_model(user_prompt)
        parsed_json = self._extract_json(raw_text)

        parsed_json.setdefault("sport", sport)
        parsed_json.setdefault("difficulty", difficulty.value)

        try:
            quiz = Quiz.model_validate(parsed_json)
        except ValidationError as exc:
            logger.error("Quiz failed schema validation: %s", exc)
            raise QuizGenerationError(
                f"The model's response did not match the expected quiz schema: {exc}"
            ) from exc

        logger.info(
            "Successfully generated quiz '%s' with %d questions.",
            quiz.quiz_id,
            len(quiz.questions),
        )
        return quiz

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_model(self, user_prompt: str) -> str:
        """Call the active provider's completion endpoint with retry/backoff."""
        if self._provider == "groq":
            return self._call_groq(user_prompt)
        return self._call_gemini(user_prompt)

    def _call_groq(self, user_prompt: str) -> str:
        """Call the Groq chat completions endpoint and return the raw text response."""
        from groq import APIError

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
        except APIError:
            logger.exception("Groq API call failed.")
            raise

        return response.choices[0].message.content or ""

    def _call_gemini(self, user_prompt: str) -> str:
        model = self._genai.GenerativeModel(
            model_name=self._model,
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "temperature": settings.LLM_TEMPERATURE,
                "max_output_tokens": settings.LLM_MAX_TOKENS,
                "response_mime_type": "application/json",
            },
        )
        response = model.generate_content(user_prompt)
        return response.text or ""

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        """
        Robustly extract a JSON object from raw LLM output.

        Handles the common failure modes: markdown code fences, leading/
        trailing commentary, or stray whitespace -- without ever guessing
        at missing fields.
        """
        text = raw_text.strip()

        # Strip ```json ... ``` or ``` ... ``` fences if present.
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        # If there's still leading/trailing noise, isolate the outermost braces.
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM output as JSON: %s\nRaw: %s", exc, raw_text[:500])
            raise QuizGenerationError(
                "The model did not return valid JSON. Please try regenerating the quiz."
            ) from exc