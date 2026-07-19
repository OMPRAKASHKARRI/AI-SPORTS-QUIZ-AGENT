"""
AI Powered Sports Quiz Generation Agent — Streamlit entrypoint.

This file is intentionally thin: it wires together the RAG pipeline, the
LLM client, and the UI components, and manages Streamlit session state. All
real logic (retrieval, prompting, generation, export) lives in `src/`.
"""

from __future__ import annotations

import datetime as dt
import time

import streamlit as st

from config.settings import settings
from src.database.chroma_client import ChromaDBManager
from src.database.populate_db import populate_database
from src.llm.client import LLMClient, QuizGenerationError
from src.models.schema import Difficulty, Quiz, RAGContext
from src.rag.pipeline import RAGPipeline
from src.search.web_search import WebSearchClient
from src.ui.components import (
    render_header,
    render_question_card,
    render_quiz_history_sidebar,
    render_rag_context_panel,
    render_score_summary,
)
from src.ui.styles import CUSTOM_CSS
from src.utils.export import (
    quiz_to_json_bytes,
    quiz_to_markdown_bytes,
    quiz_to_pdf_bytes,
    quiz_to_social_caption,
)
from src.utils.logger import get_logger
from src.utils.quiz_ops import shuffle_all_options, shuffle_question_order

logger = get_logger(__name__)

st.set_page_config(
    page_title="AI Sports Quiz Generator",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------- #
# Cached resources (built once per server process, not per rerun)
# ---------------------------------------------------------------------- #

@st.cache_resource(show_spinner="Initializing knowledge base (ChromaDB)...")
def get_chroma_manager() -> ChromaDBManager:
    return populate_database(force=False)


@st.cache_resource(show_spinner=False)
def get_rag_pipeline(_chroma_manager: ChromaDBManager) -> RAGPipeline:
    return RAGPipeline(chroma_manager=_chroma_manager, web_search_client=WebSearchClient())


@st.cache_resource(show_spinner=False)
def get_llm_client() -> LLMClient:
    return LLMClient()


# ---------------------------------------------------------------------- #
# Session state initialization
# ---------------------------------------------------------------------- #

def init_session_state() -> None:
    defaults = {
        "current_quiz": None,
        "current_context": None,
        "quiz_history": [],
        "user_answers": {},
        "revealed": False,
        "quiz_started_at": None,
        "topics_by_key": {},  # {"sport|difficulty": [question texts...]}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def topic_key(sport: str, difficulty: str) -> str:
    return f"{sport}|{difficulty}"


# ---------------------------------------------------------------------- #
# Core quiz generation action
# ---------------------------------------------------------------------- #

def generate_quiz(
    sport: str,
    difficulty: Difficulty,
    num_questions: int,
    include_web_search: bool,
) -> None:
    pipeline = get_rag_pipeline(get_chroma_manager())
    llm_client = get_llm_client()

    key = topic_key(sport, difficulty.value)
    previous_topics = st.session_state["topics_by_key"].get(key, [])

    with st.spinner("🔎 Retrieving grounded context (ChromaDB + live web search)..."):
        context: RAGContext = pipeline.build_context(
            sport=sport, difficulty=difficulty, include_web_search=include_web_search
        )

    with st.spinner("🧠 Generating quiz with grounded prompt..."):
        try:
            quiz: Quiz = llm_client.generate_quiz(
                context=context,
                sport=sport,
                difficulty=difficulty,
                num_questions=num_questions,
                previous_question_topics=previous_topics,
            )
        except QuizGenerationError as exc:
            st.error(f"⚠️ Quiz generation failed: {exc}")
            logger.error("Quiz generation error: %s", exc)
            return

    st.session_state["current_quiz"] = quiz
    st.session_state["current_context"] = context
    st.session_state["user_answers"] = {}
    st.session_state["revealed"] = False
    st.session_state["quiz_started_at"] = time.time()
    st.session_state["quiz_history"].append(quiz)

    updated_topics = previous_topics + [q.question for q in quiz.questions]
    st.session_state["topics_by_key"][key] = updated_topics[-25:]

    st.success(f"✅ Generated a fresh {difficulty.value} {sport} quiz with {len(quiz.questions)} questions!")


# ---------------------------------------------------------------------- #
# Sidebar
# ---------------------------------------------------------------------- #

def render_sidebar() -> tuple[str, Difficulty, int, bool]:
    with st.sidebar:
        st.markdown("### ⚙️ Quiz Configuration")

        sport = st.selectbox("Select Sport", options=settings.SUPPORTED_SPORTS, index=0)
        difficulty_label = st.selectbox(
            "Select Difficulty", options=settings.DIFFICULTY_LEVELS, index=1
        )
        difficulty = Difficulty(difficulty_label)

        num_questions = st.slider(
            "Number of Questions",
            min_value=settings.QUESTIONS_PER_QUIZ_MIN,
            max_value=settings.QUESTIONS_PER_QUIZ_MAX,
            value=settings.QUESTIONS_PER_QUIZ_MAX,
        )

        include_web_search = st.toggle(
            "🌐 Include live web search", value=True,
            help="Adds current DuckDuckGo results to the grounding context.",
        )

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            generate_clicked = st.button("✨ Generate Quiz", use_container_width=True, type="primary")
        with col2:
            regenerate_clicked = st.button(
                "🔁 Regenerate",
                use_container_width=True,
                disabled=st.session_state["current_quiz"] is None,
            )

        st.markdown("---")
        st.markdown("### 🧩 Bonus Tools")

        bonus_col1, bonus_col2 = st.columns(2)
        with bonus_col1:
            shuffle_q_clicked = st.button(
                "🔀 Shuffle Qs", use_container_width=True,
                disabled=st.session_state["current_quiz"] is None,
            )
        with bonus_col2:
            shuffle_o_clicked = st.button(
                "🔀 Shuffle Opts", use_container_width=True,
                disabled=st.session_state["current_quiz"] is None,
            )

        st.markdown("---")
        st.markdown("### 🗂️ Quiz History (this session)")
        render_quiz_history_sidebar(st.session_state["quiz_history"])

        st.markdown("---")
        st.caption(
            f"LLM Provider: **{settings.LLM_PROVIDER.upper()}** · "
            f"Model: `{settings.GROQ_MODEL if settings.LLM_PROVIDER == 'groq' else settings.GEMINI_MODEL}`"
        )

    if generate_clicked or regenerate_clicked:
        generate_quiz(sport, difficulty, num_questions, include_web_search)

    if shuffle_q_clicked and st.session_state["current_quiz"]:
        st.session_state["current_quiz"] = shuffle_question_order(st.session_state["current_quiz"])
        st.session_state["user_answers"] = {}
        st.session_state["revealed"] = False

    if shuffle_o_clicked and st.session_state["current_quiz"]:
        st.session_state["current_quiz"] = shuffle_all_options(st.session_state["current_quiz"])
        st.session_state["user_answers"] = {}
        st.session_state["revealed"] = False

    return sport, difficulty, num_questions, include_web_search


# ---------------------------------------------------------------------- #
# Main content area
# ---------------------------------------------------------------------- #

def render_quiz_taking_flow(quiz: Quiz) -> None:
    st.markdown(f"#### {quiz.sport} · {quiz.difficulty.value} · Quiz ID `{quiz.quiz_id}`")

    if st.session_state["quiz_started_at"] and not st.session_state["revealed"]:
        elapsed = int(time.time() - st.session_state["quiz_started_at"])
        st.caption(f"⏱️ Time elapsed: {elapsed}s")

    if not st.session_state["revealed"]:
        for i, question in enumerate(quiz.questions, start=1):
            st.markdown(f"**Q{i}. {question.question}**")
            options = question.options_dict()
            choice = st.radio(
                label=f"question_{i}",
                options=list(options.keys()),
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                key=f"radio_{quiz.quiz_id}_{i}",
                index=None,
                label_visibility="collapsed",
            )
            if choice:
                st.session_state["user_answers"][i] = choice
            st.markdown("---")

        answered_count = len(st.session_state["user_answers"])
        total = len(quiz.questions)
        st.caption(f"Answered {answered_count}/{total}")

        if st.button("✅ Submit Answers & Reveal", type="primary"):
            st.session_state["revealed"] = True
            st.rerun()

        if st.button("👁️ Just Reveal Answers (skip scoring)"):
            st.session_state["revealed"] = True
            st.rerun()

    else:
        score = sum(
            1
            for i, q in enumerate(quiz.questions, start=1)
            if st.session_state["user_answers"].get(i) == q.correct_answer.value
        )
        if st.session_state["user_answers"]:
            render_score_summary(score, len(quiz.questions))
            st.markdown("")

        for i, question in enumerate(quiz.questions, start=1):
            render_question_card(
                index=i,
                question=question,
                user_answer=st.session_state["user_answers"].get(i),
                reveal=True,
            )

        if st.button("🔄 Retake This Quiz"):
            st.session_state["user_answers"] = {}
            st.session_state["revealed"] = False
            st.session_state["quiz_started_at"] = time.time()
            st.rerun()


def render_export_panel(quiz: Quiz) -> None:
    st.markdown("#### 📤 Export & Share")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button(
            "⬇️ Download JSON",
            data=quiz_to_json_bytes(quiz),
            file_name=f"{quiz.sport}_{quiz.difficulty.value}_{quiz.quiz_id}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Download Markdown",
            data=quiz_to_markdown_bytes(quiz),
            file_name=f"{quiz.sport}_{quiz.difficulty.value}_{quiz.quiz_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "⬇️ Download PDF",
            data=quiz_to_pdf_bytes(quiz),
            file_name=f"{quiz.sport}_{quiz.difficulty.value}_{quiz.quiz_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col4:
        with st.popover("📱 Social Copy", use_container_width=True):
            caption = quiz_to_social_caption(quiz)
            st.text_area("Copy this for social media:", value=caption, height=160)
            st.caption("Select all + copy (Ctrl/Cmd+C).")


def main() -> None:
    init_session_state()
    render_header()

    problems = settings.validate()
    if problems:
        st.warning(
            "⚠️ Configuration issue(s) detected:\n\n"
            + "\n".join(f"- {p}" for p in problems)
            + "\n\nAdd the required keys to your `.env` file (see `.env.example`)."
        )

    render_sidebar()

    quiz: Quiz | None = st.session_state["current_quiz"]
    context: RAGContext | None = st.session_state["current_context"]

    if quiz is None:
        st.info(
            "👈 Choose a sport and difficulty in the sidebar, then click **Generate Quiz** "
            "to create a grounded, AI-powered quiz."
        )
        return

    render_quiz_taking_flow(quiz)

    if context is not None:
        render_rag_context_panel(context)

    st.markdown("---")
    render_export_panel(quiz)


if __name__ == "__main__":
    main()