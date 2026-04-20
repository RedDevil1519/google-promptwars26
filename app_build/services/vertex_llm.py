import os
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession

# Global variables for caching
_bot_chat: ChatSession | None = None
_mock_mode = False

def get_chat_session():
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
        
    # Initialize the Vertex AI client
    vertexai.init(project=project_id, location=location)
    
    # We use gemini-1.5-flash for faster responsiveness as an AI assistant
    model = GenerativeModel("gemini-1.5-flash")
    
    _bot_chat = model.start_chat()
    return _bot_chat

async def generate_response(user_message: str) -> str:
    """Sends a message to the Vertex AI Chat Session and returns the response."""
    try:
        chat = get_chat_session()
        
        # Local verification mode
        if _mock_mode:
            return f"[MOCK MODE - Vertex AI not initialized] I received your message: '{user_message}'. Ensure GOOGLE_CLOUD_PROJECT is exported in your terminal for real responses!"
            
        # Security guardrail: user_message is pre-validated in the router
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        # Add basic abstraction over the exception; avoid leaking credentials
        raise RuntimeError(f"Vertex AI interaction failed: {str(e)}")
