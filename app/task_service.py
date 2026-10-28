from sqlalchemy.orm import Session
from pydantic import TypeAdapter

from app.llm import call_llm
from app.task_schema import Task
from app.task_models import TaskModel


async def generate_tasks(prompt: str, db: Session) -> list[Task]:
    messages = [
        {
            "role": "system",
            "content": (
                "Extract all distinct tasks from the user's prompt. "
                "Return only a valid JSON array. "
                "Each task must contain title, description, due_date, and priority. "
                "For title, write a short, clear task name. "
                "For description, explain what needs to be done using the details "
                "provided by the user. Write a useful one-sentence description. "
                "Do not leave description empty unless the user provides no useful "
                "details beyond the task title. Never invent details. "
                "Understand dates in different formats, including today, tomorrow, "
                "next Monday, 30 October 2026, 30/10/2026, and 2026-10-30. "
                "Convert known due dates to YYYY-MM-DD format. "
                "If a date is ambiguous, use null rather than guessing. "
                "Use null when no due date is mentioned. "
                "Use medium priority by default. "
                "Use urgent only when explicitly requested or for a clear emergency. "
                "Priority must be low, medium, high, or urgent."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response = await call_llm(messages)
    tasks = TypeAdapter(list[Task]).validate_json(response)

    for task in tasks:
        db.add(
            TaskModel(
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                priority=task.priority,
                status="pending",
            )
        )

    db.commit()
    return tasks