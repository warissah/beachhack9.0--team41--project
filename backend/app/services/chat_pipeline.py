"""Orchestration for chat → draft → finalize (reuses generate_plan only on finalize)."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.chat_threads import (
    append_message_pair,
    create_thread,
    draft_from_doc,
    ensure_thread,
    get_active_plan_id_for_thread,
    get_thread,
    merge_draft,
    save_thread,
    set_active_plan_id,
    transcript_for_prompt,
)
from app.db.plans import get_plan_by_plan_id, insert_plan, plan_response_from_doc
from app.db.users import get_user_by_id
from app.schemas.chat import ChatMessageResponse, DraftPlanFields
from app.schemas.plan import PlanRequest, PlanResponse
from app.services.gemini_chat import apply_llm_draft, generate_chat_turn
from app.services.gemini_plan import generate_plan as gemini_generate_plan
from app.services.mock_plan import build_stub_plan

logger = logging.getLogger(__name__)


def _normalize_goal_text(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


async def run_chat_turn(
    db: AsyncIOMotorDatabase | None,
    *,
    thread_id: str | None,
    text: str,
    stable_thread_id: str | None = None,
) -> ChatMessageResponse:
    """
    One user message → assistant reply + updated draft.

    If stable_thread_id is set (e.g. WhatsApp), use that id instead of creating a random one.
    If thread_id is None and stable_thread_id is None, creates a new web thread.
    """
    if stable_thread_id is not None:
        tid = stable_thread_id
        doc = await ensure_thread(db, tid)
    elif thread_id is None:
        tid = await create_thread(db)
        doc = await get_thread(db, tid)
        assert doc is not None
    else:
        tid = thread_id
        doc = await get_thread(db, tid)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown thread_id")

    draft = draft_from_doc(doc)
    transcript = transcript_for_prompt(doc)
    llm_out = generate_chat_turn(transcript=transcript, draft=draft, latest_user=text)
    new_draft = apply_llm_draft(draft, llm_out)
    append_message_pair(doc, text, llm_out.reply)
    merge_draft(doc, new_draft)
    await save_thread(db, doc)

    return ChatMessageResponse(
        thread_id=tid,
        reply=llm_out.reply,
        draft=new_draft,
        ask_finalize=llm_out.ask_finalize,
    )


def _plan_from_draft(d: DraftPlanFields) -> PlanRequest:
    goal = (d.goal or "").strip()
    # Stricter than PlanRequest min_length=1 so vague one-word chats cannot finalize.
    if len(goal) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need a clearer goal first — keep chatting, then finalize.",
        )
    return PlanRequest(
        goal=goal,
        horizon=d.horizon,
        available_minutes=d.available_minutes,
        energy=d.energy,
    )


async def run_finalize(
    db: AsyncIOMotorDatabase | None,
    thread_id: str,
    *,
    user_id: str | None = None,
    reuse_linked_plan: bool = False,
) -> PlanResponse:
    plan, _ = await load_or_finalize_thread_plan(
        db,
        thread_id,
        user_id=user_id,
        reuse_linked_plan=reuse_linked_plan,
    )
    return plan


async def load_or_finalize_thread_plan(
    db: AsyncIOMotorDatabase | None,
    thread_id: str,
    *,
    user_id: str | None = None,
    reuse_linked_plan: bool = False,
) -> tuple[PlanResponse, bool]:
    doc = await get_thread(db, thread_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown thread_id")

    if reuse_linked_plan and db is not None:
        linked_plan = await load_linked_plan_for_thread(db, thread_id)
        if linked_plan is not None and _should_reuse_linked_plan(doc, linked_plan[0]):
            return linked_plan[1], False

    draft = draft_from_doc(doc)
    request = _plan_from_draft(draft)

    try:
        plan = gemini_generate_plan(request)
    except Exception:
        logger.exception("finalize: Gemini plan failed; using stub")
        plan = build_stub_plan(request.goal)

    persisted = await persist_plan_for_thread(
        db,
        thread_id,
        request,
        plan,
        user_id=user_id,
    )

    return plan, persisted


async def load_linked_plan_for_thread(
    db: AsyncIOMotorDatabase | None,
    thread_id: str,
) -> tuple[dict, PlanResponse] | None:
    if db is None:
        return None
    linked_plan_id = await get_active_plan_id_for_thread(db, thread_id)
    if not linked_plan_id:
        return None
    plan_doc = await get_plan_by_plan_id(db, linked_plan_id)
    if plan_doc is None:
        return None
    return plan_doc, plan_response_from_doc(plan_doc)


def _should_reuse_linked_plan(doc: dict, plan_doc: dict) -> bool:
    draft_goal = _normalize_goal_text(draft_from_doc(doc).goal)
    if not draft_goal:
        return True
    stored_goal = _normalize_goal_text(str(plan_doc.get("goal", "")))
    raw_plan = plan_doc.get("plan") or {}
    stored_summary = _normalize_goal_text(
        raw_plan.get("summary") if isinstance(raw_plan, dict) else ""
    )
    return draft_goal in {stored_goal, stored_summary}


async def persist_plan_for_thread(
    db: AsyncIOMotorDatabase | None,
    thread_id: str,
    request: PlanRequest,
    plan: PlanResponse,
    *,
    user_id: str | None = None,
) -> bool:
    if db is None:
        return False

    try:
        user_phone: str | None = None
        if user_id:
            user_doc = await get_user_by_id(db, user_id)
            if user_doc is not None:
                raw_phone = user_doc.get("phone")
                if isinstance(raw_phone, str) and raw_phone.strip():
                    user_phone = raw_phone.strip()

        await insert_plan(
            db,
            request.goal,
            plan,
            user_phone=user_phone,
            user_id=user_id,
        )
        await set_active_plan_id(db, thread_id, plan.plan_id)
        return True
    except Exception:
        logger.exception("persist_plan_for_thread: failed to persist plan or link thread")
        return False


def whatsapp_thread_id_for_user(user_id: str) -> str:
    return f"wa-{user_id}"
