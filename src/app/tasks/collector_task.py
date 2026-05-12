from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import Optional

from src.app.database.session import get_db
from src.app.services.collector_service import DataCollector
from src.app.models import Subreddit
from src.config import Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/collect")
def collect_data(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Trigger data collection for all tracked subreddits and comments.
    
    Returns collection summary with status, subreddits processed, comments processed, and detailed results.
    Optional API key validation via Authorization header.
    """
    
    # Optional API key validation
    settings = Settings()
    if settings.collect_api_key and authorization:
        expected_auth = f"Bearer {settings.collect_api_key}"
        if authorization != expected_auth:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    start_time = datetime.utcnow()
    logger.info("Starting data collection task")
    
    try:
        collector = DataCollector(db)
        results = {
            "status": "running",
            "start_time": start_time.isoformat(),
            "subreddits": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "results": []
            },
            "comments": {
                "processed": 0,
                "failed": 0,
                "details": {}
            }
        }
        
        # Collect subreddit data
        subreddits = db.query(Subreddit).all()
        results["subreddits"]["total"] = len(subreddits)
        
        for subreddit in subreddits:
            result = collector.collect_subreddit_data(subreddit.name)
            results["subreddits"]["results"].append(result)
            
            if result.get("status") == "success":
                results["subreddits"]["success"] += 1
            else:
                results["subreddits"]["failed"] += 1
        
        # Collect comment data
        comment_result = collector.collect_comment_data()
        results["comments"]["details"] = comment_result
        if comment_result.get("status") == "success":
            results["comments"]["processed"] = comment_result.get("comments_processed", 0)
            results["comments"]["failed"] = comment_result.get("comments_failed", 0)
        
        # Finalize results
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        results["status"] = "completed"
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        logger.info(
            f"Collection completed: {results['subreddits']['success']} subreddits succeeded, "
            f"{results['subreddits']['failed']} failed, "
            f"{results['comments']['processed']} comments processed, "
            f"{results['comments']['failed']} comments failed. "
            f"Duration: {duration:.2f}s"
        )
        
        return results
    except Exception as e:
        logger.error(f"Data collection failed: {e}", exc_info=True)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "status": "failed",
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration
        }
