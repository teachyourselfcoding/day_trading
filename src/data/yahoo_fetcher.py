"""
Yahoo Finance data fetcher module.
"""
import traceback
from datetime import datetime
import pandas as pd
import yfinance as yf

from src.utils.config import RAW_DATA_DIR, DEFAULT_INTERVAL, DEFAULT_PERIOD
from src.utils.file_utils import save_to_json
from src.utils.logger import data_logger

def fetch_yahoo_data(symbol, interval=DEFAULT_INTERVAL, period=DEFAULT_PERIOD):
    """
    Fetch data from Yahoo Finance.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        interval (str): Time interval ('1m', '5m', '15m', '1h', '1d', etc.)
        period (str): How far back to get data ('1d', '5d', '1mo', '3mo', etc.)
    
    Returns:
        dict: Data in the format expected by the signal generator or None if error
    """
    try:
        data_logger.info(f"Fetching {interval} data for {symbol} for the last {period}")
        
        # Yahoo Finance uses slightly different ticker format for some indices
        if symbol == '^GSPC':
            yahoo_symbol = '^GSPC'  # S&P 500
        elif symbol == '^DJI':
            yahoo_symbol = '^DJI'   # Dow Jones
        elif symbol == '^IXIC':
            yahoo_symbol = '^IXIC'  # NASDAQ
        else:
            yahoo_symbol = symbol
        
        # Fetch data from Yahoo Finance
        df = yf.download(
            tickers=yahoo_symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            prepost=False,
            threads=True,
            progress=False  # Disable progress bar for cleaner logs
        )
        
        # Check if data was successfully retrieved
        if df.empty:
            data_logger.error(f"No data returned for {symbol}")
            return None
        
        # Reset index to make Date/Datetime a column
        df = df.reset_index()
        
        # Log the DataFrame structure for debugging
        data_logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        
        # Create a new DataFrame with the columns we need
        processed_df = pd.DataFrame()
        
        # Handle the date column - check which column contains datetime information
        if 'Datetime' in df.columns:
            processed_df['t'] = df['Datetime'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'Date' in df.columns:
            processed_df['t'] = df['Date'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'index' in df.columns and pd.api.types.is_datetime64_any_dtype(df['index']):
            processed_df['t'] = df['index'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Try the index itself as a last resort
            processed_df['t'] = df.index.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Add price and volume data
        processed_df['o'] = df['Open']
        processed_df['h'] = df['High']
        processed_df['l'] = df['Low']
        processed_df['c'] = df['Close']
        processed_df['v'] = df['Volume']
        
        data_logger.info(f"Successfully retrieved {len(processed_df)} bars of data for {symbol}")
        
        # Convert to the format we used with Alpaca
        data = {
            'bars': processed_df.to_dict('records'),
            'symbol': symbol,
            'metadata': {
                'interval': interval,
                'period': period,
                'fetched_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'source': 'Yahoo Finance'
            }
        }
        
        # Save the data to a file
        file_path = save_to_json(
            data, 
            RAW_DATA_DIR, 
            f"{symbol}_{interval}"
        )
        data_logger.info(f"Saved raw data to {file_path}")
        
        return data
    
    except Exception as e:
        data_logger.error(f"Error fetching data from Yahoo Finance for {symbol}: {e}")
        data_logger.debug(traceback.format_exc())
        return None

def fetch_multiple_symbols(symbols, interval=DEFAULT_INTERVAL, period=DEFAULT_PERIOD):
    """
    Fetch data for multiple symbols.
    
    Args:
        symbols (list): List of stock symbols
        interval (str): Time interval
        period (str): Historical period
    
    Returns:
        dict: Dictionary mapping symbols to their data
    """
    data_logger.info(f"Fetching data for {len(symbols)} symbols")
    
    results = {}
    for symbol in symbols:
        data = fetch_yahoo_data(symbol, interval, period)
        if data:
            results[symbol] = data
    
    data_logger.info(f"Successfully fetched data for {len(results)} out of {len(symbols)} symbols")
    return results