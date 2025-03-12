"""
Prompt generator module for OpenAI.
"""
import json
from datetime import datetime

from src.utils.config import PROMPTS_DIR
from src.utils.file_utils import save_to_json
from src.utils.logger import signals_logger
from src.analysis.patterns import detect_candlestick_patterns, analyze_trend, analyze_support_resistance

def prepare_analysis_prompt(data, symbol, interval):
    """
    Prepare a prompt for OpenAI based on the analyzed data.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data with indicators
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    if not data or 'bars' not in data or len(data['bars']) == 0:
        signals_logger.error("No bars in data for prompt generation")
        return None
    
    signals_logger.info(f"Preparing analysis prompt for {symbol}")
    
    # Get the most recent bars for analysis (limit to 100 for OpenAI context window)
    recent_bars = data['bars'][-100:] if len(data['bars']) > 100 else data['bars']
    
    # Extract key data points
    latest = recent_bars[-1]
    first = recent_bars[0]
    high_of_period = max(bar['h'] for bar in recent_bars)
    low_of_period = min(bar['l'] for bar in recent_bars)
    
    # Get candlestick patterns
    patterns = detect_candlestick_patterns(recent_bars)
    
    # Analyze trend
    trend_analysis = analyze_trend(recent_bars)
    
    # Analyze support and resistance
    levels = analyze_support_resistance(recent_bars)
    
    # Collect technical indicators if available
    indicators = {}
    
    indicator_fields = [
        'sma_20', 'sma_50', 'sma_200', 
        'ema_12', 'ema_26', 
        'macd', 'macd_signal', 'macd_hist',
        'rsi', 'atr',
        'bb_upper', 'bb_middle', 'bb_lower'
    ]
    
    for field in indicator_fields:
        if field in latest:
            indicators[field] = latest[field]
    
    # Prepare the prompt
    prompt = {
        "task": "Analyze price data and technical indicators to identify trading opportunities",
        "symbol": symbol,
        "interval": interval,
        "data_source": "Yahoo Finance",
        "analysis_timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "price_summary": {
            "start_time": first['t'],
            "end_time": latest['t'],
            "open_price": first['o'],
            "current_price": latest['c'],
            "high_of_period": high_of_period,
            "low_of_period": low_of_period,
            "price_change": round(latest['c'] - first['o'], 2),
            "price_change_percent": round((latest['c'] - first['o']) / first['o'] * 100, 2),
            "current_volume": latest['v'],
            "data_points_analyzed": len(recent_bars)
        },
        "technical_analysis": {
            "indicators": indicators,
            "trend": trend_analysis,
            "support_resistance": levels
        },
        "candlestick_patterns": patterns,
        "expected_response_format": {
            "pattern_identified": "<pattern_name>",
            "pattern_confidence": "<low/medium/high>",
            "suggested_action": "<buy/sell/hold>",
            "entry_price": "<suggested_entry>",
            "stop_loss": "<suggested_stop_loss>",
            "take_profit": "<suggested_take_profit>",
            "reasoning": "<brief_reasoning_for_decision>"
        }
    }
    
    # Save the prompt
    prompt_json = json.dumps(prompt, indent=2)
    file_path = save_to_json(
        prompt, 
        PROMPTS_DIR, 
        f"{symbol}_prompt"
    )
    signals_logger.info(f"Saved prompt to {file_path}")
    
    return prompt_json

def prepare_multi_symbol_summary_prompt(signals_dict):
    """
    Prepare a prompt that summarizes multiple signals for portfolio management.
    
    Args:
        signals_dict (dict): Dictionary mapping symbols to their trading signals
    
    Returns:
        str: JSON prompt for OpenAI
    """
    if not signals_dict:
        signals_logger.error("No signals provided for multi-symbol summary")
        return None
    
    symbols = list(signals_dict.keys())
    signals_logger.info(f"Preparing multi-symbol summary prompt for {len(symbols)} symbols")
    
    # Extract summary information for each symbol
    symbols_summary = []
    
    for symbol, signal in signals_dict.items():
        if isinstance(signal, dict):
            # Basic signal fields
            symbol_data = {
                "symbol": symbol,
                "suggested_action": signal.get("suggested_action", "unknown"),
                "pattern_identified": signal.get("pattern_identified", "unknown"),
                "pattern_confidence": signal.get("pattern_confidence", "unknown")
            }
            
            # Add price targets if available
            if "entry_price" in signal:
                symbol_data["entry_price"] = signal["entry_price"]
            
            if "stop_loss" in signal:
                symbol_data["stop_loss"] = signal["stop_loss"]
            
            if "take_profit" in signal:
                symbol_data["take_profit"] = signal["take_profit"]
            
            symbols_summary.append(symbol_data)
    
    # Prepare the prompt
    prompt = {
        "task": "Analyze multiple trading signals and provide portfolio allocation recommendations",
        "symbols_analyzed": symbols,
        "analysis_timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "signals_summary": symbols_summary,
        "expected_response_format": {
            "market_outlook": "<bullish/bearish/neutral>",
            "strongest_signals": ["<symbol1>", "<symbol2>"],
            "allocation_recommendations": {
                "<symbol1>": "<allocation_percentage>",
                "<symbol2>": "<allocation_percentage>"
            },
            "risk_assessment": "<low/medium/high>",
            "reasoning": "<brief_reasoning_for_allocation_decision>"
        }
    }
    
    # Save the prompt
    prompt_json = json.dumps(prompt, indent=2)
    file_path = save_to_json(
        prompt, 
        PROMPTS_DIR, 
        f"portfolio_summary_prompt"
    )
    signals_logger.info(f"Saved portfolio summary prompt to {file_path}")
    
    return prompt_json