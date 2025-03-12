# Trading Signals Project

A modular Python application for generating trading signals using market data, technical analysis, and GPT-based pattern recognition.

## Overview

This project fetches market data from Yahoo Finance, performs technical analysis, and uses OpenAI's GPT models to generate trading signals. It can optionally execute trades through Alpaca's trading API.

## Project Structure

```
trading-signals-project/
│
├── .env                        # Environment variables (API keys)
│
├── .gitignore                  # Git ignore file (ignores .env)
│
├── data/                       # Data storage and fetching
│   ├── __init__.py
│   └── tradingview.py          # Wrapper around Yahoo Finance data fetcher
│
├── logs/                       # Logs directory
│
├── main.py                     # Enhanced main script with CLI arguments
│
├── prompts/                    # OpenAI prompts
│   ├── __init__.py
│   └── intraday_prompt.py      # Prompt generator for intraday analysis
│
├── requirements.txt            # Dependencies
│
├── schedule_runner.py          # Automated scheduling script
│
├── setup_dashboard.py          # Dashboard setup script
│
├── dashboard.py                # Web dashboard for visualizing signals
│
├── signals/                    # Trading signals
│   ├── __init__.py
│   └── llm_signals.py          # Updated OpenAI signal generator
│
├── src/                        # Source code
│   ├── __init__.py
│   │
│   ├── analysis/               # Technical analysis
│   │   ├── __init__.py
│   │   ├── patterns.py         # Candlestick pattern detection
│   │   └── technical.py        # Technical indicators calculation
│   │
│   ├── data/                   # Data processing
│   │   ├── __init__.py
│   │   ├── data_processor.py   # Data transformation utilities
│   │   └── yahoo_fetcher.py    # Yahoo Finance data fetcher
│   │
│   ├── execution/              # Trade execution (optional)
│   │   ├── __init__.py
│   │   └── alpaca_executor.py  # Alpaca trade execution
│   │
│   ├── signals/                # Signal processing
│   │   ├── __init__.py
│   │   ├── prompt_generator.py # Advanced prompt generation
│   │   └── signal_processor.py # Signal processing and filtering
│   │
│   ├── test/                   # Test scripts
│   │   ├── __init__.py
│   │   └── test_alpaca.py      # Alpaca API tests
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── config.py           # Configuration settings
│       ├── file_utils.py       # File operations
│       └── logger.py           # Logging setup
│
└── templates/                  # Dashboard HTML templates
    ├── base.html               # Base template with layout
    ├── chart.html              # Charts page
    ├── index.html              # Dashboard home page
    ├── scan.html               # Run new scans page
    └── symbol.html             # Symbol detail page
```

## Features

- **Data Acquisition**: Fetch market data from Yahoo Finance
- **Technical Analysis**: Calculate indicators (SMA, EMA, MACD, RSI, etc.)
- **Pattern Detection**: Identify candlestick patterns
- **AI-Powered Signals**: Generate trading signals using OpenAI's GPT models
- **Signal Filtering**: Filter signals based on quality metrics
- **Trade Execution**: Execute trades with Alpaca (optional)

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/trading-signals-project.git
   cd trading-signals-project
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ALPACA_API_KEY=your_alpaca_key_here
   ALPACA_SECRET_KEY=your_alpaca_secret_key_here
   ```

## Usage

### Basic Usage

Run the main script with default settings:

```bash
python main.py
```

This will:
1. Fetch data for the default symbols (AAPL, MSFT, AMZN, GOOGL, META)
2. Calculate technical indicators
3. Generate trading signals
4. Save the results to the appropriate directories

### Custom Options

Specify symbols and other options:

```bash
python main.py --symbols AAPL TSLA NVDA --interval 15Min --period 10d
```

### Execute Trades

To execute trades based on the signals (use with caution):

```bash
python main.py --execute
```

### Generate Portfolio Summary

To generate a summary across all signals:

```bash
python main.py --summary
```

## Modules

### Data Module

- `yahoo_fetcher.py`: Fetches data from Yahoo Finance
- `data_processor.py`: Processes and transforms market data

### Analysis Module

- `technical.py`: Calculates technical indicators
- `patterns.py`: Detects candlestick patterns and market structures

### Signals Module

- `prompt_generator.py`: Creates prompts for OpenAI
- `signal_processor.py`: Processes and filters trading signals

### Execution Module

- `alpaca_executor.py`: Executes trades with Alpaca

## Configuration

Edit `src/utils/config.py` to customize:

- Default symbols
- Time intervals
- Risk parameters
- Technical indicator settings

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not use it to make financial decisions. Trading involves risk, and you should always do your own research before making investment decisions.