import asyncio
import time

from agents import Runner, SQLiteSession
from agents.exceptions import AgentsException
from openai import OpenAIError

from agent import agent


def _print_exception(exc: Exception) -> None:
    print(f"Exception type: {type(exc).__name__}")
    print(f"Exception message: {exc}")

    response = getattr(exc, "response", None)
    if response is not None:
        response_text = getattr(response, "text", None)
        if response_text is not None:
            print(f"Response text: {response_text}")

    body = getattr(exc, "body", None)
    if body is not None:
        print(f"Exception body: {body}")


def _is_retryable(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    status_code = getattr(exc, "status_code", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    if status_code in (500, 503):
        return True

    details = " ".join(
        str(value)
        for value in (exc, getattr(response, "text", None), getattr(exc, "body", None))
        if value is not None
    ).lower()
    return any(marker in details for marker in ("overloaded", "high demand", "500", "503"))


def main() -> None:
    session = SQLiteSession("travel-planner-cli", "travel_history.db")
    print("Travel Planner is ready. Type 'exit' to quit.")
    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if message.lower() == "exit":
            print("Goodbye!")
            break
        if not message:
            continue

        completed = False
        for attempt in range(3):
            try:
                result = asyncio.run(
                    asyncio.wait_for(
                        Runner.run(agent, message, session=session),
                        timeout=60,
                    )
                )
                completed = True
                break
            except (AgentsException, OpenAIError) as exc:
                _print_exception(exc)
                if _is_retryable(exc) and attempt < 2:
                    print(f"Temporary Gemini server error; retrying in 5 seconds ({attempt + 2}/3).")
                    time.sleep(5)
                    continue
                break
            except TimeoutError as exc:
                _print_exception(exc)
                break

        if not completed:
            continue
        print(f"\nTravel Planner: {result.final_output}")


if __name__ == "__main__":
    main()
