"""
Prompt engineering for the Sports Quiz Generation Agent.

This module is the single source of truth for how the LLM is instructed.
It encodes:
  - A strict anti-hallucination system prompt (grounded-only generation).
  - Difficulty-specific question logic.
  - Randomization hooks so regeneration reliably produces a *different*
    quiz rather than a near-duplicate of the previous one.
"""

from __future__ import annotations

import random
import uuid
from typing import List

from src.models.schema import Difficulty, RAGContext

SYSTEM_PROMPT = """You are an expert sports quiz writer and fact-checker working for a \
sports media company. You create engaging, accurate multiple-choice quizzes for social \
media audiences.

Your absolute top priority is FACTUAL ACCURACY. You must follow these non-negotiable rules:

1. GROUNDING: You may ONLY use facts explicitly present in the "RETRIEVED CONTEXT" section \
provided in the user message. Do not use outside knowledge to invent statistics, dates, \
scores, names, or records that are not supported by the retrieved context.
2. NO HALLUCINATION: If the retrieved context does not contain enough information to write \
a confident, verifiable question, DO NOT invent one. Instead, write a simpler question that \
stays strictly within what the context actually supports.
3. INSUFFICIENT CONTEXT: If the retrieved context is empty, extremely sparse, or irrelevant \
to the requested sport, generate only as many questions as the context can truly support \
(even fewer than requested) rather than fabricating facts. Never guess.
4. NO FABRICATED EXPLANATIONS: Every "explanation" field must be directly traceable to a \
fact in the retrieved context. Do not embellish with unverified detail.
5. UNIQUENESS: Every question in the quiz must be distinct in subject matter -- do not ask \
two questions about the same fact from different angles.
6. FORMAT: You must respond with STRICT, VALID JSON ONLY -- no markdown code fences, no \
commentary, no preamble, no trailing text. The JSON must exactly match the schema given in \
the user message.
7. FAIR OPTIONS: Wrong answer options ("distractors") should be plausible and sport-relevant, \
but must not accidentally also be correct according to the retrieved context.
8. TONE: Questions should be engaging, concise, and suitable for posting on social media \
(punchy phrasing, no unnecessary jargon).

You will be given a randomization seed and a list of previously used question topics (if any) \
purely to help you produce a DIFFERENT quiz on regeneration -- this seed is not a fact and must \
never appear in your output."""


_DIFFICULTY_GUIDANCE = {
    Difficulty.EASY: (
        "EASY difficulty: Focus on simple, widely-known rules, basic terminology, and "
        "well-known facts (e.g. 'how many players are on a team', 'what is the sport's most "
        "famous tournament'). Avoid obscure statistics or rare trivia."
    ),
    Difficulty.MEDIUM: (
        "MEDIUM difficulty: Focus on notable history, well-known records, and major "
        "tournament winners/results. Assume the audience follows the sport casually but not "
        "obsessively."
    ),
    Difficulty.HARD: (
        "HARD difficulty: Focus on precise statistics, rare or lesser-known facts, historic "
        "events, and detailed player achievements. Assume the audience are serious, "
        "knowledgeable fans."
    ),
}

_OUTPUT_SCHEMA_EXAMPLE = """{
  "sport": "<sport name>",
  "difficulty": "<Easy | Medium | Hard>",
  "questions": [
    {
      "question": "<question text>",
      "option_a": "<option A>",
      "option_b": "<option B>",
      "option_c": "<option C>",
      "option_d": "<option D>",
      "correct_answer": "<A | B | C | D>",
      "explanation": "<short factual explanation grounded in the retrieved context>"
    }
  ]
}"""


def build_user_prompt(
    context: RAGContext,
    sport: str,
    difficulty: Difficulty,
    num_questions: int,
    previous_question_topics: List[str] | None = None,
) -> str:
    """
    Build the full user-turn prompt: merged context + generation instructions.

    A random seed and a summary of previously-asked topics are included so
    that "Regenerate Quiz" produces genuinely different questions instead of
    near-duplicates, without that randomization ever being treated as a fact.
    """
    randomization_seed = uuid.uuid4().hex[:12]
    shuffle_hint = random.choice(
        [
            "Prioritize questions about players and records this time.",
            "Prioritize questions about tournaments and history this time.",
            "Prioritize a balanced mix of rules, records, and milestones this time.",
            "Prioritize lesser-emphasized facts from the context this time.",
        ]
    )

    avoid_block = ""
    if previous_question_topics:
        formatted = "\n".join(f"- {t}" for t in previous_question_topics[-15:])
        avoid_block = (
            "\n\nDO NOT repeat or closely rephrase any of these previously used question "
            f"topics:\n{formatted}"
        )

    difficulty_note = _DIFFICULTY_GUIDANCE[difficulty]

    prompt = f"""RETRIEVED CONTEXT (this is the ONLY information you may use as fact):
{context.to_prompt_block()}

---

TASK:
Generate a multiple-choice sports quiz.

Sport: {sport}
Difficulty: {difficulty.value}
Number of questions: {num_questions} (fewer only if context is insufficient -- never fabricate \
to reach this number)

Difficulty guidance: {difficulty_note}

Randomization seed (for variety only, not a fact): {randomization_seed}
Variety instruction: {shuffle_hint}{avoid_block}

OUTPUT FORMAT:
Respond with STRICT JSON ONLY, matching exactly this schema (no markdown fences, no extra text):

{_OUTPUT_SCHEMA_EXAMPLE}

Remember: every fact, name, date, and statistic must come directly from the RETRIEVED CONTEXT \
above. If the context is insufficient for {num_questions} quality questions, return fewer \
questions rather than inventing facts."""

    return prompt
