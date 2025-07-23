# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration settings for the Flask application.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_please_change_this_in_production'
    # Fallback secret key for development, CHANGE THIS IN PRODUCTION
    
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Model to use for the chatbot from OpenRouter
    # You can change this to any model supported by OpenRouter
    # Example: "openai/gpt-3.5-turbo", "openai/gpt-4", "mistralai/mistral-7b-instruct-v0.2", etc.
    OPENROUTER_MODEL = "openai/gpt-3.5-turbo" # Default model

    # Database paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    USER_DB_PATH = os.path.join(DATABASE_DIR, 'User_details.db')
    CHAT_DB_PATH = os.path.join(DATABASE_DIR, 'Chat_history.db')

    # Ensure the database directory exists
    os.makedirs(DATABASE_DIR, exist_ok=True)
