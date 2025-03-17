"""
Candlestick pattern detection module using TA-Lib.
Enhanced with additional market pattern analysis functions.
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

def analyze_trend(data, periods=10, focus="medium_term"):
    """
    Analyze the price trend using technical indicators.
    
    Args:
        data (dict): Data dictionary with 'bars' or bars list
        periods (int): Number of periods to look back
        focus (str): 'short_term', 'medium_term', or 'long_term'
        
    Returns:
        dict: Trend analysis results
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
        elif isinstance(data, list):
            bars = data
        else:
            analysis_logger.warning("Invalid data format for trend analysis")
            return {"trend": "unknown", "strength": 0}
            
        if not bars or len(bars) < periods:
            analysis_logger.warning(f"Not enough bars for trend analysis (need {periods}, got {len(bars) if bars else 0})")
            return {"trend": "unknown", "strength": 0}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(bars)
        
        # Make sure columns are numeric
        for col in ['o', 'h', 'l', 'c']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
        
        # Extract key data for analysis
        latest = bars[-1]
        
        # Collect trend signals based on available indicators
        trend_signals = []
        
        # Moving average analysis for trend direction
        if 'sma_20' in latest and 'c' in latest:
            if latest['c'] > latest['sma_20']:
                trend_signals.append("Price above SMA 20 (bullish)")
            else:
                trend_signals.append("Price below SMA 20 (bearish)")
        
        if 'sma_50' in latest and 'c' in latest:
            if latest['c'] > latest['sma_50']:
                trend_signals.append("Price above SMA 50 (bullish)")
            else:
                trend_signals.append("Price below SMA 50 (bearish)")
                
        # Add SMA 200 analysis for long-term focus
        if focus == "long_term" and 'sma_200' in latest and 'c' in latest:
            if latest['c'] > latest['sma_200']:
                trend_signals.append("Price above SMA 200 (strongly bullish)")
            else:
                trend_signals.append("Price below SMA 200 (strongly bearish)")
        
        # MACD analysis
        if 'macd' in latest and 'macd_signal' in latest:
            if latest['macd'] > latest['macd_signal']:
                trend_signals.append("MACD above signal line (bullish)")
            else:
                trend_signals.append("MACD below signal line (bearish)")
                
            # Check MACD histogram direction if we have previous data
            if 'macd_hist' in latest and len(bars) > 1 and 'macd_hist' in bars[-2]:
                prev_hist = bars[-2]['macd_hist']
                curr_hist = latest['macd_hist']
                if curr_hist > prev_hist:
                    trend_signals.append("MACD histogram increasing (bullish momentum)")
                elif curr_hist < prev_hist:
                    trend_signals.append("MACD histogram decreasing (bearish momentum)")
        
        # RSI analysis
        if 'rsi' in latest:
            rsi = latest['rsi']
            if rsi > 70:
                trend_signals.append("RSI > 70 (overbought condition - potential sell)")
            elif rsi < 30:
                trend_signals.append("RSI < 30 (oversold condition - potential buy)")
            elif 40 <= rsi <= 60:
                trend_signals.append("RSI in neutral territory")
            elif 60 < rsi <= 70:
                trend_signals.append("RSI approaching overbought (bullish momentum)")
            elif 30 <= rsi < 40:
                trend_signals.append("RSI approaching oversold (bearish momentum)")
        
        # ADX for trend strength
        trend_strength = 50  # Default medium strength
        if 'adx' in latest:
            adx = latest['adx']
            if adx < 20:
                trend_signals.append("ADX < 20 (weak trend)")
                trend_strength = max(20, adx)
            elif 20 <= adx < 40:
                trend_signals.append("ADX between 20-40 (moderate trend)")
                trend_strength = 50 + (adx - 20)
            else:
                trend_signals.append("ADX > 40 (strong trend)")
                trend_strength = min(90, 70 + (adx - 40))
        
        # Determine trend direction from signals
        bullish_signals = len([s for s in trend_signals if "bullish" in s.lower()])
        bearish_signals = len([s for s in trend_signals if "bearish" in s.lower()])
        
        if bullish_signals > bearish_signals:
            trend_direction = "Uptrend"
        elif bearish_signals > bullish_signals:
            trend_direction = "Downtrend"
        else:
            trend_direction = "Sideways/Neutral"
            trend_strength = 30  # Lower strength for neutral trend
        
        # Calculate momentum using price changes across recent candles
        recent_lookback = 10
        if focus == "short_term":
            recent_lookback = 5
        elif focus == "long_term":
            recent_lookback = 20
            
        momentum = "Unknown"
        if len(bars) >= recent_lookback:
            recent_changes = []
            for i in range(1, min(recent_lookback, len(bars))):
                curr_idx = len(bars) - i
                prev_idx = len(bars) - i - 1
                if curr_idx >= 0 and prev_idx >= 0:
                    recent_changes.append(bars[curr_idx]['c'] - bars[prev_idx]['c'])
            
            positive_changes = sum(1 for change in recent_changes if change > 0)
            negative_changes = sum(1 for change in recent_changes if change < 0)
            
            if positive_changes >= int(recent_lookback * 0.7):
                momentum = "Strongly Bullish"
            elif positive_changes >= int(recent_lookback * 0.5):
                momentum = "Bullish"
            elif negative_changes >= int(recent_lookback * 0.7):
                momentum = "Strongly Bearish"
            elif negative_changes >= int(recent_lookback * 0.5):
                momentum = "Bearish"
            else:
                momentum = "Neutral"
        
        analysis_logger.info(f"Trend analysis: {trend_direction} with {trend_strength:.1f}% strength, {momentum} momentum")
        
        return {
            "direction": trend_direction,
            "strength": trend_strength,
            "momentum": momentum,
            "signals": trend_signals
        }
    
    except Exception as e:
        analysis_logger.error(f"Error in trend analysis: {e}")
        return {"trend": "error", "strength": 0, "momentum": "Unknown", "signals": []}

def analyze_support_resistance(data, lookback=20):
    """
    Identify potential support and resistance levels.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        lookback (int): Number of bars to analyze
    
    Returns:
        dict: Support and resistance levels
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
        elif isinstance(data, list):
            bars = data
        else:
            analysis_logger.warning("Invalid data format for support/resistance analysis")
            return {"support": [], "resistance": []}
            
        if not bars or len(bars) < lookback:
            analysis_logger.warning("Not enough bars for support/resistance analysis")
            return {"support": [], "resistance": []}
        
        # Use the full data set or the specified lookback period
        bars_to_analyze = bars[-min(lookback, len(bars)):]
        
        # Find significant price levels by looking for areas of price congestion
        price_points = []
        for bar in bars_to_analyze:
            price_points.extend([bar['h'], bar['l']])
        
        # Group prices into clusters
        price_points.sort()
        zones = []
        
        if price_points:
            current_zone = [price_points[0]]
            latest_close = bars[-1]['c']
            zone_threshold = latest_close * 0.005  # 0.5% threshold for zone detection
            
            for price in price_points[1:]:
                if price - current_zone[-1] < zone_threshold:
                    current_zone.append(price)
                else:
                    if len(current_zone) > 3:  # Consider it a significant zone if multiple touches
                        zones.append(sum(current_zone) / len(current_zone))
                    current_zone = [price]
            
            # Add the last zone if significant
            if len(current_zone) > 3:
                zones.append(sum(current_zone) / len(current_zone))
        
        # Separate into support and resistance based on current price
        current_price = bars[-1]['c']
        support_levels = [round(z, 2) for z in zones if z < current_price]
        resistance_levels = [round(z, 2) for z in zones if z > current_price]
        
        # Take the closest levels (up to 3)
        if support_levels:
            support_levels = sorted(support_levels, reverse=True)[:3]
        
        if resistance_levels:
            resistance_levels = sorted(resistance_levels)[:3]
        
        # Calculate relative position within range
        range_position = None
        if support_levels and resistance_levels:
            min_support = min(support_levels)
            max_resistance = max(resistance_levels)
            range_size = max_resistance - min_support
            
            if range_size > 0:
                range_position = round(((current_price - min_support) / range_size) * 100, 1)
        
        result = {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
        }
        
        if range_position is not None:
            result["current_price_location"] = f"Currently {range_position}% through the range"
            
        analysis_logger.info(f"Identified {len(support_levels)} support and {len(resistance_levels)} resistance levels")
        return result
    
    except Exception as e:
        analysis_logger.error(f"Error analyzing support/resistance: {e}")
        return {"support_levels": [], "resistance_levels": []}

def detect_breakouts(data, support_resistance):
    """
    Detect potential breakouts from support and resistance levels.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        support_resistance (dict): Support and resistance levels
        
    Returns:
        dict: Breakout information
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
        elif isinstance(data, list):
            bars = data
        else:
            analysis_logger.warning("Invalid data format for breakout detection")
            return None
            
        if not bars:
            return None
            
        current_price = bars[-1]['c']
        breakouts = {}
        
        # Get support and resistance levels
        resistance_levels = support_resistance.get('resistance_levels', [])
        support_levels = support_resistance.get('support_levels', [])
        
        # Check for resistance breakout
        if resistance_levels and current_price > min(resistance_levels):
            breakout_level = min(resistance_levels)
            breakouts["resistance_break"] = {
                "level": breakout_level,
                "occurred": True,
                "strength": "Strong" if current_price > breakout_level * 1.01 else "Moderate",
                "percentage_move": round((current_price - breakout_level) / breakout_level * 100, 2)
            }
        
        # Check for support breakdown
        if support_levels and current_price < max(support_levels):
            breakdown_level = max(support_levels)
            breakouts["support_break"] = {
                "level": breakdown_level,
                "occurred": True,
                "strength": "Strong" if current_price < breakdown_level * 0.99 else "Moderate",
                "percentage_move": round((breakdown_level - current_price) / breakdown_level * 100, 2)
            }
            
        if breakouts:
            analysis_logger.info(f"Detected breakouts: {', '.join(breakouts.keys())}")
            
        return breakouts if breakouts else None
        
    except Exception as e:
        analysis_logger.error(f"Error detecting breakouts: {e}")
        return None

def generate_market_context(data, focus="medium_term"):
    """
    Generate market context information based on recent price action.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        focus (str): 'short_term', 'medium_term', or 'long_term'
        
    Returns:
        str: Market context description
    """
    try:
        # Handle different input formats
        if isinstance(data, dict) and 'bars' in data:
            bars = data['bars']
        elif isinstance(data, list):
            bars = data
        else:
            analysis_logger.warning("Invalid data format for market context generation")
            return "Insufficient data for market context analysis."
            
        if not bars:
            return "Insufficient data for market context analysis."
            
        latest = bars[-1]
        
        # Determine volatility level
        volatility_desc = "moderate"
        if 'atr' in latest and 'c' in latest:
            atr = latest['atr']
            current_price = latest['c']
            atr_percent = (atr / current_price) * 100
            
            if atr_percent > 2.0:
                volatility_desc = "high"
            elif atr_percent < 1.0:
                volatility_desc = "low"
        
        market_context = f"Recent volatility is {volatility_desc}. "
        
        # Analyze recent price patterns
        lookback = 5
        if focus == "short_term":
            lookback = 3
        elif focus == "long_term":
            lookback = 10
            
        if len(bars) >= lookback:
            closes = [bars[-i]['c'] for i in range(1, lookback + 1)]
            
            up_days = 0
            down_days = 0
            for i in range(1, len(closes)):
                if closes[i-1] > closes[i]:  # Remember we're going backwards in time
                    up_days += 1
                elif closes[i-1] < closes[i]:
                    down_days += 1
            
            if up_days >= lookback * 0.8:
                market_context += f"Strong upward momentum over the last {lookback} periods. "
            elif up_days >= lookback * 0.6:
                market_context += f"Moderate upward momentum over the last {lookback} periods. "
            elif down_days >= lookback * 0.8:
                market_context += f"Strong downward momentum over the last {lookback} periods. "
            elif down_days >= lookback * 0.6:
                market_context += f"Moderate downward momentum over the last {lookback} periods. "
            else:
                market_context += f"Mixed price action over the last {lookback} periods. "
                
        # Add relevant time horizon context
        if focus == "short_term":
            # Check for intraday patterns
            if len(bars) >= 3:
                if bars[-1]['c'] > bars[-1]['o'] and bars[-2]['c'] > bars[-2]['o']:
                    market_context += "Recent consecutive bullish candles suggest short-term buying pressure. "
                elif bars[-1]['c'] < bars[-1]['o'] and bars[-2]['c'] < bars[-2]['o']:
                    market_context += "Recent consecutive bearish candles suggest short-term selling pressure. "
        
        elif focus == "long_term":
            # Check for longer-term trend consistency
            if 'sma_50' in latest and 'sma_200' in latest:
                if latest['sma_50'] > latest['sma_200']:
                    market_context += "The long-term trend remains bullish with 50-day SMA above 200-day SMA. "
                else:
                    market_context += "The long-term trend remains bearish with 50-day SMA below 200-day SMA. "
                    
        analysis_logger.info(f"Generated market context: {market_context[:50]}...")
        return market_context
        
    except Exception as e:
        analysis_logger.error(f"Error generating market context: {e}")
        return "Error generating market context."