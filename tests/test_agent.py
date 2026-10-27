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