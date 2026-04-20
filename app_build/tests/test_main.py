import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app_build.main import app

client = TestClient(app)

def test_read_root():
    """Test the root redirection."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@patch("app_build.main.generate_response")
@patch("app_build.main.save_chat_history")
@patch("app_build.main.log_event")
def test_chat_endpoint_success(mock_log, mock_save, mock_generate):
    """Test the successful execution of the chat path."""
    mock_generate.return_value = "This is a mock response from the LLM."
    
    response = client.post(
        "/api/chat",
        json={"message": "Hello, bot!"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"reply": "This is a mock response from the LLM."}
    
    mock_generate.assert_called_once_with("Hello, bot!")
    mock_save.assert_called_once_with("Hello, bot!", "This is a mock response from the LLM.")
    mock_log.assert_called_once_with("chat_interaction", {"message_length": 11})

def test_chat_endpoint_empty_message():
    """Test the API defense against empty packets."""
    response = client.post(
        "/api/chat",
        json={"message": "   "}
    )
    # The Pydantic validator drops the bad request before routing, yielding a 422 Unprocessable Entity
    # Alternatively our strip validation catches it and yields 400.
    assert response.status_code in [400, 422]

@patch("app_build.main.generate_response")
def test_chat_endpoint_internal_error(mock_generate):
    """Test standard 500 error abstraction to prevent secret leakage."""
    # Simulate a Vertex AI Failure
    mock_generate.side_effect = RuntimeError("Mock DB or LLM crash")
    
    response = client.post(
        "/api/chat",
        json={"message": "Crash the system"}
    )
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error while processing the request."}

def test_security_headers():
    """Verify security headers are attached implicitly via middleware."""
    response = client.get("/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
