"""
Candlestick pattern detection module.
"""
from src.utils.logger import analysis_logger

def detect_candlestick_patterns(bars, lookback=5):
    """
    Detect candlestick patterns in price data.
    
    Args:
        bars (list): List of price bars with OHLC data
        lookback (int): Number of bars to look back for pattern detection
    
    Returns:
        dict: Dictionary of detected patterns and their descriptions
    """
    if not bars or len(bars) < 3:
        analysis_logger.warning("Not enough bars for pattern detection (minimum 3 required)")
        return {}
    
    # Get the most recent bars within the lookback period
    recent_bars = bars[-min(lookback, len(bars)):]
    patterns = {}
    
    # Get the most recent bar for single-candle patterns
    latest = recent_bars[-1]
    
    # Doji Pattern (open and close are almost equal)
    body_size = abs(latest['o'] - latest['c'])
    candle_range = latest['h'] - latest['l']
    
    if candle_range > 0 and body_size <= 0.1 * candle_range:
        patterns["doji"] = "The latest candle is a doji, indicating indecision in the market."
        analysis_logger.debug(f"Detected Doji pattern")
    
    # Hammer/Hanging Man Pattern
    if candle_range > 0:
        body_size = abs(latest['o'] - latest['c'])
        lower_wick = min(latest['o'], latest['c']) - latest['l']
        upper_wick = latest['h'] - max(latest['o'], latest['c'])
        
        if (body_size <= 0.3 * candle_range and 
            lower_wick >= 2 * body_size and 
            upper_wick <= 0.1 * candle_range):
            
            if latest['c'] > latest['o']:  # Bullish (green) candle
                patterns["hammer"] = "The latest candle is a hammer, potentially signaling a bottom."
                analysis_logger.debug(f"Detected Hammer pattern")
            else:  # Bearish (red) candle
                patterns["hanging_man"] = "The latest candle is a hanging man, potentially signaling a top."
                analysis_logger.debug(f"Detected Hanging Man pattern")
    
    # Two-candle patterns (if we have at least 2 candles)
    if len(recent_bars) >= 2:
        prev = recent_bars[-2]
        curr = recent_bars[-1]
        
        # Bullish Engulfing
        if (prev['c'] < prev['o'] and  # Previous candle is bearish (red)
            curr['c'] > curr['o'] and  # Current candle is bullish (green)
            curr['o'] < prev['c'] and  # Current opens below previous close
            curr['c'] > prev['o']):    # Current closes above previous open
            
            patterns["bullish_engulfing"] = "Detected a bullish engulfing pattern, suggesting potential trend reversal to the upside."
            analysis_logger.debug(f"Detected Bullish Engulfing pattern")
        
        # Bearish Engulfing
        elif (prev['c'] > prev['o'] and  # Previous candle is bullish (green)
              curr['c'] < curr['o'] and  # Current candle is bearish (red)
              curr['o'] > prev['c'] and  # Current opens above previous close
              curr['c'] < prev['o']):    # Current closes below previous open
            
            patterns["bearish_engulfing"] = "Detected a bearish engulfing pattern, suggesting potential trend reversal to the downside."
            analysis_logger.debug(f"Detected Bearish Engulfing pattern")
    
    # Three-candle patterns (if we have at least 3 candles)
    if len(recent_bars) >= 3:
        first = recent_bars[-3]
        middle = recent_bars[-2]
        last = recent_bars[-1]
        
        first_body = abs(first['o'] - first['c'])
        middle_body = abs(middle['o'] - middle['c'])
        last_body = abs(last['o'] - last['c'])
        
        # Morning Star (bullish reversal)
        if (first['c'] < first['o'] and  # First candle is bearish
            middle_body <= 0.5 * first_body and  # Middle candle is small
            last['c'] > last['o'] and  # Last candle is bullish
            middle['h'] < first['c'] and  # Gap down to middle
            last['o'] > middle['h']):  # Gap up from middle
            
            patterns["morning_star"] = "Detected a morning star pattern, a strong bullish reversal signal."
            analysis_logger.debug(f"Detected Morning Star pattern")
        
        # Evening Star (bearish reversal)
        elif (first['c'] > first['o'] and  # First candle is bullish
              middle_body <= 0.5 * first_body and  # Middle candle is small
              last['c'] < last['o'] and  # Last candle is bearish
              middle['l'] > first['c'] and  # Gap up to middle
              last['o'] < middle['l']):  # Gap down from middle
            
            patterns["evening_star"] = "Detected an evening star pattern, a strong bearish reversal signal."
            analysis_logger.debug(f"Detected Evening Star pattern")
        
        # Three White Soldiers (bullish continuation)
        if (first['c'] > first['o'] and  # First candle is bullish
            middle['c'] > middle['o'] and  # Second candle is bullish
            last['c'] > last['o'] and  # Third candle is bullish
            middle['o'] > first['o'] and  # Each opens higher
            last['o'] > middle['o'] and
            middle['c'] > first['c'] and  # Each closes higher
            last['c'] > middle['c']):
            
            patterns["three_white_soldiers"] = "Detected three white soldiers pattern, indicating a strong bullish trend."
            analysis_logger.debug(f"Detected Three White Soldiers pattern")
        
        # Three Black Crows (bearish continuation)
        if (first['c'] < first['o'] and  # First candle is bearish
            middle['c'] < middle['o'] and  # Second candle is bearish
            last['c'] < last['o'] and  # Third candle is bearish
            middle['o'] < first['o'] and  # Each opens lower
            last['o'] < middle['o'] and
            middle['c'] < first['c'] and  # Each closes lower
            last['c'] < middle['c']):
            
            patterns["three_black_crows"] = "Detected three black crows pattern, indicating a strong bearish trend."
            analysis_logger.debug(f"Detected Three Black Crows pattern")
    
    if patterns:
        analysis_logger.info(f"Detected {len(patterns)} candlestick patterns")
    else:
        analysis_logger.info("No candlestick patterns detected")
    
    return patterns

def analyze_trend(bars, periods=10):
    """
    Analyze the price trend.
    
    Args:
        bars (list): List of price bars
        periods (int): Number of periods to look back
    
    Returns:
        dict: Trend analysis data
    """
    if not bars or len(bars) < periods:
        analysis_logger.warning(f"Not enough bars for trend analysis (need {periods}, got {len(bars) if bars else 0})")
        return {"trend": "unknown", "strength": 0}
    
    # Get the relevant bars
    trend_bars = bars[-periods:]
    
    # Calculate the price change
    start_price = trend_bars[0]['c']
    end_price = trend_bars[-1]['c']
    price_change = end_price - start_price
    percent_change = (price_change / start_price) * 100
    
    # Determine trend direction and strength
    if percent_change > 5:
        trend = "strong_uptrend"
        strength = min(100, abs(percent_change) * 2)
    elif percent_change > 1.5:
        trend = "uptrend"
        strength = min(100, abs(percent_change) * 2)
    elif percent_change < -5:
        trend = "strong_downtrend"
        strength = min(100, abs(percent_change) * 2)
    elif percent_change < -1.5:
        trend = "downtrend"
        strength = min(100, abs(percent_change) * 2)
    else:
        trend = "sideways"
        strength = min(100, 100 - abs(percent_change) * 5)
    
    analysis_logger.info(f"Trend analysis: {trend} with {strength:.1f}% strength")
    
    return {
        "trend": trend,
        "strength": round(strength, 1),
        "price_change": round(price_change, 2),
        "percent_change": round(percent_change, 2)
    }

def analyze_support_resistance(bars, lookback=20):
    """
    Identify potential support and resistance levels.
    
    Args:
        bars (list): List of price bars
        lookback (int): Number of bars to analyze
    
    Returns:
        dict: Support and resistance levels
    """
    if not bars or len(bars) < lookback:
        analysis_logger.warning("Not enough bars for support/resistance analysis")
        return {"support": [], "resistance": []}
    
    analysis_bars = bars[-lookback:]
    
    # Find local highs and lows
    highs = []
    lows = []
    
    # Simple algorithm for local extrema
    for i in range(1, len(analysis_bars) - 1):
        # Local high
        if (analysis_bars[i]['h'] > analysis_bars[i-1]['h'] and 
            analysis_bars[i]['h'] > analysis_bars[i+1]['h']):
            highs.append(analysis_bars[i]['h'])
        
        # Local low
        if (analysis_bars[i]['l'] < analysis_bars[i-1]['l'] and 
            analysis_bars[i]['l'] < analysis_bars[i+1]['l']):
            lows.append(analysis_bars[i]['l'])
    
    # Cluster close levels (within 0.5% of each other)
    support_levels = []
    resistance_levels = []
    
    if lows:
        current_price = analysis_bars[-1]['c']
        for level in lows:
            if level < current_price:  # Only levels below current price are support
                # Check if we already have a close level
                is_new = True
                for existing in support_levels:
                    if abs(existing - level) / existing < 0.005:  # Within 0.5%
                        is_new = False
                        break
                
                if is_new:
                    support_levels.append(level)
    
    if highs:
        current_price = analysis_bars[-1]['c']
        for level in highs:
            if level > current_price:  # Only levels above current price are resistance
                # Check if we already have a close level
                is_new = True
                for existing in resistance_levels:
                    if abs(existing - level) / existing < 0.005:  # Within 0.5%
                        is_new = False
                        break
                
                if is_new:
                    resistance_levels.append(level)
    
    # Sort and take the closest few levels
    support_levels.sort(reverse=True)  # Closest support first
    resistance_levels.sort()  # Closest resistance first
    
    # Take at most 3 levels
    support_levels = support_levels[:3]
    resistance_levels = resistance_levels[:3]
    
    analysis_logger.info(f"Identified {len(support_levels)} support and {len(resistance_levels)} resistance levels")
    
    return {
        "support": [round(level, 2) for level in support_levels],
        "resistance": [round(level, 2) for level in resistance_levels]
    }