import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.app.models import Subreddit, WeeklyStats, Post, PostWeeklyStats, Comment, CommentHistory
from src.app.services.reddit_service import RedditClient
from src.app.utils.exceptions import RedditAPIError, DatabaseError, SubredditNotFound

logger = logging.getLogger(__name__)


class DataCollector:
    def __init__(self, db: Session):
        self.db = db
        try:
            self.reddit = RedditClient()
        except RedditAPIError as e:
            logger.error(f"Failed to initialize RedditClient: {e}")
            raise DatabaseError(f"Collection service initialization failed: {str(e)}")
    
    def get_week_start(self) -> str:
        """Get current week start date (Monday) in YYYY-MM-DD format."""
        today = datetime.utcnow()
        monday = today - timedelta(days=today.weekday())
        return monday.strftime("%Y-%m-%d")
    
    def collect_subreddit_data(self, subreddit_name: str) -> dict:
        """Collect weekly stats for a subreddit. Handles partial failures gracefully."""
        try:
            # Get or create subreddit
            subreddit = self.db.query(Subreddit).filter(Subreddit.name == subreddit_name).first()
            if not subreddit:
                subreddit = Subreddit(name=subreddit_name)
                self.db.add(subreddit)
                self.db.commit()
            
            # Fetch posts from Reddit
            try:
                posts_data = self.reddit.get_subreddit_posts(subreddit_name, limit=100)
            except SubredditNotFound:
                logger.error(f"Subreddit r/{subreddit_name} not found on Reddit")
                return {"status": "failed", "subreddit": subreddit_name, "reason": "subreddit_not_found"}
            except RedditAPIError as e:
                logger.error(f"Reddit API error fetching r/{subreddit_name}: {e}")
                return {"status": "failed", "subreddit": subreddit_name, "reason": "reddit_api_error"}
            
            if not posts_data:
                logger.warning(f"No posts found for r/{subreddit_name}")
                return {"status": "no_posts", "subreddit": subreddit_name, "posts": 0}
            
            # Calculate weekly stats
            week = self.get_week_start()
            total_posts = len(posts_data)
            total_upvotes = sum(p.get("upvotes", 0) for p in posts_data)
            total_comments = sum(p.get("comments", 0) for p in posts_data)
            total_impressions = sum(p.get("impressions", 0) for p in posts_data)
            total_engagement = total_upvotes + total_comments
            avg_engagement_rate = (total_engagement / total_impressions * 100) if total_impressions > 0 else 0.0
            
            # Upsert weekly stats
            weekly_stat = self.db.query(WeeklyStats).filter(
                WeeklyStats.subreddit_id == subreddit.id,
                WeeklyStats.week == week
            ).first()
            
            if weekly_stat:
                weekly_stat.total_posts = total_posts
                weekly_stat.impressions = total_impressions
                weekly_stat.upvotes = total_upvotes
                weekly_stat.comments = total_comments
                weekly_stat.engagement = total_engagement
                weekly_stat.avg_engagement_rate = avg_engagement_rate
                weekly_stat.updated_at = datetime.utcnow()
            else:
                weekly_stat = WeeklyStats(
                    subreddit_id=subreddit.id,
                    week=week,
                    total_posts=total_posts,
                    impressions=total_impressions,
                    upvotes=total_upvotes,
                    comments=total_comments,
                    engagement=total_engagement,
                    avg_engagement_rate=avg_engagement_rate
                )
                self.db.add(weekly_stat)
            
            # Store posts and their stats (handle partial failures)
            posts_stored = 0
            for post_data in posts_data:
                try:
                    post = self.db.query(Post).filter(Post.reddit_post_id == post_data["reddit_post_id"]).first()
                    if not post:
                        post = Post(
                            subreddit_id=subreddit.id,
                            reddit_post_id=post_data["reddit_post_id"],
                            title=post_data["title"],
                            url=post_data["url"],
                            author=post_data["author"]
                        )
                        self.db.add(post)
                        self.db.flush()  # Get the post ID
                    
                    # Store post weekly stats
                    engagement = post_data["upvotes"] + post_data["comments"]
                    engagement_rate = (engagement / post_data["impressions"] * 100) if post_data["impressions"] > 0 else 0.0
                    
                    post_stat = self.db.query(PostWeeklyStats).filter(
                        PostWeeklyStats.post_id == post.id,
                        PostWeeklyStats.week == week
                    ).first()
                    
                    if post_stat:
                        post_stat.upvotes = post_data["upvotes"]
                        post_stat.impressions = post_data["impressions"]
                        post_stat.comments_count = post_data["comments"]
                        post_stat.engagement = engagement
                        post_stat.engagement_rate = engagement_rate
                        post_stat.updated_at = datetime.utcnow()
                    else:
                        post_stat = PostWeeklyStats(
                            post_id=post.id,
                            week=week,
                            upvotes=post_data["upvotes"],
                            impressions=post_data["impressions"],
                            comments_count=post_data["comments"],
                            engagement=engagement,
                            engagement_rate=engagement_rate
                        )
                        self.db.add(post_stat)
                    
                    posts_stored += 1
                except Exception as e:
                    logger.warning(f"Failed to store post {post_data.get('reddit_post_id')}: {e}")
                    continue  # Continue with next post
            
            self.db.commit()
            logger.info(f"Collected data for r/{subreddit_name}: {posts_stored} posts stored, {total_posts} total")
            return {
                "status": "success",
                "subreddit": subreddit_name,
                "posts": posts_stored,
                "engagement_rate": round(avg_engagement_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error collecting data for r/{subreddit_name}: {e}")
            self.db.rollback()
            return {"status": "failed", "subreddit": subreddit_name, "error": str(e)}
    
    def collect_comment_data(self) -> dict:
        """Collect view count history for tracked comments. Handles partial failures gracefully."""
        try:
            comments = self.db.query(Comment).all()
            processed = 0
            failed = 0
            
            for comment in comments:
                try:
                    view_count = self.reddit.get_comment_view_count(comment.reddit_comment_id)
                    if view_count is not None:
                        # Add history record
                        history = CommentHistory(
                            comment_id=comment.id,
                            view_count=view_count,
                            timestamp=datetime.utcnow()
                        )
                        self.db.add(history)
                        
                        # Calculate 7-day average
                        week_ago = datetime.utcnow() - timedelta(days=7)
                        recent_history = self.db.query(CommentHistory).filter(
                            CommentHistory.comment_id == comment.id,
                            CommentHistory.timestamp >= week_ago
                        ).all()
                        
                        if recent_history:
                            avg = sum(h.view_count for h in recent_history) / len(recent_history)
                            history.weekly_avg = avg
                        
                        processed += 1
                    else:
                        logger.warning(f"Could not fetch view count for comment {comment.reddit_comment_id}")
                        failed += 1
                except Exception as e:
                    logger.warning(f"Error collecting data for comment {comment.id}: {e}")
                    failed += 1
                    continue
            
            self.db.commit()
            logger.info(f"Collected comment data: {processed} processed, {failed} failed")
            return {
                "status": "success",
                "comments_processed": processed,
                "comments_failed": failed,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in comment collection: {e}")
            self.db.rollback()
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
