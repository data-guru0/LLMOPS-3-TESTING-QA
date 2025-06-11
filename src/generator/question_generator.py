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

# Import necessary tools and modules
from langchain.output_parsers import PydanticOutputParser  # Helps convert LLM text output into structured Python objects
from src.models.question_schemas import MCQQuestion, FillBlankQuestion  # Defines the structure (schema) for MCQ and Fill-in-the-Blank questions
from src.prompts.templates import mcq_prompt_template, fill_blank_prompt_template  # Templates that tell the LLM how to format its answers
from src.llm.groq_client import get_groq_llm  # Function to connect and get access to the Groq LLM
from src.config.settings import settings  # App settings, like number of retry attempts and model configs
from src.common.logger import get_logger  # Function to create a logger for printing messages
from src.common.custom_exception import CustomException  # Custom error type to handle failures in a readable way

# Main class that generates quiz questions using a language model (LLM)
class QuestionGenerator:
    def __init__(self):
        # Create an instance of the language model and a logger
        self.llm = get_groq_llm()  # This connects to Groq's LLM (like LLaMA)
        self.logger = get_logger(self.__class__.__name__)  # Logger will use the class name (QuestionGenerator)

    # Private helper method to send the prompt to the LLM, parse the response, and retry if something goes wrong
    def _retry_and_parse(self, prompt, parser, topic, difficulty):
        # Try the generation up to MAX_RETRIES times
        for attempt in range(settings.MAX_RETRIES):
            try:
                self.logger.info(f"Attempt {attempt + 1}: Generating question for topic='{topic}', difficulty='{difficulty}'")
                
                # Fill in the topic and difficulty in the prompt and send it to the LLM
                response = self.llm.invoke(prompt.format(topic=topic, difficulty=difficulty))
                
                # Use the parser to convert the response text into a Python object based on the defined schema
                parsed = parser.parse(response.content)

                self.logger.info(f"Successfully parsed question on attempt {attempt + 1}")
                return parsed  # Return the parsed (valid) question
            except Exception as e:
                # If something goes wrong, log the error
                self.logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                # If this is the last attempt, raise a custom exception
                if attempt == settings.MAX_RETRIES - 1:
                    raise CustomException(f"Generation failed after {settings.MAX_RETRIES} attempts", e)

    # Public method to generate a Multiple Choice Question
    def generate_mcq(self, topic: str, difficulty: str = 'medium') -> MCQQuestion:
        try:
            # Set up the output parser for MCQ question format
            parser = PydanticOutputParser(pydantic_object=MCQQuestion)
            
            # Generate the question and parse it using retry logic
            question = self._retry_and_parse(mcq_prompt_template, parser, topic, difficulty)

            # Extra check: MCQ must have exactly 4 options, and correct answer should be one of them
            if len(question.options) != 4 or question.correct_answer not in question.options:
                raise ValueError("Invalid MCQ structure")

            self.logger.info(f"Generated valid MCQ question for topic '{topic}'")
            return question  # Return the valid MCQ question
        except Exception as e:
            # Log and raise a custom error if something goes wrong
            self.logger.error(f"Failed to generate MCQ question: {str(e)}")
            raise CustomException("MCQ question generation failed", e)

    # Public method to generate a Fill-in-the-Blank question
    def generate_fill_blank(self, topic: str, difficulty: str = 'medium') -> FillBlankQuestion:
        try:
            # Set up the output parser for Fill-in-the-Blank question format
            parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)
            
            # Generate the question and parse it using retry logic
            question = self._retry_and_parse(fill_blank_prompt_template, parser, topic, difficulty)

            # Extra check: The question must have a blank represented by "_____"
            if "_____" not in question.question:
                raise ValueError("Fill-in-the-blank must contain '_____'")

            self.logger.info(f"Generated valid Fill-in-the-Blank question for topic '{topic}'")
            return question  # Return the valid Fill-in-the-Blank question
        except Exception as e:
            # Log and raise a custom error if something goes wrong
            self.logger.error(f"Failed to generate Fill-in-the-Blank question: {str(e)}")
            raise CustomException("Fill-in-the-Blank question generation failed", e)
