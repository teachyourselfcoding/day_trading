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

# Define correct paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(CURRENT_DIR, 'templates')
STATIC_DIR = os.path.join(TEMPLATE_DIR, 'static')

# Create Flask app with the correct paths
app = Flask(__name__, 
            static_folder=STATIC_DIR,  
            template_folder=TEMPLATE_DIR)
app.config['SECRET_KEY'] = os.urandom(24)

# Configure directories
DATA_DIR = "data/raw"
ANALYSIS_DIR = "analysis_results"

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

# Directly serve static files
@app.route('/static/<path:path>')
def serve_static_files(path):
    return send_from_directory(STATIC_DIR, path)

@app.route('/api/data/')
def get_api_data_root():
    """Handle the root API data request."""
    symbols = find_available_symbols()
    return jsonify({
        'status': 'Please specify a symbol',
        'available_symbols': symbols
    })

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

@app.route('/api/data/<symbol>')
def get_symbol_data(symbol):
    """API endpoint for symbol data."""
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

@app.route('/')
def index():
    """Home page route."""
    # Load index.html content from file
    index_html_path = os.path.join(TEMPLATE_DIR, 'index.html')
    if os.path.exists(index_html_path):
        with open(index_html_path, 'r') as f:
            index_html_content = f.read()
    else:
        # Fallback to simple HTML if the file doesn't exist
        index_html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Signal Dashboard</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
        </head>
        <body>
            <h1>Trading Signal Dashboard</h1>
            <p>Please select a symbol to analyze:</p>
            <select id="symbolSelect">
                {% for symbol in symbols %}
                <option value="{{ symbol }}">{{ symbol }}</option>
                {% endfor %}
            </select>
            <button id="loadSymbolBtn">Load Data</button>
            <div id="chartContainer"></div>
            <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
        </body>
        </html>
        """
    
    # Get list of available symbols
    symbols = find_available_symbols()
    return render_template_string(index_html_content, symbols=symbols)

# Create CSS file if needed
def create_templates():
    # Create CSS file
    css_dir = os.path.join(TEMPLATE_DIR, "static", "css")
    css_path = os.path.join(css_dir, "style.css")
    
    # Only create CSS file if it doesn't exist
    if not os.path.exists(css_path):
        css_content_path = os.path.join(TEMPLATE_DIR, 'style.css')
        if os.path.exists(css_content_path):
            # Copy from style.css if it exists
            with open(css_content_path, 'r') as src, open(css_path, 'w') as dest:
                dest.write(src.read())
        else:
            # Create a basic CSS file
            with open(css_path, 'w') as f:
                f.write("""
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                }
                
                #chartContainer {
                    width: 100%;
                    height: 500px;
                    margin-top: 20px;
                }
                """)
    
    print(f"Templates directory: {TEMPLATE_DIR}")

# Main execution
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Technical Indicator Signal Verification Dashboard')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Create templates if needed
    create_templates()
    
    # Print debug information
    print(f"Current directory: {CURRENT_DIR}")
    print(f"Template directory: {TEMPLATE_DIR}")
    print(f"Static directory: {STATIC_DIR}")
    
    # Check if important files exist
    js_file = os.path.join(STATIC_DIR, 'js', 'dashboard.js')
    css_file = os.path.join(STATIC_DIR, 'css', 'style.css')
    
    print(f"JS file exists: {os.path.exists(js_file)}")
    print(f"CSS file exists: {os.path.exists(css_file)}")
    
    print(f"Starting Signal Verification Dashboard at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)