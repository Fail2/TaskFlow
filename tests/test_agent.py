import asyncio

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.agent import build_graph


def test_agent_rejects_empty_messages():
    graph = build_graph(InMemorySaver())

    with pytest.raises(
        ValueError,
        match="At least one message is required",
    ):
        asyncio.run(
            graph.ainvoke(
                {"messages": []},
                config={
                    "configurable": {
                        "thread_id": "empty-test-thread"
                    }
                },
            )
        )


def test_agent_returns_assistant_response(monkeypatch):
    async def fake_call_llm(messages):
        return "TaskFlow test response"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    graph = build_graph(InMemorySaver())

    result = asyncio.run(
        graph.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            },
            config={
                "configurable": {
                    "thread_id": "test-thread"
                }
            },
        )
    )

    assert result["messages"][-1].content == "TaskFlow test response"

def test_agent_preserves_conversation_history(monkeypatch):
    async def fake_call_llm(messages):
        return f"Received {len(messages)} messages"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    graph = build_graph(InMemorySaver())
    config = {
        "configurable": {
            "thread_id": "conversation-test"
        }
    }

    first_result = asyncio.run(
        graph.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            },
            config=config,
        )
    )

    second_result = asyncio.run(
        graph.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "How are you?"}
                ]
            },
            config=config,
        )
    )

    assert len(first_result["messages"]) == 2
    assert len(second_result["messages"]) == 4
    assert second_result["messages"][-1].content == "Received 3 messages"