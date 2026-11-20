import os
from agents import Agent, Runner
from config import gemini_model

print("Model:", os.getenv("GEMINI_MODEL"))
agent = Agent(name="Test", instructions="Roman Urdu mein jawab do.", model=gemini_model)
result = Runner.run_sync(agent, "Salam, 1 line mein hello bolo")
print("Reply:", repr(result.final_output))