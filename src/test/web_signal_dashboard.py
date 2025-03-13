#!/usr/bin/env python3
"""
Interactive web dashboard for verifying trading signals on price charts.
This script creates a Flask web application that allows users to:
1. Select different symbols to analyze
2. Toggle various technical indicators and signals
3. Zoom in on specific time periods
4. Export analysis results
"""
import os
import json
import glob
import pandas as pd
import numpy as np
import talib as ta
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory

# Create Flask app
app = Flask(__name__, 
            static_folder='templates/static',  # Point to your actual static folder
            template_folder='templates') 
app.config['SECRET_KEY'] = os.urandom(24)

# Configure directories
DATA_DIR = "data/raw"
ANALYSIS_DIR = "analysis_results"
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Create directories if they don't exist
for directory in [ANALYSIS_DIR, TEMPLATE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Create HTML templates directory and files
os.makedirs(os.path.join(TEMPLATE_DIR, "static", "css"), exist_ok=True)
os.makedirs(os.path.join(TEMPLATE_DIR, "static", "js"), exist_ok=True)

def find_available_symbols(data_dir=DATA_DIR):
    """Find all available symbols in the data directory."""
    all_files = glob.glob(os.path.join(data_dir, "*.json"))
    symbols = set()
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        if len(parts) >= 1:
            symbols.add(parts[0])
    
    return sorted(list(symbols))

def load_data_file(file_path):
    """Load a JSON data file and return the data."""
    with open(file_path, 'r') as f:
        return json.load(f)

@app.route('/load_data', methods=['POST'])
def load_data():
    try:
        # Get data from request
        data = request.get_json()
        ticker = data.get('ticker')
        
        if not ticker:
            return jsonify({'error': 'No ticker provided'}), 400
            
        print(f"Loading data for {ticker}")  # Debug log
        
        # Your data processing logic here
        # Example: fetch stock data from your data source
        # Replace this with your actual data retrieval code
        
        # For testing, return dummy data
        dummy_data = {
            'ticker': ticker,
            'datetime': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
            'price': {
                'open': [150.0, 152.5, 157.2, 160.8, 163.5],
                'high': [155.0, 158.0, 162.5, 165.0, 164.0],
                'low': [148.0, 151.0, 156.0, 159.5, 158.0],
                'close': [152.5, 157.2, 160.8, 163.5, 159.2],
                'volume': [1250000, 1320000, 1450000, 1550000, 1650000]
            },
            'indicators': {
                'sma_20': [151.2, 153.6, 158.3, 161.2, 160.1],
                'sma_50': [149.8, 151.5, 154.2, 157.8, 159.0],
                'sma_200': [145.3, 146.8, 148.2, 150.1, 151.5],
                'ema_12': [151.8, 154.2, 158.9, 162.1, 160.2],
                'ema_26': [150.1, 152.3, 155.6, 158.9, 159.0],
                'bb_upper': [160.2, 165.3, 168.7, 170.2, 167.8],
                'bb_middle': [151.2, 153.6, 158.3, 161.2, 160.1],
                'bb_lower': [142.2, 141.9, 147.9, 152.2, 152.4],
                'rsi': [65.2, 68.7, 72.3, 74.8, 45.6],
                'macd': [1.7, 1.9, 3.3, 3.2, 1.2],
                'macd_signal': [1.2, 1.4, 2.0, 2.3, 2.0],
                'macd_hist': [0.5, 0.5, 1.3, 0.9, -0.8],
                'stoch_k': [82.3, 85.7, 88.2, 90.1, 45.3],
                'stoch_d': [78.9, 82.3, 85.4, 88.0, 74.5],
                'adx': [22.5, 24.3, 26.8, 28.9, 27.5]
            },
            'patterns': {
                'bullish': [
                    {'date': '2023-01-02', 'pattern': 'Hammer'},
                    {'date': '2023-01-04', 'pattern': 'Morning Star'}
                ],
                'bearish': [
                    {'date': '2023-01-05', 'pattern': 'Shooting Star'}
                ]
            },
            'signals': {
                'rsi': [
                    {'date': '2023-01-03', 'signal': 'Overbought'},
                    {'date': '2023-01-04', 'signal': 'Overbought'},
                    {'date': '2023-01-05', 'signal': 'Oversold'}
                ],
                'macd': [
                    {'date': '2023-01-05', 'signal': 'Bearish Crossover'}
                ],
                'bollinger': [
                    {'date': '2023-01-03', 'signal': 'Upper Band Touch'},
                    {'date': '2023-01-05', 'signal': 'Lower Band Touch'}
                ],
                'crossovers': []
            }
        }
        
        return jsonify(dummy_data)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
def find_data_files(symbol, data_dir=DATA_DIR):
    """Find data files for a given symbol."""
    pattern = f"{symbol}_*.json"
    return glob.glob(os.path.join(data_dir, pattern))

def prepare_dataframe(data):
    """Convert data to DataFrame and prepare for analysis."""
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric and explicitly convert to float64
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['t'])
    
    return df

def calculate_indicators(df):
    """Calculate technical indicators using TA-Lib."""
    try:
        # Extract arrays for TA-Lib
        close = np.array(df['c'], dtype=np.float64)
        high = np.array(df['h'], dtype=np.float64)
        low = np.array(df['l'], dtype=np.float64)
        open_prices = np.array(df['o'], dtype=np.float64)
        volume = np.array(df['v'], dtype=np.float64)
        
        # Calculate SMA indicators
        df['sma_20'] = ta.SMA(close, timeperiod=20)
        df['sma_50'] = ta.SMA(close, timeperiod=50)
        df['sma_200'] = ta.SMA(close, timeperiod=200)
        
        # Calculate EMA indicators
        df['ema_12'] = ta.EMA(close, timeperiod=12)
        df['ema_26'] = ta.EMA(close, timeperiod=26)
        
        # Calculate MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = ta.MACD(
            close, fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Calculate RSI
        df['rsi'] = ta.RSI(close, timeperiod=14)
        
        # Calculate Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(
            close, timeperiod=20, nbdevup=2, nbdevdn=2
        )
        
        # Calculate Stochastic Oscillator
        df['stoch_k'], df['stoch_d'] = ta.STOCH(
            high, low, close, fastk_period=14, slowk_period=3, slowd_period=3
        )
        
        # Calculate ATR
        df['atr'] = ta.ATR(high, low, close, timeperiod=14)
        
        # Calculate ADX
        df['adx'] = ta.ADX(high, low, close, timeperiod=14)
        
        # On-Balance Volume
        df['obv'] = ta.OBV(close, volume)
        
    except Exception as e:
        print(f"Error calculating indicators: {e}")
    
    return df

def detect_candlestick_patterns(df):
    """Detect candlestick patterns using TA-Lib."""
    try:
        # Extract arrays for TA-Lib
        open_arr = np.array(df['o'], dtype=np.float64)
        high = np.array(df['h'], dtype=np.float64)
        low = np.array(df['l'], dtype=np.float64)
        close = np.array(df['c'], dtype=np.float64)
        
        # Dictionary to store pattern results
        
        # Bullish patterns
        df['bullish_engulfing'] = ta.CDLENGULFING(open_arr, high, low, close)
        df['hammer'] = ta.CDLHAMMER(open_arr, high, low, close)
        df['morning_star'] = ta.CDLMORNINGSTAR(open_arr, high, low, close)
        df['three_white_soldiers'] = ta.CDL3WHITESOLDIERS(open_arr, high, low, close)
        df['piercing'] = ta.CDLPIERCING(open_arr, high, low, close)
        df['doji_star'] = ta.CDLDOJISTAR(open_arr, high, low, close)
        
        # Bearish patterns
        df['bearish_engulfing'] = ta.CDLENGULFING(open_arr, high, low, close) * -1  # Reverse sign for bearish
        df['hanging_man'] = ta.CDLHANGINGMAN(open_arr, high, low, close)
        df['evening_star'] = ta.CDLEVENINGSTAR(open_arr, high, low, close)
        df['three_black_crows'] = ta.CDL3BLACKCROWS(open_arr, high, low, close)
        df['dark_cloud_cover'] = ta.CDLDARKCLOUDCOVER(open_arr, high, low, close)
        df['shooting_star'] = ta.CDLSHOOTINGSTAR(open_arr, high, low, close)
        
    except Exception as e:
        print(f"Error detecting candlestick patterns: {e}")
    
    return df

def detect_indicator_signals(df):
    """Detect technical indicator signals."""
    try:
        # Initialize columns for signals
        df['rsi_oversold'] = 0
        df['rsi_overbought'] = 0
        df['macd_bullish_cross'] = 0
        df['macd_bearish_cross'] = 0
        df['bb_lower_touch'] = 0
        df['bb_upper_touch'] = 0
        df['golden_cross'] = 0
        df['death_cross'] = 0
        df['stoch_oversold'] = 0
        df['stoch_overbought'] = 0
        
        # RSI signals (oversold < 30, overbought > 70)
        df.loc[df['rsi'] < 30, 'rsi_oversold'] = 100
        df.loc[df['rsi'] > 70, 'rsi_overbought'] = 100
        
        # MACD cross signals
        # Previous MACD below signal line, current MACD above signal line = bullish cross
        df['macd_bullish_cross'] = np.where(
            (df['macd'].shift(1) < df['macd_signal'].shift(1)) & 
            (df['macd'] > df['macd_signal']),
            100, 0
        )
        
        # Previous MACD above signal line, current MACD below signal line = bearish cross
        df['macd_bearish_cross'] = np.where(
            (df['macd'].shift(1) > df['macd_signal'].shift(1)) & 
            (df['macd'] < df['macd_signal']),
            100, 0
        )
        
        # Bollinger Band signals
        df['bb_lower_touch'] = np.where(df['l'] <= df['bb_lower'], 100, 0)
        df['bb_upper_touch'] = np.where(df['h'] >= df['bb_upper'], 100, 0)
        
        # Golden Cross (SMA 50 crosses above SMA 200)
        df['golden_cross'] = np.where(
            (df['sma_50'].shift(1) <= df['sma_200'].shift(1)) & 
            (df['sma_50'] > df['sma_200']),
            100, 0
        )
        
        # Death Cross (SMA 50 crosses below SMA 200)
        df['death_cross'] = np.where(
            (df['sma_50'].shift(1) >= df['sma_200'].shift(1)) & 
            (df['sma_50'] < df['sma_200']),
            100, 0
        )
        
        # Stochastic signals
        df['stoch_oversold'] = np.where(
            (df['stoch_k'] < 20) & (df['stoch_d'] < 20),
            100, 0
        )
        
        df['stoch_overbought'] = np.where(
            (df['stoch_k'] > 80) & (df['stoch_d'] > 80),
            100, 0
        )
    
    except Exception as e:
        print(f"Error detecting indicator signals: {e}")
    
    return df

def process_symbol_data(symbol):
    """Process a symbol's data and return analysis results."""
    # Find data files
    files = find_data_files(symbol)
    
    if not files:
        return None
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Load the newest file
    data = load_data_file(files[0])
    
    # Prepare data
    df = prepare_dataframe(data)
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Detect candlestick patterns
    df = detect_candlestick_patterns(df)
    
    # Detect indicator signals
    df = detect_indicator_signals(df)
    
    # Convert to suitable format for JSON
    chart_data = {
        'symbol': symbol,
        'datetime': df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'price': {
            'open': df['o'].tolist(),
            'high': df['h'].tolist(),
            'low': df['l'].tolist(),
            'close': df['c'].tolist(),
            'volume': df['v'].tolist()
        },
        'indicators': {
            'sma_20': df['sma_20'].tolist(),
            'sma_50': df['sma_50'].tolist(),
            'sma_200': df['sma_200'].tolist() if 'sma_200' in df.columns else [],
            'ema_12': df['ema_12'].tolist(),
            'ema_26': df['ema_26'].tolist(),
            'bb_upper': df['bb_upper'].tolist(),
            'bb_middle': df['bb_middle'].tolist(),
            'bb_lower': df['bb_lower'].tolist(),
            'rsi': df['rsi'].tolist(),
            'macd': df['macd'].tolist(),
            'macd_signal': df['macd_signal'].tolist(),
            'macd_hist': df['macd_hist'].tolist(),
            'stoch_k': df['stoch_k'].tolist(),
            'stoch_d': df['stoch_d'].tolist(),
            'adx': df['adx'].tolist(),
            'atr': df['atr'].tolist(),
        },
        'patterns': {
            'bullish': {
                'bullish_engulfing': df['bullish_engulfing'].tolist(),
                'hammer': df['hammer'].tolist(),
                'morning_star': df['morning_star'].tolist(),
                'three_white_soldiers': df['three_white_soldiers'].tolist(),
                'piercing': df['piercing'].tolist(),
                'doji_star': df['doji_star'].tolist()
            },
            'bearish': {
                'bearish_engulfing': df['bearish_engulfing'].tolist(),
                'hanging_man': df['hanging_man'].tolist(),
                'evening_star': df['evening_star'].tolist(),
                'three_black_crows': df['three_black_crows'].tolist(),
                'dark_cloud_cover': df['dark_cloud_cover'].tolist(),
                'shooting_star': df['shooting_star'].tolist()
            }
        },
        'signals': {
            'rsi_oversold': df['rsi_oversold'].tolist(),
            'rsi_overbought': df['rsi_overbought'].tolist(),
            'macd_bullish_cross': df['macd_bullish_cross'].tolist(),
            'macd_bearish_cross': df['macd_bearish_cross'].tolist(),
            'bb_lower_touch': df['bb_lower_touch'].tolist(),
            'bb_upper_touch': df['bb_upper_touch'].tolist(),
            'golden_cross': df['golden_cross'].tolist(),
            'death_cross': df['death_cross'].tolist(),
            'stoch_oversold': df['stoch_oversold'].tolist(),
            'stoch_overbought': df['stoch_overbought'].tolist()
        }
    }
    
    # Save results to file
    output_file = os.path.join(ANALYSIS_DIR, f"{symbol}_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(chart_data, f)
    
    return chart_data

# Create index.html template
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Signal Verification Dashboard</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
                <div class="position-sticky pt-3">
                    <h5 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-2 mb-2">
                        <span>Trading Signal Verification</span>
                    </h5>
                    
                    <div class="p-3">
                        <label for="symbolSelect" class="form-label">Symbol:</label>
                        <select id="symbolSelect" class="form-select mb-3">
                            {% for symbol in symbols %}
                            <option value="{{ symbol }}">{{ symbol }}</option>
                            {% endfor %}
                        </select>
                        
                        <button id="loadSymbolBtn" class="btn btn-primary mb-3 w-100">Load Data</button>
                    </div>
                    
                    <div class="accordion" id="settingsAccordion">
                        <!-- Price Settings -->
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="priceHeading">
                                <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#priceCollapse" aria-expanded="true" aria-controls="priceCollapse">
                                    Price Settings
                                </button>
                            </h2>
                            <div id="priceCollapse" class="accordion-collapse collapse show" aria-labelledby="priceHeading">
                                <div class="accordion-body">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showPriceChart" checked>
                                        <label class="form-check-label" for="showPriceChart">
                                            Show Price Chart
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showVolume" checked>
                                        <label class="form-check-label" for="showVolume">
                                            Show Volume
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Moving Averages -->
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="maHeading">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#maCollapse" aria-expanded="false" aria-controls="maCollapse">
                                    Moving Averages
                                </button>
                            </h2>
                            <div id="maCollapse" class="accordion-collapse collapse" aria-labelledby="maHeading">
                                <div class="accordion-body">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showSMA20">
                                        <label class="form-check-label" for="showSMA20">
                                            SMA 20
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showSMA50">
                                        <label class="form-check-label" for="showSMA50">
                                            SMA 50
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showSMA200">
                                        <label class="form-check-label" for="showSMA200">
                                            SMA 200
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showEMA12">
                                        <label class="form-check-label" for="showEMA12">
                                            EMA 12
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showEMA26">
                                        <label class="form-check-label" for="showEMA26">
                                            EMA 26
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Bollinger Bands -->
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="bbHeading">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#bbCollapse" aria-expanded="false" aria-controls="bbCollapse">
                                    Bollinger Bands
                                </button>
                            </h2>
                            <div id="bbCollapse" class="accordion-collapse collapse" aria-labelledby="bbHeading">
                                <div class="accordion-body">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showBBUpper">
                                        <label class="form-check-label" for="showBBUpper">
                                            Upper Band
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showBBMiddle">
                                        <label class="form-check-label" for="showBBMiddle">
                                            Middle Band
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showBBLower">
                                        <label class="form-check-label" for="showBBLower">
                                            Lower Band
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Indicators -->
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="indicatorsHeading">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#indicatorsCollapse" aria-expanded="false" aria-controls="indicatorsCollapse">
                                    Technical Indicators
                                </button>
                            </h2>
                            <div id="indicatorsCollapse" class="accordion-collapse collapse" aria-labelledby="indicatorsHeading">
                                <div class="accordion-body">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showRSI">
                                        <label class="form-check-label" for="showRSI">
                                            RSI
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showMACD">
                                        <label class="form-check-label" for="showMACD">
                                            MACD
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showStochastic">
                                        <label class="form-check-label" for="showStochastic">
                                            Stochastic
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showADX">
                                        <label class="form-check-label" for="showADX">
                                            ADX
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Patterns -->
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="patternsHeading">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#patternsCollapse" aria-expanded="false" aria-controls="patternsCollapse">
                                    Candlestick Patterns
                                </button>
                            </h2>
                            <div id="patternsCollapse" class="accordion-collapse collapse" aria-labelledby="patternsHeading">
                                <div class="accordion-body">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showBullishPatterns" checked>
                                        <label class="form-check-label" for="showBullishPatterns">
                                            Bullish Patterns
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showBearishPatterns" checked>
                                        <label class="form-check-label" for="showBearishPatterns">
                                            Bearish Patterns
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Signals -->
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="signalsHeading">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#signalsCollapse" aria-expanded="false" aria-controls="signalsCollapse">
                                    Technical Signals
                                </button>
                            </h2>
                            <div id="signalsCollapse" class="accordion-collapse collapse" aria-labelledby="signalsHeading">
                                <div class="accordion-body">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showRSISignals" checked>
                                        <label class="form-check-label" for="showRSISignals">
                                            RSI Overbought/Oversold
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showMACDSignals" checked>
                                        <label class="form-check-label" for="showMACDSignals">
                                            MACD Crossovers
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showBBSignals" checked>
                                        <label class="form-check-label" for="showBBSignals">
                                            Bollinger Band Touches
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="showCrossovers" checked>
                                        <label class="form-check-label" for="showCrossovers">
                                            Golden/Death Crosses
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main content -->
            <div class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">Signal Verification Dashboard</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        <div class="btn-group me-2">
                            <button id="zoomResetBtn" class="btn btn-sm btn-outline-secondary">Reset Zoom</button>
                            <button id="exportDataBtn" class="btn btn-sm btn-outline-secondary">Export Data</button>
                        </div>
                    </div>
                </div>
                
                <div id="loadingMessage" class="text-center mt-5" style="display: none;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading and analyzing data...</p>
                </div>
                
                <div id="chartContainer">
                    <div id="priceChart" style="height: 500px;"></div>
                    <div id="indicatorCharts">
                        <div id="rsiChart" style="height: 200px; display: none;"></div>
                        <div id="macdChart" style="height: 200px; display: none;"></div>
                        <div id="stochChart" style="height: 200px; display: none;"></div>
                        <div id="adxChart" style="height: 200px; display: none;"></div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title mb-0">Signal Summary</h5>
                            </div>
                            <div class="card-body">
                                <div id="signalSummary">
                                    <p>Load a symbol to view signal summary.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title mb-0">Pattern Summary</h5>
                            </div>
                            <div class="card-body">
                                <div id="patternSummary">
                                    <p>Load a symbol to view pattern summary.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JavaScript -->
    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>
"""


css_content = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    padding-top: 10px;
}

.sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 100;
    padding: 48px 0 0;
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
    overflow-y: auto;
}

.sidebar-sticky {
    position: relative;
    top: 0;
    height: calc(100vh - 48px);
    padding-top: 0.5rem;
    padding-bottom: 1rem;
    overflow-x: hidden;
    overflow-y: auto;
}

.sidebar .nav-link {
    font-weight: 500;
    color: #333;
}

.sidebar .nav-link:hover {
    color: #007bff;
}

.sidebar-heading {
    font-size: 0.85rem;
    text-transform: uppercase;
}

.accordion-button:not(.collapsed) {
    background-color: #e7f1ff;
    color: #0d6efd;
}

#chartContainer {
    width: 100%;
    overflow: hidden;
}

.signal-indicator {
    position: absolute;
    z-index: 10;
}

.bullish-marker {
    color: green;
    font-size: 20px;
}

.bearish-marker {
    color: red;
    font-size: 20px;
}

.tooltip-inner {
    max-width: 200px;
    padding: 8px;
    color: #fff;
    text-align: center;
    background-color: #000;
    border-radius: 4px;
}

.signal-summary-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eee;
}

.signal-count {
    font-weight: bold;
}

.bullish-count {
    color: green;
}

.bearish-count {
    color: red;
}

#rsiChart, #macdChart, #stochChart, #adxChart {
    margin-top: 15px;
    border-top: 1px solid #eee;
    padding-top: 15px;
}

.table-success, .table-danger {
    font-weight: bold;
}

.table-sm td, .table-sm th {
    padding: 0.25rem 0.5rem;
}
"""


dashboard_js = """
// dashboard.js - Interactive Signal Verification Dashboard

// Global variables
let chartData = null;
let priceChart = null;
let rsiChart = null;
let macdChart = null;
let stochChart = null;
let adxChart = null;
let currentSymbol = '';

// Initialize the dashboard when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard.js loaded successfully');
    
    // Get references to DOM elements
    const selectedStock = document.getElementById('symbolSelect').value;
    const loadDataBtn = document.getElementById('loadSymbolBtn');
    const dataContainer = document.getElementById('data-container');
    
    // Simple test to verify the button is working
    if (loadDataBtn) {
        console.log('Load data button found');
        
        // Add a direct onclick handler for testing
        loadDataBtn.onclick = function() {
            console.log('Button clicked via onclick');
        };
        
        // Add a more robust event listener
        loadDataBtn.addEventListener('click', function() {
            console.log('Button clicked via addEventListener');
            
            // Get the selected stock
            const selectedStock = document.getElementById('symbolSelect') ? document.getElementById('symbolSelect').value : '';
            console.log('Selected stock:', selectedStock);
            if (!selectedStock) {
                console.log('No stock selected');
                alert('Please select a stock first');
                return;
            }
            
            // Show loading indicator
            if (dataContainer) {
                dataContainer.innerHTML = '<p>Loading data...</p>';
            }
            
            // Make the AJAX request
            fetch(`/api/data/${currentSymbol}`)
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Data received:', data);
                displayData(data);
            })
            .catch(error => {
                console.error('Error:', error);
                if (dataContainer) {
                    dataContainer.innerHTML = '<p>Error loading data: ' + error.message + '</p>';
                }
            });
        });
    } else {
        console.error('Load data button not found');
    }
    
    // Function to display the data
    function displayData(data) {
        if (!dataContainer) return;
        
        try {
            // Create a heading for the data
            let html = '<h2>Data for ' + data.ticker + '</h2>';
            
            if (data.data && data.data.length > 0) {
                // Get the column names from the first data item
                const columns = Object.keys(data.data[0]);
                
                // Create a table
                html += '<table border="1"><tr>';
                
                // Add table headers
                columns.forEach(column => {
                    html += '<th>' + column + '</th>';
                });
                html += '</tr>';
                
                // Add table rows
                data.data.forEach(row => {
                    html += '<tr>';
                    columns.forEach(column => {
                        html += '<td>' + row[column] + '</td>';
                    });
                    html += '</tr>';
                });
                
                html += '</table>';
            } else {
                html += '<p>No data available for this stock</p>';
            }
            
            // Update the data container
            dataContainer.innerHTML = html;
        } catch (error) {
            console.error('Error displaying data:', error);
            dataContainer.innerHTML = '<p>Error displaying data: ' + error.message + '</p>';
        }
    }
});

// Setup checkbox event listeners
function setupCheckboxListeners() {
    // Price settings
    document.getElementById('showPriceChart').addEventListener('change', updateCharts);
    document.getElementById('showVolume').addEventListener('change', updateCharts);
    
    // Moving averages
    document.getElementById('showSMA20').addEventListener('change', updateCharts);
    document.getElementById('showSMA50').addEventListener('change', updateCharts);
    document.getElementById('showSMA200').addEventListener('change', updateCharts);
    document.getElementById('showEMA12').addEventListener('change', updateCharts);
    document.getElementById('showEMA26').addEventListener('change', updateCharts);
    
    // Bollinger Bands
    document.getElementById('showBBUpper').addEventListener('change', updateCharts);
    document.getElementById('showBBMiddle').addEventListener('change', updateCharts);
    document.getElementById('showBBLower').addEventListener('change', updateCharts);
    
    // Indicators
    document.getElementById('showRSI').addEventListener('change', function() {
        document.getElementById('rsiChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    document.getElementById('showMACD').addEventListener('change', function() {
        document.getElementById('macdChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    document.getElementById('showStochastic').addEventListener('change', function() {
        document.getElementById('stochChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    document.getElementById('showADX').addEventListener('change', function() {
        document.getElementById('adxChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    
    // Patterns and signals
    document.getElementById('showBullishPatterns').addEventListener('change', updateCharts);
    document.getElementById('showBearishPatterns').addEventListener('change', updateCharts);
    document.getElementById('showRSISignals').addEventListener('change', updateCharts);
    document.getElementById('showMACDSignals').addEventListener('change', updateCharts);
    document.getElementById('showBBSignals').addEventListener('change', updateCharts);
    document.getElementById('showCrossovers').addEventListener('change', updateCharts);
}

// Load data for the selected symbol
function loadSymbolData() {
    // Show loading message
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('chartContainer').style.opacity = '0.5';
    
    // Get the selected symbol
    const symbolSelect = document.getElementById('symbolSelect');
    currentSymbol = symbolSelect.value;
    
    // Fetch data from the server
    fetch(`/api/data/${currentSymbol}`)
        .then(response => response.json())
        .then(data => {
            // Hide loading message
            document.getElementById('loadingMessage').style.display = 'none';
            document.getElementById('chartContainer').style.opacity = '1';
            
            // Store the data globally
            chartData = data;
            
            // Create charts
            createCharts();
            
            // Update summary tables
            updateSummaries();
        })
        .catch(error => {
            console.error('Error loading data:', error);
            document.getElementById('loadingMessage').style.display = 'none';
            document.getElementById('chartContainer').style.opacity = '1';
            alert('Error loading data. See console for details.');
        });
}

// Create all charts
function createCharts() {
    if (!chartData) return;
    
    // Create the main price chart
    createPriceChart();
    
    // Create indicator charts
    createRSIChart();
    createMACDChart();
    createStochasticChart();
    createADXChart();
}

// Create the main price chart
function createPriceChart() {
    // Prepare the main candlestick trace
    const ohlc = {
        x: chartData.datetime,
        open: chartData.price.open,
        high: chartData.price.high,
        low: chartData.price.low,
        close: chartData.price.close,
        type: 'candlestick',
        name: currentSymbol,
        yaxis: 'y1'
    };
    
    // Prepare volume bars
    const volume = {
        x: chartData.datetime,
        y: chartData.price.volume,
        type: 'bar',
        name: 'Volume',
        marker: {
            color: 'rgba(100, 100, 100, 0.3)'
        },
        yaxis: 'y2',
        visible: document.getElementById('showVolume').checked
    };
    
    // Prepare moving averages
    const sma20 = {
        x: chartData.datetime,
        y: chartData.indicators.sma_20,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA 20',
        line: {
            color: 'blue',
            width: 1
        },
        visible: document.getElementById('showSMA20').checked
    };
    
    const sma50 = {
        x: chartData.datetime,
        y: chartData.indicators.sma_50,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA 50',
        line: {
            color: 'green',
            width: 1
        },
        visible: document.getElementById('showSMA50').checked
    };
    
    const sma200 = {
        x: chartData.datetime,
        y: chartData.indicators.sma_200,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA 200',
        line: {
            color: 'red',
            width: 1
        },
        visible: document.getElementById('showSMA200').checked
    };
    
    const ema12 = {
        x: chartData.datetime,
        y: chartData.indicators.ema_12,
        type: 'scatter',
        mode: 'lines',
        name: 'EMA 12',
        line: {
            color: 'purple',
            width: 1,
            dash: 'dash'
        },
        visible: document.getElementById('showEMA12').checked
    };
    
    const ema26 = {
        x: chartData.datetime,
        y: chartData.indicators.ema_26,
        type: 'scatter',
        mode: 'lines',
        name: 'EMA 26',
        line: {
            color: 'orange',
            width: 1,
            dash: 'dash'
        },
        visible: document.getElementById('showEMA26').checked
    };
    
    // Prepare Bollinger Bands
    const bbUpper = {
        x: chartData.datetime,
        y: chartData.indicators.bb_upper,
        type: 'scatter',
        mode: 'lines',
        name: 'BB Upper',
        line: {
            color: 'gray',
            width: 1
        },
        visible: document.getElementById('showBBUpper').checked
    };
    
    const bbMiddle = {
        x: chartData.datetime,
        y: chartData.indicators.bb_middle,
        type: 'scatter',
        mode: 'lines',
        name: 'BB Middle',
        line: {
            color: 'gray',
            width: 1,
            dash: 'dash'
        },
        visible: document.getElementById('showBBMiddle').checked
    };
    
    const bbLower = {
        x: chartData.datetime,
        y: chartData.indicators.bb_lower,
        type: 'scatter',
        mode: 'lines',
        name: 'BB Lower',
        line: {
            color: 'gray',
            width: 1
        },
        visible: document.getElementById('showBBLower').checked
    };
    
    // Prepare bullish pattern markers
    const bullishPatterns = {
        x: [],
        y: [],
        text: [],
        mode: 'markers+text',
        type: 'scatter',
        name: 'Bullish Patterns',
        marker: {
            symbol: 'triangle-up',
            size: 12,
            color: 'green'
        },
        textposition: 'bottom',
        visible: document.getElementById('showBullishPatterns').checked
    };
    
    // Prepare bearish pattern markers
    const bearishPatterns = {
        x: [],
        y: [],
        text: [],
        mode: 'markers+text',
        type: 'scatter',
        name: 'Bearish Patterns',
        marker: {
            symbol: 'triangle-down',
            size: 12,
            color: 'red'
        },
        textposition: 'top',
        visible: document.getElementById('showBearishPatterns').checked
    };
    
    // Add bullish pattern markers
    if (document.getElementById('showBullishPatterns').checked) {
        const bullishPatternTypes = ['bullish_engulfing', 'hammer', 'morning_star', 'three_white_soldiers', 'piercing', 'doji_star'];
        
        for (let i = 0; i < chartData.datetime.length; i++) {
            for (const pattern of bullishPatternTypes) {
                if (chartData.patterns.bullish[pattern][i] > 0) {
                    bullishPatterns.x.push(chartData.datetime[i]);
                    bullishPatterns.y.push(chartData.price.low[i] * 0.99);  // Slightly below the low
                    bullishPatterns.text.push(pattern.replace(/_/g, ' '));
                    break;  // Only add one marker per bar
                }
            }
        }
    }
    
    // Add bearish pattern markers
    if (document.getElementById('showBearishPatterns').checked) {
        const bearishPatternTypes = ['bearish_engulfing', 'hanging_man', 'evening_star', 'three_black_crows', 'dark_cloud_cover', 'shooting_star'];
        
        for (let i = 0; i < chartData.datetime.length; i++) {
            for (const pattern of bearishPatternTypes) {
                if (chartData.patterns.bearish[pattern][i] > 0) {
                    bearishPatterns.x.push(chartData.datetime[i]);
                    bearishPatterns.y.push(chartData.price.high[i] * 1.01);  // Slightly above the high
                    bearishPatterns.text.push(pattern.replace(/_/g, ' '));
                    break;  // Only add one marker per bar
                }
            }
        }
    }
    
    // Prepare signal markers
    const signalMarkers = {
        x: [],
        y: [],
        text: [],
        mode: 'markers',
        type: 'scatter',
        name: 'Technical Signals',
        marker: {
            size: 10,
            color: []
        },
        showlegend: false
    };
    
    // Add signal markers
    if (document.getElementById('showRSISignals').checked || 
        document.getElementById('showMACDSignals').checked || 
        document.getElementById('showBBSignals').checked || 
        document.getElementById('showCrossovers').checked) {
        
        for (let i = 0; i < chartData.datetime.length; i++) {
            // RSI signals
            if (document.getElementById('showRSISignals').checked) {
                if (chartData.signals.rsi_oversold[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.low[i] * 0.99);
                    signalMarkers.text.push('RSI Oversold');
                    signalMarkers.marker.color.push('blue');
                }
                
                if (chartData.signals.rsi_overbought[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.01);
                    signalMarkers.text.push('RSI Overbought');
                    signalMarkers.marker.color.push('orange');
                }
            }
            
            // MACD signals
            if (document.getElementById('showMACDSignals').checked) {
                if (chartData.signals.macd_bullish_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.low[i] * 0.98);
                    signalMarkers.text.push('MACD Bullish Cross');
                    signalMarkers.marker.color.push('lime');
                }
                
                if (chartData.signals.macd_bearish_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.02);
                    signalMarkers.text.push('MACD Bearish Cross');
                    signalMarkers.marker.color.push('red');
                }
            }
            
            // Bollinger Band signals
            if (document.getElementById('showBBSignals').checked) {
                if (chartData.signals.bb_lower_touch[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.low[i]);
                    signalMarkers.text.push('BB Lower Touch');
                    signalMarkers.marker.color.push('cyan');
                }
                
                if (chartData.signals.bb_upper_touch[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i]);
                    signalMarkers.text.push('BB Upper Touch');
                    signalMarkers.marker.color.push('magenta');
                }
            }
            
            // Crossover signals
            if (document.getElementById('showCrossovers').checked) {
                if (chartData.signals.golden_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.03);
                    signalMarkers.text.push('Golden Cross');
                    signalMarkers.marker.color.push('gold');
                }
                
                if (chartData.signals.death_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.03);
                    signalMarkers.text.push('Death Cross');
                    signalMarkers.marker.color.push('black');
                }
            }
        }
    }
    
    // Combine all traces
    const data = [
        ohlc,
        volume,
        sma20,
        sma50,
        sma200,
        ema12,
        ema26,
        bbUpper,
        bbMiddle,
        bbLower,
        bullishPatterns,
        bearishPatterns,
        signalMarkers
    ];
    
    // Define the layout
    const layout = {
        title: `${currentSymbol} Price Chart with Technical Indicators`,
        dragmode: 'zoom',
        showlegend: true,
        xaxis: {
            rangeslider: {
                visible: false
            },
            title: 'Date'
        },
        yaxis: {
            title: 'Price',
            domain: [0.2, 1],
            tickformat: '.2f'
        },
        yaxis2: {
            title: 'Volume',
            domain: [0, 0.15],
            tickformat: '.0f'
        },
        grid: {
            rows: 2,
            columns: 1,
            pattern: 'independent'
        },
        legend: {
            orientation: 'h',
            y: 1.1
        },
        annotations: [],
        hovermode: 'closest'
    };
    
    // Add Golden Cross and Death Cross annotations if enabled
    if (document.getElementById('showCrossovers').checked) {
        for (let i = 0; i < chartData.datetime.length; i++) {
            if (chartData.signals.golden_cross[i] > 0) {
                layout.annotations.push({
                    x: chartData.datetime[i],
                    y: chartData.price.high[i] * 1.05,
                    xref: 'x',
                    yref: 'y',
                    text: 'Golden Cross',
                    showarrow: true,
                    arrowhead: 2,
                    arrowsize: 1,
                    arrowwidth: 1,
                    arrowcolor: 'gold'
                });
            }
            
            if (chartData.signals.death_cross[i] > 0) {
                layout.annotations.push({
                    x: chartData.datetime[i],
                    y: chartData.price.high[i] * 1.05,
                    xref: 'x',
                    yref: 'y',
                    text: 'Death Cross',
                    showarrow: true,
                    arrowhead: 2,
                    arrowsize: 1,
                    arrowwidth: 1,
                    arrowcolor: 'black'
                });
            }
        }
    }
    
    // Create the chart
    Plotly.newPlot('priceChart', data, layout);
}

// Create the RSI chart
function createRSIChart() {
    if (!chartData || !document.getElementById('showRSI').checked) return;
    
    const trace = {
        x: chartData.datetime,
        y: chartData.indicators.rsi,
        type: 'scatter',
        mode: 'lines',
        name: 'RSI',
        line: {
            color: 'purple',
            width: 1
        }
    };
    
    const layout = {
        title: 'RSI (14)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'RSI',
            range: [0, 100]
        },
        shapes: [
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 70,
                y1: 70,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 30,
                y1: 30,
                line: {
                    color: 'green',
                    width: 1,
                    dash: 'dash'
                }
            }
        ],
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('rsiChart', [trace], layout);
}

// Create the MACD chart
function createMACDChart() {
    if (!chartData || !document.getElementById('showMACD').checked) return;
    
    const macdLine = {
        x: chartData.datetime,
        y: chartData.indicators.macd,
        type: 'scatter',
        mode: 'lines',
        name: 'MACD',
        line: {
            color: 'blue',
            width: 1
        }
    };
    
    const signalLine = {
        x: chartData.datetime,
        y: chartData.indicators.macd_signal,
        type: 'scatter',
        mode: 'lines',
        name: 'Signal',
        line: {
            color: 'red',
            width: 1
        }
    };
    
    // Create histogram bars
    const histColors = [];
    for (let i = 0; i < chartData.indicators.macd_hist.length; i++) {
        histColors.push(chartData.indicators.macd_hist[i] >= 0 ? 'green' : 'red');
    }
    
    const histogram = {
        x: chartData.datetime,
        y: chartData.indicators.macd_hist,
        type: 'bar',
        name: 'Histogram',
        marker: {
            color: histColors
        }
    };
    
    const layout = {
        title: 'MACD (12,26,9)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'MACD'
        },
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('macdChart', [macdLine, signalLine, histogram], layout);
}

// Create the Stochastic chart
function createStochasticChart() {
    if (!chartData || !document.getElementById('showStochastic').checked) return;
    
    const kLine = {
        x: chartData.datetime,
        y: chartData.indicators.stoch_k,
        type: 'scatter',
        mode: 'lines',
        name: '%K',
        line: {
            color: 'blue',
            width: 1
        }
    };
    
    const dLine = {
        x: chartData.datetime,
        y: chartData.indicators.stoch_d,
        type: 'scatter',
        mode: 'lines',
        name: '%D',
        line: {
            color: 'red',
            width: 1
        }
    };
    
    const layout = {
        title: 'Stochastic Oscillator (14,3,3)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'Stochastic',
            range: [0, 100]
        },
        shapes: [
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 80,
                y1: 80,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 20,
                y1: 20,
                line: {
                    color: 'green',
                    width: 1,
                    dash: 'dash'
                }
            }
        ],
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('stochChart', [kLine, dLine], layout);
}

// Create the ADX chart
function createADXChart() {
    if (!chartData || !document.getElementById('showADX').checked) return;
    
    const adxLine = {
        x: chartData.datetime,
        y: chartData.indicators.adx,
        type: 'scatter',
        mode: 'lines',
        name: 'ADX',
        line: {
            color: 'black',
            width: 1
        }
    };
    
    const layout = {
        title: 'ADX (14)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'ADX',
            range: [0, 100]
        },
        shapes: [
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 25,
                y1: 25,
                line: {
                    color: 'orange',
                    width: 1,
                    dash: 'dash'
                }
            }
        ],
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('adxChart', [adxLine], layout);
}

// Update all charts based on current settings
function updateCharts() {
    createCharts();
}

// Reset zoom on all charts
function resetZoom() {
    if (priceChart) {
        Plotly.relayout('priceChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (rsiChart) {
        Plotly.relayout('rsiChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (macdChart) {
        Plotly.relayout('macdChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (stochChart) {
        Plotly.relayout('stochChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (adxChart) {
        Plotly.relayout('adxChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
}

// Export data to CSV
function exportData() {
    if (!chartData) return;
    
    // Create CSV content
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add header row
    csvContent += "DateTime,Open,High,Low,Close,Volume,SMA20,SMA50,SMA200,EMA12,EMA26,BB_Upper,BB_Middle,BB_Lower,RSI,MACD,MACD_Signal,MACD_Hist,Stoch_K,Stoch_D,ADX";
    
    // Add data rows
    for (let i = 0; i < chartData.datetime.length; i++) {
        const row = [
            chartData.datetime[i],
            chartData.price.open[i],
            chartData.price.high[i],
            chartData.price.low[i],
            chartData.price.close[i],
            chartData.price.volume[i],
            chartData.indicators.sma_20[i] || "",
            chartData.indicators.sma_50[i] || "",
            chartData.indicators.sma_200[i] || "",
            chartData.indicators.ema_12[i] || "",
            chartData.indicators.ema_26[i] || "",
            chartData.indicators.bb_upper[i] || "",
            chartData.indicators.bb_middle[i] || "",
            chartData.indicators.bb_lower[i] || "",
            chartData.indicators.rsi[i] || "",
            chartData.indicators.macd[i] || "",
            chartData.indicators.macd_signal[i] || "",
            chartData.indicators.macd_hist[i] || "",
            chartData.indicators.stoch_k[i] || "",
            chartData.indicators.stoch_d[i] || "",
            chartData.indicators.adx[i] || ""
        ];
        
        csvContent += row.join(",");
    }
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${currentSymbol}_data.csv`);
    document.body.appendChild(link);
    
    // Trigger download and remove link
    link.click();
    document.body.removeChild(link);
}

// Update the summary tables
function updateSummaries() {
    if (!chartData) return;
    
    // Update signal summary
    updateSignalSummary();
    
    // Update pattern summary
    updatePatternSummary();
}

// Update signal summary table
function updateSignalSummary() {
    const signalSummaryElement = document.getElementById('signalSummary');
    
    // Count signals
    const signalCounts = {
        rsi_oversold: 0,
        rsi_overbought: 0,
        macd_bullish_cross: 0,
        macd_bearish_cross: 0,
        bb_lower_touch: 0,
        bb_upper_touch: 0,
        golden_cross: 0,
        death_cross: 0,
        stoch_oversold: 0,
        stoch_overbought: 0
    };
    
    for (const signalType in chartData.signals) {
        signalCounts[signalType] = chartData.signals[signalType].filter(val => val > 0).length;
    }
    
    // Create HTML content
    let html = '<table class="table table-sm">';
    html += '<thead><tr><th>Signal Type</th><th>Count</th></tr></thead>';
    html += '<tbody>';
    
    // Bullish signals
    html += '<tr class="table-success"><td colspan="2"><strong>Bullish Signals</strong></td></tr>';
    html += `<tr><td>RSI Oversold</td><td>${signalCounts.rsi_oversold}</td></tr>`;
    html += `<tr><td>MACD Bullish Cross</td><td>${signalCounts.macd_bullish_cross}</td></tr>`;
    html += `<tr><td>Bollinger Lower Touch</td><td>${signalCounts.bb_lower_touch}</td></tr>`;
    html += `<tr><td>Golden Cross</td><td>${signalCounts.golden_cross}</td></tr>`;
    html += `<tr><td>Stochastic Oversold</td><td>${signalCounts.stoch_oversold}</td></tr>`;
    
    // Bearish signals
    html += '<tr class="table-danger"><td colspan="2"><strong>Bearish Signals</strong></td></tr>';
    html += `<tr><td>RSI Overbought</td><td>${signalCounts.rsi_overbought}</td></tr>`;
    html += `<tr><td>MACD Bearish Cross</td><td>${signalCounts.macd_bearish_cross}</td></tr>`;
    html += `<tr><td>Bollinger Upper Touch</td><td>${signalCounts.bb_upper_touch}</td></tr>`;
    html += `<tr><td>Death Cross</td><td>${signalCounts.death_cross}</td></tr>`;
    html += `<tr><td>Stochastic Overbought</td><td>${signalCounts.stoch_overbought}</td></tr>`;
    
    html += '</tbody></table>';
    
    signalSummaryElement.innerHTML = html;
}

// Update pattern summary table
function updatePatternSummary() {
    const patternSummaryElement = document.getElementById('patternSummary');
    
    // Count patterns
    const patternCounts = {
        bullish: {},
        bearish: {}
    };
    
    // Bullish patterns
    for (const patternType in chartData.patterns.bullish) {
        patternCounts.bullish[patternType] = chartData.patterns.bullish[patternType].filter(val => val > 0).length;
    }
    
    // Bearish patterns
    for (const patternType in chartData.patterns.bearish) {
        patternCounts.bearish[patternType] = chartData.patterns.bearish[patternType].filter(val => val > 0).length;
    }
    
    // Create HTML content
    let html = '<table class="table table-sm">';
    html += '<thead><tr><th>Pattern Type</th><th>Count</th></tr></thead>';
    html += '<tbody>';
    
    // Bullish patterns
    html += '<tr class="table-success"><td colspan="2"><strong>Bullish Patterns</strong></td></tr>';
    for (const pattern in patternCounts.bullish) {
        const displayName = pattern.replace(/_/g, ' ');
        html += `<tr><td>${displayName}</td><td>${patternCounts.bullish[pattern]}</td></tr>`;
    }
    
    // Bearish patterns
    html += '<tr class="table-danger"><td colspan="2"><strong>Bearish Patterns</strong></td></tr>';
    for (const pattern in patternCounts.bearish) {
        const displayName = pattern.replace(/_/g, ' ');
        html += `<tr><td>${displayName}</td><td>${patternCounts.bearish[pattern]}</td></tr>`;
    }
    
    html += '</tbody></table>';
    
    patternSummaryElement.innerHTML = html;
}"""

# Add these Flask routes to the web_signal_dashboard.py file

# Serve the static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(os.path.join(TEMPLATE_DIR, 'static'), path)

# Home page route
@app.route('/')
def index():
    # Get list of available symbols
    symbols = find_available_symbols()
    return render_template_string(index_html, symbols=symbols)

# API endpoint for symbol data
@app.route('/api/data/<symbol>')
def get_symbol_data(symbol):
    # Check if analysis already exists
    analysis_file = os.path.join(ANALYSIS_DIR, f"{symbol}_analysis.json")
    
    if os.path.exists(analysis_file):
        # Load existing analysis
        with open(analysis_file, 'r') as f:
            return jsonify(json.load(f))
    
    # Process the data
    data = process_symbol_data(symbol)
    
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": f"No data found for symbol {symbol}"}), 404

# Create CSS and JS files
def create_templates():
    # Create CSS file
    css_dir = os.path.join(TEMPLATE_DIR, "static", "css")
    css_path = os.path.join(css_dir, "style.css")
    
    with open(css_path, 'w') as f:
        f.write(css_content)
    
    # Create JS file
    js_dir = os.path.join(TEMPLATE_DIR, "static", "js")
    js_path = os.path.join(js_dir, "dashboard.js")
    
    with open(js_path, 'w') as f:
        f.write(dashboard_js)
    
    print(f"Created template files at {TEMPLATE_DIR}")

# Main execution
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Technical Indicator Signal Verification Dashboard')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Create template files
    create_templates()
    
    print(f"Starting Signal Verification Dashboard at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)