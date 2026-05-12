from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional


# Subreddit Schemas
class SubredditCreate(BaseModel):
    name: str


class SubredditResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Weekly Stats Schemas
class WeeklyStatsResponse(BaseModel):
    id: int
    week: str
    total_posts: int
    impressions: int
    upvotes: int
    comments: int
    engagement: int
    avg_engagement_rate: float
    
    class Config:
        from_attributes = True


# Post Schemas
class PostCreate(BaseModel):
    title: str
    url: str
    reddit_post_id: str


class PostResponse(BaseModel):
    id: int
    reddit_post_id: str
    title: str
    url: str
    author: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Post Weekly Stats Schemas
class PostWeeklyStatsResponse(BaseModel):
    id: int
    week: str
    upvotes: int
    impressions: int
    comments_count: int
    engagement: int
    engagement_rate: float
    
    class Config:
        from_attributes = True


# Comment Schemas
class CommentCreate(BaseModel):
    reddit_url: str


class CommentResponse(BaseModel):
    id: int
    reddit_url: str
    reddit_comment_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Comment History Schemas
class CommentHistoryResponse(BaseModel):
    id: int
    view_count: int
    weekly_avg: float
    timestamp: datetime
    
    class Config:
        from_attributes = True


class CommentDetailResponse(BaseModel):
    id: int
    reddit_url: str
    reddit_comment_id: str
    created_at: datetime
    history: List[CommentHistoryResponse]
    
    class Config:
        from_attributes = True
