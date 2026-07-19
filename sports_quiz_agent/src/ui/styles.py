"""Custom CSS injected into the Streamlit app for a polished, dark-theme-friendly UI."""

CUSTOM_CSS = """
<style>
:root {
    --accent: #22c55e;
    --accent-soft: rgba(34, 197, 94, 0.12);
    --card-bg: rgba(255, 255, 255, 0.03);
    --card-border: rgba(255, 255, 255, 0.10);
}

/* App title header */
.quiz-app-header {
    padding: 1.25rem 1.5rem;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(34,197,94,0.18), rgba(59,130,246,0.12));
    border: 1px solid var(--card-border);
    margin-bottom: 1.25rem;
}
.quiz-app-header h1 {
    margin: 0;
    font-size: 1.7rem;
}
.quiz-app-header p {
    margin: 0.25rem 0 0 0;
    opacity: 0.75;
    font-size: 0.95rem;
}

/* Question card */
.question-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 1rem;
}
.question-card .q-number {
    display: inline-block;
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 700;
    font-size: 0.78rem;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
    letter-spacing: 0.03em;
}
.question-card .q-text {
    font-size: 1.08rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}
.option-row {
    padding: 0.5rem 0.75rem;
    border-radius: 10px;
    border: 1px solid var(--card-border);
    margin-bottom: 0.4rem;
    font-size: 0.95rem;
}
.option-correct {
    border-color: var(--accent);
    background: var(--accent-soft);
}
.option-wrong-selected {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.12);
}
.explanation-box {
    margin-top: 0.6rem;
    padding: 0.6rem 0.8rem;
    border-radius: 10px;
    background: rgba(59, 130, 246, 0.08);
    border-left: 3px solid #3b82f6;
    font-size: 0.88rem;
    opacity: 0.92;
}

/* Sidebar polish */
section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    border-radius: 10px;
    font-weight: 600;
}

/* Score badge */
.score-badge {
    display: inline-block;
    padding: 0.5rem 1.1rem;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 700;
    font-size: 1.05rem;
    border: 1px solid var(--accent);
}

/* Context source chip */
.source-chip {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.1rem 0.55rem;
    border-radius: 999px;
    margin-right: 0.4rem;
    background: rgba(255,255,255,0.08);
    letter-spacing: 0.03em;
}
</style>
"""
