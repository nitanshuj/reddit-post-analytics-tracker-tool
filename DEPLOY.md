# Deployment Guide: Reddit Analytics Tracker Backend

This guide covers deploying the FastAPI backend to Render or Railway without Docker.

## Overview

Both Render and Railway support direct Python deployments:
- Auto-detect Python projects via `requirements.txt`
- Install dependencies automatically
- Support environment variables in dashboard
- Free tier includes 750 hours/month
- Automatic HTTPS

## Pre-Deployment Checklist

- [ ] GitHub repo connected to Render/Railway
- [ ] `.env` configured locally with all required variables
- [ ] Database schema created in Supabase
- [ ] Reddit API credentials valid
- [ ] (Optional) Google Sheets service account JSON created

## Deployment Steps

### Step 1: Prepare Database Connection String

#### For Supabase:
1. Go to your Supabase project settings
2. Copy the connection string under "Database" → "Connection pooling"
3. Format: `postgresql://postgres:[PASSWORD]@[HOST]/postgres`

#### Set Environment Variable:
```bash
# In your Render/Railway dashboard:
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_HOST/postgres
```

### Step 2: Deploy to Render

#### 2.1 Connect GitHub Repository

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Select your GitHub repository
5. Choose branch (e.g., `main`)

#### 2.2 Configure Service

**Service Details:**
- **Name:** reddit-tracker-backend
- **Environment:** Python 3.11
- **Region:** Choose closest to your users

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

**Important:** Render automatically assigns `$PORT` from environment.

#### 2.3 Add Environment Variables

In Render dashboard, go to "Environment" and add all variables:

```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=script:reddit.tracker:v1

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://postgres:PASSWORD@HOST/postgres

GOOGLE_SHEETS_ID=your_google_sheets_id
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=/etc/secrets/service-account.json

COLLECT_API_KEY=your_secret_api_key
ENV=production
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

#### 2.4 Add Google Service Account Secret (Optional)

If using Google Sheets integration:

1. Create a service account in Google Cloud Console
2. Download JSON file
3. In Render, go to "Environment" → "Add Secret File"
4. **File Name:** `/etc/secrets/service-account.json`
5. **Contents:** Paste entire JSON file
6. **Path in Environment:** `/etc/secrets/service-account.json`

#### 2.5 Deploy

Click "Deploy" button. Render will:
1. Clone repository
2. Install dependencies from `requirements.txt`
3. Run your app with the start command
4. Assign a public URL (e.g., `https://reddit-tracker-backend.onrender.com`)

**Deployment usually takes 2-5 minutes**

### Step 3: Deploy to Railway (Alternative)

#### 3.1 Connect Repository

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository

#### 3.2 Configure Service

Railway auto-detects Python from `requirements.txt`

**Set Start Command (in railway.toml):**

Create file `railway.toml` in repo root:
```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
```

Or just create `Procfile` in root:
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

#### 3.3 Add Environment Variables

In Railway dashboard, go to "Variables" and add:
- Same list as Render (see Step 2.3)

#### 3.4 Deploy

Railway auto-deploys on git push. Monitor via dashboard.

### Step 4: Initialize Database Schema

After deployment, you need to create the database tables in Supabase.

#### Option A: Using SQL Editor (Supabase)

1. Go to Supabase dashboard → SQL Editor
2. Run the following SQL script:

```sql
-- Create tables
CREATE TABLE subreddits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weekly_stats (
    id SERIAL PRIMARY KEY,
    subreddit_id INTEGER NOT NULL REFERENCES subreddits(id) ON DELETE CASCADE,
    week VARCHAR(50) NOT NULL,
    total_posts INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    upvotes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    engagement INTEGER DEFAULT 0,
    avg_engagement_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    subreddit_id INTEGER NOT NULL REFERENCES subreddits(id) ON DELETE CASCADE,
    reddit_post_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    author VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE post_weekly_stats (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    week VARCHAR(50) NOT NULL,
    upvotes INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    engagement INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    reddit_url VARCHAR(1000) UNIQUE NOT NULL,
    reddit_comment_id VARCHAR(255) NOT NULL,
    subreddit VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comment_history (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    view_count INTEGER DEFAULT 0,
    weekly_avg FLOAT DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_weekly_stats_subreddit ON weekly_stats(subreddit_id);
CREATE INDEX idx_posts_subreddit ON posts(subreddit_id);
CREATE INDEX idx_post_weekly_stats_post ON post_weekly_stats(post_id);
CREATE INDEX idx_comment_history_comment ON comment_history(comment_id);
```

#### Option B: Using Python Script (Local)

Create `init_db.py` in repo root:

```python
from src.app.models import Base
from src.app.database.session import engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
```

Run locally:
```bash
python init_db.py
```

### Step 5: Test Deployment

#### Test Health Endpoint
```bash
curl https://your-deployed-url/health
# Expected response: {"status":"ok","timestamp":"2026-05-12T..."}
```

#### Test API Docs
Visit: `https://your-deployed-url/docs` (Swagger UI)

#### Test Collection Endpoint
```bash
curl -X POST https://your-deployed-url/api/tasks/collect \
  -H "Authorization: Bearer YOUR_COLLECT_API_KEY"
```

### Step 6: Set Up GitHub Actions Scheduled Collection

Create `.github/workflows/collect-schedule.yml`:

```yaml
name: Scheduled Data Collection

on:
  schedule:
    # Run daily at 10 AM UTC
    - cron: '0 10 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  collect:
    runs-on: ubuntu-latest
    
    steps:
      - name: Trigger collection
        run: |
          curl -X POST https://YOUR_DEPLOYED_URL/api/tasks/collect \
            -H "Authorization: Bearer ${{ secrets.COLLECT_API_KEY }}" \
            -H "Content-Type: application/json"
      
      - name: Log response
        if: always()
        run: echo "Collection job completed"
```

**Add GitHub Secret:**
1. Go to repo Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `COLLECT_API_KEY`
4. Value: Your COLLECT_API_KEY from env

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REDDIT_CLIENT_ID` | Yes | Reddit OAuth client ID | `abc123xyz` |
| `REDDIT_CLIENT_SECRET` | Yes | Reddit OAuth client secret | `secret123` |
| `REDDIT_USERNAME` | Yes | Reddit bot username | `myredditbot` |
| `REDDIT_PASSWORD` | Yes | Reddit bot password | `password123` |
| `SUPABASE_URL` | Yes | Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Yes | Supabase anon key | `key123xyz` |
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://...` |
| `COLLECT_API_KEY` | No | Secret key for collection endpoint | `secret_key_123` |
| `GOOGLE_SHEETS_ID` | No | Google Sheets ID for sync | `1a2b3c4d...` |
| `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` | No | Path to service account JSON | `/etc/secrets/service-account.json` |
| `ENV` | No | Environment mode | `production` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `LOG_FILE` | No | Log file path | `logs/app.log` |

## Troubleshooting

### Deployment Failed: Module not found

**Issue:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
- Ensure `src/` directory is in repo root
- Check `requirements.txt` has all dependencies
- Verify Python version is 3.11+

### Database Connection Error

**Issue:** `psycopg2.OperationalError: connection refused`

**Solution:**
- Verify `DATABASE_URL` is correct
- Check Supabase project is active
- Test connection locally first
- Check IP whitelist (if using managed database)

### Google Sheets Sync Fails

**Issue:** `google.auth.exceptions.DefaultCredentialsError`

**Solution:**
- Verify service account JSON file exists at path
- Check `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` env var is set
- Ensure service account has Sheets API enabled
- Test locally with actual JSON file

### Collection Endpoint Returns 401

**Issue:** Collection task fails with 401 Unauthorized

**Solution:**
- Verify `COLLECT_API_KEY` matches in GitHub Secrets and deployed env vars
- Check Authorization header format: `Bearer YOUR_KEY`
- If no key needed, leave `COLLECT_API_KEY` empty in env

## Monitoring & Logs

### View Logs in Render
1. Dashboard → Service → Logs
2. See real-time app output
3. Check for errors during collection tasks

### View Logs in Railway
1. Dashboard → Service → Logs
2. Filter by date/time
3. Search for keywords

### Export Logs
Both platforms allow exporting logs for analysis

## Scaling Considerations

### When to Scale:
- **More Subreddits:** Current free tier handles 100+
- **More Frequent Collection:** Use GitHub Actions for daily/hourly
- **Larger File Exports:** Use Render/Railway's paid tier (higher memory)

### Scaling Options:
- **Render Pro:** $25/month (1 GB RAM, more bandwidth)
- **Railway Deployments:** Pay-per-use (~$5/month typical)
- **Supabase Pro:** $25/month (more storage, better performance)

## Security Best Practices

1. **Never commit secrets:**
   - Always use dashboard env vars
   - Add `.env` to `.gitignore`

2. **Rotate API Keys:**
   - Change `COLLECT_API_KEY` regularly
   - Update Reddit credentials if compromised

3. **Use HTTPS:**
   - All traffic encrypted automatically
   - Render/Railway provide free SSL

4. **Monitor Logs:**
   - Check for unusual API calls
   - Alert on repeated errors

## Updating the App

To update after code changes:

**For Render:**
1. Push code to GitHub
2. Render auto-deploys on push (if auto-deploy enabled)
3. Or click "Manual Deploy"

**For Railway:**
1. Push code to GitHub
2. Railway auto-deploys on push
3. Monitor logs during deployment

## Backup & Data Retention

### Database Backups
- Supabase auto-backs up daily
- Keep 7-day rolling backups free tier
- Export data regularly via Excel export endpoint

### Export Data Regularly
```bash
# Download Excel file (no auth needed for MVP)
curl https://your-deployed-url/api/export/excel -o backup.xlsx

# Or sync to Google Sheets (if configured)
curl -X POST https://your-deployed-url/api/export/sheets
```

## Further Resources

- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
