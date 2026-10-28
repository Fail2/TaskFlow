import pytest   
from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4

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

    thread_id = f"api-conversation-test-{uuid4()}"

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

def test_chat_endpoint_generates_new_thread_id(monkeypatch):
    async def fake_call_llm(messages):
        return "Hello!"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    first = client.post("/chat", json={"message": "Hi"})
    second = client.post("/chat", json={"message": "Hello"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["thread_id"] != second.json()["thread_id"]


def test_get_conversation_history(monkeypatch):
    thread_id = f"history-test-{uuid4()}"

    async def fake_call_llm(messages):
        return "Hello from TaskFlow!"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    chat_response = client.post(
        "/chat",
        json={
            "message": "Hello",
            "thread_id": thread_id,
        },
    )
    assert chat_response.status_code == 200

    history_response = client.get(f"/history/{thread_id}")

    assert history_response.status_code == 200
    data = history_response.json()
    assert data["thread_id"] == thread_id
    assert data["messages"][-2]["content"] == "Hello"
    assert data["messages"][-1]["content"] == "Hello from TaskFlow!"

def test_get_conversation_history_returns_404():
    response = client.get(
        f"/history/nonexistent-{uuid4()}"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conversation not found"
    }


def test_generate_tasks(monkeypatch):
    async def fake_call_llm(messages):
        return """
        [
            {
                "title": "Prepare project report",
                "description": "Write the project report.",
                "due_date": null,
                "priority": "medium"
            }
        ]
        """

    monkeypatch.setattr("app.task_service.call_llm", fake_call_llm)

    response = client.post(
        "/tasks/generate",
        json={"prompt": "Prepare a project report"},
    )

    assert response.status_code == 200

    tasks = response.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Prepare project report"
    assert tasks[0]["priority"] == "medium"



def test_get_tasks():
    response = client.get("/tasks")

    assert response.status_code == 200
    assert "tasks" in response.json()
    assert isinstance(response.json()["tasks"], list)


def test_update_task(monkeypatch):
    async def fake_call_llm(messages):
        return """
        [
            {
                "title": "Prepare a project report",
                "description": "Write the project report",
                "due_date": null,
                "priority": "medium"
            }
        ]
        """

    monkeypatch.setattr(
        "app.task_service.call_llm",
        fake_call_llm,
    )

    create_response = client.post(
        "/tasks/generate",
        json={"prompt": "Prepare a project report"},
    )

    assert create_response.status_code == 200

    tasks_response = client.get("/tasks")
    tasks = tasks_response.json()["tasks"]
    task_id = tasks[-1]["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Updated project report",
            "description": "Finish the report",
            "due_date": "2026-10-30",
            "priority": "high",
            "status": "in_progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated project report"
    assert response.json()["description"] == "Finish the report"
    assert response.json()["due_date"] == "2026-10-30"
    assert response.json()["priority"] == "high"
    assert response.json()["status"] == "in_progress"


def test_delete_task(monkeypatch):
    async def fake_call_llm(messages):
        return """
        [
            {
                "title": "Task to delete",
                "description": "Test deleting a task",
                "due_date": null,
                "priority": "medium"
            }
        ]
        """

    monkeypatch.setattr("app.task_service.call_llm", fake_call_llm)

    create_response = client.post(
        "/tasks/generate",
        json={"prompt": "Create a task for deletion test"},
    )
    assert create_response.status_code == 200

    tasks_response = client.get("/tasks")
    tasks = tasks_response.json()["tasks"]
    task_id = tasks[-1]["id"]

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204

    tasks_response = client.get("/tasks")
    remaining_ids = [
        task["id"] for task in tasks_response.json()["tasks"]
    ]
    assert task_id not in remaining_ids
