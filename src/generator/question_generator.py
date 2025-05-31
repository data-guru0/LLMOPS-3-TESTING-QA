"""
Overall Purpose:
---------------
This module defines the `QuestionGenerator` class that automatically generates quiz questions 
(Multiple Choice Questions and Fill-in-the-Blank) using a large language model (LLM) like Groq's LLaMA.

Here's what's happening:
- Prompts are sent to an LLM (e.g., LLaMA 3 via Groq).
- The response is parsed into structured question formats using Pydantic models.
- There is built-in error handling and retry logic to ensure reliable generation.
- It logs the progress and errors using a custom logger.
- It uses custom exceptions to handle any failures cleanly.

The main goal: to programmatically generate and validate high-quality quiz questions from a given topic and difficulty level.
"""
from langchain.output_parsers import PydanticOutputParser  # Parses LLM output into structured Pydantic models
from src.models.question_schemas import MCQQuestion, FillBlankQuestion  # Data models for questions
from src.prompts.templates import mcq_prompt_template, fill_blank_prompt_template  # Prompt templates for question generation
from src.llm.groq_client import get_groq_llm  # Function to initialize and return the Groq LLM client
from src.config.settings import settings  # Configuration settings like retries and model name
from src.common.logger import get_logger  # Logger utility for logging information and errors
from src.common.custom_exception import CustomException  # Custom exception class for error handling

# Class to generate quiz questions using an LLM (e.g., Groq with LLaMA model)
class QuestionGenerator:
    def __init__(self):
        # Initialize the LLM and logger
        self.llm = get_groq_llm()
        self.logger = get_logger(self.__class__.__name__)

    # Private method to call the LLM, retry if needed, and parse output
    def _retry_and_parse(self, prompt, parser, topic, difficulty):
        for attempt in range(settings.MAX_RETRIES):  # Try up to MAX_RETRIES times
            try:
                self.logger.info(f"Attempt {attempt + 1}: Generating question for topic='{topic}', difficulty='{difficulty}'")
                
                # Invoke the LLM with the formatted prompt
                response = self.llm.invoke(prompt.format(topic=topic, difficulty=difficulty))
                
                # Parse the output using the Pydantic parser
                parsed = parser.parse(response.content)
                self.logger.info(f"Successfully parsed question on attempt {attempt + 1}")
                return parsed  # Return the valid parsed question
            except Exception as e:
                # Log the error and retry if attempts are left
                self.logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt == settings.MAX_RETRIES - 1:
                    # Raise a custom exception after the final failed attempt
                    raise CustomException(f"Generation failed after {settings.MAX_RETRIES} attempts", e)

    # Public method to generate a Multiple Choice Question (MCQ)
    def generate_mcq(self, topic: str, difficulty: str = 'medium') -> MCQQuestion:
        try:
            parser = PydanticOutputParser(pydantic_object=MCQQuestion)  # Set up the parser for MCQs
            question = self._retry_and_parse(mcq_prompt_template, parser, topic, difficulty)  # Generate and parse

            # Validate structure: must have 4 options and the correct answer must be one of them
            if len(question.options) != 4 or question.correct_answer not in question.options:
                raise ValueError("Invalid MCQ structure")

            self.logger.info(f"Generated valid MCQ question for topic '{topic}'")
            return question
        except Exception as e:
            self.logger.error(f"Failed to generate MCQ question: {str(e)}")
            raise CustomException("MCQ question generation failed", e)

    # Public method to generate a Fill-in-the-Blank question
    def generate_fill_blank(self, topic: str, difficulty: str = 'medium') -> FillBlankQuestion:
        try:
            parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)  # Set up the parser for fill-in-the-blanks
            question = self._retry_and_parse(fill_blank_prompt_template, parser, topic, difficulty)  # Generate and parse

            # Ensure the question contains a blank space represented by "_____"
            if "_____" not in question.question:
                raise ValueError("Fill-in-the-blank must contain '_____'")

            self.logger.info(f"Generated valid Fill-in-the-Blank question for topic '{topic}'")
            return question
        except Exception as e:
            self.logger.error(f"Failed to generate Fill-in-the-Blank question: {str(e)}")
            raise CustomException("Fill-in-the-Blank question generation failed", e)
