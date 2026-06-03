# Agentic DevOps Platform

Corporate multi-tenant AI code review and functional test reporting platform.

## Architecture

- **Backend:** FastAPI + SQLAlchemy + SQLite + Gemini API
- **Frontend:** React + Vite + Tailwind CSS
- **Agents:** ReviewerAgent (Gemini LLM + deterministic policy) + FunctionalTestAgent (subprocess)
- **Providers:** GitHub (full), GitLab/Azure DevOps (stubs)

## Setup

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your GEMINI_API_KEY, SMTP credentials, GITHUB_TOKEN

python run.py
# Backend starts at http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install

# Configure environment
copy .env.example .env.local
# Edit .env.local if your backend is not at http://localhost:8000

npm run dev
# Frontend starts at http://localhost:5173
```

## Local End-to-End Test Flow

1. Start backend (`python run.py`)
2. Start frontend (`npm run dev`)
3. Open http://localhost:5173

### Configure

1. **Create a Tenant** — go to Tenants → New Tenant
2. **Create a GitHub Integration:**
   - Provider: `github`
   - Repository Full Name: `owner/repo`
   - Sprint Branch Pattern: `sprint/*`
   - Task Branch Pattern: `task/*`
   - Development Branch: `development`
   - Test Branch: `test`
   - Add manager email and notification recipients
3. Click **Webhook** on the integration to see the webhook URL and secret
4. **Create Review Rules** for that tenant
5. **Create a Functional Test Config** with a test command (e.g., `pytest tests/ -v`)

### GitHub Webhook Setup

1. Start ngrok: `ngrok http 8000`
2. In your GitHub repo → Settings → Webhooks → Add webhook:
   - Payload URL: `https://<ngrok-id>.ngrok.io/api/webhooks/github/<integration_id>`
   - Content type: `application/json`
   - Secret: (from webhook info panel)
   - Events: Pull requests + Pushes
3. Save

### Trigger the Pipeline

1. Create a task branch: `task/sprint-3/TASK-128-login-validation`
2. Make changes and push
3. Open a PR to merge into `sprint/sprint-3`
4. Merge the PR manually in GitHub
5. GitHub sends a `pull_request` closed+merged webhook
6. System detects `task_to_sprint_merge`
7. ReviewerAgent runs → report saved → email sent
8. If review passes → FunctionalTestAgent runs → report saved → email sent
9. If tests pass → EnvironmentPromotionLog created → promotion email sent
10. Check the UI: Events, Merge Reviews, Functional Tests, Promotions

## API

Interactive docs at: `http://localhost:8000/docs`

Key endpoints:
- `GET /api/debug/health`
- `POST /api/tenants`
- `POST /api/integrations`
- `GET /api/integrations/{id}/webhook-info`
- `POST /api/review-rules`
- `POST /api/functional-test-configs`
- `POST /api/webhooks/{provider}/{integration_id}`
- `GET /api/merge-reviews`
- `GET /api/functional-tests`
- `GET /api/promotions`
- `GET /api/stats/users`

## Branch Naming Convention

```
Task branch:   task/sprint-3/TASK-128-login-validation
Sprint branch: sprint/sprint-3
Dev branch:    development
Test branch:   test
```

Detected event types:
- `task_to_sprint_merge` — triggers review + test pipeline
- `sprint_to_development_event` — logged only
- `development_test_event` — logged only
- `push` — logged only

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite or PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Model name (default: gemini-1.5-flash) |
| `SMTP_HOST` | SMTP host for email |
| `SMTP_USERNAME` | SMTP username |
| `SMTP_PASSWORD` | SMTP password |
| `SMTP_FROM_EMAIL` | Sender email address |
| `GITHUB_TOKEN` | GitHub personal access token (for fetching diffs) |
| `FRONTEND_URL` | Frontend URL for CORS |
