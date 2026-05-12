from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from src.app.database.session import get_db
from src.app.models import Subreddit, WeeklyStats, Post, PostWeeklyStats
from src.app.schemas import SubredditCreate, SubredditResponse, WeeklyStatsResponse, PostResponse, PostWeeklyStatsResponse
from src.app.services.reddit_service import RedditClient
from src.app.utils.exceptions import SubredditNotFound, ValidationError

router = APIRouter(prefix="/api/subreddits", tags=["subreddits"])


class SubredditWithStats(SubredditResponse):
    """Subreddit with latest weekly stats."""
    latest_week: Optional[str] = None
    total_posts: int = 0
    impressions: int = 0
    avg_engagement_rate: float = 0.0


@router.post("", response_model=SubredditResponse, status_code=201)
def add_subreddit(subreddit: SubredditCreate, db: Session = Depends(get_db)):
    """Add a subreddit to track. Validates subreddit exists on Reddit."""
    # Validate input
    if not subreddit.name or not subreddit.name.strip():
        raise HTTPException(status_code=400, detail="Subreddit name cannot be empty")
    
    # Check if already tracked
    existing = db.query(Subreddit).filter(Subreddit.name == subreddit.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subreddit already tracked")
    
    # Validate subreddit exists on Reddit
    try:
        reddit = RedditClient()
        if not reddit.is_subreddit_valid(subreddit.name):
            raise HTTPException(status_code=404, detail=f"Subreddit r/{subreddit.name} not found on Reddit")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not validate subreddit: {str(e)}")
    
    new_subreddit = Subreddit(name=subreddit.name)
    db.add(new_subreddit)
    db.commit()
    db.refresh(new_subreddit)
    return new_subreddit


@router.get("", response_model=List[dict])
def list_subreddits(db: Session = Depends(get_db)):
    """List all tracked subreddits with latest stats summary."""
    subreddits = db.query(Subreddit).all()
    result = []
    
    for sub in subreddits:
        # Get latest weekly stats
        latest_stat = db.query(WeeklyStats).filter(
            WeeklyStats.subreddit_id == sub.id
        ).order_by(WeeklyStats.week.desc()).first()
        
        result.append({
            "id": sub.id,
            "name": sub.name,
            "created_at": sub.created_at,
            "latest_week": latest_stat.week if latest_stat else None,
            "total_posts": latest_stat.total_posts if latest_stat else 0,
            "impressions": latest_stat.impressions if latest_stat else 0,
            "avg_engagement_rate": round(latest_stat.avg_engagement_rate, 2) if latest_stat else 0.0
        })
    
    return result


@router.get("/{name}/weekly", response_model=List[WeeklyStatsResponse])
def get_weekly_stats(name: str, db: Session = Depends(get_db)):
    """Get weekly stats for a subreddit (last 12 weeks, sorted DESC)."""
    subreddit = db.query(Subreddit).filter(Subreddit.name == name).first()
    if not subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    
    stats = db.query(WeeklyStats).filter(
        WeeklyStats.subreddit_id == subreddit.id
    ).order_by(desc(WeeklyStats.week)).limit(12).all()
    
    return stats


@router.get("/{name}/posts", response_model=List[PostResponse])
def get_subreddit_posts(
    name: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get posts for a subreddit, sorted by engagement rate DESC."""
    subreddit = db.query(Subreddit).filter(Subreddit.name == name).first()
    if not subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    
    posts = db.query(Post).filter(
        Post.subreddit_id == subreddit.id
    ).order_by(desc(Post.id)).limit(limit).all()
    
    return posts


@router.delete("/{name}", status_code=204)
def delete_subreddit(name: str, db: Session = Depends(get_db)):
    """Remove a tracked subreddit and cascade delete all related data."""
    subreddit = db.query(Subreddit).filter(Subreddit.name == name).first()
    if not subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    
    db.delete(subreddit)
    db.commit()
    return None
