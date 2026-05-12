from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from src.app.models import Base, Subreddit, Post, Comment
from src.app.database.session import engine, SessionLocal
from src.app.routes import subreddits, comments, export
from src.app.tasks import collector_task
from src.app.utils.exceptions import InvalidRedditURL, SubredditNotFound, RedditAPIError, DatabaseError, ValidationError
from src.config import Settings, configure_logging

# Configure structured logging
configure_logging()
logger = logging.getLogger(__name__)

logger.info("Initializing Reddit Analytics Tracker backend...")

# Create FastAPI app
app = FastAPI(
    title="Reddit Analytics Tracker",
    description="Track Reddit comment and subreddit metrics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables initialized")


# Exception handlers
@app.exception_handler(InvalidRedditURL)
async def invalid_url_handler(request: Request, exc: InvalidRedditURL):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid Reddit URL", "detail": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation error", "detail": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(SubredditNotFound)
async def subreddit_not_found_handler(request: Request, exc: SubredditNotFound):
    return JSONResponse(
        status_code=404,
        content={"error": "Subreddit not found", "detail": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(RedditAPIError)
async def reddit_api_error_handler(request: Request, exc: RedditAPIError):
    return JSONResponse(
        status_code=500,
        content={"error": "Reddit API error", "detail": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database error", "detail": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("FastAPI application started")


# System statistics endpoint
@app.get("/api/stats")
def get_system_stats():
    """Get system statistics."""
    try:
        db = SessionLocal()
        total_subreddits = db.query(Subreddit).count()
        total_posts = db.query(Post).count()
        total_comments = db.query(Comment).count()
        db.close()
        
        return {
            "total_subreddits": total_subreddits,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "error": "Failed to get stats",
            "timestamp": datetime.utcnow().isoformat()
        }


# Include routers
logger.info("Loading API routers...")
app.include_router(subreddits.router)
app.include_router(comments.router)
app.include_router(export.router)
app.include_router(collector_task.router)
logger.info("Backend initialized successfully. API docs available at /docs")
