"""
Overall Purpose:
----------------
This Streamlit-based module defines the `QuizManager` class to:
- Dynamically generate quizzes using an LLM (via `QuestionGenerator`).
- Allow users to answer MCQ or Fill-in-the-Blank questions interactively.
- Evaluate user answers and calculate correctness.
- Display results and optionally save them as a CSV file.

Use Case:
---------
Create an interactive quiz app that auto-generates questions using LLMs and tracks user performance.
"""

import os
import streamlit as st
import pandas as pd
from src.generator.question_generator import QuestionGenerator

# -------------------------------
# Helper function to rerun the app
# -------------------------------
def rerun():
    """Trigger Streamlit app rerun by changing a session state key."""
    st.session_state['rerun_trigger'] = not st.session_state.get('rerun_trigger', False)

# ------------------------------------
# Main class to manage the quiz flow
# ------------------------------------
class QuizManager:
    def __init__(self):
        # Store generated questions, user answers, and results
        self.questions = []
        self.user_answers = []
        self.results = []

    # -----------------------------
    # Generate quiz questions using LLM
    # -----------------------------
    def generate_questions(self, generator: QuestionGenerator, topic: str, question_type: str, difficulty: str, num_questions: int):
        # Clear any previous quiz data
        self.questions = []
        self.user_answers = []
        self.results = []

        try:
            for _ in range(num_questions):
                if question_type == "Multiple Choice":
                    # Generate MCQ from LLM
                    question = generator.generate_mcq(topic, difficulty.lower())
                    self.questions.append({
                        'type': 'MCQ',
                        'question': question.question,
                        'options': question.options,
                        'correct_answer': question.correct_answer
                    })
                else:
                    # Generate Fill-in-the-Blank from LLM
                    question = generator.generate_fill_blank(topic, difficulty.lower())
                    self.questions.append({
                        'type': 'Fill in the Blank',
                        'question': question.question,
                        'correct_answer': question.answer
                    })
        except Exception as e:
            # Show error in Streamlit if generation fails
            st.error(f"Error generating questions: {e}")
            return False

        return True  # Successfully generated all questions

    # -------------------------------------
    # Show questions and collect user input
    # -------------------------------------
    def attempt_quiz(self):
        for i, q in enumerate(self.questions):
            st.markdown(f"**Question {i + 1}: {q['question']}**")

            if q['type'] == 'MCQ':
                # Show options for MCQ and get selected answer
                user_answer = st.radio(
                    f"Select an answer for Question {i + 1}",
                    q['options'],
                    key=f"mcq_{i}"
                )
                self.user_answers.append(user_answer)
            else:
                # Show input box for Fill-in-the-Blank
                user_answer = st.text_input(
                    f"Fill in the blank for Question {i + 1}",
                    key=f"fill_blank_{i}"
                )
                self.user_answers.append(user_answer)

    # --------------------------------------------
    # Check user answers and store evaluation info
    # --------------------------------------------
    def evaluate_quiz(self):
        self.results = []

        # Compare each user answer with the correct one
        for i, (q, user_ans) in enumerate(zip(self.questions, self.user_answers)):
            result_dict = {
                'question_number': i + 1,
                'question': q['question'],
                'question_type': q['type'],
                'user_answer': user_ans,
                'correct_answer': q['correct_answer'],
                'is_correct': False
            }

            # Check correctness for both MCQ and Fill-in-the-Blank
            if q['type'] == 'MCQ':
                result_dict['options'] = q['options']
                result_dict['is_correct'] = user_ans == q['correct_answer']
            else:
                result_dict['options'] = []
                result_dict['is_correct'] = user_ans.strip().lower() == q['correct_answer'].strip().lower()

            self.results.append(result_dict)

    # -------------------------------
    # Convert results to a DataFrame
    # -------------------------------
    def generate_result_dataframe(self):
        if not self.results:
            return pd.DataFrame()  # Return empty DataFrame if no results
        return pd.DataFrame(self.results)

    # -------------------------------
    # Save results to a CSV file
    # -------------------------------
    def save_to_csv(self, filename_prefix='quiz_results'):
        if not self.results:
            st.warning("No results to save. Please complete the quiz first.")
            return None

        df = self.generate_result_dataframe()

        # Create a timestamped filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{filename_prefix}_{timestamp}.csv"

        # Make sure the results directory exists
        os.makedirs('results', exist_ok=True)
        full_path = os.path.join('results', unique_filename)

        try:
            # Save the results as CSV
            df.to_csv(full_path, index=False)
            st.success(f"Results saved to {full_path}")
            return full_path
        except Exception as e:
            st.error(f"Failed to save results: {e}")
            return None
