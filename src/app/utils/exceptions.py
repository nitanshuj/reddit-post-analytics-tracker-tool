class InvalidRedditURL(Exception):
    """Raised when Reddit URL is malformed or invalid."""
    pass


class SubredditNotFound(Exception):
    """Raised when subreddit doesn't exist on Reddit."""
    pass


class PostNotFound(Exception):
    """Raised when post doesn't exist on Reddit."""
    pass


class CommentNotFound(Exception):
    """Raised when comment doesn't exist on Reddit."""
    pass


class RedditAPIError(Exception):
    """Raised when Reddit API call fails."""
    pass


class DatabaseError(Exception):
    """Raised when database operation fails."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass
