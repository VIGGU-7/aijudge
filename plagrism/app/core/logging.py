import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings

def setup_logging():
    """
    Sets up structured JSON logging.
    In Cloud Run/GCP, JSON logs are automatically parsed by Cloud Logging.
    """
    # Root logger
    root_logger = logging.getLogger()
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatting for production-like environments
    if settings.ENVIRONMENT == "production":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        # Cleaner output for local development
        formatter = logging.Formatter(
            "%(levelname)s: [%(name)s] %(message)s"
        )
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Adjust levels for noisy libraries
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    logging.info(f"Logging initialized in {settings.ENVIRONMENT} mode")
