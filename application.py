import os
import streamlit as st
import pandas as pd

from dotenv import load_dotenv  

load_dotenv()

# Import core logic classes and rerun utility
from src.utils.helpers import rerun, QuizManager

# Main Streamlit app logic
def main():
    st.set_page_config(page_title="Study Buddy AI", page_icon="📝")

    # Initialize session state variables if not already present
    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = QuizManager()
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'rerun_trigger' not in st.session_state:
        st.session_state.rerun_trigger = False  

    st.title("Study Buddy AI")

    # Sidebar input: quiz settings
    st.sidebar.header("Quiz Settings")

    # (Optional placeholder for multiple APIs in future)
    api_choice = st.sidebar.selectbox("Select API", ["Groq"], index=0)

    # Choose MCQ or Fill-in-the-Blank
    question_type = st.sidebar.selectbox(
        "Select Question Type", ["Multiple Choice", "Fill in the Blank"], index=0
    )

    # Input the topic for quiz generation
    topic = st.sidebar.text_input("Enter Topic", placeholder="Indian History, Geography, etc.")

    # Choose difficulty level
    difficulty = st.sidebar.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)

    # Set number of questions
    num_questions = st.sidebar.number_input(
        "Number of Questions", min_value=1, max_value=10, value=5
    )

    # Generate quiz button — creates questions using the QuestionGenerator
    if st.sidebar.button("Generate Quiz"):
        st.session_state.quiz_submitted = False
        from src.generator.question_generator import QuestionGenerator
        generator = QuestionGenerator()
        success = st.session_state.quiz_manager.generate_questions(
            generator, topic, question_type, difficulty, num_questions
        )
        st.session_state.quiz_generated = success
        rerun()  # Rerun to reflect changes in UI

    # If quiz was successfully generated, show it
    if st.session_state.quiz_generated and st.session_state.quiz_manager.questions:
        st.header("Quiz")
        st.session_state.quiz_manager.attempt_quiz()

        # Submit button: evaluates answers and displays results
        if st.button("Submit Quiz"):
            st.session_state.quiz_manager.evaluate_quiz()
            st.session_state.quiz_submitted = True
            rerun()

    # After submission, show results
    if st.session_state.quiz_submitted:
        st.header("Quiz Results")
        results_df = st.session_state.quiz_manager.generate_result_dataframe()

        if not results_df.empty:
            # Score summary
            correct_count = results_df['is_correct'].sum()
            total_questions = len(results_df)
            score_percentage = (correct_count / total_questions) * 100
            st.write(f"Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)")

            # Show detailed result for each question
            for _, result in results_df.iterrows():
                question_num = result['question_number']
                if result['is_correct']:
                    st.success(f"✅ Question {question_num}: {result['question']}")
                else:
                    st.error(f"❌ Question {question_num}: {result['question']}")
                    st.write(f"Your Answer: {result['user_answer']}")
                    st.write(f"Correct Answer: {result['correct_answer']}")

                st.markdown("---")

            # Option to save and download results
            if st.button("Save Results"):
                saved_file = st.session_state.quiz_manager.save_to_csv()
                if saved_file:
                    with open(saved_file, 'rb') as f:
                        st.download_button(
                            label="Download Results",
                            data=f.read(),
                            file_name=os.path.basename(saved_file),
                            mime='text/csv'
                        )
        else:
            st.warning("No results available. Please complete the quiz first.")

# Entry point
if __name__ == "__main__":
    main()