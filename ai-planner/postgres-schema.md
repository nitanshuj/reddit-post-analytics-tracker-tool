# PostgreSQL Schema for Comment Analytics Tracker

## Overview
This document defines the database schema for the Comment Analytics Tracker MVP. The schema tracks Reddit subreddit performance metrics including weekly stats (posts, impressions, engagement) and individual post/comment details.

**Tracking Scope:**
- Weekly subreddit statistics (posts, impressions, upvotes, comments, engagement)
- Individual post metrics and history
- Comment view counts and engagement
- Calculated engagement rates

---

## Data Model Relationships

```
┌──────────────────┐
│   subreddits     │
├──────────────────┤
│ id (PK)          │◄─────┐
│ name             │      │
│ created_at       │      │ 1:N
│ updated_at       │      │
└──────────────────┘      │
        ▲                  │
        │                  │
        ├──────────────────┼───────────────┐
        │                  │               │
        │         ┌────────┴────────┐  ┌───┴────────────────┐
        │         │                 │  │                    │
        │    ┌─────────────────┐   ┌────────────────┐   ┌──────────────────┐
        │    │ posts           │   │ weekly_stats   │   │ comments         │
        │    ├─────────────────┤   ├────────────────┤   ├──────────────────┤
        │    │ id (PK)         │   │ id (PK)        │   │ id (PK)          │
        │    │ subreddit_id──┐ │   │ subreddit_id──┐│   │ reddit_url       │
        │    │ reddit_post_id│ │   │ week          ││   │ reddit_comment_id│
        └────│ title         │ │   │ total_posts   ││   │ subreddit        │
             │ url           │ │   │ impressions   ││   │ created_at       │
             │ author        │ │   │ upvotes       ││   │ updated_at       │
             │ created_at    │ │   │ comments      ││   └──────────────────┘
             └─────────────────┘   │ engagement    ││
                      │            │ avg_engagement││
                      │            │ timestamp     ││
                      │            └────────────────┘
                      │                  │
                      ▼                  │
             ┌──────────────────────┐   │
             │ post_weekly_stats    │   │
             ├──────────────────────┤   │
             │ id (PK)              │◄──┘
             │ post_id (FK)─────┐   │
             │ week             │   │
             │ upvotes          │   │
             │ impressions      │   │
             │ comments_count   │   │
             │ engagement       │   │
             │ engagement_rate  │   │
             │ timestamp        │   │
             └──────────────────────┘
```

- **One-to-Many**: Each subreddit → many weekly_stats, posts, comments
- **One-to-Many**: Each post → many post_weekly_stats
- **Cascade Delete**: Deleting subreddit/post deletes related records

---

## Tables

### 1. `subreddits` Table
Tracks which subreddits are being monitored.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing primary key |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE | Subreddit name (e.g., AskReddit) |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | When added to tracker (UTC) |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Last update (UTC) |

---

### 2. `weekly_stats` Table
Weekly aggregated statistics for a subreddit.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing primary key |
| `subreddit_id` | BIGINT | NOT NULL, FK | Foreign key to `subreddits.id` |
| `week` | DATE | NOT NULL | Start date of week (Monday) |
| `total_posts` | INT | NOT NULL | Total posts in subreddit for this week |
| `total_impressions` | BIGINT | NOT NULL | Total impressions across all posts |
| `total_upvotes` | BIGINT | NOT NULL | Total upvotes across all posts |
| `total_comments` | BIGINT | NOT NULL | Total comments across all posts |
| `total_engagement` | BIGINT | NOT NULL | Sum of (upvotes + comments) |
| `avg_engagement_rate` | DECIMAL(10, 2) | NOT NULL | engagement / impressions * 100 |
| `timestamp` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | When collected (UTC) |

**Indexes:**
- `idx_weekly_stats_subreddit_id` on `subreddit_id`
- `idx_weekly_stats_week` on `week`
- `idx_weekly_stats_subreddit_week` on `(subreddit_id, week)` (unique)

---

### 3. `posts` Table
Individual posts from tracked subreddits.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing primary key |
| `subreddit_id` | BIGINT | NOT NULL, FK | Foreign key to `subreddits.id` |
| `reddit_post_id` | VARCHAR(10) | NOT NULL | Reddit's post ID |
| `title` | TEXT | NOT NULL | Post title |
| `url` | VARCHAR(500) | NOT NULL | Post URL |
| `author` | VARCHAR(255) | NULL | Post author (nullable, some may be deleted) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Post creation time (UTC) |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Last tracking update (UTC) |

**Indexes:**
- `idx_posts_subreddit_id` on `subreddit_id`
- `idx_posts_reddit_post_id` on `reddit_post_id`
- `idx_posts_created_at` on `created_at`

---

### 4. `post_weekly_stats` Table
Weekly metrics for individual posts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing primary key |
| `post_id` | BIGINT | NOT NULL, FK | Foreign key to `posts.id` |
| `week` | DATE | NOT NULL | Week start date (UTC) |
| `upvotes` | INT | NOT NULL | Upvotes for this week |
| `impressions` | INT | NOT NULL | Impressions/views for this week |
| `comments_count` | INT | NOT NULL | Comment count for this week |
| `engagement` | INT | NOT NULL | upvotes + comments_count |
| `engagement_rate` | DECIMAL(10, 2) | NOT NULL | engagement / impressions * 100 |
| `timestamp` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | When collected (UTC) |

**Indexes:**
- `idx_post_weekly_stats_post_id` on `post_id`
- `idx_post_weekly_stats_week` on `week`
- `idx_post_weekly_stats_post_week` on `(post_id, week)` (unique)

---

### 5. `comments` Table
Individual comments being tracked (original functionality retained).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing primary key |
| `reddit_url` | VARCHAR(500) | NOT NULL, UNIQUE | Full Reddit comment URL |
| `reddit_comment_id` | VARCHAR(10) | NOT NULL, UNIQUE | Reddit's internal comment ID |
| `subreddit` | VARCHAR(255) | NOT NULL | Subreddit name |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | When added to tracker (UTC) |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | Last update (UTC) |

**Indexes:**
- `idx_comments_comment_id` on `reddit_comment_id`
- `idx_comments_subreddit` on `subreddit`
- `idx_comments_created_at` on `created_at`

---

### 6. `comment_history` Table
View count snapshots for tracked comments (original functionality retained).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing primary key |
| `comment_id` | BIGINT | NOT NULL, FK | Foreign key to `comments.id` |
| `view_count` | INT | NOT NULL | Views at time of collection |
| `timestamp` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | When collected (UTC) |
| `weekly_avg` | DECIMAL(10, 2) | NULL | 7-day rolling average |

**Indexes:**
- `idx_comment_history_comment_id` on `comment_id`
- `idx_comment_history_timestamp` on `timestamp`
- `idx_comment_history_comment_timestamp` on `(comment_id, timestamp)`

---

## SQL Creation Queries

Run this SQL script to create all tables and indexes:

```sql
-- Create subreddits table
CREATE TABLE IF NOT EXISTS subreddits (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create weekly_stats table
CREATE TABLE IF NOT EXISTS weekly_stats (
    id BIGSERIAL PRIMARY KEY,
    subreddit_id BIGINT NOT NULL REFERENCES subreddits(id) ON DELETE CASCADE,
    week DATE NOT NULL,
    total_posts INT NOT NULL,
    total_impressions BIGINT NOT NULL,
    total_upvotes BIGINT NOT NULL,
    total_comments BIGINT NOT NULL,
    total_engagement BIGINT NOT NULL,
    avg_engagement_rate DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subreddit_id, week)
);

-- Create posts table
CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    subreddit_id BIGINT NOT NULL REFERENCES subreddits(id) ON DELETE CASCADE,
    reddit_post_id VARCHAR(10) NOT NULL,
    title TEXT NOT NULL,
    url VARCHAR(500) NOT NULL,
    author VARCHAR(255) NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create post_weekly_stats table
CREATE TABLE IF NOT EXISTS post_weekly_stats (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    week DATE NOT NULL,
    upvotes INT NOT NULL,
    impressions INT NOT NULL,
    comments_count INT NOT NULL,
    engagement INT NOT NULL,
    engagement_rate DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, week)
);

-- Create comments table
CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    reddit_url VARCHAR(500) NOT NULL UNIQUE,
    reddit_comment_id VARCHAR(10) NOT NULL UNIQUE,
    subreddit VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create comment_history table
CREATE TABLE IF NOT EXISTS comment_history (
    id BIGSERIAL PRIMARY KEY,
    comment_id BIGINT NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    view_count INT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    weekly_avg DECIMAL(10, 2) NULL
);

-- Create indexes on subreddits table
CREATE INDEX IF NOT EXISTS idx_subreddits_name ON subreddits(name);

-- Create indexes on weekly_stats table
CREATE INDEX IF NOT EXISTS idx_weekly_stats_subreddit_id ON weekly_stats(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_weekly_stats_week ON weekly_stats(week);
CREATE INDEX IF NOT EXISTS idx_weekly_stats_subreddit_week ON weekly_stats(subreddit_id, week);

-- Create indexes on posts table
CREATE INDEX IF NOT EXISTS idx_posts_subreddit_id ON posts(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_posts_reddit_post_id ON posts(reddit_post_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);

-- Create indexes on post_weekly_stats table
CREATE INDEX IF NOT EXISTS idx_post_weekly_stats_post_id ON post_weekly_stats(post_id);
CREATE INDEX IF NOT EXISTS idx_post_weekly_stats_week ON post_weekly_stats(week);
CREATE INDEX IF NOT EXISTS idx_post_weekly_stats_post_week ON post_weekly_stats(post_id, week);

-- Create indexes on comments table
CREATE INDEX IF NOT EXISTS idx_comments_comment_id ON comments(reddit_comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_subreddit ON comments(subreddit);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at);

-- Create indexes on comment_history table
CREATE INDEX IF NOT EXISTS idx_comment_history_comment_id ON comment_history(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_history_timestamp ON comment_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_comment_history_comment_timestamp ON comment_history(comment_id, timestamp);
```

---

## Sample Queries

### 1. Get Weekly Stats for a Subreddit
```sql
SELECT 
    s.name,
    ws.week,
    ws.total_posts,
    ws.total_impressions,
    ws.total_upvotes,
    ws.total_comments,
    ws.avg_engagement_rate
FROM subreddits s
JOIN weekly_stats ws ON s.id = ws.subreddit_id
WHERE s.name = $1
ORDER BY ws.week DESC
LIMIT 12;  -- Last 12 weeks
```

### 2. Get Top Posts by Engagement Rate
```sql
SELECT 
    p.title,
    p.url,
    pws.upvotes,
    pws.impressions,
    pws.comments_count,
    pws.engagement_rate
FROM posts p
JOIN post_weekly_stats pws ON p.id = pws.post_id
WHERE p.subreddit_id = $1 AND pws.week = $2
ORDER BY pws.engagement_rate DESC
LIMIT 10;
```

### 3. Calculate Average Engagement Rate for a Week
```sql
SELECT 
    AVG(engagement_rate) as avg_engagement
FROM post_weekly_stats
WHERE week = $1;
```

### 4. Compare Weekly Performance
```sql
SELECT 
    s.name,
    ws.week,
    ws.total_posts,
    ws.avg_engagement_rate,
    LAG(ws.avg_engagement_rate) OVER (PARTITION BY s.id ORDER BY ws.week) as prev_week_rate
FROM subreddits s
JOIN weekly_stats ws ON s.id = ws.subreddit_id
WHERE s.id = $1
ORDER BY ws.week DESC;
```

---

## Metrics Definitions

- **Impressions**: Total views/impressions across all posts in the period
- **Engagement**: Sum of upvotes and comments (upvotes + comments_count)
- **Engagement Rate**: (Engagement / Impressions) × 100 (percentage)
- **Average Engagement Rate**: Mean engagement rate across all posts in the period

## Notes

- **Timestamps**: All timestamps use `TIMESTAMP WITH TIME ZONE` (UTC)
- **Week**: Start date of week (Monday) for consistent grouping
- **Cascade Delete**: Deletes maintain referential integrity
- **Engagement Calculation**: Simple formula (upvotes + comments) / impressions * 100
- **Unique Constraints**: `(subreddit_id, week)` and `(post_id, week)` prevent duplicate reporting

---

## Migration Path

1. **Local Development**: Run initialization script in local Supabase instance
2. **Production Deployment**: Run script on Supabase-hosted PostgreSQL database
3. **Future Migrations**: Use SQL scripts or ORM migration tools (SQLAlchemy Alembic)

### 1. Get Latest View Count for All Comments
```sql
SELECT 
    c.id,
    c.reddit_url,
    c.subreddit,
    ch.view_count,
    ch.timestamp
FROM comments c
JOIN comment_history ch ON c.id = ch.comment_id
WHERE (c.id, ch.timestamp) IN (
    SELECT comment_id, MAX(timestamp) 
    FROM comment_history 
    GROUP BY comment_id
)
ORDER BY c.created_at DESC;
```

### 2. Get Weekly Average for a Specific Comment
```sql
SELECT 
    c.reddit_url,
    AVG(ch.view_count) as weekly_avg
FROM comments c
JOIN comment_history ch ON c.id = ch.comment_id
WHERE c.id = $1
    AND ch.timestamp >= NOW() - INTERVAL '7 days'
GROUP BY c.id, c.reddit_url;
```

### 3. Get Top 10 Comments by View Count
```sql
SELECT 
    c.reddit_url,
    c.subreddit,
    MAX(ch.view_count) as max_views,
    COUNT(ch.id) as collection_count
FROM comments c
JOIN comment_history ch ON c.id = ch.comment_id
GROUP BY c.id, c.reddit_url, c.subreddit
ORDER BY max_views DESC
LIMIT 10;
```

### 4. Check for Comments with No Recent Data (>24 hours)
```sql
SELECT 
    c.id,
    c.reddit_url,
    MAX(ch.timestamp) as last_collection
FROM comments c
LEFT JOIN comment_history ch ON c.id = ch.comment_id
GROUP BY c.id, c.reddit_url
HAVING MAX(ch.timestamp) < NOW() - INTERVAL '24 hours' 
    OR MAX(ch.timestamp) IS NULL
ORDER BY MAX(ch.timestamp) ASC;
```

---

## Notes

- **Timestamps**: All timestamps use `TIMESTAMP WITH TIME ZONE` (UTC) for consistency across time zones
- **Scaling**: BIGSERIAL supports up to ~9 billion records per table; sufficient for MVP and beyond
- **View Count**: Stored as INT (sufficient for Reddit view counts, max ~2 billion)
- **Weekly Average**: DECIMAL(10, 2) provides precision for fractional averages (up to 99999999.99)
- **Cascade Delete**: Ensures data integrity when comments are removed
- **Indexes**: Cover common query patterns (filters, joins, ordering)

---

## Migration Path

1. **Local Development**: Run initialization script in local Supabase instance
2. **Production Deployment**: Run script on Supabase-hosted PostgreSQL database
3. **Future Migrations**: Use SQL scripts or ORM migration tools (SQLAlchemy Alembic) if schema changes needed
