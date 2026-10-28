
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    due_date: date | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
