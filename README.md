# Comment Analytics Tracker Tool

A FastAPI backend application that tracks Reddit comment view counts on a schedule and stores them in Supabase. Includes automated data collection via GitHub Actions, Excel/Google Sheets export, and weekly average calculations.

---

## Features

✅ **Track Reddit Comments** — Add comments by URL or ID  
✅ **Automated Collection** — GitHub Actions triggers data collection on schedule  
✅ **View Count History** — Store and analyze view counts over time  
✅ **Weekly Averages** — Automatic calculation of 7-day rolling averages  
✅ **Export Options** — Download data as Excel or sync to Google Sheets  
✅ **Cloud Ready** — Deploy to Render, Railway, or similar platforms  
✅ **Free Tier Compatible** — Works with Supabase free tier

---

## Project Structure

```
comments-analytics-tracker-tool/
├── src/                              # Main backend application
│   ├── main.py                       # FastAPI app initialization
│   ├── config.py                     # Configuration & environment loading
│   │
│   └── app/
│       ├── models.py                 # SQLAlchemy ORM models
│       ├── schemas.py                # Pydantic request/response schemas
│       │
│       ├── routes/                   # API endpoints
│       │   ├── comments.py           # POST/GET/DELETE comment endpoints
│       │   └── export.py             # Excel & Google Sheets export
│       │
│       ├── services/                 # Business logic
│       │   ├── reddit_service.py     # PRAW Reddit API integration
│       │   └── collector_service.py  # Data collection & storage
│       │
│       ├── tasks/                    # Scheduled tasks
│       │   └── collector_task.py     # Collection task endpoint
│       │
│       ├── utils/                    # Utilities
│       │   └── exceptions.py         # Custom exception classes
│       │
│       └── database/                 # Database management
│           └── session.py            # SQLAlchemy session manager
│
├── .github/
│   └── workflows/
│       └── collect-schedule.yml      # GitHub Actions schedule (to be created)
│
├── ai-planner/                       # Project planning & documentation
│   ├── initial-plan-1.md             # Full implementation plan
│   └── postgres-schema.md            # Database schema & queries
│
├── .env.example                      # Environment variables template
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project metadata & dependencies
├── README.md                         # This file
└── LICENSE
```

---

## Quick Start

### Prerequisites
- Python 3.12+
- Supabase account (free tier available)
- Reddit API credentials (from https://www.reddit.com/prefs/apps)
- (Optional) Google Sheets for data export

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd comments-analytics-tracker-tool
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   Fill in your credentials in `.env`:
   - Supabase URL & API key
   - Reddit client ID & secret
   - (Optional) Google Sheets ID & service account

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   - Go to Supabase console
   - Run SQL from `ai-planner/postgres-schema.md`
   - Or use the initialization script provided

5. **Run locally**
   ```bash
   uvicorn src.main:app --reload
   ```
   API docs available at: `http://localhost:8000/docs`

---

## API Endpoints

### Comments Management
- `POST /api/comments` — Add new comment to track
- `GET /api/comments` — List all tracked comments with latest stats
- `GET /api/comments/{id}` — Get detailed view of one comment
- `DELETE /api/comments/{id}` — Remove tracked comment

### Data Collection
- `POST /api/tasks/collect` — Manually trigger data collection (called by GitHub Actions)
- `GET /api/health` — Health check
- `GET /api/stats` — System statistics

### Export
- `GET /api/export/excel` — Download all data as Excel file
- `POST /api/export/sheets` — Sync data to Google Sheet

---

## Configuration

See `.env.example` for all environment variables:

**Required:**
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase API key
- `REDDIT_CLIENT_ID` — Reddit app client ID
- `REDDIT_CLIENT_SECRET` — Reddit app secret
- `REDDIT_USERNAME` — Reddit account username
- `REDDIT_PASSWORD` — Reddit account password

**Optional:**
- `GOOGLE_SHEETS_ID` — Google Sheet to sync data
- `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` — Path to service account JSON
- `COLLECT_API_KEY` — API key for `/api/tasks/collect` endpoint

---

## Deployment

### To Render/Railway

1. Create account on Render or Railway
2. Connect GitHub repository
3. Set environment variables from `.env`
4. Deploy

### GitHub Actions Workflow

Create `.github/workflows/collect-schedule.yml` to schedule data collection:

```yaml
name: Collect Reddit Data
on:
  schedule:
    - cron: '0 10 * * *'  # Daily at 10 AM UTC

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger data collection
        run: |
          curl -X POST https://your-app-url.com/api/tasks/collect \
            -H "Authorization: Bearer ${{ secrets.COLLECT_API_KEY }}"
```

---

## Documentation

- **[Implementation Plan](ai-planner/initial-plan-1.md)** — Full project roadmap
- **[Database Schema](ai-planner/postgres-schema.md)** — Table definitions & sample queries
- **[API Docs](http://localhost:8000/docs)** — Auto-generated Swagger UI (when running locally)

---

## Development

### Run Tests
```bash
# Manual testing with curl
curl -X POST http://localhost:8000/api/comments \
  -H "Content-Type: application/json" \
  -d '{"reddit_url": "https://reddit.com/r/..."}'
```

### Logs
- Console output: All logs printed to terminal
- File logs: Check `./logs/app.log` (if configured)

---

## Troubleshooting

**Issue:** "No module named 'praw'"
- Solution: Run `pip install -r requirements.txt`

**Issue:** Database connection failed
- Solution: Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

**Issue:** Reddit API errors
- Solution: Verify Reddit credentials and ensure app is created at https://www.reddit.com/prefs/apps

See [.env.example](.env.example) for detailed setup instructions.

---

## License

See [LICENSE](LICENSE) file