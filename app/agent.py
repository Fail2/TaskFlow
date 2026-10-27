
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class AgentState(TypedDict):
    messages: list[dict[str, str]]


def receive_message(state: AgentState) -> dict:
    return {"messages": state["messages"]}


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("receive_message", receive_message)
    graph.add_edge(START, "receive_message")
    graph.add_edge("receive_message", END)

    return graph.compile()
