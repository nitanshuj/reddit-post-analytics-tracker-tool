from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.app.database.session import get_db
from src.app.models import Comment, CommentHistory
from src.app.schemas import CommentCreate, CommentResponse, CommentDetailResponse
from src.app.services.reddit_service import RedditClient
from src.app.utils.exceptions import InvalidRedditURL

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("", response_model=CommentResponse, status_code=201)
def add_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    """Add a comment to track. Validates Reddit URL format."""
    try:
        # Validate Reddit URL and extract comment ID
        reddit = RedditClient()
        comment_id = reddit.extract_comment_id(comment.reddit_url)
        
        # Check if already tracked
        existing = db.query(Comment).filter(Comment.reddit_url == comment.reddit_url).first()
        if existing:
            raise HTTPException(status_code=400, detail="Comment already tracked")
        
        new_comment = Comment(
            reddit_url=comment.reddit_url,
            reddit_comment_id=comment_id
        )
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        return new_comment
    except InvalidRedditURL as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[CommentResponse])
def list_comments(db: Session = Depends(get_db)):
    """List all tracked comments."""
    comments = db.query(Comment).all()
    return comments


@router.get("/{comment_id}", response_model=CommentDetailResponse)
def get_comment_detail(comment_id: int, db: Session = Depends(get_db)):
    """Get detailed view of a tracked comment with full history."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    history = db.query(CommentHistory).filter(
        CommentHistory.comment_id == comment_id
    ).order_by(CommentHistory.timestamp.desc()).all()
    
    return {
        "id": comment.id,
        "reddit_url": comment.reddit_url,
        "reddit_comment_id": comment.reddit_comment_id,
        "created_at": comment.created_at,
        "history": history
    }


@router.delete("/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    """Remove a tracked comment and all associated history."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(comment)
    db.commit()
    return None
