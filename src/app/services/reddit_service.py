import praw
import logging
import time
from typing import Optional, List, Dict
from src.config import Settings
from src.app.utils.exceptions import InvalidRedditURL, RedditAPIError, SubredditNotFound

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
BACKOFF_FACTOR = 2


class RedditClient:
    def __init__(self):
        settings = Settings()
        try:
            self.reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
                username=settings.reddit_username,
                password=settings.reddit_password,
                check_for_async=False
            )
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise RedditAPIError(f"Reddit authentication failed: {str(e)}")
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        delay = RETRY_DELAY
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except praw.exceptions.ResponseException as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Reddit API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= BACKOFF_FACTOR
                else:
                    raise RedditAPIError(f"Reddit API error after {MAX_RETRIES} retries: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error in retry logic: {e}")
                raise
    
    def get_subreddit_posts(self, subreddit_name: str, limit: int = 10) -> List[Dict]:
        """Fetch posts from a subreddit with retry logic."""
        if not self.reddit:
            raise RedditAPIError("Reddit client not initialized")
        
        try:
            def fetch():
                sub = self.reddit.subreddit(subreddit_name)
                posts = []
                for submission in sub.new(limit=limit):
                    posts.append({
                        "reddit_post_id": submission.id,
                        "title": submission.title,
                        "url": submission.url,
                        "author": str(submission.author),
                        "upvotes": submission.score,
                        "impressions": submission.score + submission.num_comments,
                        "comments": submission.num_comments,
                    })
                return posts
            
            posts = self._retry_with_backoff(fetch)
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
            return posts
        except praw.exceptions.InvalidSubreddit:
            logger.error(f"Subreddit r/{subreddit_name} not found")
            raise SubredditNotFound(f"Subreddit r/{subreddit_name} does not exist")
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            raise RedditAPIError(f"Failed to fetch posts from r/{subreddit_name}: {str(e)}")
    
    def get_comment_view_count(self, comment_id: str) -> Optional[int]:
        """Fetch view count for a comment with retry logic."""
        if not self.reddit:
            return None
        
        try:
            def fetch():
                comment = self.reddit.comment(comment_id)
                return comment.score
            
            view_count = self._retry_with_backoff(fetch)
            return view_count
        except praw.exceptions.InvalidComment:
            logger.warning(f"Comment {comment_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching comment {comment_id}: {e}")
            return None
    
    def extract_comment_id(self, url: str) -> Optional[str]:
        """Extract comment ID from Reddit URL."""
        if not url or "/comments/" not in url:
            raise InvalidRedditURL(f"Invalid Reddit URL format: {url}")
        try:
            # Reddit URL format: https://reddit.com/r/subreddit/comments/post_id/title/comment_id
            parts = url.split("/comments/")[1].split("/")
            comment_id = parts[2] if len(parts) > 2 else None
            if not comment_id:
                raise InvalidRedditURL("Could not extract comment ID from URL")
            return comment_id
        except Exception as e:
            logger.error(f"Error extracting comment ID from {url}: {e}")
            raise InvalidRedditURL(f"Could not parse Reddit URL: {str(e)}")
    
    def is_subreddit_valid(self, subreddit_name: str) -> bool:
        """Check if subreddit exists."""
        if not self.reddit:
            return False
        
        try:
            def check():
                sub = self.reddit.subreddit(subreddit_name)
                sub.id  # Trigger API call to validate
                return True
            
            return self._retry_with_backoff(check)
        except praw.exceptions.InvalidSubreddit:
            logger.warning(f"Subreddit {subreddit_name} validation failed: not found")
            return False
        except Exception as e:
            logger.error(f"Error validating subreddit {subreddit_name}: {e}")
            return False
