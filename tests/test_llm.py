
import asyncio

from app.llm import call_llm


async def main():
    messages = [
        {
            "role": "user",
            "content": "Reply with exactly: TaskFlow LLM connection successful!",
        }
    ]

    response = await call_llm(messages)
    print("LLM response:", response)


if __name__ == "__main__":
    asyncio.run(main())
