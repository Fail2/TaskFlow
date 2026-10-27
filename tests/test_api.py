
from urllib import response

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_endpoint(monkeypatch):
    async def fake_call_llm(messages):
        return "TaskFlow API test successful!"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    response = client.post(
        "/chat",
        json={"message": "Hello TaskFlow!"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == "TaskFlow API test successful!"
    assert isinstance(response.json()["thread_id"], str)
    assert response.json()["thread_id"]


def test_chat_endpoint_rejects_missing_message():
    response = client.post(
        "/chat",
        json={},
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_empty_message():
    response = client.post(
        "/chat",
        json={"message": ""},
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_whitespace_message():
    response = client.post(
        "/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422

def test_chat_endpoint_returns_502_when_llm_fails(monkeypatch):
    async def fake_call_llm(messages):
        raise RuntimeError("Provider unavailable")

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    error_client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = error_client.post(
        "/chat",
        json={"message": "Hello"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The AI service could not process your request."
    }


def test_chat_endpoint_preserves_conversation_history(monkeypatch):
    async def fake_call_llm(messages):
        return f"Received {len(messages)} messages"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    thread_id = "api-conversation-test"

    first_response = client.post(
        "/chat",
        json={
            "message": "Hello!",
            "thread_id": thread_id,
        },
    )

    second_response = client.post(
        "/chat",
        json={
            "message": "How are you?",
            "thread_id": thread_id,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["thread_id"] == thread_id
    assert second_response.json()["thread_id"] == thread_id
    assert second_response.json()["response"] == "Received 3 messages"
