from openai import AsyncOpenAI

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def create_llm_client() -> AsyncOpenAI:
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY is not configured")

    return AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )


async def call_llm(messages: list[dict[str, str]]) -> str:
    client = create_llm_client()

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
        )
        content = response.choices[0].message.content

        if content is None:
            raise ValueError("LLM returned an empty response")

        return content
    finally:
        await client.close()


async def call_llm_with_tools(messages: list[dict],tools: list[dict],) :
    client = create_llm_client()

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        return response.choices[0].message
    finally:
        await client.close()
