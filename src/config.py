import os
import logging
from logging.handlers import RotatingFileHandler
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Reddit API
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    reddit_username: str = os.getenv("REDDIT_USERNAME", "")
    reddit_password: str = os.getenv("REDDIT_PASSWORD", "")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "script:reddit.tracker:v1")
    
    # Supabase / Database
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    
    # Google Sheets (optional)
    google_sheets_id: str = os.getenv("GOOGLE_SHEETS_ID", "")
    google_service_account_json_path: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH", "")
    
    # Collection API
    collect_api_key: str = os.getenv("COLLECT_API_KEY", "")
    
    # App Settings
    env: str = os.getenv("ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    
    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection string from Supabase credentials."""
        if self.supabase_url and self.supabase_key:
            # Convert Supabase URL to PostgreSQL connection string
            return f"postgresql://postgres:{self.supabase_key}@{self.supabase_url.split('://')[1].split('/')[0]}/postgres"
        return os.getenv("DATABASE_URL", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def configure_logging():
    """Configure structured logging with console and file handlers."""
    settings = Settings()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Formatter with timestamp and context
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler (DEBUG level with rotation)
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB 
        backupCount=5  # Keep 5 backups
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger
