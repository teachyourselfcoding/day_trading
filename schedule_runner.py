#!/usr/bin/env python3
"""
Scheduler for Trading Signals Project

This script sets up an automated schedule to run the trading signal generator
at specific times during trading days. It can be run in the background as a service.
"""
import os
import time
import sys
import subprocess
import logging
import schedule
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scheduler.log')
    ]
)
logger = logging.getLogger('scheduler')

# Load environment variables
load_dotenv()

# Configuration
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(PROJECT_DIR, 'main.py')

# Default symbols to analyze
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]

# You can customize these configurations
CONFIG = {
    'timezone': 'US/Eastern',  # Eastern Time for US markets
    'pre_market_time': '09:15',
    'morning_time': '10:30',
    'midday_time': '12:30',
    'afternoon_time': '14:30',
    'closing_time': '15:45',
    'post_market_time': '16:15',
    'symbols': os.getenv('TRADING_SYMBOLS', ','.join(DEFAULT_SYMBOLS)).split(','),
    'intervals': {
        'pre_market': '5m',
        'intraday': '15m',
        'closing': '5m',
        'post_market': '5m'
    }
}

def is_trading_day():
    """Check if today is a trading day (weekday, not holiday)."""
    now = datetime.now(pytz.timezone(CONFIG['timezone']))
    
    # Weekend check
    if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
    
    # TODO: Add holiday check if needed
    # This would require a calendar of market holidays
    
    return True

def run_trading_signals(interval='15m', execute=False, symbols=None):
    """Run the trading signals generator with specified parameters."""
    if symbols is None:
        symbols = CONFIG['symbols']
    
    try:
        logger.info(f"Running trading signals generator for {len(symbols)} symbols with {interval} interval")
        
        # Build the command
        cmd = [sys.executable, MAIN_SCRIPT, '--interval', interval]
        
        # Add symbols
        cmd.extend(['--symbols'] + symbols)
        
        # Add execute flag if needed
        if execute:
            cmd.append('--execute')
        
        # Log the command
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Run the process
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Log output
        if process.stdout:
            logger.info(f"Output: {process.stdout.strip()}")
        
        # Log errors
        if process.returncode != 0:
            logger.error(f"Error running command: {process.stderr.strip()}")
            return False
        
        logger.info(f"Successfully ran trading signals generator")
        return True
    
    except Exception as e:
        logger.error(f"Error running trading signals generator: {e}")
        return False

def pre_market_job():
    """Run pre-market analysis."""
    if not is_trading_day():
        logger.info("Not a trading day, skipping pre-market job")
        return
    
    logger.info("Running pre-market analysis")
    run_trading_signals(interval=CONFIG['intervals']['pre_market'])

def morning_job():
    """Run morning analysis."""
    if not is_trading_day():
        logger.info("Not a trading day, skipping morning job")
        return
    
    logger.info("Running morning analysis")
    run_trading_signals(interval=CONFIG['intervals']['intraday'])

def midday_job():
    """Run midday analysis."""
    if not is_trading_day():
        logger.info("Not a trading day, skipping midday job")
        return
    
    logger.info("Running midday analysis")
    run_trading_signals(interval=CONFIG['intervals']['intraday'])

def afternoon_job():
    """Run afternoon analysis."""
    if not is_trading_day():
        logger.info("Not a trading day, skipping afternoon job")
        return
    
    logger.info("Running afternoon analysis")
    run_trading_signals(interval=CONFIG['intervals']['intraday'])

def closing_job():
    """Run closing analysis."""
    if not is_trading_day():
        logger.info("Not a trading day, skipping closing job")
        return
    
    logger.info("Running closing analysis")
    run_trading_signals(interval=CONFIG['intervals']['closing'])

def post_market_job():
    """Run post-market analysis."""
    if not is_trading_day():
        logger.info("Not a trading day, skipping post-market job")
        return
    
    logger.info("Running post-market analysis")
    run_trading_signals(interval=CONFIG['intervals']['post_market'])

def setup_schedule():
    """Set up the job schedule."""
    # Pre-market
    schedule.every().day.at(CONFIG['pre_market_time']).do(pre_market_job)
    
    # Morning
    schedule.every().day.at(CONFIG['morning_time']).do(morning_job)
    
    # Midday
    schedule.every().day.at(CONFIG['midday_time']).do(midday_job)
    
    # Afternoon
    schedule.every().day.at(CONFIG['afternoon_time']).do(afternoon_job)
    
    # Closing
    schedule.every().day.at(CONFIG['closing_time']).do(closing_job)
    
    # Post-market
    schedule.every().day.at(CONFIG['post_market_time']).do(post_market_job)
    
    logger.info("Schedule setup complete")

def run_now():
    """Run the analysis immediately."""
    logger.info("Running immediate analysis")
    run_trading_signals()

def main():
    """Main function to set up and run the scheduler."""
    logger.info("Starting Trading Signals Scheduler")
    
    # Set up the schedule
    setup_schedule()
    
    # Print the schedule
    logger.info("Scheduled jobs:")
    for job in schedule.get_jobs():
        logger.info(f"  {job}")
    
    # Optionally run immediately
    if "--run-now" in sys.argv:
        run_now()
    
    # Run the scheduler loop
    logger.info("Entering scheduler loop. Press Ctrl+C to exit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
    
    logger.info("Scheduler stopped")

if __name__ == "__main__":
    main()