import os
from dotenv import load_dotenv
import requests

load_dotenv()

ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

headers = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

# Step 1: Fetch intraday data from Alpaca
def fetch_intraday_data(symbol, interval='5Min'):
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars?timeframe={interval}&limit=100"
    headers = {
        'APCA-API-KEY-ID': ALPACA_API_KEY,
        'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
    }
    response = requests.get(url, headers=headers)
    return response.json()

# Step 2: Prepare LLM prompt
def prepare_llm_prompt(data, symbol, interval):
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

# Step 3: Send prompt to OpenAI and get structured trading signal
def get_trading_signal(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message['content']
    return json.loads(content)

# Example Usage
if __name__ == '__main__':
    symbol = 'AAPL'
    interval = '5Min'

    data = fetch_intraday_data(symbol, interval)
    prompt = prepare_llm_prompt(data, symbol, interval)
    trading_signal = get_trading_signal(prompt)

    print("LLM Trading Signal:")
    print(json.dumps(trading_signal, indent=2))
