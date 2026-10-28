from pyexpat.errors import messages

from fastapi import FastAPI, HTTPException
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.agent import build_graph, get_conversation_history


app = FastAPI(title="TaskFlow API")



class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank")

        return value



@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    thread_id = request.thread_id or str(uuid4())
    async with AsyncSqliteSaver.from_conn_string(
        "taskflow.db"
    ) as checkpointer:
        graph = build_graph(checkpointer)

        try:
            result = await graph.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": request.message,
                        }
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": thread_id
                    }
                },
            )
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="The AI service could not process your request.",
            ) from None

    return {
        "response": result["messages"][-1].content,
        "thread_id": thread_id,
    }


@app.get("/history/{thread_id}")
async def get_history(thread_id: str) -> dict:
    async with AsyncSqliteSaver.from_conn_string(
        "taskflow.db"
    ) as checkpointer:
        graph = build_graph(checkpointer)
        messages = await get_conversation_history(graph, thread_id)

        if not messages:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

    return {
        "thread_id": thread_id,
        "messages": [
            {
                "role": (
                    "user" if message.type == "human"
                    else "assistant" if message.type == "ai"
                    else message.type
                ),
                "content": message.content,
            }
            for message in messages
        ],
    }
