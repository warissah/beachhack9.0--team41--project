# T4 — DevOps, Fetch.ai, Mongo Atlas, Vultr, demo

You make the **demo reliable**: deploy, secrets, Fetch → HTTPS callback, and the **story** for judges.

**Load balancing — help the backend (T2):** After deploy exists, take point on **server env** (Mongo, Twilio, `INTERNAL_API_KEY`), **`curl`** verification of `/health` and `/internal/reminders/fire`, **CORS** for the production frontend origin, and **incident-style** debugging (502, wrong bind port, missing env). You do **not** own Pydantic schemas or core business logic unless T2 delegates a tiny, well-scoped task. You can also help **T1** with **`VITE_API_URL`** for prod and static build checks. Full table: **Load balancing** in [`../MASTER_PLAN.md`](../MASTER_PLAN.md).

## Your mission

- **MongoDB Atlas**: cluster + connection string in `MONGODB_URI` (local `.env` only).
- **Vultr**: host FastAPI + static frontend (or split); public **HTTPS** URL required for Twilio + Fetch webhooks.
- **Fetch.ai (mandatory)**: one agent/workflow that **POST**s to `POST /internal/reminders/fire` with `X-Internal-Key` and JSON body `{ user_id, task_id, reminder_kind }`. Start with **`check_in_15m`** only.
- **Demo**: 2-minute script + screen recording backup; show Fetch dashboard/logs if available.

## Where to work

- Root [`README.md`](../../README.md) — keep env table accurate.
- `backend/.env.example` — document every variable; no real values.
- Deployment notes: add `docs/DEPLOY.md` if helpful (optional).

## Fetch vs Gemini (talk track)

- **Gemini**: generates plan/nudge **text** when the **backend** asks.
- **Fetch**: decides **when** to trigger the **callback** so the user gets a **proactive** WhatsApp ping.

## Testing

- **Integration**: from deployed URL, `curl` the internal endpoint with the secret; expect 200 + logged “would send” (until Twilio wired).
- **End-to-end**: Fetch fires → backend → Twilio sandbox message arrives.

## Checklist

- [ ] `INTERNAL_API_KEY` rotated if exposed; never committed.
- [ ] CORS updated for production frontend origin.
- [ ] Crisis disclaimer appears in web + WhatsApp copy.

See root [`README.md`](../../README.md).
