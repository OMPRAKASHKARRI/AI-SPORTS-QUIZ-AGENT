"""
In-memory quiz transformations: shuffling question order and shuffling
the option order *within* each question (while correctly re-mapping which
letter is now the correct answer). Used by the "Shuffle Questions" /
"Shuffle Options" bonus features in the UI.
"""

from __future__ import annotations

import random

from src.models.schema import OptionKey, Quiz, QuizQuestion


def shuffle_question_order(quiz: Quiz) -> Quiz:
    """Return a new Quiz with the same questions in randomized order."""
    shuffled = quiz.questions.copy()
    random.shuffle(shuffled)
    return quiz.model_copy(update={"questions": shuffled})


def shuffle_question_options(question: QuizQuestion) -> QuizQuestion:
    """Return a new QuizQuestion with options reshuffled and the correct-answer key remapped."""
    options = question.options_dict()
    correct_text = question.correct_answer_text()

    keys = ["A", "B", "C", "D"]
    values = [options[k] for k in keys]
    random.shuffle(values)

    new_correct_key = OptionKey(keys[values.index(correct_text)])

    return question.model_copy(
        update={
            "option_a": values[0],
            "option_b": values[1],
            "option_c": values[2],
            "option_d": values[3],
            "correct_answer": new_correct_key,
        }
    )


def shuffle_all_options(quiz: Quiz) -> Quiz:
    """Return a new Quiz with every question's options independently reshuffled."""
    new_questions = [shuffle_question_options(q) for q in quiz.questions]
    return quiz.model_copy(update={"questions": new_questions})
