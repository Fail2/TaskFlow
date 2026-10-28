from datetime import date
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.task_models import TaskModel
from app.task_service import generate_tasks


@pytest.mark.anyio
async def test_generate_multiple_tasks(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    response = """
    [
        {
            "title": "Finish report",
            "description": "Complete the project report",
            "due_date": "2026-11-01",
            "priority": "high"
        },
        {
            "title": "Send email",
            "description": "Email the project update",
            "due_date": null,
            "priority": "medium"
        }
    ]
    """

    monkeypatch.setattr(
        "app.task_service.call_llm",
        AsyncMock(return_value=response),
    )

    with TestingSession() as db:
        tasks = await generate_tasks("Finish report and send an email", db)

        assert len(tasks) == 2
        assert tasks[0].title == "Finish report"
        assert tasks[1].title == "Send email"

        saved_tasks = db.scalars(select(TaskModel)).all()
        assert len(saved_tasks) == 2
        assert saved_tasks[0].priority == "high"
        assert saved_tasks[1].priority == "medium"

    Base.metadata.drop_all(bind=engine)
    engine.dispose()