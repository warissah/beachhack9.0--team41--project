"""Simple event bus for the hackathon demo — lets WhatsApp commands push state to the web app."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "demo_events"


def _dedupe_key(event_type: str, data: dict[str, Any]) -> str:
    return json.dumps({"type": event_type, "data": data}, sort_keys=True, default=str)


async def insert_demo_event(db: AsyncIOMotorDatabase, event_type: str, data: dict[str, Any]) -> None:
    # Deduplicate only exact repeats in the last 30 seconds (guards against Twilio retries
    # without suppressing distinct new_plan events for different plans).
    from datetime import timedelta
    cutoff = datetime.now(UTC) - timedelta(seconds=30)
    dedupe_key = _dedupe_key(event_type, data)
    existing = await db[COLLECTION].find_one(
        {"dedupe_key": dedupe_key, "timestamp": {"$gt": cutoff}}
    )
    if existing:
        return
    await db[COLLECTION].insert_one({
        "type": event_type,
        "data": data,
        "dedupe_key": dedupe_key,
        "timestamp": datetime.now(UTC),
    })


async def get_events_since(db: AsyncIOMotorDatabase, since_ts: float | None = None) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if since_ts is not None:
        query["timestamp"] = {"$gt": datetime.fromtimestamp(since_ts, tz=UTC)}
    cursor = db[COLLECTION].find(query).sort("timestamp", 1).limit(50)
    events = []
    async for doc in cursor:
        events.append({
            "id": str(doc["_id"]),
            "type": doc["type"],
            "data": doc.get("data", {}),
            "timestamp": doc["timestamp"].timestamp(),
        })
    return events
