from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from app.services.session_logic import record_session_completion


def test_record_session_completion_closes_open_session() -> None:
    async def _run() -> None:
        db = object()
        ended_at = datetime.now(UTC)
        with patch(
            "app.services.session_logic.complete_session",
            AsyncMock(return_value=1),
        ) as complete_session:
            with patch(
                "app.services.session_logic.insert_session_start",
                AsyncMock(),
            ) as insert_session_start:
                result = await record_session_completion(
                    db,
                    "plan-123",
                    ended_at,
                    "done",
                )

        assert result == "completed"
        complete_session.assert_awaited_once_with(db, "plan-123", ended_at, "done")
        insert_session_start.assert_not_awaited()

    asyncio.run(_run())


def test_record_session_completion_backfills_missing_session() -> None:
    async def _run() -> None:
        db = object()
        ended_at = datetime.now(UTC)
        with patch(
            "app.services.session_logic.complete_session",
            AsyncMock(side_effect=[0, 1]),
        ) as complete_session:
            with patch(
                "app.services.session_logic.insert_session_start",
                AsyncMock(),
            ) as insert_session_start:
                result = await record_session_completion(
                    db,
                    "plan-123",
                    ended_at,
                    "done",
                )

        assert result == "backfilled"
        insert_session_start.assert_awaited_once_with(db, "plan-123", ended_at)
        assert complete_session.await_count == 2

    asyncio.run(_run())
