import os 
from dotenv import load_dotenv  

load_dotenv()

# Define a class to store configuration settings
class Settings:
    # Get the GROQ API key from the environment variables
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Set the model name to be used (e.g., LLaMA 3.1 - 8B Instant)
    MODEL_NAME = "llama-3.1-8b-instant"
    
    # Define the temperature for response randomness (higher = more creative)
    TEMPERATURE = 0.9
    
    # Set the maximum number of retries for API calls if they fail
    MAX_RETRIES = 3

# Create an instance of the Settings class to use its values throughout the project
settings = Settings()
