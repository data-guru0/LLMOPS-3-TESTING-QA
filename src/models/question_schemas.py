# Import necessary typing and validation tools
from typing import List  # Used to specify that 'options' is a list of strings
from pydantic import BaseModel, Field, validator  # Used to define and validate structured data models
# -----------------------------
# Model for Multiple Choice Question (MCQ)
# -----------------------------
class MCQQuestion(BaseModel):
    # The actual question text (e.g., "What is the capital of France?")
    question: str = Field(description="The question text")

    # A list of 4 answer choices (e.g., ["Paris", "Berlin", "Rome", "Madrid"])
    options: List[str] = Field(description="List of 4 possible answers")

    # The correct answer from the above options (e.g., "Paris")
    correct_answer: str = Field(description="The correct answer from the options")

    # Validator to clean or fix the question input before assigning it
    @validator('question', pre=True)
    def clean_question(cls, v):
        # If the question is passed as a dictionary (e.g., {"description": "What is..."}), extract the text
        if isinstance(v, dict):
            return v.get('description', str(v))  # Get the 'description' key, or convert dict to string
        return str(v)  # Otherwise, just make sure it is a string

# -----------------------------
# Model for Fill-in-the-Blank Question
# -----------------------------
class FillBlankQuestion(BaseModel):
    # The question with a blank (e.g., "The capital of France is _____")
    question: str = Field(description="The question text with '_____' for the blank")

    # The correct answer to fill in the blank (e.g., "Paris")
    answer: str = Field(description="The correct word or phrase for the blank")

    # Validator to clean or fix the question input before assigning it
    @validator('question', pre=True)
    def clean_question(cls, v):
        # If the question is passed as a dictionary, extract the 'description' field
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)
