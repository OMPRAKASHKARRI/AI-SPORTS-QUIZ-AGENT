"""
Typed data models shared across the application.

Using Pydantic here gives us free validation of every quiz the LLM produces
before it is ever shown to a user -- if the model hallucinates a malformed
question (missing option, duplicate answer key, etc.) validation fails and
the pipeline can retry instead of silently shipping bad data.
"""

from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class OptionKey(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class QuizQuestion(BaseModel):
    """A single multiple-choice quiz question."""

    question: str = Field(..., min_length=5, description="The question text.")
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_answer: OptionKey = Field(
        ..., description="Which option (A/B/C/D) is correct."
    )
    explanation: str = Field(
        ..., min_length=5, description="Short factual explanation, grounded in context."
    )

    @model_validator(mode="after")
    def options_must_be_distinct(self) -> "QuizQuestion":
        options = [self.option_a, self.option_b, self.option_c, self.option_d]
        normalized = [o.strip().lower() for o in options]
        if len(set(normalized)) != len(normalized):
            raise ValueError("All four options must be distinct.")
        return self

    def options_dict(self) -> dict:
        return {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }

    def correct_answer_text(self) -> str:
        return self.options_dict()[self.correct_answer.value]


class Quiz(BaseModel):
    """A complete generated quiz."""

    quiz_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    sport: str
    difficulty: Difficulty
    generated_at: str = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat()
    )
    questions: List[QuizQuestion]

    @field_validator("questions")
    @classmethod
    def must_have_reasonable_question_count(
        cls, questions: List[QuizQuestion]
    ) -> List[QuizQuestion]:
        if not (3 <= len(questions) <= 6):
            raise ValueError(
                f"Expected 4-5 questions, got {len(questions)}. "
                "Quiz generation likely malformed."
            )
        return questions

    @model_validator(mode="after")
    def questions_must_not_be_duplicated(self) -> "Quiz":
        seen = set()
        for q in self.questions:
            key = q.question.strip().lower()
            if key in seen:
                raise ValueError(f"Duplicate question detected: '{q.question}'")
            seen.add(key)
        return self


class RetrievedFact(BaseModel):
    """A single fact retrieved from ChromaDB (historical context)."""

    text: str
    sport: str
    category: Optional[str] = None
    source: str = "chromadb"
    distance: Optional[float] = None


class WebResult(BaseModel):
    """A single cleaned/summarized live web search result."""

    title: str
    snippet: str
    url: Optional[str] = None
    source: str = "duckduckgo"


class RAGContext(BaseModel):
    """The full merged context passed into the LLM prompt."""

    sport: str
    difficulty: Difficulty
    historical_facts: List[RetrievedFact] = Field(default_factory=list)
    web_results: List[WebResult] = Field(default_factory=list)

    def has_any_context(self) -> bool:
        return bool(self.historical_facts or self.web_results)

    def to_prompt_block(self) -> str:
        """Render the merged context as plain text for the LLM prompt."""
        lines: List[str] = []

        if self.historical_facts:
            lines.append("### HISTORICAL / KNOWLEDGE BASE FACTS (from ChromaDB)")
            for i, fact in enumerate(self.historical_facts, start=1):
                tag = f" [{fact.category}]" if fact.category else ""
                lines.append(f"{i}. {fact.text}{tag}")

        if self.web_results:
            lines.append("\n### LIVE WEB SEARCH RESULTS (DuckDuckGo, recent)")
            for i, res in enumerate(self.web_results, start=1):
                lines.append(f"{i}. {res.title}: {res.snippet}")

        if not lines:
            lines.append(
                "No retrieved context was found for this sport. "
                "Do not fabricate facts -- state that context is insufficient."
            )

        return "\n".join(lines)
