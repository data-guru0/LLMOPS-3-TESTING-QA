"""
Overall Purpose:
----------------
This Streamlit-based module defines the `QuizManager` class to:
- Dynamically generate quizzes using an LLM (via `QuestionGenerator`).
- Allow users to answer MCQ or Fill-in-the-Blank questions interactively.
- Evaluate user answers and calculate correctness.
- Display results and optionally save them as a CSV file.

It supports:
- LLM-backed question generation (MCQ and Fill-in-the-Blank)
- User interaction and quiz attempts through Streamlit
- Evaluation and storage of quiz results

Use Case:
---------
Build a fully interactive quiz app that uses LLMs to auto-generate questions and validate user performance.
"""

import os
import streamlit as st
import pandas as pd
from src.generator.question_generator import QuestionGenerator

# Utility function to rerun the Streamlit app
def rerun():
    """Trigger rerun of Streamlit app by toggling a session_state key."""
    st.session_state['rerun_trigger'] = not st.session_state.get('rerun_trigger', False)

# Manages quiz lifecycle: generate -> take -> evaluate -> save
class QuizManager:
    def __init__(self):
        # Stores questions, user answers, and final results
        self.questions = []
        self.user_answers = []
        self.results = []

    # Generates MCQ or Fill-in-the-Blank questions using the LLM
    def generate_questions(self, generator: QuestionGenerator, topic: str, question_type: str, difficulty: str, num_questions: int):
        self.questions = []
        self.user_answers = []
        self.results = []

        try:
            for _ in range(num_questions):
                if question_type == "Multiple Choice":
                    # Generate an MCQ using the LLM
                    question = generator.generate_mcq(topic, difficulty.lower())
                    self.questions.append({
                        'type': 'MCQ',
                        'question': question.question,
                        'options': question.options,
                        'correct_answer': question.correct_answer
                    })
                else:
                    # Generate a Fill-in-the-Blank using the LLM
                    question = generator.generate_fill_blank(topic, difficulty.lower())
                    self.questions.append({
                        'type': 'Fill in the Blank',
                        'question': question.question,
                        'correct_answer': question.answer
                    })
        except Exception as e:
            st.error(f"Error generating questions: {e}")
            return False
        return True

    # Renders the quiz UI in Streamlit and captures user answers
    def attempt_quiz(self):
        for i, q in enumerate(self.questions):
            st.markdown(f"**Question {i + 1}: {q['question']}**")

            if q['type'] == 'MCQ':
                # Show options for MCQ and capture selection
                user_answer = st.radio(
                    f"Select an answer for Question {i + 1}",
                    q['options'],
                    key=f"mcq_{i}"
                )
                self.user_answers.append(user_answer)
            else:
                # Capture text input for Fill-in-the-Blank
                user_answer = st.text_input(
                    f"Fill in the blank for Question {i + 1}",
                    key=f"fill_blank_{i}"
                )
                self.user_answers.append(user_answer)

    # Compares user answers with correct answers and stores results
    def evaluate_quiz(self):
        self.results = []
        for i, (q, user_ans) in enumerate(zip(self.questions, self.user_answers)):
            result_dict = {
                'question_number': i + 1,
                'question': q['question'],
                'question_type': q['type'],
                'user_answer': user_ans,
                'correct_answer': q['correct_answer'],
                'is_correct': False
            }

            # Determine correctness for MCQ or Fill-in-the-Blank
            if q['type'] == 'MCQ':
                result_dict['options'] = q['options']
                result_dict['is_correct'] = user_ans == q['correct_answer']
            else:
                result_dict['options'] = []
                result_dict['is_correct'] = user_ans.strip().lower() == q['correct_answer'].strip().lower()

            self.results.append(result_dict)

    # Converts the evaluation results into a DataFrame
    def generate_result_dataframe(self):
        if not self.results:
            return pd.DataFrame()
        return pd.DataFrame(self.results)

    # Saves the result DataFrame to a timestamped CSV file
    def save_to_csv(self, filename_prefix='quiz_results'):
        if not self.results:
            st.warning("No results to save. Please complete the quiz first.")
            return None

        df = self.generate_result_dataframe()
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{filename_prefix}_{timestamp}.csv"
        os.makedirs('results', exist_ok=True)
        full_path = os.path.join('results', unique_filename)
        try:
            df.to_csv(full_path, index=False)
            st.success(f"Results saved to {full_path}")
            return full_path
        except Exception as e:
            st.error(f"Failed to save results: {e}")
            return None
