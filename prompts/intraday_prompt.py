"""
Enhanced prompt generator with technical indicator analysis for different timeframes.
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.logger import signals_logger


def prepare_medium_term_prompt(data, symbol, interval):
    """
    Prepare a prompt for medium-term trading analysis with a defined role for the LLM.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    try:
        # First, make sure we have data to work with
        if not data or 'bars' not in data or not data['bars']:
            signals_logger.error(f"No bars in data for prompt generation for {symbol}")
            return None
            
        signals_logger.info(f"Preparing medium_term prompt for {symbol}")
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(data['bars'])
        
        # Extract key data points
        latest = data['bars'][-1]
        first = data['bars'][0]
        high_of_period = max(candle['h'] for candle in data['bars'])
        low_of_period = min(candle['l'] for candle in data['bars'])
        
        # Define the LLM's role and approach
        role_definition = {
                "role": "Experienced Technical Analyst",
                "expertise": "Medium-term market analysis focusing on swing trading opportunities",
                "approach": "Balanced analysis of technical indicators, price action, and market structure",
                "time_horizon": "5-20 days holding period",
                "risk_management": "Emphasis on favorable risk-reward ratios with clear stop loss levels",
                "analysis_style": "Objective, data-driven with focus on probability rather than certainty"
            }
        
        # Prepare the prompt
        prompt = {
            "role_definition": role_definition,
            "task": f"Analyze market data and technical indicators to generate medium term trading signals for {symbol}.",
            "symbol": symbol,
            "interval": interval,
            "market_data": {
                "start_time": first['t'],
                "end_time": latest['t'],
                "open_price": first['o'],
                "current_price": latest['c'],
                "high_of_period": high_of_period,
                "low_of_period": low_of_period,
                "price_change": round(latest['c'] - first['o'], 2),
                "price_change_percent": round((latest['c'] - first['o']) / first['o'] * 100, 2),
                "current_volume": latest['v'],
                "data_points_analyzed": len(data['bars'])
            },
            "technical_analysis": {},
            "trading_style": "medium_term",
            "expected_response_format": {
                "pattern_identified": "<pattern_name>",
                "pattern_confidence": "<low/medium/high>",
                "suggested_action": "<buy/sell/hold>",
                "entry_price": "<suggested_entry>",
                "stop_loss": "<suggested_stop_loss>",
                "take_profit": "<suggested_take_profit>",
                "risk_reward_ratio": "<calculated_ratio>",
                "reasoning": "<evidence-based_reasoning_for_decision>",
                "alternative_scenario": "<what_could_invalidate_this_analysis>",
                "timeframe": "<expected_holding_period>"
            }
        }
        
        # Add technical indicators if available
        indicators = {}
        indicator_fields = [
            'sma_20', 'sma_50', 'sma_200', 
            'ema_12', 'ema_26', 
            'macd', 'macd_signal', 'macd_hist',
            'rsi', 'atr',
            'bb_upper', 'bb_middle', 'bb_lower',
            'stoch_k', 'stoch_d'
        ]
        
        for field in indicator_fields:
            if field in latest:
                indicators[field] = latest[field]
        
        # Add indicators to the prompt
        if indicators:
            prompt["technical_analysis"]["current_indicators"] = indicators
        
        # Add trend analysis
        trend_signals = []
        if 'sma_20' in indicators and 'c' in latest:
            if latest['c'] > indicators['sma_20']:
                trend_signals.append("Price above SMA 20 (bullish)")
            else:
                trend_signals.append("Price below SMA 20 (bearish)")
        
        if 'sma_50' in indicators and 'c' in latest:
            if latest['c'] > indicators['sma_50']:
                trend_signals.append("Price above SMA 50 (bullish)")
            else:
                trend_signals.append("Price below SMA 50 (bearish)")
        
        if 'macd' in indicators and 'macd_signal' in indicators:
            if indicators['macd'] > indicators['macd_signal']:
                trend_signals.append("MACD above signal line (bullish)")
            else:
                trend_signals.append("MACD below signal line (bearish)")
        
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi > 70:
                trend_signals.append("RSI > 70 (overbought condition - potential sell)")
            elif rsi < 30:
                trend_signals.append("RSI < 30 (oversold condition - potential buy)")
            elif 40 <= rsi <= 60:
                trend_signals.append("RSI in neutral territory")
        
        # Determine trend direction
        bullish_signals = len([s for s in trend_signals if "bullish" in s.lower()])
        bearish_signals = len([s for s in trend_signals if "bearish" in s.lower()])
        
        if bullish_signals > bearish_signals:
            trend_direction = "Uptrend"
            trend_strength = min(100, bullish_signals * 20)
        elif bearish_signals > bullish_signals:
            trend_direction = "Downtrend"
            trend_strength = min(100, bearish_signals * 20)
        else:
            trend_direction = "Sideways/Neutral"
            trend_strength = 30
        
        # Calculate momentum using price changes across the last several candles
        if len(data['bars']) >= 10:
            recent_changes = [data['bars'][i]['c'] - data['bars'][i-1]['c'] for i in range(-1, -10, -1)]
            positive_changes = sum(1 for change in recent_changes if change > 0)
            negative_changes = sum(1 for change in recent_changes if change < 0)
            
            if positive_changes >= 7:
                momentum = "Strongly Bullish"
            elif positive_changes >= 5:
                momentum = "Bullish"
            elif negative_changes >= 7:
                momentum = "Strongly Bearish"
            elif negative_changes >= 5:
                momentum = "Bearish"
            else:
                momentum = "Neutral"
        else:
            momentum = "Insufficient data for momentum calculation"
        
        # Add trend analysis to the prompt
        prompt["technical_analysis"]["trend_analysis"] = {
            "direction": trend_direction,
            "strength": trend_strength,
            "momentum": momentum,
            "signals": trend_signals
        }
        
        # Add support and resistance levels - more sophisticated approach
        # Find significant price levels by looking for areas of price congestion
        price_points = []
        for bar in data['bars']:
            price_points.extend([bar['h'], bar['l']])
        
        # Group prices into clusters
        price_points.sort()
        zones = []
        
        if price_points:
            current_zone = [price_points[0]]
            avg_price = latest['c']
            zone_threshold = avg_price * 0.005  # 0.5% threshold for zone detection
            
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
        current_price = latest['c']
        support_levels = [round(z, 2) for z in zones if z < current_price]
        resistance_levels = [round(z, 2) for z in zones if z > current_price]
        
        # Take the 3 closest levels
        if support_levels:
            support_levels = sorted(support_levels, reverse=True)[:3]
        
        if resistance_levels:
            resistance_levels = sorted(resistance_levels)[:3]
        
        # Add support/resistance to the prompt
        prompt["technical_analysis"]["support_resistance"] = {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "current_price_location": f"Currently {round(((current_price - min(support_levels)) / (max(resistance_levels) - min(support_levels)) * 100) if support_levels and resistance_levels else 0, 1)}% through the range"
        }
        
        # Add volume analysis
        if len(data['bars']) >= 10:
            recent_volumes = [bar['v'] for bar in data['bars'][-10:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            latest_volume = latest['v']
            
            volume_analysis = {
                "average_10_period": avg_volume,
                "current_volume": latest_volume,
                "volume_trend": "Increasing" if latest_volume > avg_volume * 1.2 else "Decreasing" if latest_volume < avg_volume * 0.8 else "Stable"
            }
            
            prompt["technical_analysis"]["volume_analysis"] = volume_analysis
        
        # Detect breakout conditions
        breakouts = {}
        
        # Check for potential breakouts
        if resistance_levels and current_price > min(resistance_levels):
            breakout_level = min(resistance_levels)
            breakouts["resistance_break"] = {
                "level": breakout_level,
                "occurred": True,
                "strength": "Strong" if current_price > breakout_level * 1.01 else "Moderate",
                "percentage_move": round((current_price - breakout_level) / breakout_level * 100, 2)
            }
        
        if support_levels and current_price < max(support_levels):
            breakdown_level = max(support_levels)
            breakouts["support_break"] = {
                "level": breakdown_level,
                "occurred": True,
                "strength": "Strong" if current_price < breakdown_level * 0.99 else "Moderate",
                "percentage_move": round((breakdown_level - current_price) / breakdown_level * 100, 2)
            }
        
        if breakouts:
            prompt["technical_analysis"]["breakouts"] = breakouts
        
        # Generate market context
        market_context = f"Recent volatility is {('high' if 'atr' in indicators and indicators['atr'] > latest['c'] * 0.02 else 'moderate' if 'atr' in indicators and indicators['atr'] > latest['c'] * 0.01 else 'low')}. "
        
        # Add previous 5 day pattern description
        if len(data['bars']) >= 5:
            last_5_close = [data['bars'][-i]['c'] for i in range(1, 6)]
            
            up_days = sum(1 for i in range(1, 5) if last_5_close[i-1] > last_5_close[i])
            down_days = sum(1 for i in range(1, 5) if last_5_close[i-1] < last_5_close[i])
            
            if up_days >= 4:
                market_context += "Strong upward momentum over the last 5 periods. "
            elif up_days >= 3:
                market_context += "Moderate upward momentum over the last 5 periods. "
            elif down_days >= 4:
                market_context += "Strong downward momentum over the last 5 periods. "
            elif down_days >= 3:
                market_context += "Moderate downward momentum over the last 5 periods. "
            else:
                market_context += "Mixed price action over the last 5 periods. "
        
        prompt["market_context"] = market_context
        
        # Generate an overall summary
        summary = f"The {symbol} price is in a {trend_direction.lower()} with {bullish_signals} bullish and {bearish_signals} bearish signals. "
        
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi > 70:
                summary += f"RSI is overbought at {rsi:.1f}. "
            elif rsi < 30:
                summary += f"RSI is oversold at {rsi:.1f}. "
            else:
                summary += f"RSI is neutral at {rsi:.1f}. "
        
        price_change = prompt["market_data"]["price_change_percent"]
        if price_change > 0:
            summary += f"Price has increased by {price_change:.2f}% over the analyzed period. "
        else:
            summary += f"Price has decreased by {abs(price_change):.2f}% over the analyzed period. "
        
        # Add breakout information
        if "breakouts" in prompt["technical_analysis"]:
            if "resistance_break" in prompt["technical_analysis"]["breakouts"]:
                level = prompt["technical_analysis"]["breakouts"]["resistance_break"]["level"]
                strength = prompt["technical_analysis"]["breakouts"]["resistance_break"]["strength"].lower()
                summary += f"Price has shown a {strength} breakout above the {level} resistance level. "
            
            if "support_break" in prompt["technical_analysis"]["breakouts"]:
                level = prompt["technical_analysis"]["breakouts"]["support_break"]["level"]
                strength = prompt["technical_analysis"]["breakouts"]["support_break"]["strength"].lower()
                summary += f"Price has shown a {strength} breakdown below the {level} support level. "
        
        prompt["technical_analysis"]["overall_summary"] = summary
        
        # Convert to JSON string
        return json.dumps(prompt, indent=2)
    
    except Exception as e:
        signals_logger.error(f"Error preparing medium_term prompt for {symbol}: {e}")
        return None
    
def prepare_short_term_prompt(data, symbol, interval):
    """
    Prepare a prompt for short-term trading analysis.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    # Simply call the base function with short_term trading style
    return prepare_llm_prompt(data, symbol, interval, trading_style="short_term")


def prepare_long_term_prompt(data, symbol, interval):
    """
    Prepare a prompt for long-term trading analysis.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    # Simply call the base function with long_term trading style
    return prepare_llm_prompt(data, symbol, interval, trading_style="long_term")

def prepare_llm_prompt(data, symbol, interval, trading_style="medium_term"):
    """
    Prepare a prompt for OpenAI based on the intraday data and technical indicators.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
        trading_style (str): 'short_term', 'medium_term', or 'long_term'
    
    Returns:
        str: JSON prompt for OpenAI
    """
    if not data or 'bars' not in data or len(data['bars']) == 0:
        signals_logger.error("No bars in data for prompt generation")
        return None
        
    signals_logger.info(f"Preparing {trading_style} prompt for {symbol}")
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(data['bars'])
    
    # Extract key data points
    latest = data['bars'][-1]
    first = data['bars'][0]
    high_of_period = max(candle['h'] for candle in data['bars'])
    low_of_period = min(candle['l'] for candle in data['bars'])
    
    # Determine which indicators to include based on trading style
    technical_analysis = extract_technical_analysis(df, trading_style)
    
    # Prepare the prompt
    prompt = {
        "task": f"Analyze market data and technical indicators to generate {trading_style.replace('_', ' ')} trading signals.",
        "symbol": symbol,
        "interval": interval,
        "market_data": {
            "start_time": first['t'],
            "end_time": latest['t'],
            "open_price": first['o'],
            "current_price": latest['c'],
            "high_of_period": high_of_period,
            "low_of_period": low_of_period,
            "price_change": round(latest['c'] - first['o'], 2),
            "price_change_percent": round((latest['c'] - first['o']) / first['o'] * 100, 2),
            "current_volume": latest['v'],
            "data_points_analyzed": len(data['bars'])
        },
        "technical_analysis": technical_analysis,
        "trading_style": trading_style,
        "expected_response_format": {
            "pattern_identified": "<pattern_name>",
            "pattern_confidence": "<low/medium/high>",
            "suggested_action": "<buy/sell/hold>",
            "entry_price": "<suggested_entry>",
            "stop_loss": "<suggested_stop_loss>",
            "take_profit": "<suggested_take_profit>",
            "reasoning": "<brief_reasoning_for_decision>",
            "timeframe": "<expected_holding_period>"
        }
    }
    
    return json.dumps(prompt)

def extract_technical_analysis(df, trading_style):
    """
    Extract technical indicators based on trading style.
    
    Args:
        df (DataFrame): DataFrame with price and indicator data
        trading_style (str): 'short_term', 'medium_term', or 'long_term'
    
    Returns:
        dict: Technical analysis data
    """
    # Common indicators for all trading styles
    analysis = {
        "current_indicators": {},
        "trend_analysis": {},
        "support_resistance": {},
        "oscillators": {},
        "overall_summary": ""
    }
    
    # Extract the most recent values for technical indicators
    for col in df.columns:
        if col.startswith(('sma_', 'ema_', 'bb_', 'rsi', 'macd', 'stoch_', 'adx', 'atr')):
            analysis["current_indicators"][col] = float(df[col].iloc[-1]) if not pd.isna(df[col].iloc[-1]) else 0
    
    # Determine indicator signals
    signals = []
    
    # Moving average analysis
    if 'sma_20' in df.columns and 'sma_50' in df.columns:
        current_sma20 = df['sma_20'].iloc[-1]
        current_sma50 = df['sma_50'].iloc[-1]
        prev_sma20 = df['sma_20'].iloc[-2] if len(df) > 2 else None
        prev_sma50 = df['sma_50'].iloc[-2] if len(df) > 2 else None
        
        if pd.notna(current_sma20) and pd.notna(current_sma50):
            # Price relative to SMAs
            if df['c'].iloc[-1] > current_sma20:
                signals.append("Price above SMA 20 (bullish)")
            else:
                signals.append("Price below SMA 20 (bearish)")
            
            if df['c'].iloc[-1] > current_sma50:
                signals.append("Price above SMA 50 (bullish)")
            else:
                signals.append("Price below SMA 50 (bearish)")
            
            # Golden/Death cross
            if pd.notna(prev_sma20) and pd.notna(prev_sma50):
                if current_sma20 > current_sma50 and prev_sma20 <= prev_sma50:
                    signals.append("Golden Cross (SMA 20 crossed above SMA 50) - strongly bullish")
                elif current_sma20 < current_sma50 and prev_sma20 >= prev_sma50:
                    signals.append("Death Cross (SMA 20 crossed below SMA 50) - strongly bearish")
    
    # MACD analysis
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        current_macd = df['macd'].iloc[-1]
        current_signal = df['macd_signal'].iloc[-1]
        prev_macd = df['macd'].iloc[-2] if len(df) > 2 else None
        prev_signal = df['macd_signal'].iloc[-2] if len(df) > 2 else None
        
        if pd.notna(current_macd) and pd.notna(current_signal):
            if current_macd > current_signal:
                signals.append("MACD above signal line (bullish)")
            else:
                signals.append("MACD below signal line (bearish)")
            
            # MACD crossover
            if pd.notna(prev_macd) and pd.notna(prev_signal):
                if current_macd > current_signal and prev_macd <= prev_signal:
                    signals.append("MACD bullish crossover (buy signal)")
                elif current_macd < current_signal and prev_macd >= prev_signal:
                    signals.append("MACD bearish crossover (sell signal)")
    
    # RSI analysis
    if 'rsi' in df.columns:
        current_rsi = df['rsi'].iloc[-1]
        
        if pd.notna(current_rsi):
            if current_rsi > 70:
                signals.append("RSI > 70 (overbought condition - potential sell)")
            elif current_rsi < 30:
                signals.append("RSI < 30 (oversold condition - potential buy)")
            elif 40 <= current_rsi <= 60:
                signals.append("RSI in neutral territory")
    
    # Bollinger Bands analysis
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        close = df['c'].iloc[-1]
        
        if pd.notna(bb_upper) and pd.notna(bb_lower):
            if close > bb_upper:
                signals.append("Price above upper Bollinger Band (potential overbought)")
            elif close < bb_lower:
                signals.append("Price below lower Bollinger Band (potential oversold)")
            # Bollinger Band squeeze (volatility indicator)
            band_width = (bb_upper - bb_lower) / df['bb_middle'].iloc[-1] if 'bb_middle' in df.columns else 0
            avg_band_width = band_width
            if len(df) > 20:
                # Calculate average band width over last 20 periods for comparison
                past_widths = []
                for i in range(-20, -1):
                    if (pd.notna(df['bb_upper'].iloc[i]) and pd.notna(df['bb_lower'].iloc[i]) and 
                        pd.notna(df['bb_middle'].iloc[i]) and df['bb_middle'].iloc[i] != 0):
                        past_widths.append((df['bb_upper'].iloc[i] - df['bb_lower'].iloc[i]) / df['bb_middle'].iloc[i])
                if past_widths:
                    avg_band_width = sum(past_widths) / len(past_widths)
                
                if band_width < 0.8 * avg_band_width:
                    signals.append("Bollinger Band squeeze (low volatility - potential breakout ahead)")
                elif band_width > 1.2 * avg_band_width:
                    signals.append("Wide Bollinger Bands (high volatility)")
    
    # Add support and resistance levels based on recent price action
    support_levels = []
    resistance_levels = []
    
    # Use a simple method to find recent lows as support and highs as resistance
    window_size = min(20, len(df)-1)  # Look at last 20 bars or less if not enough data
    window = df.iloc[-window_size:]
    
    # Find local minima and maxima
    for i in range(1, window_size-1):
        # Local minimum (potential support)
        if window['l'].iloc[i] < window['l'].iloc[i-1] and window['l'].iloc[i] < window['l'].iloc[i+1]:
            support_levels.append(float(window['l'].iloc[i]))
        
        # Local maximum (potential resistance)
        if window['h'].iloc[i] > window['h'].iloc[i-1] and window['h'].iloc[i] > window['h'].iloc[i+1]:
            resistance_levels.append(float(window['h'].iloc[i]))
    
    # Sort and keep only the most significant levels (closest to current price)
    current_price = df['c'].iloc[-1]
    support_levels = sorted([level for level in support_levels if level < current_price], reverse=True)[:3]
    resistance_levels = sorted([level for level in resistance_levels if level > current_price])[:3]
    
    analysis["support_resistance"] = {
        "support_levels": support_levels,
        "resistance_levels": resistance_levels
    }
    
    # Overall trend determination
    uptrend_signals = [signal for signal in signals if "bullish" in signal.lower()]
    downtrend_signals = [signal for signal in signals if "bearish" in signal.lower()]
    
    if len(uptrend_signals) > len(downtrend_signals):
        trend_direction = "Uptrend"
        trend_strength = min(100, len(uptrend_signals) * 20)  # Simple scaling for strength
    elif len(downtrend_signals) > len(uptrend_signals):
        trend_direction = "Downtrend"
        trend_strength = min(100, len(downtrend_signals) * 20)
    else:
        trend_direction = "Sideways/Neutral"
        trend_strength = 30  # Lower strength for neutral trend
    
    # Calculate price momentum
    if len(df) >= 5:
        # Simple momentum calculation using last 5 periods
        recent_price_changes = [df['c'].iloc[i] - df['c'].iloc[i-1] for i in range(-4, 0)]
        momentum = sum(1 for change in recent_price_changes if change > 0) - sum(1 for change in recent_price_changes if change < 0)
        momentum_signal = "Strong Bullish" if momentum >= 3 else "Bullish" if momentum > 0 else "Bearish" if momentum < 0 else "Strong Bearish" if momentum <= -3 else "Neutral"
    else:
        momentum = 0
        momentum_signal = "Insufficient data"
        
    analysis["trend_analysis"] = {
        "direction": trend_direction,
        "strength": trend_strength,
        "momentum": momentum_signal,
        "signals": signals
    }
    
    # Add oscillator analysis
    oscillators = {}
    
    # Calculate additional oscillator values based on trading style
    if trading_style == "short_term":
        # For short-term, focus on faster oscillators and more recent data
        if len(df) >= 7 and 'rsi' in df.columns:
            oscillators["rsi_short_term"] = {
                "current": float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else 0,
                "previous": float(df['rsi'].iloc[-2]) if not pd.isna(df['rsi'].iloc[-2]) else 0,
                "change": float(df['rsi'].iloc[-1] - df['rsi'].iloc[-2]) if not pd.isna(df['rsi'].iloc[-1]) and not pd.isna(df['rsi'].iloc[-2]) else 0
            }
    elif trading_style == "long_term":
        # For long-term, include additional trend indicators
        if 'sma_200' in df.columns:
            long_term_trend = "Bullish" if df['c'].iloc[-1] > df['sma_200'].iloc[-1] else "Bearish"
            days_above_sma200 = sum(1 for i in range(-min(20, len(df)), 0) if df['c'].iloc[i] > df['sma_200'].iloc[i])
            analysis["trend_analysis"]["long_term_trend"] = {
                "direction": long_term_trend,
                "days_above_sma200": days_above_sma200,
                "sma_200_value": float(df['sma_200'].iloc[-1]) if not pd.isna(df['sma_200'].iloc[-1]) else 0
            }
    
    if 'rsi' in df.columns:
        oscillators["rsi"] = {
            "current": float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else 0,
            "signal": "Overbought" if df['rsi'].iloc[-1] > 70 else "Oversold" if df['rsi'].iloc[-1] < 30 else "Neutral"
        }
        
    if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
        oscillators["stochastic"] = {
            "k_line": float(df['stoch_k'].iloc[-1]) if not pd.isna(df['stoch_k'].iloc[-1]) else 0,
            "d_line": float(df['stoch_d'].iloc[-1]) if not pd.isna(df['stoch_d'].iloc[-1]) else 0,
            "signal": "Overbought" if df['stoch_k'].iloc[-1] > 80 and df['stoch_d'].iloc[-1] > 80 else 
                      "Oversold" if df['stoch_k'].iloc[-1] < 20 and df['stoch_d'].iloc[-1] < 20 else "Neutral"
        }
    
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        oscillators["macd"] = {
            "macd_line": float(df['macd'].iloc[-1]) if not pd.isna(df['macd'].iloc[-1]) else 0,
            "signal_line": float(df['macd_signal'].iloc[-1]) if not pd.isna(df['macd_signal'].iloc[-1]) else 0,
            "histogram": float(df['macd_hist'].iloc[-1]) if 'macd_hist' in df.columns and not pd.isna(df['macd_hist'].iloc[-1]) else 0,
            "signal": "Bullish" if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] else "Bearish"
        }