from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.sessions import complete_session, insert_session_start


async def record_session_completion(
    db: AsyncIOMotorDatabase | None,
    task_id: str,
    ended_at: datetime,
    reflection: str,
) -> str:
    """
    Close the latest open session for a task. If none exists, backfill a minimal
    session using ended_at as the start time so completion is still persisted.
    """
    if db is None:
        return "skipped"

    modified = await complete_session(db, task_id, ended_at, reflection)
    if modified:
        return "completed"

    await insert_session_start(db, task_id, ended_at)
    modified = await complete_session(db, task_id, ended_at, reflection)
    return "backfilled" if modified else "skipped"
