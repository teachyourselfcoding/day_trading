"""
Technical analysis functions using TA-Lib for processing market data.
"""
import numpy as np
import pandas as pd
import talib as ta
from datetime import datetime

from src.utils.config import PROCESSED_DATA_DIR, TECHNICAL_SETTINGS
from src.utils.file_utils import save_to_json
from src.utils.logger import analysis_logger

# Update the calculate_technical_indicators function to ensure proper data types
def calculate_technical_indicators(data):
    """
    Calculate technical indicators for the data using TA-Lib.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
    
    Returns:
        dict: Data with technical indicators added
    """
    if not data or 'bars' not in data or not data['bars']:
        analysis_logger.error("No bars data provided for technical analysis")
        return data
    
    symbol = data['symbol']
    analysis_logger.info(f"Calculating technical indicators for {symbol} using TA-Lib")
    
    # Convert to DataFrame for easier calculation
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric and explicitly convert to float64 (double)
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
    
    # Convert columns to numpy arrays for TA-Lib, explicitly as float64
    close = np.array(df['c'], dtype=np.float64)
    high = np.array(df['h'], dtype=np.float64)
    low = np.array(df['l'], dtype=np.float64)
    open_prices = np.array(df['o'], dtype=np.float64)
    volume = np.array(df['v'], dtype=np.float64)

    # Calculate Simple Moving Averages (SMA)
    sma_periods = TECHNICAL_SETTINGS['sma']
    for period in sma_periods:
        if len(df) >= period:
            df[f'sma_{period}'] = ta.SMA(close, timeperiod=period)
            analysis_logger.debug(f"Calculated SMA {period} for {symbol}")
    
    # Calculate Exponential Moving Averages (EMA)
    ema_periods = TECHNICAL_SETTINGS['ema']
    for period in ema_periods:
        if len(df) >= period:
            df[f'ema_{period}'] = ta.EMA(close, timeperiod=period)
            analysis_logger.debug(f"Calculated EMA {period} for {symbol}")
    
    # Calculate MACD
    if len(df) >= TECHNICAL_SETTINGS['macd']['slow']:
        fast = TECHNICAL_SETTINGS['macd']['fast']
        slow = TECHNICAL_SETTINGS['macd']['slow']
        signal_period = TECHNICAL_SETTINGS['macd']['signal']
        
        macd, macd_signal, macd_hist = ta.MACD(
            close, 
            fastperiod=fast, 
            slowperiod=slow, 
            signalperiod=signal_period
        )
        
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        analysis_logger.debug(f"Calculated MACD for {symbol}")
    
    # Calculate RSI
    rsi_period = TECHNICAL_SETTINGS['rsi']
    if len(df) >= rsi_period:
        df['rsi'] = ta.RSI(close, timeperiod=rsi_period)
        analysis_logger.debug(f"Calculated RSI for {symbol}")
    
    # Calculate Bollinger Bands
    bb_period = TECHNICAL_SETTINGS['bollinger']['period']
    if len(df) >= bb_period:
        std_dev = TECHNICAL_SETTINGS['bollinger']['std_dev']
        
        upper, middle, lower = ta.BBANDS(
            close, 
            timeperiod=bb_period, 
            nbdevup=std_dev, 
            nbdevdn=std_dev, 
            matype=0  # Simple moving average
        )
        
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        analysis_logger.debug(f"Calculated Bollinger Bands for {symbol}")
    
    # Calculate ATR (Average True Range)
    atr_period = TECHNICAL_SETTINGS['atr']
    if len(df) >= atr_period:
        df['atr'] = ta.ATR(high, low, close, timeperiod=atr_period)
        analysis_logger.debug(f"Calculated ATR for {symbol}")
    
    # Additional indicators (extend beyond original implementation)
    
    # Stochastic Oscillator
    if len(df) >= 14:  # Default for stochastic
        df['stoch_k'], df['stoch_d'] = ta.STOCH(
            high, low, close, 
            fastk_period=14, 
            slowk_period=3, 
            slowk_matype=0, 
            slowd_period=3, 
            slowd_matype=0
        )
        analysis_logger.debug(f"Calculated Stochastic Oscillator for {symbol}")
    
    # Average Directional Index (ADX)
    if len(df) >= 14:  # Default for ADX
        df['adx'] = ta.ADX(high, low, close, timeperiod=14)
        analysis_logger.debug(f"Calculated ADX for {symbol}")
    
    # On-Balance Volume (OBV)
    if len(df) >= 1:
        df['obv'] = ta.OBV(close, volume)
        analysis_logger.debug(f"Calculated OBV for {symbol}")
    
    # Commodity Channel Index (CCI)
    if len(df) >= 14:
        df['cci'] = ta.CCI(high, low, close, timeperiod=14)
        analysis_logger.debug(f"Calculated CCI for {symbol}")
    
    # Money Flow Index (MFI)
    if len(df) >= 14:
        df['mfi'] = ta.MFI(high, low, close, volume, timeperiod=14)
        analysis_logger.debug(f"Calculated MFI for {symbol}")
    
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
        'stochastic': 'stoch_k' in df.columns,
        'adx': 'adx' in df.columns,
        'obv': 'obv' in df.columns,
        'cci': 'cci' in df.columns,
        'mfi': 'mfi' in df.columns,
        'processed_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'library': 'TA-Lib'
    }
    
    data['metadata']['indicators'] = calculated_indicators
    
    # Save the processed data
    file_path = save_to_json(
        data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_processed"
    )
    analysis_logger.info(f"Saved processed data with TA-Lib indicators to {file_path}")
    
    return data

def process_multiple_symbols(data_dict):
    """
    Process technical indicators for multiple symbols.
    
    Args:
        data_dict (dict): Dictionary mapping symbols to their data
    
    Returns:
        dict: Dictionary mapping symbols to their processed data
    """
    analysis_logger.info(f"Processing TA-Lib technical indicators for {len(data_dict)} symbols")
    
    results = {}
    for symbol, data in data_dict.items():
        processed_data = calculate_technical_indicators(data)
        if processed_data:
            results[symbol] = processed_data
    
    analysis_logger.info(f"Successfully processed indicators for {len(results)} symbols")
    return results