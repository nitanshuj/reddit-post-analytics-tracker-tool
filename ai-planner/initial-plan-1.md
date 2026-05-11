# Plan: FastAPI Backend for Comment Analytics Tracker (MVP)

## TL;DR
Build a FastAPI backend that tracks Reddit subreddit performance metrics on a schedule and stores them in Supabase. MVP scope: monitor specific subreddits for weekly stats (posts, impressions, upvotes, comments, engagement), track individual posts/comments, calculate engagement rates, and expose REST endpoints. No authentication needed (single-user dev mode). Deploy to cloud (Render/Railway).

---

## Overview

**Database Tables:**
- `subreddits` — Tracked subreddits
- `weekly_stats` — Weekly aggregated metrics per subreddit
- `posts` — Individual posts
- `post_weekly_stats` — Weekly metrics per post
- `comments` — Individual comments (original functionality)
- `comment_history` — View count history for comments

**Key Metrics Calculated:**
- Engagement: upvotes + comments
- Engagement Rate: (engagement / impressions) × 100

---

## Stage 1: ORM Models & Schemas

### 1.1 Create SQLAlchemy ORM Models
- Define `Subreddit` model (maps to subreddits table)
- Define `WeeklyStats` model (maps to weekly_stats table)
- Define `Post` model (maps to posts table)
- Define `PostWeeklyStats` model (maps to post_weekly_stats table)
- Define `Comment` model (maps to comments table - original)
- Define `CommentHistory` model (maps to comment_history table - original)
- Set up relationships: Subreddit ↔ WeeklyStats, Subreddit ↔ Posts, Post ↔ PostWeeklyStats, Comment ↔ CommentHistory
- Add timestamps (created_at, updated_at) to all models
- Configure cascade delete for parent-child relationships

**File:** `src/app/models.py`

### 1.2 Create Pydantic Request/Response Schemas
- `SubredditCreate` — POST request schema (name)
- `SubredditResponse` — GET response (id, name, created_at, latest_stats)
- `WeeklyStatsResponse` — (week, total_posts, impressions, upvotes, comments, engagement, avg_engagement_rate)
- `PostCreate` — POST schema (title, url, reddit_post_id)
- `PostResponse` — GET schema (id, title, url, author)
- `PostWeeklyStatsResponse` — (week, upvotes, impressions, comments_count, engagement_rate)
- `CommentCreate` — POST schema (reddit_url)
- `CommentResponse` — GET schema (id, reddit_url, latest_view_count)
- Add Pydantic validators for URLs, required fields, date ranges

**File:** `src/app/schemas.py`

### 1.3 Set Up Database Configuration
- Create database session manager in `src/app/database/session.py`
- Configure SQLAlchemy engine with Supabase connection string
- Set up sessionmaker for dependency injection
- Create `get_db()` dependency for routes
- Add connection pooling configuration
- Test connection string from .env file

**File:** `src/app/database/session.py`

### 1.4 Initialize FastAPI App & Middleware
- Create FastAPI app instance in `src/main.py`
- Add CORS middleware (allow frontend requests)
- Add error handling middleware (catch and log exceptions)
- Add request/response logging middleware (optional)
- Set up exception handlers for custom exceptions
- Configure app settings from config.py

**File:** `src/main.py`

---

## Phase 1: Core API Endpoints

### 1.1 Create Subreddit Management Endpoints
- `POST /api/subreddits` — Add subreddit to track
  - Accept: subreddit name
  - Validate: name not empty, not already tracked
  - Return: SubredditResponse with id
  - Status: 201 Created

- `GET /api/subreddits` — List all tracked subreddits
  - Return: array of SubredditResponse
  - Include latest weekly stats summary
  - Status: 200 OK

- `DELETE /api/subreddits/{name}` — Remove subreddit and all related data
  - Delete cascade: posts, weekly_stats, post_weekly_stats
  - Return: {status: "deleted"}
  - Status: 204 No Content

**File:** `src/app/routes/subreddits.py`

### 1.2 Create Subreddit Statistics Endpoints
- `GET /api/subreddits/{name}/weekly` — Get weekly stats (last 12 weeks)
  - Return: array of WeeklyStatsResponse sorted by week DESC
  - Include: week, total_posts, impressions, avg_engagement_rate
  - Status: 200 OK

- `GET /api/subreddits/{name}/posts` — Get posts with weekly metrics
  - Query params: week (optional), limit (default 50)
  - Return: array of PostResponse with latest PostWeeklyStatsResponse
  - Sort: by engagement_rate DESC
  - Status: 200 OK

**File:** `src/app/routes/subreddits.py`

### 1.3 Create Comment Management Endpoints (Original Functionality)
- `POST /api/comments` — Add comment to track
  - Accept: reddit_url
  - Validate: valid Reddit URL format
  - Return: CommentResponse with id
  - Status: 201 Created

- `GET /api/comments` — List tracked comments
  - Return: array of CommentResponse with latest view counts
  - Status: 200 OK

- `GET /api/comments/{id}` — Get comment details
  - Return: CommentResponse + comment_history (last 30 days)
  - Status: 200 OK

- `DELETE /api/comments/{id}` — Remove tracked comment
  - Delete cascade: comment_history
  - Status: 204 No Content

**File:** `src/app/routes/comments.py`

### 1.4 Create Health & Status Endpoints
- `GET /health` — Health check
  - Return: {status: "ok", timestamp: ISO8601}
  - Status: 200 OK

- `GET /api/stats` — System statistics
  - Return: {total_subreddits, total_posts, total_comments, last_collection_time}
  - Status: 200 OK

**File:** `src/main.py` or `src/app/routes/health.py`

---

## Phase 2: Reddit API Integration

### 2.1 Implement Reddit Client Service
- Create `RedditClient` class in `src/app/services/reddit_service.py`
- Initialize PRAW with credentials from env variables
- Implement error handling for invalid credentials
- Add logging for API calls (success/failure/rate limits)

**Methods:**
- `get_subreddit_posts(name: str, limit: int)` → list of {post_id, title, url, author, created_at}
- `get_post_stats(post_id: str)` → {upvotes, impressions, comments_count}
- `get_comment_view_count(comment_id: str)` → int (original functionality)
- `extract_comment_id(url: str)` → str or raise InvalidRedditURL
- `is_subreddit_valid(name: str)` → bool (check if subreddit exists)

**File:** `src/app/services/reddit_service.py`

### 2.2 Add Error Handling & Rate Limiting
- Create custom exception classes in `src/app/utils/exceptions.py`:
  - `InvalidRedditURL`
  - `SubredditNotFound`
  - `PostNotFound`
  - `RedditAPIError`
  - `DatabaseError`
  - `ValidationError`
- Add retry logic with exponential backoff for rate limits
- Log rate limit warnings with retry countdown

**File:** `src/app/utils/exceptions.py` & `src/app/services/reddit_service.py`

### 2.3 Implement Data Collection Service
- Create `DataCollector` class in `src/app/services/collector_service.py`
- Implement subreddit data collection:
  - Fetch all posts from subreddit (current week)
  - Extract: total_posts, total_impressions, total_upvotes, total_comments
  - Calculate: engagement = upvotes + comments, avg_engagement_rate = (engagement / impressions) * 100
  - Upsert into weekly_stats table
- Implement post data collection:
  - For each tracked post, fetch current metrics
  - Calculate engagement_rate per post
  - Upsert into post_weekly_stats table
- Implement comment data collection (original):
  - Query all tracked comments
  - Fetch view counts from Reddit
  - Insert into comment_history table
  - Calculate 7-day rolling average
- Log all collection events (successes, failures, skipped)
- Handle partial failures gracefully

**File:** `src/app/services/collector_service.py`

### 2.4 Create Collection Task Endpoint
- Create `POST /api/tasks/collect` endpoint in `src/app/tasks/collector_task.py`
- Trigger function: `collect_all_data()`
  - Execute subreddit collection
  - Execute post collection
  - Execute comment collection
  - Return summary: {status, subreddits_processed, posts_processed, comments_processed, success_count, error_count, timestamp}
- Add optional API key validation (check COLLECT_API_KEY header)
- Log collection start/end times

**File:** `src/app/tasks/collector_task.py`

---

## Phase 3: Data Export & Integration

### 3.1 Create Excel Export Endpoint
- Create `GET /api/export/excel` endpoint in `src/app/routes/export.py`
- Generate Excel workbook with multiple sheets:
  - Sheet 1: "Subreddits" — subreddit name, latest week, total_posts, impressions, avg_engagement_rate
  - Sheet 2: "Weekly Stats" — full weekly_stats data with all columns
  - Sheet 3: "Posts" — post titles, URLs, authors, latest metrics
  - Sheet 4: "Comments" — tracked comments, latest view counts
- Format: timestamps as ISO8601, decimals to 2 places
- Return as file download: `comment_data_YYYY-MM-DD.xlsx`
- Status: 200 with file attachment

**File:** `src/app/routes/export.py`

### 3.2 Create Google Sheets Sync Endpoint
- Create `POST /api/export/sheets` endpoint in `src/app/routes/export.py`
- Authenticate using service account JSON (from GOOGLE_SERVICE_ACCOUNT_JSON_PATH)
- Open Google Sheet by ID (GOOGLE_SHEETS_ID)
- Create/update sheets:
  - "Subreddits" sheet
  - "Weekly Stats" sheet
  - "Posts" sheet
  - "Comments" sheet
- Append headers and data rows
- Return: {status: "synced", sheets_updated: int, rows_written: int, timestamp}
- Log sync events and errors

**File:** `src/app/routes/export.py`

### 3.3 Add Logging & Monitoring
- Configure Python logging in `src/config.py`
  - Console handler (INFO level)
  - File handler to `logs/app.log` (DEBUG level)
  - Rotation: daily or 10MB max
- Add structured logging for:
  - Collection events (start/end times, record counts, errors)
  - Reddit API calls (method, status, response time)
  - Database operations (inserts, updates, errors)
  - Export operations (start/end, rows exported)
- Include: timestamp, level, function name, message

**File:** `src/config.py` & all service files

### 3.4 Create Dockerfile & Deployment Config
- Create `Dockerfile` (multi-stage build)
  - Stage 1: Builder (install dependencies)
  - Stage 2: Runtime (copy deps, copy app, expose port)
- Create `.dockerignore` (exclude .git, venv, __pycache__, .env, *.pyc)
- Create deployment guide in `DEPLOY.md`:
  - Environment variables needed
  - Database initialization steps
  - How to deploy to Render/Railway
  - Scaling considerations

**File:** `Dockerfile`, `.dockerignore`, `DEPLOY.md`

---

## Phase 4: Error Handling & Validation

### 4.1 Add Comprehensive Error Handling
- Create FastAPI exception handlers in `src/main.py`
- Map custom exceptions to HTTP status codes:
  - 400 Bad Request: ValidationError, InvalidRedditURL
  - 404 Not Found: SubredditNotFound, PostNotFound
  - 500 Internal Server Error: RedditAPIError, DatabaseError
- Return consistent error response: {error: str, detail: str, timestamp}
- Add request ID for tracing (optional)

**File:** `src/main.py` & `src/app/utils/exceptions.py`

### 4.2 Add Input Validation
- Validate subreddit names (alphanumeric, no spaces)
- Validate Reddit URLs (match Reddit domain pattern)
- Validate date ranges (week dates must be Mondays)
- Validate pagination params (limit: 1-100, default 50)
- Add Pydantic validators to all request schemas

**File:** `src/app/schemas.py`

### 4.3 Create Configuration Management
- Load environment variables in `src/config.py`:
  - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
  - `REDDIT_USERNAME`, `REDDIT_PASSWORD`
  - `SUPABASE_URL`, `SUPABASE_KEY`
  - `DATABASE_URL` (derived from Supabase)
  - `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON_PATH`
  - `COLLECT_API_KEY` (optional)
  - `ENV` (development/production)
  - `LOG_LEVEL`, `LOG_FILE`
- Validate all required vars are present on startup
- Add config class for type hints

**File:** `src/config.py`

### 4.4 Add Security Measures
- Validate COLLECT_API_KEY header if set
- Sanitize user inputs (prevent SQL injection)
- Add rate limiting per IP (optional, for Phase 2)
- Hide sensitive data from logs (mask API keys)

**File:** `src/main.py` & middleware

---

## Phase 5: Testing & Documentation

### 5.1 Create Manual Test Checklist
**Subreddit Endpoints:**
- Add subreddit → verify stored in DB and returned with id
- Get subreddits → verify list returns all tracked
- Get weekly stats → verify returns last 12 weeks sorted DESC
- Get posts → verify returns with engagement rates
- Delete subreddit → verify cascades to posts and stats

**Comment Endpoints:**
- Add comment → verify stored in DB
- Get comments → verify list with latest view counts
- Get comment detail → verify includes history

**Collection Task:**
- Trigger `/api/tasks/collect` → verify updates weekly_stats and post_weekly_stats
- Verify calculations: avg_engagement_rate = (engagement / impressions) * 100
- Verify partial failure: one post fails but others succeed

**Export:**
- Excel export → verify file downloads with all sheets
- Google Sheets sync → verify data appears in sheets

**Error Scenarios:**
- Invalid subreddit name → returns 400
- Non-existent subreddit → returns 404
- Database connection failure → returns 500
- Invalid Reddit credentials → returns error on collect

**File:** `TESTING.md`

### 5.2 Create Setup Documentation
- Local development setup:
  - Clone repo
  - Create `.env` from `.env.example`
  - Fill in Reddit credentials and Supabase details
  - Run `pip install -r requirements.txt`
  - Run database initialization script
- How to run locally:
  - `uvicorn src.main:app --reload`
  - Visit `http://localhost:8000/docs` for API docs
- Troubleshooting common issues:
  - Import errors → verify virtual env activated
  - Database connection fails → check SUPABASE_URL/KEY
  - Reddit errors → verify credentials at reddit.com/prefs/apps

**File:** `README_SETUP.md`

### 5.3 Create API Documentation
- FastAPI auto-generates OpenAPI docs at `/docs` (Swagger UI)
- Add docstrings to all endpoints:
  - Summary (one line)
  - Description (detailed)
  - Parameters with types
  - Response examples (200, 400, 404, 500)
- Add docstrings to all service methods
- Create endpoint reference markdown

**File:** All route files + docstrings

### 5.4 Create GitHub Actions Workflow
- Create `.github/workflows/collect-schedule.yml`:
  - Trigger: `schedule` cron (e.g., "0 10 * * *" = daily 10 AM UTC)
  - Steps:
    1. Checkout repo
    2. Call `POST https://{deployed-url}/api/tasks/collect`
    3. Add header: `Authorization: Bearer {COLLECT_API_KEY}`
    4. Log response
    5. Notify on failure (optional: email or Slack)
- Document how to customize schedule
- Store COLLECT_API_KEY in GitHub Secrets

**File:** `.github/workflows/collect-schedule.yml`

---

## Verification Checklist

### Pre-Launch
- [ ] All dependencies install without errors: `pip install -r requirements.txt`
- [ ] Database schema created in Supabase (run SQL initialization script)
- [ ] `.env` configured with all required variables
- [ ] No environment variables hardcoded in code

### Local Testing
- [ ] App starts: `uvicorn src.main:app --reload` (no import errors)
- [ ] Health check: `curl http://localhost:8000/health` → returns 200
- [ ] Swagger docs load: `http://localhost:8000/docs`
- [ ] All test scenarios pass (from 5.1)

### Deployment
- [ ] Docker image builds: `docker build -t tracker-backend .`
- [ ] Docker runs locally with env vars
- [ ] Deploy to Render/Railway platform
- [ ] Health check responds from deployed URL
- [ ] GitHub Actions workflow executes successfully
- [ ] Data syncs to Supabase and Google Sheets

---

## Decisions & Scope

### Included (MVP)
- Subreddit performance tracking (weekly stats)
- Post-level engagement metrics and engagement rates
- Weekly statistics aggregation (posts, impressions, upvotes, comments)
- Comment tracking (original functionality retained)
- Automated data collection via GitHub Actions
- Excel and Google Sheets export
- Error handling and validation
- Cloud-ready deployment (Render/Railway compatible)

### Excluded (Future Phases)
- User authentication / multi-tenant support
- Advanced analytics (trend detection, ML predictions)
- Real-time data updates (weekly collection only)
- Rate limiting on endpoints
- API key authentication (except collection task)
- Batch import of subreddits
- Email notifications
- Dashboard UI (frontend responsibility)

### Key Assumptions
- Reddit API credentials available
- Supabase free tier sufficient
- GitHub Actions free tier for scheduling
- Engagement = (upvotes + comments) / impressions * 100
- Weekly cycle acceptable (not real-time)
- No RLS needed for single-user dev mode
- Manual SQL initialization acceptable

---

## Further Considerations

1. **Engagement Calculation:**
   Current: (upvotes + comments) / impressions * 100
   Future: Allow custom weighting, trending algorithms

2. **Data Retention:**
   How long to keep historical data? Recommend: 2 years rolling window

3. **Collection Frequency:**
   Current: Daily (configurable via GitHub Actions)
   Future: Support hourly, real-time updates

4. **Rate Limiting:**
   Current: PRAW handles Reddit rate limits
   Future: Add request rate limiting per IP, API key tier limits

5. **Multi-User Support:**
   Current: Single-user dev mode (no auth)
   Future: Add user authentication, separate data per user

### Setup

1. **Create project structure**
   - Initialize Python project with proper directory layout:
     - `backend/` root folder
     - `app/` (main application code)
     - `app/models/` (SQLAlchemy ORM models)
     - `app/schemas/` (Pydantic request/response models)
     - `app/routes/` (API endpoints)
     - `app/services/` (business logic: Reddit API, calculations)
     - `app/database/` (Supabase connection, migrations)
     - `app/tasks/` (scheduled jobs)
     - `app/utils/` (helpers, validators)
     - `config.py` (environment config)
     - `main.py` (FastAPI app initialization)
   - Create `.env.example` with placeholder variables (REDDIT_CLIENT_ID, REDDIT_SECRET, SUPABASE_URL, SUPABASE_KEY)

2. **Set up dependencies**
   - Create `requirements.txt` with:
     - `fastapi` (web framework)
     - `uvicorn` (ASGI server)
     - `praw` (Reddit API client)
     - `sqlalchemy` (ORM)
     - `psycopg2-binary` (PostgreSQL adapter)
     - `python-dotenv` (environment variables)
     - `pydantic` (data validation)
     - `httpx` (async HTTP client, optional but good for CORS/middleware)
     - `supabase` (Supabase client)
     - `openpyxl` (Excel export)
     - `gspread` (Google Sheets integration)
     - `google-auth` (Google authentication)

3. **Configure environment & secrets**
   - Create `config.py` to load environment variables:
     - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` (Reddit OAuth)
     - `SUPABASE_URL`, `SUPABASE_KEY` (database connection)
     - `DATABASE_URL` (PostgreSQL connection string, can be derived from Supabase)
     - `SCHEDULER_INTERVAL` (hours between data collection, default 24)
     - `ENV` (development/production flag)
   - Add `.env` to `.gitignore`

4. **Initialize Supabase project & database schema**
   - Create Supabase project (free tier)
   - Design PostgreSQL schema:
     - **subreddits** table: id (PK), name, created_at, updated_at
     - **weekly_stats** table: id (PK), subreddit_id (FK), week, total_posts, total_impressions, total_upvotes, total_comments, total_engagement, avg_engagement_rate
     - **posts** table: id (PK), subreddit_id (FK), reddit_post_id, title, url, author, created_at, updated_at
     - **post_weekly_stats** table: id (PK), post_id (FK), week, upvotes, impressions, comments_count, engagement, engagement_rate
     - **comments** table: id (PK), reddit_url, reddit_comment_id, subreddit, created_at, updated_at (original functionality)
     - **comment_history** table: id (PK), comment_id (FK), view_count, timestamp, weekly_avg (original functionality)
   - Create migrations or SQL initialization script
   - Store Supabase URL & API key in `.env`

### Phase 2:ORM models:
     - `Subreddit` model (maps to subreddits table)
     - `WeeklyStats` model (maps to weekly_stats table)
     - `Post` model (maps to posts table)
     - `PostWeeklyStats` model (maps to post_weekly_stats table)
     - `Comment` model (maps to comments table, original)
     - `CommentHistory` model (maps to comment_history table, original)
   - Create Pydantic schemas:
     - `SubredditCreate`, `SubredditResponse`
     - `WeeklyStatsResponse` (week, total_posts, impressions, avg_engagement_rate, etc.)
     - `PostResponse` (title, url, author)
     - `PostWeeklyStatsResponse` (upvotes, engagement_rate)
     - `CommentCreate`, `CommentResponse` (original)
   - Use appropriate validation (URL format, non-empty fields, date rangeid)
     - `CommentResponse` (GET response: id, url, latest view count, etc.)
     - `CommentHistoryResponse` (single history record)
     - `CommentDetailResponse` (full comment + recent history + weekly avg)
   - Use appropriate validation (URL format, non-empty fields)

6. **Set up FastAPI app & database connection**
   - Initialize FastAPI app in `main.py`subreddits.py)**
   - `POST /api/subreddits` — Add subreddit to track (accepts subreddit name)
   - `GET /api/subreddits` — List all tracked subreddits with latest stats
   - `GET /api/subreddits/{name}/weekly` — Get weekly stats for a subreddit (last 12 weeks)
   - `GET /api/subreddits/{name}/posts` — List posts for a subreddit with weekly metrics
   - `DELETE /api/subreddits/{name}` — Remove tracked subreddit

7b. **Create comment tracking endpoints (routes/comments.py)** (original functionality)
   - `POST /api/comments` — Add comment to track
   - `GET /api/comments` — List tracked comments
   - `GET /api/comments/{id}` — Get comment details
   - `DELETE /api/comments/{id}` — Remove
     - Validate comment exists on Reddit (make initial PRAW call)
     - Store in comments table
     - Return CommentResponse
   - `GET /api/comments` — List all tracked comments with latest stats
     - Return list of CommentResponse (id, url, current view count, last updated)
   - `DELETE /api/comments/{comment_id}` — Remove a tracked comment

8. **Create health check & status endpoint**
   - `GET /` orsubreddit data: `get_subreddit_posts(subreddit_name, limit)` → list of posts with stats
     - Fetches post metrics: `get_post_stats(post_id)` → {upvotes, impressions, comments_count}
     - Fetches comment data: `get_comment_view_count(comment_id)` (original functionality)
     - Parses Reddit URLs to extract IDs
     - Handles rate limiting gracefully (log warnings, retry with backoff)
     - Handles deleted/removed content gracefully
*Depends on Phase 2 completion*

9. **Implement Reddit API integration (services/reddit_service.py)**
   - Create `RedditClient` class that:
     - Initializes PRAW with credentials from env variables
     - Fetches a single comment by ID: `get_comment_view_count(comment_id)` → returns int or None
     - Parses Reddit URLs to extract comment ID: `extract_comment_id(url)` → returns string or raises error
     - Handles rate limiting gracefully (log warnings, retry with backoff)
     - H**Subreddit Collection:**
        - For each tracked subreddit, fetch posts for current week
        - Extract: total_posts, total_impressions, total_upvotes, total_comments
        - Calculate: engagement (upvotes + comments), avg_engagement_rate (engagement / impressions * 100)
        - Store in weekly_stats table
      - **Post Collection:**
        - For each post, fetch/update metrics (upvotes, impressions, comments)
        - Calculate engagement_rate per post
        - Store in post_weekly_stats table
      - **Comment Collection (original):**
        - Queries all tracked comments from database
        - Calls `RedditClient.get_comment_view_count()`
        - Records in comment_history table
        - Calculates 7-day average
      - Log collection events (successes, failures, skipped)
    - Handle partial failures (don't fail entire job if one subreddit/pos
      - For each, call `RedditClient.get_comment_view_count()`
      - Record result in comment_history table with current timestamp
      - Calculate weekly average: fetch history from last 7 days, compute mean, store
      - Log collection events (successes, failures, skipped)
    - Handle partial failures (don't fail entire job if one comment fails)
data collection task endpoint (tasks/collector_task.py)**
    - Create async endpoint: `POST /api/tasks/collect`

11. **Implement data collection task endpoint (tasks/collector_task.py)**
    - Create async endpoint: `POST /api/tasks/collect`
      - Trigger function: `collect_and_store_comment_data()`
      - Executes data collection job immediately (queries all comments, fetches view counts, stores history)
      - Calculates weekly averages as part of collection
      - Returns result summary: {status, comments_processed, success_count, error_count, timestamp}
      - Add basic authentication header check (optional API key validation)
    - Log all collection events (start, success, errors per comment)
    - This endpoint will be called by GitHub Actions workflow at scheduled times13)
*Parallel-ready: Can be done independently*

12. **Create Excel export endpoint (routes/export.py)**
    - `GET /api/export/excel` — Download all comments and history as Excel file
      - Uses `openpyxl` to create workbook with two sheets:
        - Sheet 1: Comments summary (id, url, subreddit, comment_id, created_at, current_view_count, last_updated)
        - Sheet 2: Full history (comment_id, timestamp, view_count, weekly_avg)
      - Returns file as downloadable attachment
      - Include timestamp in filename: `comment_data_YYYY-MM-DD.xlsx`

13. **Create Google Sheets sync endpoint (routes/export.py)**
    - `POST /api/export/sheets` — Sync all data to Google Sheet
      - Uses `gspread` and `google-auth` libraries
      - Authenticate via service account JSON (stored in env var or file)
      - Target spreadsheet specified via env var `GOOGLE_SHEETS_ID`
      - Create/update two sheets:
        - Sheet 1: Comments summary (same fields as Excel)
        - Sheet 2: History (same fields as Excel)
      - Returns result: {status, sheets_updated, rows_written, timestamp}
      - Logs sync events and errors

### Phase 5: Error Handling, Validation & Deployment Config (Steps 14-16)
*Parallel-ready: Steps 14 & 15, then 16 depends on both*

14. **Add comprehensive error handling**
    - Create `app/utils/exceptions.py` with custom exception classes:
      - `InvalidRedditURL` (malformed URL)
      - `CommentNotFound` (Reddit comment doesn't exist)
      - `RedditAPIError` (PRAW errors)
      - `DatabaseError` (Supabase connection issues)
    - Update all services to use these exceptions
    - Update FastAPI exception handlers to catch and return appropriate HTTP status codes (400, 404, 500)

15. **Add logging & monitoring**
    - Configure Python logging in `config.py` (log to console + file)
    - Add structured logs for:
      - Scheduler events (job start/end/error)
      - Reddit API calls (success/failure, retry attempts)
      - Database operations (inserts, errors)
      - API request/response (optional, can use middleware)
    - Include timestamp, level, message in all logs

16. **Create deployment configuration files**
    - `Dockerfile` (multi-stage: dependencies → app)
    - `.dockerignore` (exclude .git, venv, __pycache__, .env)
    - `requirements.txt` with exact versions (for reproducibility)
    - Deployment guide (README or DEPLOY.md) with:
      - How to set up environment variables on Render/Railway
      - How to run migrations on first deploy
      - How to scale (if needed)

### Phase 6: Testing & Documentation (Steps 17-19)
*Parallel-ready: Steps 17 & 18, then 19 after both*

17. **Create manual test checklist**
    - Test Reddit integration:
      - Add valid Reddit comment URL → confirm stored in DB
      - Fetch view count for tracked comment → confirm returns number
      - Trigger collection manually via `POST /api/tasks/collect` → confirm history records created
      - Add invalid URL → confirm error response
    - Test API endpoints:
      - POST /api/comments with valid/invalid inputs
      - GET /api/comments → list all
      - GET /api/comments/{id} → detail view
    - Test export & integration:
      - `GET /api/export/excel` → verify Excel file downloads with correct data
      - `POST /api/export/sheets` → verify data appears in Google Sheet
    - Test error scenarios:
      - Deleted Reddit comment
      - Invalid Reddit credentials
      - Database connection failure
      - Collection endpoint retry behavior

18. **Create setup documentation (README for backend)**
    - Local development setup: clone, `pip install -r requirements.txt`, `.env` config
    - How to run locally: `uvicorn app.main:app --reload`
    - How to test manually: curl examples or Postman collection
    - Environment variables explained (including GOOGLE_SHEETS_ID, Google service account)
    - GitHub Actions workflow setup: `.github/workflows/collect-schedule.yml` template
    - Troubleshooting common issues

19. **Add API documentation & GitHub Actions workflow**
    - Create `.github/workflows/collect-schedule.yml` file:
      - Trigger: `schesubreddits.py` — Subreddit tracking endpoints (add/list/stats/posts)
- `backend/app/routes/comments.py` — Comment tracking endpoints (original functionality
      - Action: Make HTTP POST request to deployed `/api/tasks/collect` endpoint
      - Include optional API key header for basic auth
      - Log response and notify on failure (email or Slack)
    - FastAPI auto-generates OpenAPI docs at `/docs` (Swagger UI)
    - Add docstrings to all endpoints and services (FastAPI will include in auto-docs)
    - Optional: Create simple endpoint reference markdown

---

## Relevant Files
- `backend/main.py` — FastAPI app initialization, router includes
- `backend/config.py` — Environment and configuration loading
- `backend/app/models.py` — SQLAlchemy ORM for Comment and CommentHistory
- `backend/app/schemas.py` — Pydantic request/response models
- `backend/app/routes/comments.py` — All API endpoint handlers (add/list/detail/delete)
- `backend/app/routes/export.py` — Export endpoints (Excel, Google Sheets)
- `backend/app/services/reddit_service.py` — PRAW integration and Reddit API logic
- `backend/app/services/collector_service.py` — Data collection, storage, averaging
- `backend/app/tasks/collector_task.py` — Data collection task endpoint (called by GitHub Actions)
- `backend/app/utils/exceptions.py` — Custom exception classes
- `backend/app/database/` — Database session management and connection
- `backend/.env.example` — Template for environment variables (including Google Sheets config)
- `backend/requirements.txt` — Python dependencies (updated with gspread, google-auth, openpyxl)
- `.github/workflows/collect-schedule.yml` — GitHub Actions workflow for scheduled data collection
- `backend/Dockerfile` — Containerization for deployment
- `backensubreddit: `curl -X POST http://localhost:8000/api/subreddits -H "Content-Type: application/json" -d '{"name": "AskReddit"}'` → returns 201
2. ✅ Get weekly stats: `GET /api/subreddits/AskReddit/weekly` → returns array of weekly metrics
3. ✅ Get posts: `GET /api/subreddits/AskReddit/posts` → returns posts with engagement rates
4. ✅ Trigger collection: `POST /api/tasks/collect` → updates weekly_stats and post_weekly_stats
5. ✅ Verify calculations: Check avg_engagement_rate = (total_engagement / total_impressions) * 100
6. ✅ Add comment: `POST /api/comments` with URL → stored in comments table (original)
7. ✅ Export data: `GET /api/export/excel` includes both subreddit stats and comment data
8. ✅ Handle errors: Invalid subreddit name → returns 400 with error message
2. FastAPI app starts: `uvicorn app.main:app --reload` (no import errors)
3. Health check endpoint returns 200: `curl http://localhost:8000/health`
4. GitHub Actions workflow file exists and has valid syntax: `.github/workflows/collect-schedule.yml`

### Manual Testing
1. ✅ Add a comment: `curl -X POST http://localhost:8000/api/comments -H "Content-Type: application/json" -d '{"reddit_url": "<valid Reddit comment URL>"}'` → returns 201 with comment ID
2. ✅ Fetch comment list: `GET /api/comments` → returns array of comments
3. ✅ Trigger collection: `POST http://localhost:8000/api/tasks/collect` → returns success, check database for new history records
4. ✅ Export to Excel: `GET http://localhost:8000/api/export/excel` → downloads Excel file with data
5. ✅ Export to Google Sheets: `POST http://localhost:8000/api/export/sheets` → syncs data to Google Sheet
6. ✅ Verify weekly avg calculation: After 7+ days of data, `GET /api/comments/{id}` includes `weekly_avg` field
7.Subreddit performance tracking (weekly stats)
- Post-level metrics and engagement rates
- Weekly statistics aggregation (posts, impressions, upvotes, comments, engagement)
- Calculated engagement rates (engagement / impressions * 100)
- Comment tracking (original functionality retained)
- Automated daily data collection via GitHub Actions
- Excel and Google Sheets export (includes all subreddit and comment data)
1. ✅ Build Docker image: `docker build -t tracker-backend .`
2. ✅ Run container locally: `docker run -e DATABASE_URL=... tracker-backend` (with env vars)
3. ✅ Deploy to Render/Railway: Follow platform-specific steps, verify `/health` responds from deployed URL

---ML predictions, comparisons)
- Export to PDF/CSV
- Dashboard visualization (handled by frontend)
- Rate-limiting on API endpoints
- API key authentication for backend endpoints
- Batch import of subreddits
- Email notifications
- Real-time data updates (weekly collection only)a collection via GitHub Actions (external scheduler)
- Weekly average calculation
- Excel aAPI credentials available (user will supply)
- Supabase free tier sufficient for tracking multiple subreddits
- GitHub Actions free tier available for scheduled workflow
- Data collection weekly or daily is acceptable frequency (configurable)
- Google Sheets integration optional for users
- Engagement calculation: (upvotes + comments) / impressions * 100
- No need for real-time updates (weekly collection sufficient)
- Database migrations managed manually or via simple SQL script
- Export to PDF/CSV
- Dashboard visualization (handled by frontend)
- Rate-limiting on API endpoints
- API key authentication for backend endpoints
- Batch import of comments
- Email notifications

### Key Assumptions
- Reddit OAuth credentials available (user will supply)
- Supabase free tier sufficient for MVP scale
- GitHub Actions free tier available for scheduled workflow (allows up to 20 concurrent jobs)
- Data collection via external HTTP trigger acceptable (no persistent in-process scheduler)
- Google Sheets integration optional for users (config stored in env var)
- No need for API rate-limiting initially (small-scale use)
- Database migrations managed manually or via simple SQL script (not full ORM migration framework)

## Further Considerations

1. **GitHub Actions Scheduling:**  
   Cron syntax in GitHub Actions uses UTC timezone. Should times be user-configurable via `.env` or hardcoded?  
   *Recommendation*: Hardcode UTC 10:00 AM in workflow (MVP). Allow env-based override in Phase 2.

2. **Google Sheets Authentication:**  
   Service account vs OAuth flow for Google Sheets?  
   *Recommendation*: Service account JSON (simpler for automated workflows). Include setup guide for generating service account.

3. **Reddit API Rate Limits:**  
   PRAW handles rate limits via backoff. Should we add configurable backoff strategy or accept defaults?  
   *Recommendation*: Accept PRAW defaults for MVP, add custom strategy if needed.

4. **Weekly Average Timing:**  
   Should weekly averages reset Sunday→Sunday, or every 7 days from comment creation?  
   *Recommendation*: Every 7 days from first collection (simpler to implement).

5. **Collection Endpoint Security:**  
   Should `POST /api/tasks/collect` require authentication to prevent abuse?  
   *Recommendation*: Add optional `COLLECT_API_KEY` env var with basic header validation (MVP). Enforce in production.
