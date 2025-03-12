"""
Intraday analysis prompt generator for OpenAI.
"""
import json
from src.utils.logger import signals_logger

def prepare_llm_prompt(data, symbol, interval):
    """
    Prepare a prompt for OpenAI based on the intraday data.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    if not data or 'bars' not in data or len(data['bars']) == 0:
        signals_logger.error("No bars in data for prompt generation")
        return None
        
    signals_logger.info(f"Preparing intraday prompt for {symbol}")
    
    # Extract key data points
    latest = data['bars'][-1]
    first = data['bars'][0]
    high_of_day = max(candle['h'] for candle in data['bars'])
    low_of_day = min(candle['l'] for candle in data['bars'])
    
    # Prepare the prompt
    prompt = {
        "task": "Analyze intraday price data and identify chart patterns.",
        "symbol": symbol,
        "interval": interval,
        "intraday_summary": {
            "open": first['o'],
            "current_price": latest['c'],
            "high_of_day": high_of_day,
            "low_of_day": low_of_day,
            "recent_pattern": f"Current price is {latest['c']} with intraday high at {high_of_day} and low at {low_of_day}."
        },
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
    
    return json.dumps(prompt)