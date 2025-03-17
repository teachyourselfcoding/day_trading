"""
Technical analysis functions using TA-Lib for processing market data.
Enhanced with support for custom indicator settings based on timeframe.
"""
import numpy as np
import pandas as pd
import talib as ta
from datetime import datetime

from src.utils.config import PROCESSED_DATA_DIR, TECHNICAL_SETTINGS
from src.utils.file_utils import save_to_json
from src.utils.logger import analysis_logger

def calculate_technical_indicators(data, settings=None):
    """
    Calculate technical indicators for the data using TA-Lib.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        settings (dict): Custom settings for technical indicators, or None to use defaults
    
    Returns:
        dict: Data with technical indicators added
    """
    if not data or 'bars' not in data or not data['bars']:
        analysis_logger.error("No bars data provided for technical analysis")
        return data
    
    # Use default settings if none provided
    if settings is None:
        settings = TECHNICAL_SETTINGS
    
    symbol = data.get('symbol', 'unknown')
    interval = data.get('metadata', {}).get('interval', 'unknown')
    analysis_logger.info(f"Calculating technical indicators for {symbol} using {interval} interval")
    
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
    sma_periods = settings.get('sma', [20, 50, 200])
    for period in sma_periods:
        if len(df) >= period:
            df[f'sma_{period}'] = ta.SMA(close, timeperiod=period)
            analysis_logger.debug(f"Calculated SMA {period} for {symbol}")
        else:
            analysis_logger.warning(f"Not enough bars to calculate SMA {period}. Need {period}, have {len(df)}")
    
    # Calculate Exponential Moving Averages (EMA)
    ema_periods = settings.get('ema', [12, 26])
    for period in ema_periods:
        if len(df) >= period:
            df[f'ema_{period}'] = ta.EMA(close, timeperiod=period)
            analysis_logger.debug(f"Calculated EMA {period} for {symbol}")
        else:
            analysis_logger.warning(f"Not enough bars to calculate EMA {period}. Need {period}, have {len(df)}")
    
    # Calculate MACD
    macd_settings = settings.get('macd', {'fast': 12, 'slow': 26, 'signal': 9})
    fast = macd_settings.get('fast', 12)
    slow = macd_settings.get('slow', 26)
    signal_period = macd_settings.get('signal', 9)
    
    if len(df) >= slow:
        macd, macd_signal, macd_hist = ta.MACD(
            close, 
            fastperiod=fast, 
            slowperiod=slow, 
            signalperiod=signal_period
        )
        
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        analysis_logger.debug(f"Calculated MACD for {symbol} (fast={fast}, slow={slow}, signal={signal_period})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate MACD. Need {slow}, have {len(df)}")
    
    # Calculate RSI
    rsi_period = settings.get('rsi', 14)
    if len(df) >= rsi_period:
        df['rsi'] = ta.RSI(close, timeperiod=rsi_period)
        analysis_logger.debug(f"Calculated RSI for {symbol} (period={rsi_period})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate RSI. Need {rsi_period}, have {len(df)}")
    
    # Calculate Bollinger Bands
    bb_settings = settings.get('bollinger', {'period': 20, 'std_dev': 2})
    bb_period = bb_settings.get('period', 20)
    std_dev = bb_settings.get('std_dev', 2)
    
    if len(df) >= bb_period:
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
        analysis_logger.debug(f"Calculated Bollinger Bands for {symbol} (period={bb_period}, std_dev={std_dev})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate Bollinger Bands. Need {bb_period}, have {len(df)}")
    
    # Calculate ATR (Average True Range)
    atr_period = settings.get('atr', 14)
    if len(df) >= atr_period:
        df['atr'] = ta.ATR(high, low, close, timeperiod=atr_period)
        analysis_logger.debug(f"Calculated ATR for {symbol} (period={atr_period})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate ATR. Need {atr_period}, have {len(df)}")
    
    # Additional indicators (extend beyond original implementation)
    
    # Stochastic Oscillator
    stoch_settings = settings.get('stochastic', {'k_period': 14, 'k_slowing': 3, 'd_period': 3})
    k_period = stoch_settings.get('k_period', 14)
    
    if len(df) >= k_period:
        df['stoch_k'], df['stoch_d'] = ta.STOCH(
            high, low, close, 
            fastk_period=k_period, 
            slowk_period=stoch_settings.get('k_slowing', 3), 
            slowk_matype=0, 
            slowd_period=stoch_settings.get('d_period', 3), 
            slowd_matype=0
        )
        analysis_logger.debug(f"Calculated Stochastic Oscillator for {symbol}")
    else:
        analysis_logger.warning(f"Not enough bars to calculate Stochastic. Need {k_period}, have {len(df)}")
    
    # Average Directional Index (ADX)
    adx_period = settings.get('adx', 14)
    if len(df) >= adx_period:
        df['adx'] = ta.ADX(high, low, close, timeperiod=adx_period)
        analysis_logger.debug(f"Calculated ADX for {symbol} (period={adx_period})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate ADX. Need {adx_period}, have {len(df)}")
    
    # On-Balance Volume (OBV)
    if len(df) >= 1:
        df['obv'] = ta.OBV(close, volume)
        analysis_logger.debug(f"Calculated OBV for {symbol}")
    
    # Commodity Channel Index (CCI)
    cci_period = settings.get('cci', 14)
    if len(df) >= cci_period:
        df['cci'] = ta.CCI(high, low, close, timeperiod=cci_period)
        analysis_logger.debug(f"Calculated CCI for {symbol} (period={cci_period})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate CCI. Need {cci_period}, have {len(df)}")
    
    # Money Flow Index (MFI)
    mfi_period = settings.get('mfi', 14)
    if len(df) >= mfi_period:
        df['mfi'] = ta.MFI(high, low, close, volume, timeperiod=mfi_period)
        analysis_logger.debug(f"Calculated MFI for {symbol} (period={mfi_period})")
    else:
        analysis_logger.warning(f"Not enough bars to calculate MFI. Need {mfi_period}, have {len(df)}")
    
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
        'settings_used': {
            'sma': sma_periods,
            'ema': ema_periods,
            'macd': macd_settings,
            'rsi': rsi_period,
            'bollinger': bb_settings,
            'atr': atr_period,
            'stochastic': stoch_settings,
            'adx': adx_period,
            'cci': settings.get('cci', 14),
            'mfi': settings.get('mfi', 14)
        },
        'library': 'TA-Lib',
        'timeframe': {
            'interval': interval,
            'bars_count': len(df)
        }
    }
    
    data['metadata']['indicators'] = calculated_indicators
    
    # Save the processed data
    file_path = save_to_json(
        data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_{interval}_processed"
    )
    analysis_logger.info(f"Saved processed data with TA-Lib indicators to {file_path}")
    
    return data

def process_multiple_symbols(data_dict, settings=None):
    """
    Process technical indicators for multiple symbols.
    
    Args:
        data_dict (dict): Dictionary mapping symbols to their data
        settings (dict): Custom settings for technical indicators
    
    Returns:
        dict: Dictionary mapping symbols to their processed data
    """
    analysis_logger.info(f"Processing TA-Lib technical indicators for {len(data_dict)} symbols")
    
    results = {}
    for symbol, data in data_dict.items():
        processed_data = calculate_technical_indicators(data, settings)
        if processed_data:
            results[symbol] = processed_data
    
    analysis_logger.info(f"Successfully processed indicators for {len(results)} symbols")
    return results

def get_timeframe_adjusted_settings(interval):
    """
    Get adjusted indicator settings based on the timeframe.
    
    Args:
        interval (str): Chart interval (e.g., '1m', '5m', '1d')
        
    Returns:
        dict: Adjusted technical indicator settings
    """
    # Copy default settings
    settings = TECHNICAL_SETTINGS.copy()
    
    # Adjust settings based on timeframe
    if interval in ['1m', '2m', '3m']:
        # For very short timeframes, use shorter periods
        settings['sma'] = [5, 10, 20]
        settings['ema'] = [5, 10]
        settings['macd'] = {'fast': 6, 'slow': 13, 'signal': 5}
        settings['rsi'] = 7
        settings['bollinger'] = {'period': 10, 'std_dev': 2}
        settings['atr'] = 7
    elif interval in ['5m', '15m']:
        # For short timeframes, use slightly reduced periods
        settings['sma'] = [10, 20, 50]
        settings['ema'] = [9, 21]
        settings['macd'] = {'fast': 12, 'slow': 26, 'signal': 9}
        settings['rsi'] = 14
        settings['bollinger'] = {'period': 20, 'std_dev': 2}
        settings['atr'] = 14
    elif interval in ['30m', '1h', '2h']:
        # For medium timeframes, use standard periods
        # Default settings are fine
        pass
    elif interval in ['4h', '1d']:
        # For longer timeframes, use extended periods
        settings['sma'] = [20, 50, 200]
        settings['ema'] = [12, 26, 50]
        settings['macd'] = {'fast': 12, 'slow': 26, 'signal': 9}
        settings['rsi'] = 14
        settings['bollinger'] = {'period': 20, 'std_dev': 2}
        settings['atr'] = 14
    elif interval in ['1wk', '1mo']:
        # For very long timeframes, use even longer periods
        settings['sma'] = [10, 30, 60]
        settings['ema'] = [9, 21, 50]
        settings['macd'] = {'fast': 12, 'slow': 26, 'signal': 9}
        settings['rsi'] = 14
        settings['bollinger'] = {'period': 20, 'std_dev': 2.5}
        settings['atr'] = 14
    
    return settings

def analyze_volume(data, periods=10):
    """
    Analyze volume patterns from price data.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        periods (int): Number of periods to analyze
        
    Returns:
        dict: Volume analysis information
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
        elif isinstance(data, list):
            bars = data
        else:
            analysis_logger.warning("Invalid data format for volume analysis")
            return None
            
        if not bars or len(bars) < periods:
            analysis_logger.warning(f"Not enough bars for volume analysis (need {periods}, have {len(bars) if bars else 0})")
            return None
        
        # Extract recent volumes
        recent_volumes = [bar['v'] for bar in bars[-periods:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        latest_volume = bars[-1]['v']
        
        # Determine if volume is increasing or decreasing
        if latest_volume > avg_volume * 1.2:
            volume_trend = "Increasing"
        elif latest_volume < avg_volume * 0.8:
            volume_trend = "Decreasing"
        else:
            volume_trend = "Stable"
        
        # Check for volume spike
        volume_spike = latest_volume > avg_volume * 2
        
        # Check for volume divergence (price up, volume down or vice versa)
        price_change = bars[-1]['c'] - bars[-2]['c']
        prev_volume = bars[-2]['v']
        volume_change = latest_volume - prev_volume
        
        divergence = None
        if price_change > 0 and volume_change < 0:
            divergence = "Bearish (price up, volume down)"
        elif price_change < 0 and volume_change > 0:
            divergence = "Bearish (price down, volume up)"
        elif price_change > 0 and volume_change > 0:
            divergence = "Bullish (price up, volume up)"
        elif price_change < 0 and volume_change < 0:
            divergence = "Bullish (price down, volume down)"
            
        # Calculate volume-weighted average price (VWAP) if needed
        vwap = None
        if all('o' in bar and 'h' in bar and 'l' in bar and 'c' in bar and 'v' in bar for bar in bars[-periods:]):
            try:
                typical_prices = [(bar['h'] + bar['l'] + bar['c']) / 3 for bar in bars[-periods:]]
                volumes = [bar['v'] for bar in bars[-periods:]]
                vwap = sum(tp * vol for tp, vol in zip(typical_prices, volumes)) / sum(volumes)
            except Exception as e:
                analysis_logger.warning(f"Failed to calculate VWAP: {e}")
        
        result = {
            "average_period": avg_volume,
            "current_volume": latest_volume,
            "volume_trend": volume_trend,
            "volume_spike": volume_spike,
            "divergence": divergence
        }
        
        if vwap is not None:
            result["vwap"] = round(vwap, 2)
            
        analysis_logger.info(f"Analyzed volume: trend={volume_trend}, spike={volume_spike}")
        return result
        
    except Exception as e:
        analysis_logger.error(f"Error analyzing volume: {e}")
        return None

def extract_price_summary(data):
    """
    Extract key price summary data from the bars data.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
    
    Returns:
        dict: Price summary information
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
        elif isinstance(data, list):
            bars = data
        else:
            analysis_logger.warning("Invalid data format for price summary extraction")
            return {}
            
        if not bars:
            return {}
            
        # Extract key data points
        latest = bars[-1]
        first = bars[0]
        high_of_period = max(candle['h'] for candle in bars)
        low_of_period = min(candle['l'] for candle in bars)
        
        return {
            "start_time": first['t'],
            "end_time": latest['t'],
            "open_price": first['o'],
            "current_price": latest['c'],
            "high_of_period": high_of_period,
            "low_of_period": low_of_period,
            "price_change": round(latest['c'] - first['o'], 2),
            "price_change_percent": round((latest['c'] - first['o']) / first['o'] * 100, 2),
            "current_volume": latest['v'],
            "data_points_analyzed": len(bars)
        }
    except Exception as e:
        analysis_logger.error(f"Error extracting price summary: {e}")
        return {}

def generate_overall_summary(data, trend_analysis, breakouts=None, focus="medium_term"):
    """
    Generate an overall summary of the market analysis.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        trend_analysis (dict): Trend analysis information
        breakouts (dict): Breakout information
        focus (str): 'short_term', 'medium_term', or 'long_term'
        
    Returns:
        str: Overall summary
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
            symbol = data.get('symbol', 'The asset')
        elif isinstance(data, list):
            bars = data
            symbol = "The asset"
        else:
            analysis_logger.warning("Invalid data format for summary generation")
            return "Insufficient data for analysis."
            
        if not bars:
            return "Insufficient data for analysis."
        
        # Get trend information
        trend_direction = trend_analysis.get('direction', 'unknown')
        bullish_signals = len([s for s in trend_analysis.get('signals', []) if "bullish" in s.lower()])
        bearish_signals = len([s for s in trend_analysis.get('signals', []) if "bearish" in s.lower()])
        
        # Start building the summary
        summary = f"{symbol} price is in a {trend_direction.lower()} with {bullish_signals} bullish and {bearish_signals} bearish signals. "
        
        # Add RSI information if available
        latest = bars[-1]
        if 'rsi' in latest:
            rsi = latest['rsi']
            if rsi > 70:
                summary += f"RSI is overbought at {rsi:.1f}. "
            elif rsi < 30:
                summary += f"RSI is oversold at {rsi:.1f}. "
            else:
                summary += f"RSI is neutral at {rsi:.1f}. "
        
        # Add price change information
        first = bars[0]
        price_change = ((latest['c'] - first['c']) / first['c']) * 100
        if price_change > 0:
            summary += f"Price has increased by {price_change:.2f}% over the analyzed period. "
        else:
            summary += f"Price has decreased by {abs(price_change):.2f}% over the analyzed period. "
        
        # Add breakout information
        if breakouts:
            if "resistance_break" in breakouts:
                level = breakouts["resistance_break"]["level"]
                strength = breakouts["resistance_break"]["strength"].lower()
                summary += f"Price has shown a {strength} breakout above the {level} resistance level. "
            
            if "support_break" in breakouts:
                level = breakouts["support_break"]["level"]
                strength = breakouts["support_break"]["strength"].lower()
                summary += f"Price has shown a {strength} breakdown below the {level} support level. "
        
        # Add time-frame specific insights
        if focus == "short_term":
            if 'macd' in latest and 'macd_signal' in latest:
                if latest['macd'] > latest['macd_signal']:
                    summary += "Short-term momentum is positive with MACD above signal line. "
                else:
                    summary += "Short-term momentum is negative with MACD below signal line. "
        
        elif focus == "long_term":
            if 'sma_200' in latest:
                if latest['c'] > latest['sma_200']:
                    summary += "Price remains above the 200-day moving average, maintaining the long-term uptrend. "
                else:
                    summary += "Price remains below the 200-day moving average, maintaining the long-term downtrend. "
        
        analysis_logger.info(f"Generated overall summary: {summary[:50]}...")
        return summary
        
    except Exception as e:
        analysis_logger.error(f"Error generating overall summary: {e}")
        return "Error generating market summary."