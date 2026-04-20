import os
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession

# Global variables for caching
_bot_chat: Optional[ChatSession] = None
_mock_mode: bool = False

def get_chat_session() -> Optional[ChatSession]:
    """
    Initializes and returns the Vertex AI ChatSession singleton.
    Falls back to mock mode if environment configurations are absent.
    
    Returns:
        Optional[ChatSession]: The active chat session object, or None if in mock mode.
    """
    global _bot_chat, _mock_mode
    if _bot_chat is not None or _mock_mode:
        return _bot_chat

    # Security Guardrail: Validate environment variables exist without hardcoding
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    
    if not project_id or project_id == "your-project-id" or not location:
        # Fallback to mock mode for local browser testing 
        # when ADC or ENV vars are not fully configured.
        _mock_mode = True
        return None
        
    # Initialize the Vertex AI client securely
    vertexai.init(project=project_id, location=location)
    
    # We use gemini-1.5-flash for faster responsiveness as an AI assistant
    model = GenerativeModel("gemini-1.5-flash")
    
    _bot_chat = model.start_chat()
    return _bot_chat

async def generate_response(user_message: str) -> str:
    """
    Sends a validated user message to the Vertex AI model and returns the text response.
    
    Args:
        user_message (str): The prompt submitted by the user.
        
    Returns:
        str: The AI's generated reply.
        
    Raises:
        RuntimeError: If the Vertex AI service fails to generate a response.
    """
    try:
        chat = get_chat_session()
        
        # Local verification mode
        if _mock_mode or chat is None:
            return f"[MOCK MODE - Vertex AI not initialized] I received your message: '{user_message}'. Ensure GOOGLE_CLOUD_PROJECT is exported in your terminal for real responses!"
            
        # Security guardrail: user_message is pre-validated in the router
        response = chat.send_message(user_message)
        return str(response.text)
    except Exception as e:
        error_msg = str(e).lower()
        if "billing" in error_msg or "403" in error_msg or "permissiondenied" in error_msg:
            return f"[BILLING DISABLED - Fallback Mode] I received your message: '{user_message}'. I am temporarily returning this fallback because Vertex AI requires an active Google Cloud Billing account associated with your project."
        # Add basic abstraction over the exception; avoid leaking credentials
        raise RuntimeError(f"Vertex AI interaction failed: {str(e)}")
