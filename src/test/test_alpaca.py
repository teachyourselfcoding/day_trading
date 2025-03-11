import os
from dotenv import load_dotenv
import requests
import json
import openai
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up headers for Alpaca API
headers = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

# Set up OpenAI client
openai.api_key = OPENAI_API_KEY

def fetch_daily_data(symbol, days=30):
    """
    Fetch daily data for a symbol using Alpaca's free market data.
    
    Parameters:
    symbol (str): Stock symbol (e.g., 'AAPL')
    days (int): Number of days to look back
    
    Returns:
    dict: JSON response with bars data
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for API request
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    params = {
        'timeframe': 'day',
        'start': start_str,
        'end': end_str,
        'limit': 50
    }
    
    try:
        print(f"Fetching daily data for {symbol} from {start_str} to {end_str}")
        response = requests.get(url, headers=headers, params=params)
        
        # Handle errors
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        
        if 'bars' in data and len(data['bars']) > 0:
            print(f"Successfully retrieved {len(data['bars'])} daily bars for {symbol}")
            return data
        else:
            print(f"No data returned for {symbol}")
            return None
            
    except Exception as e:
        print(f"Exception fetching data: {e}")
        return None

def simulate_intraday_from_daily(daily_data, interval='5Min'):
    """
    Simulate intraday data from daily data.
    
    Parameters:
    daily_data (dict): Daily data from Alpaca
    interval (str): Simulated interval (e.g., '5Min', '15Min')
    
    Returns:
    dict: Simulated intraday data
    """
    if not daily_data or 'bars' not in daily_data or len(daily_data['bars']) == 0:
        return None
    
    # Get symbol from daily data
    symbol = daily_data.get('symbol', 'UNKNOWN')
    
    # Take the last few days for simulation
    days_to_use = min(5, len(daily_data['bars']))
    daily_bars = daily_data['bars'][-days_to_use:]
    
    # Create simulated intraday bars
    intraday_bars = []
    
    for day_bar in daily_bars:
        # Extract base values for this day
        base_open = day_bar['o']
        base_close = day_bar['c']
        base_high = day_bar['h']
        base_low = day_bar['l']
        date_str = day_bar['t'].split('T')[0]
        
        # Decide how many bars to create based on interval
        if interval == '5Min':
            num_bars = 78  # ~6.5 hours / 5 minutes
        elif interval == '15Min':
            num_bars = 26  # ~6.5 hours / 15 minutes
        else:
            num_bars = 8   # Default to hourly-like
        
        # Create a price path that roughly follows open->high->low->close pattern
        # This is a simple simulation and not realistic market behavior
        for i in range(num_bars):
            progress = i / (num_bars - 1)  # 0 to 1
            
            # Simple price calculation - not realistic but good enough for testing
            if base_close > base_open:  # Uptrend day
                # In uptrends, often goes up, pulls back, then continues up
                if progress < 0.3:
                    curr_price = base_open + (base_high - base_open) * (progress / 0.3)
                elif progress < 0.7:
                    curr_price = base_high - (base_high - base_low) * ((progress - 0.3) / 0.4)
                else:
                    curr_price = base_low + (base_close - base_low) * ((progress - 0.7) / 0.3)
            else:  # Downtrend day
                # In downtrends, often drops, bounces, then continues down
                if progress < 0.3:
                    curr_price = base_open - (base_open - base_low) * (progress / 0.3)
                elif progress < 0.7:
                    curr_price = base_low + (base_high - base_low) * ((progress - 0.3) / 0.4)
                else:
                    curr_price = base_high - (base_high - base_close) * ((progress - 0.7) / 0.3)
            
            # Calculate time
            minutes = 0
            if interval == '5Min':
                minutes = i * 5
            elif interval == '15Min':
                minutes = i * 15
            else:
                minutes = i * 30
                
            hours = 9 + (minutes // 60)
            mins = minutes % 60
            timestamp = f"{date_str}T{hours:02d}:{mins:02d}:00Z"
            
            # Create a simulated bar with some random variation
            # For simplicity, we'll make the open/high/low/close all based on the calculated price
            variation = (base_high - base_low) * 0.05  # Small random variation
            
            # For testing purposes, generate reasonable OHLC values
            if i > 0:
                prev_close = intraday_bars[-1]['c']
                curr_open = prev_close + (curr_price - prev_close) * 0.2  # Small gap from previous
            else:
                curr_open = base_open
                
            curr_high = max(curr_price, curr_open) + variation * 0.5
            curr_low = min(curr_price, curr_open) - variation * 0.5
            curr_close = curr_price
            
            # Calculate volume - higher at open and close
            volume_factor = 1.5 if (progress < 0.2 or progress > 0.8) else 0.8
            volume = int(day_bar['v'] / num_bars * volume_factor)
            
            bar = {
                't': timestamp,
                'o': round(curr_open, 2),
                'h': round(curr_high, 2),
                'l': round(curr_low, 2),
                'c': round(curr_close, 2),
                'v': volume
            }
            
            intraday_bars.append(bar)
    
    # Create the final data structure
    simulated_data = {
        'bars': intraday_bars,
        'symbol': symbol,
        'next_page_token': None
    }
    
    return simulated_data

def fetch_intraday_data(symbol, interval='5Min'):
    """
    Attempt to fetch intraday data, falling back to simulated data from daily bars.
    
    Parameters:
    symbol (str): Stock symbol (e.g., 'AAPL')
    interval (str): Time interval (e.g., '5Min', '15Min')
    
    Returns:
    dict: JSON response with bars data (real or simulated)
    """
    # Try to load from a pre-generated simulation file first (for testing)
    sim_file = f"{symbol}_simulated_{interval}_data.json"
    if os.path.exists(sim_file):
        print(f"Loading pre-generated simulation from {sim_file}")
        with open(sim_file, 'r') as f:
            return json.load(f)
    
    # First, try to fetch real intraday data
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    params = {
        'timeframe': interval,
        'limit': 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # Check if we got valid intraday data
        if response.status_code == 200 and 'bars' in data and len(data['bars']) > 0:
            print(f"Successfully fetched real intraday data for {symbol}")
            return data
        
        # If we got an error about market data subscription
        print(f"Could not fetch real intraday data. Status: {response.status_code}")
        print("Falling back to simulated intraday data based on daily bars...")
        
        # Fetch daily data and simulate intraday
        daily_data = fetch_daily_data(symbol)
        if daily_data:
            simulated_data = simulate_intraday_from_daily(daily_data, interval)
            if simulated_data:
                print(f"Successfully created simulated intraday data for {symbol}")
                
                # Save the simulation for later use
                with open(sim_file, 'w') as f:
                    json.dump(simulated_data, f, indent=2)
                print(f"Saved simulation to {sim_file}")
                
                return simulated_data
    
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"Failed to fetch or simulate data for {symbol}")
    return None

def prepare_llm_prompt(data, symbol, interval):
    """Prepare a prompt for OpenAI based on the intraday data"""
    if not data or 'bars' not in data or len(data['bars']) == 0:
        print("Error: No bars in data.")
        return None
        
    latest = data['bars'][-1]
    high_of_day = max(candle['h'] for candle in data['bars'])
    low_of_day = min(candle['l'] for candle in data['bars'])
    
    prompt = {
        "task": "Analyze intraday price data and identify chart patterns.",
        "symbol": symbol,
        "interval": interval,
        "intraday_summary": {
            "open": data['bars'][0]['o'],
            "current_price": latest['c'],
            "high_of_day": high_of_day,
            "low_of_day": low_of_day,
            "recent_pattern": f"Current price is {latest['c']} with intraday high at {high_of_day} and low at {low_of_day}.",
            "data_source": "This data is simulated from daily bars for testing purposes."
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

def get_trading_signal(prompt):
    """Send prompt to OpenAI and get structured trading signal"""
    try:
        print("Sending request to OpenAI...")
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        content = response.choices[0].message['content']
        print("Received response from OpenAI")
        
        # Try to parse the response as JSON
        try:
            trading_signal = json.loads(content)
            return trading_signal
        except json.JSONDecodeError:
            print("Warning: Could not parse response as JSON:")
            print(content[:200] + "..." if len(content) > 200 else content)
            return {"error": "Could not parse response", "raw_content": content}
            
    except Exception as e:
        print(f"Error getting trading signal: {e}")
        return None

# Example Usage
if __name__ == '__main__':
    symbol = 'AAPL'
    interval = '5Min'
    
    print(f"===== TESTING FULL TRADING SIGNAL PIPELINE FOR {symbol} =====\n")
    
    # Step 1: Fetch intraday data (real or simulated)
    data = fetch_intraday_data(symbol, interval)
    if not data:
        print("Failed to fetch intraday data. Exiting.")
        exit(1)
    
    # Step 2: Prepare LLM prompt
    prompt = prepare_llm_prompt(data, symbol, interval)
    if not prompt:
        print("Failed to prepare prompt. Exiting.")
        exit(1)
    
    # Save the prompt for reference
    with open(f"{symbol}_prompt.json", "w") as f:
        f.write(prompt)
    print(f"Saved prompt to {symbol}_prompt.json")
    
    # Step 3: Get trading signal
    trading_signal = get_trading_signal(prompt)
    if not trading_signal:
        print("Failed to get trading signal. Exiting.")
        exit(1)
    
    # Step 4: Print the trading signal
    print("\n===== TRADING SIGNAL =====")
    print(json.dumps(trading_signal, indent=2))
    
    # Save the trading signal for reference
    with open(f"{symbol}_trading_signal.json", "w") as f:
        json.dump(trading_signal, f, indent=2)
    print(f"Saved trading signal to {symbol}_trading_signal.json")
    
    print("\n===== TEST COMPLETE =====")