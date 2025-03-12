from dotenv import load_dotenv
import os
from src.data.tradingview import fetch_intraday_data
from prompts.intraday_prompt import prepare_llm_prompt
from signals.llm_signals import get_trading_signal

load_dotenv()

symbol = 'AAPL'
interval = '5m'

data = fetch_intraday_data(symbol, interval)
prompt = prepare_llm_prompt(data, symbol, interval)
trading_signal = get_trading_signal(prompt)

print("Structured LLM Trading Signal:")
print(trading_signal)
