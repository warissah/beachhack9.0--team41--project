from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.schemas.plan import PlanRequest
from app.schemas.chat import DraftPlanFields
from app.services.chat_pipeline import load_or_finalize_thread_plan, persist_plan_for_thread
from app.services.mock_plan import build_stub_plan


def test_persist_plan_for_thread_links_active_plan_and_user_phone() -> None:
    async def _run() -> None:
        db = object()
        request = PlanRequest(
            goal="do linkedlists assignment",
            horizon="today",
            available_minutes=30,
            energy="medium",
        )
        plan = build_stub_plan(request.goal)

        with patch(
            "app.services.chat_pipeline.get_user_by_id",
            AsyncMock(return_value={"user_id": "user-123", "phone": "+15551234567"}),
        ):
            with patch(
                "app.services.chat_pipeline.insert_plan",
                AsyncMock(),
            ) as insert_plan:
                with patch(
                    "app.services.chat_pipeline.set_active_plan_id",
                    AsyncMock(),
                ) as set_active_plan_id:
                    await persist_plan_for_thread(
                        db,
                        "wa-user-123",
                        request,
                        plan,
                        user_id="user-123",
                    )

        insert_plan.assert_awaited_once()
        _, kwargs = insert_plan.await_args
        assert kwargs["user_id"] == "user-123"
        assert kwargs["user_phone"] == "+15551234567"
        set_active_plan_id.assert_awaited_once_with(db, "wa-user-123", plan.plan_id)

    asyncio.run(_run())


def test_load_or_finalize_thread_plan_reuses_linked_saved_plan_when_draft_matches() -> None:
    async def _run() -> None:
        db = object()
        plan = build_stub_plan("do linkedlists assignment")
        thread_doc = {
            "thread_id": "wa-user-123",
            "draft": DraftPlanFields(
                goal="do linkedlists assignment",
                horizon="today",
                available_minutes=30,
                energy="medium",
            ).model_dump(),
            "messages": [],
            "active_plan_id": plan.plan_id,
        }
        saved_plan_doc = {
            "plan_id": plan.plan_id,
            "goal": "do linkedlists assignment",
            "plan": plan.model_dump(mode="json"),
        }

        with patch(
            "app.services.chat_pipeline.get_thread",
            AsyncMock(return_value=thread_doc),
        ):
            with patch(
                "app.services.chat_pipeline.get_active_plan_id_for_thread",
                AsyncMock(return_value=plan.plan_id),
            ):
                with patch(
                    "app.services.chat_pipeline.get_plan_by_plan_id",
                    AsyncMock(return_value=saved_plan_doc),
                ):
                    with patch(
                        "app.services.chat_pipeline.persist_plan_for_thread",
                        AsyncMock(),
                    ) as persist_plan:
                        loaded_plan, created_new = await load_or_finalize_thread_plan(
                            db,
                            "wa-user-123",
                            user_id="user-123",
                            reuse_linked_plan=True,
                        )

        assert created_new is False
        assert loaded_plan.plan_id == plan.plan_id
        persist_plan.assert_not_awaited()

    asyncio.run(_run())
