import logging
import os
import sys
from pathlib import Path


def setup_logging(console_level=logging.INFO, file_level=logging.DEBUG):
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parents[3] / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Log file path
    log_file = logs_dir / "parent_co_pilot.log"

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set root logger to capture all levels

    # Clear existing handlers to avoid duplicates on reload
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Console handler - less verbose
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(simple_formatter)

    # File handler - more verbose
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(detailed_formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)

    # Application logger
    logger = logging.getLogger("parent_co_pilot")
    logger.info(f"Logging configured successfully. Log file: {log_file}")

    return logger
