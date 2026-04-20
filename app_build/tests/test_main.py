import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app_build.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # Following the redirect, the URL should eventually point to static files or serve them.
    # The TestClient automatically follows redirects.
    assert "text/html" in response.headers["content-type"]

@patch("app_build.main.generate_response")
@patch("app_build.main.save_chat_history")
@patch("app_build.main.log_event")
def test_chat_endpoint(mock_log, mock_save, mock_generate):
    # Mock the LLM response
    mock_generate.return_value = "This is a mock response from the LLM."
    
    # Send a request to the chat endpoint
    response = client.post(
        "/api/chat",
        json={"message": "Hello, bot!"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"reply": "This is a mock response from the LLM."}
    
    # Verify that the mocked functions were called correctly
    mock_generate.assert_called_once_with("Hello, bot!")
    mock_save.assert_called_once_with("Hello, bot!", "This is a mock response from the LLM.")
    mock_log.assert_called_once_with("chat_interaction", {"message_length": 11})

def test_chat_endpoint_empty_message():
    response = client.post(
        "/api/chat",
        json={"message": ""}
    )
    # Pydantic validation should block empty messages (max_length/min_length configured)
    assert response.status_code == 422 # Unprocessable Entity
