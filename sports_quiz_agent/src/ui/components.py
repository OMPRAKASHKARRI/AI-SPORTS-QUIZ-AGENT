"""
Reusable Streamlit UI components.

Keeping rendering logic here (separate from app.py's orchestration and
session-state handling) keeps the main app file readable and keeps
presentation concerns testable/swappable independently of the pipeline.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from src.models.schema import Quiz, QuizQuestion, RAGContext


def render_header() -> None:
    st.markdown(
        """
        <div class="quiz-app-header">
            <h1>🏆 AI Powered Sports Quiz Generation Agent</h1>
            <p>Grounded with ChromaDB + live web search · Never hallucinates · A fresh quiz every time</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rag_context_panel(context: RAGContext) -> None:
    """Render the retrieved context in an expandable transparency panel."""
    with st.expander("🔍 View Retrieved RAG Context (transparency)", expanded=False):
        st.caption(
            "Every question above is grounded ONLY in the facts retrieved below. "
            "This is exactly what was sent to the LLM."
        )

        if context.historical_facts:
            st.markdown(
                '<span class="source-chip">📚 CHROMADB</span> **Historical Knowledge Base**',
                unsafe_allow_html=True,
            )
            for fact in context.historical_facts:
                cat = f" _({fact.category})_" if fact.category else ""
                st.markdown(f"- {fact.text}{cat}")
        else:
            st.info("No historical facts were retrieved from ChromaDB for this sport.")

        st.markdown("---")

        if context.web_results:
            st.markdown(
                '<span class="source-chip">🌐 LIVE WEB</span> **DuckDuckGo Search Results**',
                unsafe_allow_html=True,
            )
            for res in context.web_results:
                link = f" [source]({res.url})" if res.url else ""
                st.markdown(f"- **{res.title}**: {res.snippet}{link}")
        else:
            st.info("No live web results were retrieved (or web search was disabled).")


def render_question_card(
    index: int,
    question: QuizQuestion,
    user_answer: Optional[str] = None,
    reveal: bool = False,
) -> None:
    """
    Render a single question card.

    If ``reveal`` is True, correct/incorrect styling is shown based on
    ``user_answer``. Otherwise the question renders as a plain, unanswered card.
    """
    st.markdown('<div class="question-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="q-number">QUESTION {index}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="q-text">{question.question}</div>', unsafe_allow_html=True)

    options = question.options_dict()
    for key, text in options.items():
        css_class = "option-row"
        suffix = ""
        if reveal:
            if key == question.correct_answer.value:
                css_class += " option-correct"
                suffix = " ✅"
            elif key == user_answer and key != question.correct_answer.value:
                css_class += " option-wrong-selected"
                suffix = " ❌"
        st.markdown(
            f'<div class="{css_class}"><strong>{key}.</strong> {text}{suffix}</div>',
            unsafe_allow_html=True,
        )

    if reveal:
        st.markdown(
            f'<div class="explanation-box">💡 <strong>Explanation:</strong> {question.explanation}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_score_summary(score: int, total: int) -> None:
    pct = round((score / total) * 100) if total else 0
    st.markdown(
        f'<span class="score-badge">Score: {score} / {total} ({pct}%)</span>',
        unsafe_allow_html=True,
    )


def render_quiz_history_sidebar(history: list[Quiz]) -> None:
    if not history:
        st.caption("No quizzes generated yet this session.")
        return
    for quiz in reversed(history[-10:]):
        label = f"{quiz.sport} · {quiz.difficulty.value} · {quiz.quiz_id}"
        st.caption(f"🗂️ {label}")
