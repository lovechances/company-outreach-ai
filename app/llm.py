from openai import OpenAI
from app.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def call_llm(prompt: str) -> str:
    response = client.responses.create(
        model=settings.OPENAI_MODEL,
        input=prompt,
    )
    return response.output_text