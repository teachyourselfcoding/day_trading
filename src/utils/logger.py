"""
Logging module for the trading signals project.
"""
import os
import logging
from datetime import datetime
from src.utils.config import LOGS_DIR

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file (optional)
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # Create default log file if none provided
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(LOGS_DIR, f"{name}_{timestamp}.log")
    
    # Create a custom logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    # Create formatters and add to handlers
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    file_handler.setFormatter(file_format)
    console_handler.setFormatter(console_format)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instances
main_logger = setup_logger('main')
data_logger = setup_logger('data')
analysis_logger = setup_logger('analysis')
signals_logger = setup_logger('signals')
execution_logger = setup_logger('execution')