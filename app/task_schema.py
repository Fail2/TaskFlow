from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Task(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    due_date: date | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1)

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Prompt must not be blank")
        return value


class TaskUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    due_date: date | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    status: Literal["pending", "in_progress", "completed"] = "pending"

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title must not be blank")
        return value