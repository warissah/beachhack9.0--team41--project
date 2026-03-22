from typing import Any

from app.services.mock_logic import handle_done, handle_stuck, handle_unknown
from app.services.mock_plan import build_stub_plan


def _extract_first_step(plan: Any) -> str | None:
    """
    Safely extract the first step from different possible PlanResponse shapes.
    Works whether build_stub_plan returns:
    - a Pydantic model
    - a dict
    - steps as strings
    - steps as objects/dicts with title/text/description
    """
    if plan is None:
        return None

    # Pydantic model -> dict
    if hasattr(plan, "model_dump"):
        data = plan.model_dump()
    elif isinstance(plan, dict):
        data = plan
    else:
        data = None

    # Case 1: dict-like object with a steps list
    if isinstance(data, dict):
        steps = data.get("steps") or data.get("tasks") or data.get("subtasks") or []
        if steps:
            first = steps[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                return (
                    first.get("title")
                    or first.get("text")
                    or first.get("description")
                    or first.get("task")
                )

    # Case 2: object with steps/tasks/subtasks attributes
    for attr in ("steps", "tasks", "subtasks"):
        if hasattr(plan, attr):
            steps = getattr(plan, attr) or []
            if steps:
                first = steps[0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict):
                    return (
                        first.get("title")
                        or first.get("text")
                        or first.get("description")
                        or first.get("task")
                    )
                for field in ("title", "text", "description", "task"):
                    if hasattr(first, field):
                        value = getattr(first, field)
                        if value:
                            return str(value)

    return None


def get_whatsapp_reply(user_id: str, command: str) -> str:
    try:
        if command == "start":
            plan = build_stub_plan("Help me get started on my task.")
            first_step = _extract_first_step(plan)

            if first_step:
                return f"Start here: {first_step}"

            return "Start here: do the smallest possible first step."

        if command == "stuck":
            return handle_stuck(user_id)

        if command == "done":
            return handle_done(user_id)

        return handle_unknown()

    except Exception as e:
        print(f"[WhatsApp Error] {e}")
        return "Something went wrong on our side. Please try again."