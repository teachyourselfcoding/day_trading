"""
TradingView data fetcher module (using Yahoo Finance as the data source).
"""
import json
from src.data.yahoo_fetcher import fetch_yahoo_data
from src.utils.logger import data_logger

def fetch_intraday_data(symbol, interval='5m'):
    """
    Fetch intraday data for a symbol using Yahoo Finance.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        interval (str): Time interval ('1m', '5m', '15m', etc.)
    
    Returns:
        dict: Data in the format expected by the signal generator or None if error
    """
    data_logger.info(f"Fetching intraday data for {symbol} at {interval} interval")
    
    # Map between different interval formats if needed
    interval_mapping = {
        '5Min': '5m',
        '15Min': '15m', 
        '30Min': '30m',
        '1H': '1h'
    }
    
    # Convert interval format if needed
    yahoo_interval = interval_mapping.get(interval, interval)
    
    # Use Yahoo Finance to fetch the data
    data = fetch_yahoo_data(symbol, interval=yahoo_interval, period='1d')
    
    if data:
        data_logger.info(f"Successfully fetched {len(data['bars'])} bars for {symbol}")
    else:
        data_logger.error(f"Failed to fetch data for {symbol}")
    
    return data