"""
Export utilities for generated quizzes.

Supports exporting a Quiz to JSON, Markdown, a printable PDF, and a
ready-to-paste social media caption -- covering the assignment's bonus
"export / download / social copy" requirements.
"""

from __future__ import annotations

import json

from fpdf import FPDF

from src.models.schema import Quiz


def quiz_to_json_bytes(quiz: Quiz) -> bytes:
    """Serialize a quiz to pretty-printed JSON bytes for download."""
    return json.dumps(quiz.model_dump(mode="json"), indent=2, ensure_ascii=False).encode("utf-8")


def quiz_to_markdown(quiz: Quiz) -> str:
    """Render a quiz as a Markdown document."""
    lines = [
        f"# {quiz.sport} Quiz ({quiz.difficulty.value})",
        f"*Generated: {quiz.generated_at}*",
        "",
    ]
    for i, q in enumerate(quiz.questions, start=1):
        lines.append(f"## Q{i}. {q.question}")
        opts = q.options_dict()
        for key in ["A", "B", "C", "D"]:
            marker = "✅" if key == q.correct_answer.value else "-"
            lines.append(f"- **{key}.** {opts[key]} {marker if key == q.correct_answer.value else ''}")
        lines.append(f"\n**Correct Answer:** {q.correct_answer.value}. {q.correct_answer_text()}")
        lines.append(f"**Explanation:** {q.explanation}\n")
    return "\n".join(lines)


def quiz_to_markdown_bytes(quiz: Quiz) -> bytes:
    return quiz_to_markdown(quiz).encode("utf-8")


def quiz_to_pdf_bytes(quiz: Quiz) -> bytes:
    """Render a quiz as a simple, printable PDF document."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)
    pdf.add_page()

    def write_line(text: str, size: int, style: str = "", line_height: int = 7) -> None:
        """
        Render one line of text with a guaranteed-safe, explicit width.

        Using ``pdf.epw`` (effective page width) instead of the "auto" width
        value ``0`` avoids a known fpdf2 edge case where ``multi_cell(0, ...)``
        can miscompute the remaining line width -- especially right after a
        font-size change -- and raise "Not enough horizontal space to render
        a single character" even for short, plain text.
        """
        pdf.set_font("Helvetica", style, size)
        pdf.set_x(pdf.l_margin)
        clean_text = _sanitize(text) or " "
        pdf.multi_cell(pdf.epw, line_height, clean_text)

    write_line(f"{quiz.sport} Quiz - {quiz.difficulty.value}", size=16, style="B", line_height=10)
    write_line(f"Generated: {quiz.generated_at}", size=9, line_height=6)
    pdf.ln(4)

    for i, q in enumerate(quiz.questions, start=1):
        write_line(f"Q{i}. {q.question}", size=12, style="B", line_height=8)

        opts = q.options_dict()
        for key in ["A", "B", "C", "D"]:
            prefix = "* " if key == q.correct_answer.value else "  "
            write_line(f"{prefix}{key}. {opts[key]}", size=11, line_height=7)

        write_line(
            f"Correct Answer: {q.correct_answer.value}  |  Explanation: {q.explanation}",
            size=10,
            style="I",
            line_height=6,
        )
        pdf.ln(4)

    output = pdf.output()
    if isinstance(output, str):
        return output.encode("latin-1", errors="replace")
    return bytes(output)


def _sanitize(text: str) -> str:
    """FPDF's base fonts only support latin-1; degrade unsupported chars gracefully."""
    cleaned = " ".join((text or "").split())  # collapse newlines / stray whitespace
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")


def quiz_to_social_caption(quiz: Quiz) -> str:
    """Generate a ready-to-post social media teaser for the quiz."""
    first_q = quiz.questions[0] if quiz.questions else None
    teaser = f'"{first_q.question}"' if first_q else "Test your knowledge!"

    hashtags = f"#{quiz.sport.replace(' ', '')}Quiz #SportsTrivia #{quiz.difficulty.value}Mode"
    lines = [
        f"🏆 {quiz.sport} Quiz Time! ({quiz.difficulty.value} difficulty)",
        "",
        f"Question 1: {teaser}",
        "",
        f"Think you know {quiz.sport}? Drop your answer below! 👇",
        "",
        hashtags,
    ]
    return "\n".join(lines)