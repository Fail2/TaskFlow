from pyexpat.errors import messages
from fastapi import FastAPI, HTTPException, Depends, Response
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.agent import build_graph, get_conversation_history
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import SessionLocal, engine, Base
from app.task_models import TaskModel
from app.task_service import generate_tasks
from app.task_schema import TaskRequest, TaskUpdateRequest
from pathlib import Path

app = FastAPI(title="TaskFlow API")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DB = str(DATA_DIR / "taskflow.db")


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tasks/generate")
async def create_tasks(request: TaskRequest, db: Session = Depends(get_db),) -> dict:
    tasks = await generate_tasks(request.prompt, db)

    return {
        "tasks": [task.model_dump(mode="json") for task in tasks]
    }

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)) -> dict:
    tasks = db.scalars(
        select(TaskModel).order_by(TaskModel.id)
    ).all()

    return {
        "tasks": [
            {
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
            for task in tasks
        ]
    }

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db),) -> Response:
    task = db.get(TaskModel, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()

    return Response(status_code=204)

@app.put("/tasks/{task_id}")
def update_task(task_id: int, request: TaskUpdateRequest, db: Session = Depends(get_db),) -> dict:
    task = db.get(TaskModel, task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = request.title
    task.description = request.description
    task.due_date = request.due_date
    task.priority = request.priority
    task.status = request.status

    db.commit()
    db.refresh(task)

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "priority": task.priority,
        "status": task.status,
    }

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
        CHECKPOINT_DB
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
        CHECKPOINT_DB
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
