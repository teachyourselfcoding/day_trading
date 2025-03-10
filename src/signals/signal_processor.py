"""
Signal processor module for handling OpenAI responses.
"""
import json
from datetime import datetime
import openai

from src.utils.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OUTPUTS_DIR
from src.utils.file_utils import save_to_json
from src.utils.logger import signals_logger

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

def get_trading_signal(prompt, symbol):
    """
    Send prompt to OpenAI and get structured trading signal.
    
    Args:
        prompt (str): JSON prompt for OpenAI
        symbol (str): Symbol being analyzed
    
    Returns:
        dict: Trading signal response
    """
    try:
        signals_logger.info(f"Sending request to OpenAI for {symbol}")
        
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=OPENAI_TEMPERATURE
        )
        
        content = response.choices[0].message['content']
        signals_logger.info(f"Received response from OpenAI for {symbol}")
        
        # Try to parse the response as JSON
        try:
            signals_logger.debug("Attempting to parse OpenAI response as JSON")
            trading_signal = json.loads(content)
            
            # Add metadata
            if isinstance(trading_signal, dict):
                trading_signal['metadata'] = {
                    'symbol': symbol,
                    'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'model': OPENAI_MODEL,
                    'temperature': OPENAI_TEMPERATURE
                }
            
            signals_logger.info(f"Successfully parsed OpenAI response as JSON for {symbol}")
        except json.JSONDecodeError:
            signals_logger.warning(f"Could not parse response as JSON for {symbol}, attempting text extraction")
            
            # Try to extract structured information from the text response
            signal = {
                "raw_response": content,
                "error": "Could not parse as JSON",
                "metadata": {
                    'symbol': symbol,
                    'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'model': OPENAI_MODEL,
                    'temperature': OPENAI_TEMPERATURE
                }
            }
            
            # Look for pattern markers in the response
            if "pattern_identified" in content:
                signals_logger.debug("Found pattern markers in text response, attempting to extract")
                lines = content.split('\n')
                for line in lines:
                    if ":" in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        signal[key] = value
                signals_logger.info(f"Extracted {len(signal) - 3} fields from text response")  # -3 for the initial keys
            
            trading_signal = signal
        
        # Save the trading signal
        file_path = save_to_json(
            trading_signal, 
            OUTPUTS_DIR, 
            f"{symbol}_signal"
        )
        signals_logger.info(f"Saved trading signal to {file_path}")
        
        return trading_signal
            
    except Exception as e:
        signals_logger.error(f"Error getting trading signal for {symbol}: {e}")
        return None

def process_signals_batch(prompts_dict):
    """
    Process a batch of trading signal prompts.
    
    Args:
        prompts_dict (dict): Dictionary mapping symbols to their prompts
    
    Returns:
        dict: Dictionary mapping symbols to their trading signals
    """
    signals_logger.info(f"Processing batch of {len(prompts_dict)} trading signals")
    
    results = {}
    for symbol, prompt in prompts_dict.items():
        signal = get_trading_signal(prompt, symbol)
        if signal:
            results[symbol] = signal
    
    signals_logger.info(f"Successfully processed {len(results)} out of {len(prompts_dict)} signals")
    return results

def analyze_signal_quality(signal):
    """
    Analyze the quality of a trading signal.
    
    Args:
        signal (dict): Trading signal
    
    Returns:
        dict: Signal quality metrics
    """
    if not signal:
        return {"quality": "error", "score": 0, "reasons": ["Signal is empty or None"]}
    
    quality_score = 0
    reasons = []
    
    # Check for required fields
    required_fields = ["suggested_action", "pattern_identified", "stop_loss", "take_profit"]
    missing_fields = [field for field in required_fields if field not in signal]
    
    if missing_fields:
        reasons.append(f"Missing required fields: {', '.join(missing_fields)}")
    else:
        quality_score += 50  # Base score for having all required fields
    
    # Check action clarity
    action = signal.get("suggested_action", "").lower()
    if action in ["buy", "sell", "hold"]:
        quality_score += 10
    else:
        reasons.append(f"Unclear action: {action}")
    
    # Check confidence
    confidence = signal.get("pattern_confidence", "").lower()
    if confidence in ["high"]:
        quality_score += 20
    elif confidence in ["medium"]:
        quality_score += 10
    elif confidence in ["low"]:
        quality_score += 5
    else:
        reasons.append(f"Unclear confidence: {confidence}")
    
    # Check reasoning
    reasoning = signal.get("reasoning", "")
    if reasoning and len(reasoning) > 50:  # At least 50 chars
        quality_score += 20
    else:
        reasons.append("Insufficient reasoning")
    
    # Determine quality category
    if quality_score >= 80:
        quality = "high"
    elif quality_score >= 50:
        quality = "medium"
    else:
        quality = "low"
    
    signals_logger.info(f"Signal quality assessment: {quality} ({quality_score}/100)")
    if reasons:
        signals_logger.debug(f"Quality issues: {', '.join(reasons)}")
    
    return {
        "quality": quality,
        "score": quality_score,
        "reasons": reasons
    }

def filter_signals_by_quality(signals_dict, min_quality_score=50):
    """
    Filter signals by their quality score.
    
    Args:
        signals_dict (dict): Dictionary mapping symbols to their trading signals
        min_quality_score (int): Minimum quality score to include
    
    Returns:
        dict: Filtered dictionary of high-quality signals
    """
    signals_logger.info(f"Filtering {len(signals_dict)} signals by quality (min score: {min_quality_score})")
    
    filtered_signals = {}
    
    for symbol, signal in signals_dict.items():
        quality = analyze_signal_quality(signal)
        if quality["score"] >= min_quality_score:
            # Add quality assessment to the signal
            signal["quality_assessment"] = quality
            filtered_signals[symbol] = signal
    
    signals_logger.info(f"Filtered to {len(filtered_signals)} high-quality signals")
    return filtered_signals