import logging
import os


def setup_logging(log_filename):
    """
    Configure logging with both file and console handlers.

    Args:
        log_filename: Name of the log file (without path, e.g., 'app.log')

    Returns:
        logging.Logger: Configured logger for the module
    """
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    log_path = f"logs/{log_filename}"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path)
        ]
    )

    # Get logger for the calling module
    logger = logging.getLogger(log_filename.replace('.log', ''))
    return logger
