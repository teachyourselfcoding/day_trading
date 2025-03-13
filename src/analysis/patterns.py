"""
Candlestick pattern detection module using TA-Lib.
"""
import pandas as pd
import numpy as np
import talib as ta
from src.utils.logger import analysis_logger

def detect_candlestick_patterns(bars, lookback=None):
    """
    Detect candlestick patterns in price data using TA-Lib.
    
    Args:
        bars (list): List of price bars with OHLC data
        lookback (int): Ignored for TA-Lib implementation as it uses internal lookback
    
    Returns:
        dict: Dictionary of detected patterns and their descriptions
    """
    if not bars or len(bars) < 3:
        analysis_logger.warning("Not enough bars for pattern detection (minimum 3 required)")
        return {}
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(bars)
    
    # Make sure columns are numeric and explicitly convert to float64 (double)
    for col in ['o', 'h', 'l', 'c']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
    
    # Convert columns to numpy arrays for TA-Lib, explicitly as float64
    open_prices = np.array(df['o'], dtype=np.float64)
    high = np.array(df['h'], dtype=np.float64)
    low = np.array(df['l'], dtype=np.float64)
    close = np.array(df['c'], dtype=np.float64)
    
    # Initialize patterns dictionary
    patterns = {}
    
    # Define pattern functions to check
    pattern_functions = {
        # Single candle patterns
        'doji': (ta.CDLDOJI, "A doji candlestick pattern, indicating indecision in the market."),
        'hammer': (ta.CDLHAMMER, "A hammer pattern, potentially signaling a bottom."),
        'hanging_man': (ta.CDLHANGINGMAN, "A hanging man pattern, potentially signaling a top."),
        'shooting_star': (ta.CDLSHOOTINGSTAR, "A shooting star pattern, suggesting a potential bearish reversal."),
        'inverted_hammer': (ta.CDLINVERTEDHAMMER, "An inverted hammer pattern, potentially signaling a bottom."),
        
        # Two candle patterns
        'engulfing': (ta.CDLENGULFING, "An engulfing pattern, suggesting a potential trend reversal."),
        'harami': (ta.CDLHARAMI, "A harami pattern, indicating a potential trend reversal."),
        'harami_cross': (ta.CDLHARAMICROSS, "A harami cross pattern, showing strong reversal potential."),
        'tweezer_top': (ta.CDLTWEEZERTOP, "A tweezer top pattern, suggesting a bearish reversal."),
        'tweezer_bottom': (ta.CDLTWEEZERBOTTOM, "A tweezer bottom pattern, suggesting a bullish reversal."),
        
        # Three candle patterns
        'morning_star': (ta.CDLMORNINGSTAR, "A morning star pattern, a strong bullish reversal signal."),
        'evening_star': (ta.CDLEVENINGSTAR, "An evening star pattern, a strong bearish reversal signal."),
        'three_white_soldiers': (ta.CDL3WHITESOLDIERS, "Three white soldiers pattern, indicating a strong bullish trend."),
        'three_black_crows': (ta.CDL3BLACKCROWS, "Three black crows pattern, indicating a strong bearish trend."),
        'three_inside_up': (ta.CDL3INSIDE, "Three inside up pattern, suggesting a bullish reversal."),
        'abandoned_baby': (ta.CDLABANDONEDBABY, "Abandoned baby pattern, a strong reversal signal."),
        
        # Complex patterns
        'rising_three': (ta.CDLRISEFALL3METHODS, "Rising three methods pattern, suggesting continuation."),
        'mat_hold': (ta.CDLMATHOLD, "Mat hold pattern, a bullish continuation pattern."),
        'kicking': (ta.CDLKICKING, "Kicking pattern, a strong trend reversal signal."),
        'unique_three_river': (ta.CDLUNIQUE3RIVER, "Unique three river pattern, a bullish reversal pattern."),
    }
    
    # Check each pattern
    for pattern_name, (pattern_func, description) in pattern_functions.items():
        result = pattern_func(open_prices, high, low, close)
        
        # TA-Lib returns an array of zeros and non-zeros
        # Non-zero values (usually +100 or -100) indicate pattern detected at that index
        # +100 typically means bullish pattern, -100 means bearish
        
        # Check if pattern was detected in the most recent few bars
        recent_bars = min(5, len(result))
        recent_result = result[-recent_bars:]
        
        if np.any(recent_result != 0):
            # Get the index of the most recent detection
            last_index = len(result) - 1 - np.argmax(recent_result[::-1] != 0)
            
            # Determine if it's a bullish or bearish pattern
            direction = "bullish" if result[last_index] > 0 else "bearish"
            
            # Add to the patterns dictionary
            pattern_key = f"{direction}_{pattern_name}" if result[last_index] != 0 else pattern_name
            patterns[pattern_key] = f"Detected a {direction} {pattern_name} pattern: {description}"
            analysis_logger.debug(f"Detected {direction} {pattern_name} pattern")
    
    if patterns:
        analysis_logger.info(f"Detected {len(patterns)} candlestick patterns using TA-Lib")
    else:
        analysis_logger.info("No candlestick patterns detected")
    
    return patterns

def analyze_trend(bars, periods=10):
    """
    Analyze the price trend using TA-Lib indicators.
    
    Args:
        bars (list): List of price bars
        periods (int): Number of periods to look back
    
    Returns:
        dict: Trend analysis data
    """
    if not bars or len(bars) < periods:
        analysis_logger.warning(f"Not enough bars for trend analysis (need {periods}, got {len(bars) if bars else 0})")
        return {"trend": "unknown", "strength": 0}
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(bars)
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Convert to numpy arrays
    close = np.array(df['c'])
    high = np.array(df['h'])
    low = np.array(df['l'])
    
    # Calculate ADX for trend strength
    if len(bars) >= 14:  # ADX requires at least 14 periods
        adx = ta.ADX(high, low, close, timeperiod=14)
        last_adx = adx[-1]
    else:
        last_adx = 0
    
    # Calculate directional indicators for trend direction
    if len(bars) >= 14:
        plus_di = ta.PLUS_DI(high, low, close, timeperiod=14)
        minus_di = ta.MINUS_DI(high, low, close, timeperiod=14)
        last_plus_di = plus_di[-1]
        last_minus_di = minus_di[-1]
    else:
        # Calculate simple price change as fallback
        start_price = df['c'].iloc[0]
        end_price = df['c'].iloc[-1]
        price_change = end_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        if price_change_pct > 0:
            last_plus_di = 25
            last_minus_di = 0
        else:
            last_plus_di = 0
            last_minus_di = 25
    
    # Get the relevant bars for simple trend calculation
    trend_bars = bars[-periods:]
    
    # Calculate the price change as a simple backup
    start_price = trend_bars[0]['c']
    end_price = trend_bars[-1]['c']
    price_change = end_price - start_price
    percent_change = (price_change / start_price) * 100
    
    # Determine trend based on ADX and directional indicators
    if last_adx >= 25:
        if last_plus_di > last_minus_di:
            if last_adx >= 50:
                trend = "strong_uptrend"
            else:
                trend = "uptrend"
        else:
            if last_adx >= 50:
                trend = "strong_downtrend"
            else:
                trend = "downtrend"
        
        strength = min(100, last_adx * 2)
    else:
        # Weak ADX, potentially sideways market
        if abs(percent_change) < 1.5:
            trend = "sideways"
            strength = min(100, 100 - last_adx * 2)
        else:
            # Still has some direction despite weak ADX
            if percent_change > 0:
                trend = "weak_uptrend"
            else:
                trend = "weak_downtrend"
            strength = min(100, last_adx * 2)
    
    analysis_logger.info(f"Trend analysis using TA-Lib indicators: {trend} with {strength:.1f}% strength")
    
    return {
        "trend": trend,
        "strength": round(strength, 1),
        "price_change": round(price_change, 2),
        "percent_change": round(percent_change, 2),
        "adx": round(float(last_adx), 2) if last_adx is not np.nan else 0,
        "plus_di": round(float(last_plus_di), 2) if last_plus_di is not np.nan else 0,
        "minus_di": round(float(last_minus_di), 2) if last_minus_di is not np.nan else 0
    }

def analyze_support_resistance(bars, lookback=20):
    """
    Identify potential support and resistance levels using TA-Lib.
    
    Args:
        bars (list): List of price bars
        lookback (int): Number of bars to analyze
    
    Returns:
        dict: Support and resistance levels
    """
    if not bars or len(bars) < lookback:
        analysis_logger.warning("Not enough bars for support/resistance analysis")
        return {"support": [], "resistance": []}
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(bars)
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Convert to numpy arrays
    close = np.array(df['c'])
    high = np.array(df['h'])
    low = np.array(df['l'])
    
    # Use Pivot Points as a way to find support/resistance
    # Get the most recent completed bar
    last_idx = len(bars) - 1
    
    # Try to identify recent high and low points
    # TA-Lib doesn't have a direct function for support/resistance,
    # so we'll use a Pivot Points approach
    
    # First, find local maxima and minima
    local_max = []
    local_min = []
    
    for i in range(1, min(lookback, len(bars) - 1)):
        if high[-i] > high[-(i+1)] and high[-i] > high[-(i-1)]:
            local_max.append(high[-i])
        
        if low[-i] < low[-(i+1)] and low[-i] < low[-(i-1)]:
            local_min.append(low[-i])
    
    # Current price
    current_price = close[-1]
    
    # Filter support and resistance
    support_levels = [price for price in local_min if price < current_price]
    resistance_levels = [price for price in local_max if price > current_price]
    
    # Sort and remove duplicates
    support_levels = sorted(set(support_levels), reverse=True)
    resistance_levels = sorted(set(resistance_levels))
    
    # Take at most 3 levels
    support_levels = support_levels[:3]
    resistance_levels = resistance_levels[:3]
    
    # If we don't have enough levels, add calculated pivot levels
    if len(support_levels) < 3 or len(resistance_levels) < 3:
        # Get high, low, close from last complete session 
        last_high = high[-2]
        last_low = low[-2]
        last_close = close[-2]
        
        # Calculate classic pivot point
        pivot = (last_high + last_low + last_close) / 3
        
        # Calculate support levels
        s1 = (2 * pivot) - last_high
        s2 = pivot - (last_high - last_low)
        
        # Calculate resistance levels
        r1 = (2 * pivot) - last_low
        r2 = pivot + (last_high - last_low)
        
        # Add missing support levels
        for level in [s1, s2]:
            if level < current_price and len(support_levels) < 3:
                support_levels.append(float(level))
        
        # Add missing resistance levels
        for level in [r1, r2]:
            if level > current_price and len(resistance_levels) < 3:
                resistance_levels.append(float(level))
        
        # Sort again
        support_levels = sorted(set(support_levels), reverse=True)
        resistance_levels = sorted(set(resistance_levels))
        
        # Take at most 3 levels
        support_levels = support_levels[:3]
        resistance_levels = resistance_levels[:3]
    
    analysis_logger.info(f"Identified {len(support_levels)} support and {len(resistance_levels)} resistance levels")
    
    return {
        "support": [round(level, 2) for level in support_levels],
        "resistance": [round(level, 2) for level in resistance_levels]
    }