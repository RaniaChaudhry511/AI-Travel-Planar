import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

set_tracing_disabled(True)

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    openai_client=client,
)
