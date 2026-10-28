from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.llm import call_llm


class AgentState(TypedDict):
    messages: Annotated[
        list[dict[str, str]],
        add_messages,
    ]


async def receive_message(state: AgentState) -> dict:
    messages = state["messages"]

    if not messages:
        raise ValueError("At least one message is required")

    llm_messages = [
        {
            "role": (
                "user"
                if message.type == "human"
                else "assistant"
                if message.type == "ai"
                else message.type
            ),
            "content": message.content,
        }
        if hasattr(message, "type")
        else message
        for message in messages
    ]

    response = await call_llm(llm_messages)

    return {
        "messages": messages + [
            {"role": "assistant", "content": response}
        ]
    }

def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("receive_message", receive_message)
    graph.add_edge(START, "receive_message")
    graph.add_edge("receive_message", END)

    return graph.compile(checkpointer=checkpointer)


async def get_conversation_history(graph, thread_id: str) -> list:
    state = await graph.aget_state(
        {
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return state.values.get("messages", [])