import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta
import time

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Set up headers for Alpaca API
headers = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

def fetch_latest_bars(symbol, limit=15):
    """
    Fetch the latest bars for a symbol.
    Note: According to the error message, the 'latest' endpoint may not accept timeframe and limit
    as it did before. Let's try a different approach.
    """
    # Instead of using the 'latest' endpoint, we'll use the regular bars endpoint
    # with a short recent time window
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=30)  # Get data from the last 30 minutes
    
    # Format dates for API
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # For 1-minute bars
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    params = {
        'start': start_str,
        'end': end_str,
        'timeframe': '1Min'
    }
    
    try:
        print(f"\n===== Fetching recent bars for {symbol} =====")
        print(f"Time range: {start_str} to {end_str}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
        
        data = response.json()
        
        # Check if we got valid data
        if 'bars' in data and len(data['bars']) > 0:
            print(f"Success! Received {len(data['bars'])} recent bars.")
            
            # Print the first and last bars to verify data
            first_bar = data['bars'][0]
            last_bar = data['bars'][-1]
            
            print("\nFirst bar:")
            print(json.dumps(first_bar, indent=2))
            
            print("\nLast bar:")
            print(json.dumps(last_bar, indent=2))
            
            # Limit the number of bars to match the original request
            if len(data['bars']) > limit:
                data['bars'] = data['bars'][-limit:]
                print(f"Limited to the last {limit} bars")
            
            # Save the data to a file
            file_name = f"{symbol}_latest_data.json"
            with open(file_name, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nSaved latest data to {file_name}")
            
            return data
        else:
            print("Response did not contain expected 'bars' data:")
            print(json.dumps(data, indent=2))
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def fetch_daily_data(symbol, days=30):
    """
    Fetch daily data for a symbol.
    According to the error, 'day' might not be a valid timeframe.
    Let's try the correct timeframe format.
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for API request
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    params = {
        'timeframe': '1Day',  # Try '1Day' instead of 'day'
        'start': start_str,
        'end': end_str
    }
    
    try:
        print(f"\n===== Fetching daily data for {symbol} from {start_str} to {end_str} =====")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            
            # If '1Day' doesn't work, try 'D' as an alternative
            if '1Day' in params['timeframe']:
                print("Trying alternative timeframe format 'D'...")
                params['timeframe'] = 'D'
                response = requests.get(url, headers=headers, params=params)
                print(f"Status Code with 'D': {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error response with 'D': {response.text}")
                    return None
            else:
                return None
        
        data = response.json()
        
        if 'bars' in data and len(data['bars']) > 0:
            print(f"Success! Received {len(data['bars'])} daily bars.")
            
            # Print the first and last bars to verify data
            first_bar = data['bars'][0]
            last_bar = data['bars'][-1]
            
            print("\nFirst daily bar:")
            print(json.dumps(first_bar, indent=2))
            
            print("\nLast daily bar:")
            print(json.dumps(last_bar, indent=2))
            
            # Save the data to a file
            file_name = f"{symbol}_daily_data.json"
            with open(file_name, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nSaved daily data to {file_name}")
            
            return data
        else:
            print("Response did not contain expected 'bars' data:")
            print(json.dumps(data, indent=2))
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_available_timeframes():
    """
    Test various timeframes to see which ones are supported by the API.
    This will help us understand what options are available.
    """
    timeframes = ['1Min', '5Min', '15Min', '1H', '1D', 'D', 'day', '1Day', 'Day']
    symbol = 'AAPL'  # Use a common stock for testing
    
    print("\n===== Testing available timeframes =====")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Format dates for API request
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    
    results = {}
    
    for timeframe in timeframes:
        params = {
            'timeframe': timeframe,
            'start': start_str,
            'end': end_str
        }
        
        try:
            print(f"\nTesting timeframe: {timeframe}")
            response = requests.get(url, headers=headers, params=params)
            status = response.status_code
            
            results[timeframe] = {
                'status': status,
                'response': response.text[:100] + '...' if len(response.text) > 100 else response.text
            }
            
            print(f"Status: {status}")
            if status != 200:
                print(f"Error: {response.text}")
            else:
                data = response.json()
                if 'bars' in data:
                    print(f"Success! Returned {len(data['bars'])} bars")
                else:
                    print("No bars in response")
        except Exception as e:
            results[timeframe] = {
                'status': 'Error',
                'response': str(e)
            }
            print(f"Error: {e}")
    
    print("\n===== Timeframe Test Results =====")
    for timeframe, result in results.items():
        print(f"{timeframe}: {result['status']}")
    
    # Save results for reference
    with open('timeframe_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def test_account():
    """
    Test API keys and check account information
    """
    url = "https://paper-api.alpaca.markets/v2/account"
    
    try:
        print("\n===== Testing Alpaca Account =====")
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            account_info = response.json()
            print(f"Account ID: {account_info.get('id')}")
            print(f"Account Status: {account_info.get('status')}")
            print(f"Currency: {account_info.get('currency')}")
            print(f"Buying Power: {account_info.get('buying_power')}")
            print(f"Portfolio Value: {account_info.get('portfolio_value')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def build_hybrid_dataset(symbol, intraday_data, daily_data, target_interval='5Min'):
    """
    Build a hybrid dataset combining real latest data with simulated historical data.
    We'll use the same logic as before, but make sure we're using the data correctly.
    """
    if not intraday_data or not daily_data or 'bars' not in intraday_data or 'bars' not in daily_data:
        print("Missing required data for building hybrid dataset")
        return None
    
    # Extract the real latest bars
    real_bars = intraday_data['bars']
    
    # Get the timestamp of the earliest real bar to avoid overlap
    if real_bars:
        earliest_real_time = datetime.fromisoformat(real_bars[0]['t'].replace('Z', '+00:00'))
    else:
        earliest_real_time = datetime.now()
    
    # Select a few recent days from daily data for simulation
    daily_bars = daily_data['bars'][-5:]  # Last 5 days
    
    # Create simulated historical intraday bars
    simulated_bars = []
    
    for day_bar in daily_bars:
        # Extract base values for this day
        base_open = day_bar['o']
        base_close = day_bar['c']
        base_high = day_bar['h']
        base_low = day_bar['l']
        date_str = day_bar['t'].split('T')[0]
        
        # Parse the date
        bar_date = datetime.fromisoformat(day_bar['t'].replace('Z', '+00:00'))
        
        # Skip simulation if this day is today (we have real data)
        if bar_date.date() == datetime.now().date():
            continue
        
        # Determine number of bars based on interval
        if target_interval == '5Min':
            num_bars = 78  # ~6.5 hours / 5 minutes
            minutes_per_bar = 5
        elif target_interval == '15Min':
            num_bars = 26  # ~6.5 hours / 15 minutes
            minutes_per_bar = 15
        else:
            num_bars = 13   # Default to 30-minute bars
            minutes_per_bar = 30
        
        # Generate simulated bars for this day
        for i in range(num_bars):
            progress = i / (num_bars - 1)  # 0 to 1
            
            # Calculate time
            market_open_hour = 9
            market_open_minute = 30
            minutes_from_open = i * minutes_per_bar
            
            hours_from_open = minutes_from_open // 60
            mins_from_open = minutes_from_open % 60
            
            bar_hour = market_open_hour + hours_from_open
            bar_minute = market_open_minute + mins_from_open
            
            # Adjust if minutes overflow
            if bar_minute >= 60:
                bar_hour += 1
                bar_minute -= 60
            
            # Create timestamp
            timestamp = f"{date_str}T{bar_hour:02d}:{bar_minute:02d}:00Z"
            
            # Convert to datetime for comparison
            bar_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Skip if this bar would overlap with real data
            if bar_time >= earliest_real_time:
                continue
            
            # Price simulation logic - create realistic OHLC pattern
            if base_close > base_open:  # Uptrend day
                # In uptrends, often goes up, pulls back, then continues up
                if progress < 0.3:
                    mid_price = base_open + (base_high - base_open) * (progress / 0.3) * 0.8
                elif progress < 0.7:
                    mid_price = base_high * 0.9 - (base_high * 0.9 - base_low * 1.1) * ((progress - 0.3) / 0.4)
                else:
                    mid_price = base_low * 1.1 + (base_close - base_low * 1.1) * ((progress - 0.7) / 0.3)
            else:  # Downtrend day
                # In downtrends, often drops, bounces, then continues down
                if progress < 0.3:
                    mid_price = base_open - (base_open - base_low) * (progress / 0.3) * 0.8
                elif progress < 0.7:
                    mid_price = base_low * 1.1 + (base_high * 0.9 - base_low * 1.1) * ((progress - 0.3) / 0.4)
                else:
                    mid_price = base_high * 0.9 - (base_high * 0.9 - base_close) * ((progress - 0.7) / 0.3)
            
            # Create price spread for OHLC
            price_spread = (base_high - base_low) * 0.1
            
            # Previous bar's close (if available)
            if i > 0 and simulated_bars:
                prev_close = simulated_bars[-1]['c']
            else:
                prev_close = base_open
            
            # Generate OHLC with some randomness but maintain consistency
            if i == 0:  # First bar of the day
                curr_open = base_open
            else:
                # Small gap from previous close
                curr_open = prev_close * (1 + (mid_price/prev_close - 1) * 0.3)
            
            # Calculate high, low, close
            if mid_price > curr_open:
                curr_high = mid_price + price_spread * 0.5
                curr_low = min(curr_open, mid_price) - price_spread * 0.3
                curr_close = mid_price + (mid_price - curr_open) * 0.2
            else:
                curr_high = max(curr_open, mid_price) + price_spread * 0.3
                curr_low = mid_price - price_spread * 0.5
                curr_close = mid_price - (curr_open - mid_price) * 0.2
            
            # Ensure the relationship between OHLC makes sense
            curr_high = max(curr_high, curr_open, curr_close)
            curr_low = min(curr_low, curr_open, curr_close)
            
            # Volume profile - typically higher at open and close
            if progress < 0.2:
                volume_factor = 1.5  # Higher volume at open
            elif progress > 0.8:
                volume_factor = 1.3  # Higher volume at close
            else:
                volume_factor = 0.8  # Lower volume mid-day
            
            volume = int(day_bar['v'] / num_bars * volume_factor)
            
            # Create the simulated bar
            bar = {
                't': timestamp,
                'o': round(curr_open, 2),
                'h': round(curr_high, 2),
                'l': round(curr_low, 2),
                'c': round(curr_close, 2),
                'v': volume
            }
            
            simulated_bars.append(bar)
    
    # Combine simulated historical bars with real latest bars
    all_bars = simulated_bars + real_bars
    
    # Sort by timestamp to ensure chronological order
    all_bars.sort(key=lambda x: x['t'])
    
    # Create the hybrid dataset
    hybrid_data = {
        'bars': all_bars,
        'symbol': symbol,
        'next_page_token': None
    }
    
    # Save the hybrid dataset
    file_name = f"{symbol}_hybrid_{target_interval}_data.json"
    with open(file_name, 'w') as f:
        json.dump(hybrid_data, f, indent=2)
    print(f"\nCreated and saved hybrid dataset to {file_name}")
    print(f"Dataset contains {len(simulated_bars)} simulated bars and {len(real_bars)} real bars")
    print(f"Total of {len(all_bars)} bars in the dataset")
    
    return hybrid_data

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT", "AMZN"]
    target_interval = '5Min'
    
    print("===== ALPACA API TEST SCRIPT =====")
    print("This script helps diagnose and fix Alpaca API issues")
    
    choice = input("\nOptions:\n1. Test account access\n2. Check available timeframes\n3. Test fetching latest data\n4. Test fetching daily data\n5. Build hybrid dataset\nChoose option (1-5): ")
    
    if choice == '1':
        # Test account
        test_account()
    
    elif choice == '2':
        # Test timeframes
        get_available_timeframes()
    
    elif choice == '3':
        # Test fetching latest data
        for symbol in symbols:
            fetch_latest_bars(symbol)
    
    elif choice == '4':
        # Test fetching daily data
        for symbol in symbols:
            fetch_daily_data(symbol)
    
    elif choice == '5':
        # Build hybrid dataset
        for symbol in symbols:
            # First fetch the latest data
            latest_data = fetch_latest_bars(symbol)
            
            # Then fetch daily data
            daily_data = fetch_daily_data(symbol)
            
            if latest_data and daily_data:
                # Build and save hybrid dataset
                hybrid_data = build_hybrid_dataset(symbol, latest_data, daily_data, target_interval)
                
                if hybrid_data:
                    print(f"\nSuccessfully created hybrid dataset for {symbol}")
    
    else:
        print("Invalid choice. Exiting.")