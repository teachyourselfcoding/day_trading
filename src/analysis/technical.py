"""
Technical analysis functions for processing market data.
"""
import numpy as np
import pandas as pd
from datetime import datetime

from src.utils.config import PROCESSED_DATA_DIR, TECHNICAL_SETTINGS
from src.utils.file_utils import save_to_json
from src.utils.logger import analysis_logger

def calculate_technical_indicators(data):
    """
    Calculate technical indicators for the data.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
    
    Returns:
        dict: Data with technical indicators added
    """
    if not data or 'bars' not in data or not data['bars']:
        analysis_logger.error("No bars data provided for technical analysis")
        return data
    
    symbol = data['symbol']
    analysis_logger.info(f"Calculating technical indicators for {symbol}")
    
    # Convert to DataFrame for easier calculation
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Calculate Simple Moving Averages (SMA)
    sma_periods = TECHNICAL_SETTINGS['sma']
    for period in sma_periods:
        if len(df) >= period:
            df[f'sma_{period}'] = df['c'].rolling(window=period).mean()
            analysis_logger.debug(f"Calculated SMA {period} for {symbol}")
    
    # Calculate Exponential Moving Averages (EMA)
    ema_periods = TECHNICAL_SETTINGS['ema']
    for period in ema_periods:
        if len(df) >= period:
            df[f'ema_{period}'] = df['c'].ewm(span=period, adjust=False).mean()
            analysis_logger.debug(f"Calculated EMA {period} for {symbol}")
    
    # Calculate MACD
    if len(df) >= TECHNICAL_SETTINGS['macd']['slow']:
        fast = TECHNICAL_SETTINGS['macd']['fast']
        slow = TECHNICAL_SETTINGS['macd']['slow']
        signal = TECHNICAL_SETTINGS['macd']['signal']
        
        df['macd'] = df[f'ema_{fast}'] - df[f'ema_{slow}']
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        analysis_logger.debug(f"Calculated MACD for {symbol}")
    
    # Calculate RSI
    rsi_period = TECHNICAL_SETTINGS['rsi']
    if len(df) >= rsi_period:
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        
        # Avoid division by zero
        avg_loss = avg_loss.replace(0, 0.0001)
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        analysis_logger.debug(f"Calculated RSI for {symbol}")
    
    # Calculate Bollinger Bands
    bb_period = TECHNICAL_SETTINGS['bollinger']['period']
    if len(df) >= bb_period:
        std_dev = TECHNICAL_SETTINGS['bollinger']['std_dev']
        
        df['bb_middle'] = df['c'].rolling(window=bb_period).mean()
        df['bb_std'] = df['c'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_dev)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_dev)
        analysis_logger.debug(f"Calculated Bollinger Bands for {symbol}")
    
    # Calculate ATR (Average True Range)
    atr_period = TECHNICAL_SETTINGS['atr']
    if len(df) >= atr_period:
        high_low = df['h'] - df['l']
        high_close = np.abs(df['h'] - df['c'].shift())
        low_close = np.abs(df['l'] - df['c'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(atr_period).mean()
        analysis_logger.debug(f"Calculated ATR for {symbol}")
    
    # Round all values to 2 decimal places (except timestamp)
    for col in df.columns:
        if col != 't' and df[col].dtype != 'object':
            df[col] = df[col].round(2)
    
    # Handle NaN values
    df = df.fillna(0)
    
    # Convert back to dictionary
    data['bars'] = df.to_dict('records')
    
    # Add indicator metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    
    # Track which indicators were calculated
    calculated_indicators = {
        'sma': [period for period in sma_periods if f'sma_{period}' in df.columns],
        'ema': [period for period in ema_periods if f'ema_{period}' in df.columns],
        'macd': 'macd' in df.columns,
        'rsi': 'rsi' in df.columns,
        'bollinger_bands': 'bb_middle' in df.columns,
        'atr': 'atr' in df.columns,
        'processed_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    data['metadata']['indicators'] = calculated_indicators
    
    # Save the processed data
    file_path = save_to_json(
        data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_processed"
    )
    analysis_logger.info(f"Saved processed data with indicators to {file_path}")
    
    return data

def process_multiple_symbols(data_dict):
    """
    Process technical indicators for multiple symbols.
    
    Args:
        data_dict (dict): Dictionary mapping symbols to their data
    
    Returns:
        dict: Dictionary mapping symbols to their processed data
    """
    analysis_logger.info(f"Processing technical indicators for {len(data_dict)} symbols")
    
    results = {}
    for symbol, data in data_dict.items():
        processed_data = calculate_technical_indicators(data)
        if processed_data:
            results[symbol] = processed_data
    
    analysis_logger.info(f"Successfully processed indicators for {len(results)} symbols")
    return results