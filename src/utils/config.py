"""
Configuration module for trading signals project.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Directory structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
SIGNALS_DIR = os.path.join(BASE_DIR, 'signals')
PROMPTS_DIR = os.path.join(SIGNALS_DIR, 'prompts')
OUTPUTS_DIR = os.path.join(SIGNALS_DIR, 'outputs')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
DIRS_TO_CREATE = [RAW_DATA_DIR, PROCESSED_DATA_DIR, PROMPTS_DIR, OUTPUTS_DIR, LOGS_DIR]

# Yahoo Finance settings
DEFAULT_INTERVAL = '5m'  # Available: 1m, 5m, 15m, 30m, 60m, 1h, 1d, 1wk, 1mo
DEFAULT_PERIOD = '5d'    # Available: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

# OpenAI settings
OPENAI_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0

# Trading settings
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
RISK_PER_TRADE = 0.02    # 2% risk per trade

# Interval mapping (Alpaca to Yahoo Finance)
INTERVAL_MAPPING = {
    '1Min': '1m',
    '5Min': '5m',
    '15Min': '15m',
    '1H': '1h',
    '1D': '1d'
}

# Technical indicator settings
TECHNICAL_SETTINGS = {
    'sma': [20, 50, 200],
    'ema': [12, 26],
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'rsi': 14,
    'bollinger': {'period': 20, 'std_dev': 2},
    'atr': 14
}