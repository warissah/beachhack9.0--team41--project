import html
import logging

from fastapi import APIRouter, Request, Response

from app.routers.nudge import nudge as run_nudge
from app.schemas.nudge import NudgeRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# Until phone→task lives in Mongo, Twilio sandbox can hit /nudge with this id.
HACKATHON_DEMO_TASK_ID = "hackathon-demo"


def _twiml_message(text: str) -> str:
    """Twilio expects XML (not JSON) if the HTTP response should send a WhatsApp/SMS reply."""
    safe = html.escape(text[:1500], quote=True)
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>'


@router.post("/twilio")
async def twilio_whatsapp(request: Request) -> Response:
    """
    Inbound WhatsApp (Twilio). Returns TwiML so Twilio can deliver a reply in the sandbox.

    Hackathon demo: message contains \"stuck\" → same logic as POST /nudge (task_id=hackathon-demo).
    """
    form = await request.form()
    body_raw = str(form.get("Body", "")).strip()
    from_num = str(form.get("From", ""))
    logger.info("twilio inbound from=%s body_len=%s", from_num, len(body_raw))

    lower = body_raw.lower()
    if "stuck" in lower:
        try:
            out = run_nudge(
                NudgeRequest(
                    task_id=HACKATHON_DEMO_TASK_ID,
                    context=body_raw or "whatsapp stuck",
                )
            )
            text = f"{out.message}\n\n2 min try: {out.two_minute_action}"
        except Exception:
            logger.exception("nudge from twilio webhook failed")
            text = "Something broke on our side—try STUCK again in a minute."
    else:
        text = (
            "Hi—this is the hackathon coach (demo). Text STUCK when you need a tiny next step. "
            + (f'You said: "{body_raw[:120]}"' if body_raw else "")
        ).strip()

    return Response(content=_twiml_message(text), media_type="application/xml")
