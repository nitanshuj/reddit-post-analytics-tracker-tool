from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Subreddit(Base):
    __tablename__ = "subreddits"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    weekly_stats = relationship("WeeklyStats", back_populates="subreddit", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="subreddit", cascade="all, delete-orphan")


class WeeklyStats(Base):
    __tablename__ = "weekly_stats"
    
    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"), nullable=False)
    week = Column(String, nullable=False)
    total_posts = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    avg_engagement_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subreddit = relationship("Subreddit", back_populates="weekly_stats")


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddits.id"), nullable=False)
    reddit_post_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    author = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subreddit = relationship("Subreddit", back_populates="posts")
    weekly_stats = relationship("PostWeeklyStats", back_populates="post", cascade="all, delete-orphan")


class PostWeeklyStats(Base):
    __tablename__ = "post_weekly_stats"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    week = Column(String, nullable=False)
    upvotes = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    post = relationship("Post", back_populates="weekly_stats")


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True)
    reddit_url = Column(String, unique=True, nullable=False)
    reddit_comment_id = Column(String, nullable=False)
    subreddit = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    history = relationship("CommentHistory", back_populates="comment", cascade="all, delete-orphan")


class CommentHistory(Base):
    __tablename__ = "comment_history"
    
    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    view_count = Column(Integer, default=0)
    weekly_avg = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    comment = relationship("Comment", back_populates="history")
