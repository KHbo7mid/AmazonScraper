import logging
import os

def setup_logger(name: str, level=logging.INFO):
    """Create and configure a logger."""
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger is reused
    if not logger.handlers:
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        ))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        ))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
