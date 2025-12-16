"""
OpenAI service utility for competitor research project.

This module provides a convenient interface for interacting with OpenAI's API.
"""

from django.conf import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service class for OpenAI API interactions."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from settings."""
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in Django settings")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def chat_completion(self, messages, model="gpt-4.1", **kwargs):
        """
        Create a chat completion using OpenAI's API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Example: [{"role": "user", "content": "Hello!"}]
            model: The model to use (default: "gpt-3.5-turbo")
            **kwargs: Additional parameters to pass to the API (temperature, max_tokens, etc.)
        
        Returns:
            The response object from OpenAI API
        
        Example:
            service = OpenAIService()
            response = service.chat_completion([
                {"role": "user", "content": "What is competitor research?"}
            ])
            print(response.choices[0].message.content)
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def get_text_completion(self, prompt, model="gpt-3.5-turbo", **kwargs):
        """
        Get a simple text completion from OpenAI.
        
        Args:
            prompt: The text prompt to send to the model
            model: The model to use (default: "gpt-3.5-turbo")
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            The generated text as a string
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, model=model, **kwargs)
        return response.choices[0].message.content
    
    def analyze_text(self, text, analysis_type="summary", **kwargs):
        """
        Analyze text using OpenAI.
        
        Args:
            text: The text to analyze
            analysis_type: Type of analysis (summary, sentiment, keywords, etc.)
            **kwargs: Additional parameters for the API
        
        Returns:
            The analysis result as a string
        """
        prompts = {
            "summary": f"Please provide a concise summary of the following text:\n\n{text}",
            "sentiment": f"Analyze the sentiment of the following text:\n\n{text}",
            "keywords": f"Extract the main keywords from the following text:\n\n{text}",
        }
        
        prompt = prompts.get(analysis_type, f"Analyze the following text:\n\n{text}")
        return self.get_text_completion(prompt, **kwargs)


# Convenience function to get a service instance
def get_openai_service():
    """Get an instance of OpenAIService."""
    return OpenAIService()

