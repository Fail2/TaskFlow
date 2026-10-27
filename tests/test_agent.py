import asyncio

import pytest

from app.agent import build_graph


def test_agent_rejects_empty_messages():
    graph = build_graph()

    with pytest.raises(
        ValueError,
        match="At least one message is required",
    ):
        asyncio.run(
            graph.ainvoke({"messages": []})
        )


def test_agent_returns_assistant_response(monkeypatch):
    async def fake_call_llm(messages):
        return "TaskFlow test response"

    monkeypatch.setattr(
        "app.agent.call_llm",
        fake_call_llm,
    )

    graph = build_graph()

    result = asyncio.run(
        graph.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )
    )

    assert result["messages"][-1] == {
        "role": "assistant",
        "content": "TaskFlow test response",
    }
