from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import json
from langchain_core.messages import AIMessage, ToolMessage
from datetime import date
from sqlalchemy.orm import Session
from app.task_service import (create_tasks, list_tasks, update_task, delete_task,)

from app.llm import call_llm, call_llm_with_tools


TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_tasks",
            "description": (
                "Create one or more tasks. Extract details from the user's "
                "prompt. Ask for clarification if the task itself is unclear. "
                "Use medium priority and null due_date when not specified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "due_date": {
                                    "type": ["string", "null"]
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "urgent"],
                                },
                            },
                            "required": ["title"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["tasks"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": (
                "Show all tasks by default, or find tasks matching a clear "
                "user query. Use this to identify a task before updating or deleting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": ["string", "null"]}
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": (
                "Update an existing task. First identify exactly one task. "
                "Only include fields the user wants to change. If multiple "
                "tasks match, ask the user which one."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": ["string", "null"]},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                    },
                },
                "required": ["task_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": (
                "Delete a task by its database ID. Identify the exact task "
                "first. Never guess when multiple tasks match; ask for clarification. "
                "Follow the app's deletion confirmation policy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"}
                },
                "required": ["task_id"],
                "additionalProperties": False,
            },
        },
    },
]


class AgentState(TypedDict):
    messages: Annotated[
        list[dict[str, str]],
        add_messages,
    ]



async def receive_message(state: AgentState, db: Session,) -> dict:
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

    system_prompt = {
        "role": "system",
        "content": (
            "You are TaskFlow, an AI task management assistant. "
            "You can create, list, update, and delete tasks using tools. "
            "A user message may request multiple operations. "
            "Complete all clear, requested operations. "
            
            "For updates and deletions, first use list_tasks to identify "
            "the exact existing task. Never guess when multiple tasks match. "
            "If multiple tasks match, show every matching task with its ID, "
            "title, due date, status, and priority. If a due date is missing, "
            "show 'No due date'. Then ask the user to select the task by ID. "

            "Before deleting any task, always ask for explicit confirmation. "
            "Show the selected task's ID, title, due date, status, and priority "
            "before asking for confirmation. If multiple tasks are selected, "
            "show all selected tasks with these details. "

            "Do not call delete_task until the user explicitly confirms the exact "
            "task IDs shown in the most recent deletion proposal. "
            "Treat a clear positive command that explicitly confirms the proposed "
            "deletion as confirmation, not only replies like 'yes' or 'confirm'. "
            "For example, 'yes, delete it' or 'delete task ID 5' may confirm the "
            "proposal if the task IDs match exactly. "
            "If the user says no or cancels, do not delete. "
            "Never interpret an unrelated request as confirmation. "

            "If the user selects task IDs, verify that those IDs correspond "
            "to the intended tasks before proposing deletion. If any ID is "
            "invalid or ambiguous, ask for clarification. "

            "If the user changes the request before confirming, do not treat "
            "that message as confirmation. Resolve the new request first. "

            "Do not claim an operation succeeded unless the tool confirms "
            "success. If clarification is needed, ask a clear question and "
            "wait for the user's answer before proceeding."
        ),
    }



    llm_messages.insert(0, system_prompt)

    print("Conversation messages:", len(messages))
    print("LLM input messages:", len(llm_messages))
    print(
        "Approx input characters:",
        sum(
            len(str(message.get("content", "")))
            for message in llm_messages
        ),
    )

    for _ in range(8):
        response = await call_llm_with_tools(
            llm_messages,
            TASK_TOOLS,
        )

        if not response.tool_calls:
            return {
                "messages": [
                    AIMessage(content=response.content or "")
                ]
            }

        tool_calls_data = []

        for tool_call in response.tool_calls:
            tool_calls_data.append({
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            })

        llm_messages.append({
            "role": "assistant",
            "content": response.content,
            "tool_calls": tool_calls_data,
        })

        for tool_call in response.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )
                result = execute_tool(db, tool_name, arguments)
            except (json.JSONDecodeError, TypeError, ValueError):
                result = {"error": "Invalid tool arguments"}

            llm_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

    return {
        "messages": [
            AIMessage(
                content=(
                    "I couldn't finish all requested operations in this turn. "
                    "Please try again."
                )
            )
        ]
    }



def get_tool_definition(tool_name: str) -> dict | None:
    for tool in TASK_TOOLS:
        if tool["function"]["name"] == tool_name:
            return tool

    return None


def task_to_dict(task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": (
            task.due_date.isoformat()
            if task.due_date
            else None
        ),
        "priority": task.priority,
        "status": task.status,
    }


def execute_tool(db: Session, tool_name: str, arguments: dict,) -> dict:
    if get_tool_definition(tool_name) is None:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        if tool_name == "create_tasks":
            tasks = create_tasks(db, arguments["tasks"])
            return {
                "created": [task_to_dict(task) for task in tasks]
            }

        if tool_name == "list_tasks":
            tasks = list_tasks(db, arguments.get("query"))
            return {
                "tasks": [task_to_dict(task) for task in tasks]
            }

        if tool_name == "update_task":
            task_id = arguments["task_id"]
            changes = {
                key: value
                for key, value in arguments.items()
                if key != "task_id"
            }

            if "due_date" in changes and changes["due_date"] is not None:
                changes["due_date"] = date.fromisoformat(
                    changes["due_date"]
                )

            task = update_task(db, task_id, changes)

            if task is None:
                return {"error": "Task not found"}

            return {"updated": task_to_dict(task)}

        if tool_name == "delete_task":
            deleted = delete_task(db, arguments["task_id"])

            if not deleted:
                return {"error": "Task not found"}

            return {
                "deleted": True,
                "task_id": arguments["task_id"],
            }

        return {"error": "Unsupported tool"}

    except (ValueError, KeyError, TypeError) as exc:
        db.rollback()
        return {"error": f"Invalid tool arguments: {exc}"}



def build_graph(checkpointer, db: Session | None = None):
    graph = StateGraph(AgentState)

    async def run_agent(state: AgentState) -> dict:
        if db is None:
            raise RuntimeError(
                "Database session is required to run the agent"
            )

        return await receive_message(state, db)

    graph.add_node("receive_message", run_agent)
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

    if not state.values:
        return []

    return state.values.get("messages", [])
