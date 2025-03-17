"""
GPT-based trading signal generation module.
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from src.utils.logger import signals_logger
from src.utils.config import OUTPUTS_DIR
from src.utils.file_utils import save_to_json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_trading_signal(prompt):
    """
    Send prompt to OpenAI and get structured trading signal.
    
    Args:
        prompt (str): JSON prompt for OpenAI
    
    Returns:
        dict: Trading signal response or None if error
    """
    try:
        signals_logger.info("Sending request to OpenAI")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        content = response.choices[0].message.content
        signals_logger.info("Received response from OpenAI")
        
        # Try to parse the response as JSON
        try:
            signals_logger.debug("Attempting to parse OpenAI response as JSON")
            trading_signal = json.loads(content)
            
            # Add metadata
            if isinstance(trading_signal, dict):
                symbol = json.loads(prompt).get('symbol', 'unknown')
                trading_signal['metadata'] = {
                    'symbol': symbol,
                    'model': "gpt-4",
                    'temperature': 0
                }
            
            # Save the trading signal
            try:
                file_path = save_to_json(
                    trading_signal, 
                    OUTPUTS_DIR, 
                    f"{trading_signal['metadata']['symbol']}_signal"
                )
                signals_logger.info(f"Saved trading signal to {file_path}")
            except Exception as e:
                signals_logger.error(f"Error saving trading signal: {e}")
            
            return trading_signal
                
        except json.JSONDecodeError:
            signals_logger.warning("Could not parse response as JSON, attempting text extraction")
            
            # Try to extract structured information from the text response
            signal = {
                "raw_response": content,
                "error": "Could not parse as JSON"
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
                signals_logger.info(f"Extracted {len(signal) - 2} fields from text response")
            
            return signal
            
    except Exception as e:
        signals_logger.error(f"Error getting trading signal: {e}")
        return None

# Example Usage
if __name__ == '__main__':
    # This is just an example of how to use this module
    from src.data.tradingview import fetch_intraday_data
    from prompts.intraday_prompt import prepare_llm_prompt
    
    symbol = 'AAPL'
    interval = '5m'
    
    data = fetch_intraday_data(symbol, interval)
    prompt = prepare_llm_prompt(data, symbol, interval)
    trading_signal = get_trading_signal(prompt)
    
    print("LLM Trading Signal:")
    print(json.dumps(trading_signal, indent=2))