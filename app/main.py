
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from app.agent import build_graph


app = FastAPI(title="TaskFlow API")



class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank")

        return value



@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    graph = build_graph()

    result = await graph.ainvoke(
        {
            "messages": [
                {"role": "user", "content": request.message}
            ]
        }
    )

    return {
        "response": result["messages"][-1]["content"]
    }
