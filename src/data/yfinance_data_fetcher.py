import os
from dotenv import load_dotenv
import json
import openai
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Get API key for OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up OpenAI client
openai.api_key = OPENAI_API_KEY

def fetch_yahoo_data(symbol, interval='5m', period='5d'):
    """
    Fetch data from Yahoo Finance.
    
    Parameters:
    symbol (str): Stock symbol (e.g., 'AAPL')
    interval (str): Time interval ('1m', '5m', '15m', '1h', '1d', etc.)
    period (str): How far back to get data ('1d', '5d', '1mo', '3mo', etc.)
    
    Returns:
    dict: Data in the format expected by the signal generator
    """
    try:
        print(f"Fetching {interval} data for {symbol} for the last {period}")
        
        # Yahoo Finance uses slightly different ticker format for some indices
        # Convert common index symbols if needed
        if symbol == '^GSPC':
            yahoo_symbol = '^GSPC'  # S&P 500
        elif symbol == '^DJI':
            yahoo_symbol = '^DJI'   # Dow Jones
        elif symbol == '^IXIC':
            yahoo_symbol = '^IXIC'  # NASDAQ
        else:
            yahoo_symbol = symbol
        
        # Fetch data from Yahoo Finance
        df = yf.download(
            tickers=yahoo_symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            prepost=False,
            threads=True
        )
        
        # Check if data was successfully retrieved
        if df.empty:
            print(f"Error: No data returned for {symbol}")
            return None
        
        # Reset index to make Date/Datetime a column
        df = df.reset_index()
        
        # Inspect the dataframe to understand its structure
        print(f"DataFrame columns: {df.columns.tolist()}")
        
        # Create a new DataFrame with the columns we need
        processed_df = pd.DataFrame()
        
        # Handle the date column - check which column contains datetime information
        if 'Datetime' in df.columns:
            processed_df['t'] = df['Datetime'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'Date' in df.columns:
            processed_df['t'] = df['Date'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif 'index' in df.columns and pd.api.types.is_datetime64_any_dtype(df['index']):
            processed_df['t'] = df['index'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Try the index itself as a last resort
            processed_df['t'] = df.index.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Add price and volume data
        processed_df['o'] = df['Open']
        processed_df['h'] = df['High']
        processed_df['l'] = df['Low']
        processed_df['c'] = df['Close']
        processed_df['v'] = df['Volume']
        
        print(f"Successfully retrieved {len(processed_df)} bars of data")
        
        # Convert to the format we used with Alpaca
        data = {
            'bars': processed_df.to_dict('records'),
            'symbol': symbol
        }
        
        # Save the data to a file
        file_name = f"{symbol}_yahoo_{interval}_data.json"
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved data to {file_name}")
        
        return data
    
    except Exception as e:
        print(f"Error fetching data from Yahoo Finance: {e}")
        # Print more diagnostic information
        import traceback
        traceback.print_exc()
        return None

def calculate_technical_indicators(data):
    """
    Calculate technical indicators for the data.
    
    Parameters:
    data (dict): Data dictionary with 'bars' key containing price data
    
    Returns:
    dict: Data with technical indicators added
    """
    if not data or 'bars' not in data or not data['bars']:
        return data
    
    # Convert to DataFrame for easier calculation
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Calculate SMA
    if len(df) >= 20:
        df['sma_20'] = df['c'].rolling(window=20).mean()
    
    if len(df) >= 50:
        df['sma_50'] = df['c'].rolling(window=50).mean()
    
    if len(df) >= 200:
        df['sma_200'] = df['c'].rolling(window=200).mean()
    
    # Calculate EMA
    if len(df) >= 12:
        df['ema_12'] = df['c'].ewm(span=12, adjust=False).mean()
    
    if len(df) >= 26:
        df['ema_26'] = df['c'].ewm(span=26, adjust=False).mean()
    
    # Calculate MACD
    if 'ema_12' in df.columns and 'ema_26' in df.columns:
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # Calculate RSI
    if len(df) >= 14:
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        # Avoid division by zero
        avg_loss = avg_loss.replace(0, 0.0001)
        
        rs = avg_gain / avg_loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Calculate Bollinger Bands
    if len(df) >= 20:
        df['bb_middle'] = df['c'].rolling(window=20).mean()
        df['bb_std'] = df['c'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
    
    # Calculate ATR (Average True Range)
    if len(df) >= 14:
        high_low = df['h'] - df['l']
        high_close = np.abs(df['h'] - df['c'].shift())
        low_close = np.abs(df['l'] - df['c'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr_14'] = true_range.rolling(14).mean()
    
    # Round all values to 2 decimal places
    for col in df.columns:
        if col != 't' and df[col].dtype != 'object':
            df[col] = df[col].round(2)
    
    # Handle NaN values
    df = df.fillna(0)
    
    # Convert back to dictionary
    data['bars'] = df.to_dict('records')
    
    return data

def detect_candlestick_patterns(recent_bars):
    """
    Simple detection of common candlestick patterns.
    
    Parameters:
    recent_bars (list): List of recent price bars
    
    Returns:
    dict: Detected patterns and their description
    """
    patterns = {}
    
    if len(recent_bars) < 3:
        return patterns
    
    # Doji (open and close are almost equal)
    latest = recent_bars[-1]
    if abs(latest['o'] - latest['c']) <= 0.1 * (latest['h'] - latest['l']):
        patterns["doji"] = "The latest candle is a doji, indicating indecision in the market."
    
    # Hammer (small body at the top, long lower wick)
    body_size = abs(latest['o'] - latest['c'])
    lower_wick = min(latest['o'], latest['c']) - latest['l']
    upper_wick = latest['h'] - max(latest['o'], latest['c'])
    
    if (body_size <= 0.3 * (latest['h'] - latest['l']) and 
        lower_wick >= 2 * body_size and 
        upper_wick <= 0.1 * (latest['h'] - latest['l'])):
        patterns["hammer"] = "The latest candle is a hammer, potentially signaling a bottom."
    
    # Engulfing pattern
    if len(recent_bars) >= 2:
        prev = recent_bars[-2]
        current = recent_bars[-1]
        
        # Bullish engulfing
        if (prev['c'] < prev['o'] and  # Previous candle is bearish (red)
            current['c'] > current['o'] and  # Current candle is bullish (green)
            current['o'] < prev['c'] and  # Current opens below previous close
            current['c'] > prev['o']):  # Current closes above previous open
            
            patterns["bullish_engulfing"] = "Detected a bullish engulfing pattern, suggesting potential trend reversal to the upside."
        
        # Bearish engulfing
        elif (prev['c'] > prev['o'] and  # Previous candle is bullish (green)
              current['c'] < current['o'] and  # Current candle is bearish (red)
              current['o'] > prev['c'] and  # Current opens above previous close
              current['c'] < prev['o']):  # Current closes below previous open
            
            patterns["bearish_engulfing"] = "Detected a bearish engulfing pattern, suggesting potential trend reversal to the downside."
    
    # Morning/Evening Star (requires 3 candles)
    if len(recent_bars) >= 3:
        first = recent_bars[-3]
        middle = recent_bars[-2]
        last = recent_bars[-1]
        
        first_body = abs(first['o'] - first['c'])
        middle_body = abs(middle['o'] - middle['c'])
        last_body = abs(last['o'] - last['c'])
        
        # Morning star (bullish reversal)
        if (first['c'] < first['o'] and  # First candle is bearish
            middle_body <= 0.3 * first_body and  # Middle candle is small
            last['c'] > last['o'] and  # Last candle is bullish
            middle['h'] < first['c'] and  # Gap down to middle
            last['o'] > middle['h']):  # Gap up from middle
            
            patterns["morning_star"] = "Detected a morning star pattern, a strong bullish reversal signal."
        
        # Evening star (bearish reversal)
        elif (first['c'] > first['o'] and  # First candle is bullish
              middle_body <= 0.3 * first_body and  # Middle candle is small
              last['c'] < last['o'] and  # Last candle is bearish
              middle['l'] > first['c'] and  # Gap up to middle
              last['o'] < middle['l']):  # Gap down from middle
            
            patterns["evening_star"] = "Detected an evening star pattern, a strong bearish reversal signal."
    
    return patterns

def prepare_llm_prompt(data, symbol, interval):
    """
    Prepare a prompt for OpenAI based on the intraday data.
    
    Parameters:
    data (dict): Data dictionary with 'bars' key containing price data with indicators
    symbol (str): Stock symbol
    interval (str): Time interval
    
    Returns:
    str: JSON prompt for OpenAI
    """
    if not data or 'bars' not in data or len(data['bars']) == 0:
        print("Error: No bars in data.")
        return None
    
    # Get the most recent bars for analysis
    # Use up to 100 bars for pattern recognition, but not more to avoid overwhelming the model
    recent_bars = data['bars'][-100:] if len(data['bars']) > 100 else data['bars']
    
    # Extract key data points
    latest = recent_bars[-1]
    first = recent_bars[0]
    high_of_period = max(bar['h'] for bar in recent_bars)
    low_of_period = min(bar['l'] for bar in recent_bars)
    
    # Calculate if we're in an uptrend, downtrend, or sideways
    if len(recent_bars) >= 10:
        price_10_bars_ago = recent_bars[-10]['c']
        price_change_pct = (latest['c'] - price_10_bars_ago) / price_10_bars_ago * 100
        
        if price_change_pct > 1.5:
            trend = "uptrend"
        elif price_change_pct < -1.5:
            trend = "downtrend"
        else:
            trend = "sideways"
    else:
        trend = "unknown"
    
    # Collect technical indicators if available
    indicators = {}
    
    indicator_fields = [
        'sma_20', 'sma_50', 'sma_200', 
        'ema_12', 'ema_26', 
        'macd', 'macd_signal', 'macd_hist',
        'rsi_14',
        'bb_upper', 'bb_middle', 'bb_lower',
        'atr_14'
    ]
    
    for field in indicator_fields:
        if field in latest:
            indicators[field] = latest[field]
    
    # Add candlestick pattern recognition
    patterns = detect_candlestick_patterns(recent_bars[-5:])
    
    # Prepare the prompt
    prompt = {
        "task": "Analyze price data and technical indicators to identify trading opportunities.",
        "symbol": symbol,
        "interval": interval,
        "data_source": "Yahoo Finance",
        "price_summary": {
            "start_time": first['t'],
            "end_time": latest['t'],
            "open": first['o'],
            "current_price": latest['c'],
            "high_of_period": high_of_period,
            "low_of_period": low_of_period,
            "price_change": round(latest['c'] - first['o'], 2),
            "price_change_percent": round((latest['c'] - first['o']) / first['o'] * 100, 2),
            "current_trend": trend,
            "volume": latest['v'],
            "data_points_analyzed": len(recent_bars)
        },
        "technical_indicators": indicators,
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
    
    return json.dumps(prompt)

def get_trading_signal(prompt):
    """
    Send prompt to OpenAI and get structured trading signal.
    
    Parameters:
    prompt (str): JSON prompt for OpenAI
    
    Returns:
    dict: Trading signal response
    """
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
            print("Warning: Could not parse response as JSON. Using raw content.")
            
            # Try to extract structured information from the text response
            signal = {
                "raw_response": content,
                "error": "Could not parse as JSON"
            }
            
            # Look for pattern markers in the response
            if "pattern_identified" in content:
                lines = content.split('\n')
                for line in lines:
                    if ":" in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        signal[key] = value
            
            return signal
            
    except Exception as e:
        print(f"Error getting trading signal: {e}")
        return None

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
    
    # Yahoo Finance interval mapping
    # Alpaca -> Yahoo Finance
    interval_mapping = {
        '1Min': '1m',
        '5Min': '5m',
        '15Min': '15m',
        '1H': '1h',
        '1D': '1d'
    }
    
    chosen_interval = '5Min'
    yahoo_interval = interval_mapping.get(chosen_interval, '5m')
    
    print("===== TRADING SIGNAL GENERATOR WITH YAHOO FINANCE =====")
    
    for symbol in symbols:
        print(f"\n===== Processing {symbol} =====")
        
        # Fetch data from Yahoo Finance
        data = fetch_yahoo_data(symbol, interval=yahoo_interval, period='5d')
        
        if not data or not data.get('bars'):
            print(f"No data available for {symbol}. Skipping.")
            continue
        
        # Calculate technical indicators
        data = calculate_technical_indicators(data)
        
        # Prepare LLM prompt
        prompt = prepare_llm_prompt(data, symbol, chosen_interval)
        
        if not prompt:
            print(f"Failed to prepare prompt for {symbol}. Skipping.")
            continue
        
        # Save the prompt for reference
        prompt_file = f"{symbol}_trading_prompt.json"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        print(f"Saved prompt to {prompt_file}")
        
        # Get trading signal
        trading_signal = get_trading_signal(prompt)
        
        if not trading_signal:
            print(f"Failed to get trading signal for {symbol}.")
            continue
        
        # Print the trading signal
        print(f"\n===== TRADING SIGNAL FOR {symbol} =====")
        print(json.dumps(trading_signal, indent=2))
        
        # Save the trading signal
        signal_file = f"{symbol}_trading_signal.json"
        with open(signal_file, 'w') as f:
            json.dump(trading_signal, f, indent=2)
        print(f"Saved trading signal to {signal_file}")