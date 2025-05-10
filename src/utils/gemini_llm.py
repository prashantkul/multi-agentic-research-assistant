"""Gemini LLM utility module."""
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.env import config

class GeminiLLM:
    """Utility class for Gemini LLM integration."""
    
    @staticmethod
    def initialize():
        """Initialize the Gemini API."""
        genai.configure(api_key=config.GOOGLE_API_KEY)
    
    @staticmethod
    def get_llm():
        """Get a configured LangChain chat model for Gemini."""
        GeminiLLM.initialize()
        
        return ChatGoogleGenerativeAI(
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_TOKENS,
            convert_system_message_to_human=True,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )