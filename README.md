# Event KhataBook

Event KhataBook - an AI-powered trust and audit layer for student event payments.

## The problem

If you have run college level student events, the pain is familiar: duplicate registrations come in through rushed payment retries, refund calls happen over WhatsApp with no consistent policy trail, and faculty sign-off becomes a manual chase through screenshots and memory. The result is not just operational friction; it is a trust gap between organizers, participants, and reviewers.

## What it does

- Detects duplicate registrations and duplicate payments before they disappear into a spreadsheet backlog.
- Triggers live voice verification through Twilio when a suspicious entry needs participant confirmation.
- Evaluates refund requests against fixed policy clauses instead of free-form model improvisation.
- Writes actor-attributed audit logs for registrations, flags, and refund decisions.
- Gives organizers a live reconciliation dashboard for collection totals, flags, calls, refunds, and audit activity.

## Why it's not just an LLM wrapper

- Agent outputs are forced into structured JSON and validated against typed schemas before the app acts on them.
- The refund engine uses a hardcoded non-negotiable policy; the model classifies against policy clauses instead of inventing one.
- Every important decision is actor-attributed in the audit log, so you can see whether `ai_*` reasoning or fallback logic handled it.

## Architecture

```text
+--------------------+        HTTP / JSON         +-------------------------+
| Next.js Frontend   | -------------------------> | FastAPI Backend         |
| dashboard, flags,  |                            | routes, audit, metrics  |
| refunds, audit     | <------------------------- | response contracts      |
+--------------------+                            +------------+------------+
                                                            |
                                                            |
                              +-----------------------------+------------------------------+
                              |                             |                              |
                              v                             v                              v
                    +-------------------+         +-------------------+         +-------------------+
                    | Duplicate Detector |         | Intent Parser     |         | Refund Reasoner   |
                    | duplicate flags    |         | voice transcript  |         | policy clauses    |
                    +-------------------+         +-------------------+         +-------------------+
                              |                             |                              |
                              +-----------------------------+------------------------------+
                                                            |
                                                            v
                                                 +-------------------------+
                                                 | SQLite + Audit Log      |
                                                 | registrations, flags,   |
                                                 | payments, decisions     |
                                                 +-------------------------+
                                                            |
                               +----------------------------+-----------------------------+
                               |                                                          |
                               v                                                          v
                     +-------------------+                                      +-------------------+
                     | Twilio Voice      |                                      | Razorpay          |
                     | outbound verify   |                                      | order/payment     |
                     +-------------------+                                      +-------------------+
```

## Tech stack

| Layer | Stack | Why it is here |
| --- | --- | --- |
| Frontend | Next.js 16, React 19, TypeScript | Operator UI for reconciliation, flags, refunds, and audit review |
| Styling | Global CSS tokens and utility classes | Dense ledger UI with controlled typography and alignment |
| Backend API | FastAPI, Pydantic | Typed request and response contracts with quick route iteration |
| Database | SQLite, SQLAlchemy | Local persistence for registrations, payments, flags, calls, and audits |
| Agents | Gemini/OpenAI-backed fallbacks plus deterministic logic | Duplicate detection, call intent parsing, and refund reasoning |
| Voice | Twilio Voice webhooks | Participant verification over a real phone call flow |
| Payments | Razorpay order/payment integration | Event payment order creation and refund workflow surface |
| Testing | Pytest, HTTPX | Reproducible demo metrics and rule-compliance checks |

## The demo metric

- Duplicate detection: `8/8` planted duplicates caught in `backend/tests/test_demo_metric.py`.
- False positives: `0` false positives in the same automated test.
- Refund policy compliance: `4/4` fixed clauses asserted in the automated refund policy test.
- Audit coverage: the current test suite verifies `8` `FLAG_RAISED` audit entries with explicit actor attribution; it does not yet contain a dedicated automated refund-audit-coverage assertion, so that metric is still a known gap.

## How to run it locally

1. Install frontend dependencies.

```bash
cd frontend
npm install
```

2. Install backend dependencies.

```bash
cd ../backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file inside `backend/` with these variable names only:

```env
PORT=
DATABASE_URL=
BASE_URL=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
GEMINI_API_KEY=
GEMINI_MODEL=
OPENAI_API_KEY=
```

4. Seed the database.

```bash
cd backend
python seed.py
```

5. Start the backend API.

```bash
uvicorn app.main:app --reload --port 8000
```

6. Start the frontend in a second terminal.

```bash
cd frontend
npm run dev
```

7. Optional: run the automated demo-metric test suite.

```bash
cd backend
pytest tests/test_demo_metric.py -q
```

## What's next / known limitations

- Twilio verification is still a single-turn gather flow, not a full conversational voice agent.
- The project currently assumes a single-event operating model rather than a multi-event organizer workspace.
- Refund audit coverage is partially observable today, but not yet asserted as a first-class automated metric in tests.
- Real outbound calling can be limited by Twilio trial account restrictions and verified-number constraints.
