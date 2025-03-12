#!/usr/bin/env python3
"""
Trading Signals Dashboard

A web-based dashboard for monitoring and visualizing trading signals.
"""
import os
import json
import glob
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project utilities
from src.utils.config import OUTPUTS_DIR, DEFAULT_SYMBOLS
from src.utils.file_utils import create_directories

# Create app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Ensure directories exist
create_directories()

def load_signals(days_back=7, symbol=None):
    """
    Load trading signals from the outputs directory.
    
    Args:
        days_back (int): Number of days to look back
        symbol (str): Filter by symbol (optional)
    
    Returns:
        list: List of signal dictionaries
    """
    # Get all signal files
    pattern = f"{symbol}_*_signal.json" if symbol else "*_signal.json"
    signal_files = glob.glob(os.path.join(OUTPUTS_DIR, pattern))
    
    # Sort by modification time (newest first)
    signal_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Calculate cutoff date
    cutoff = datetime.now() - timedelta(days=days_back)
    cutoff_timestamp = cutoff.timestamp()
    
    signals = []
    for file_path in signal_files:
        # Check if the file is within our date range
        if os.path.getmtime(file_path) >= cutoff_timestamp:
            try:
                with open(file_path, 'r') as f:
                    signal = json.load(f)
                
                # Extract symbol from filename
                filename = os.path.basename(file_path)
                parts = filename.split('_')
                if len(parts) >= 1:
                    signal['symbol'] = parts[0]
                
                # Format date from filename or use file modification time
                if len(parts) >= 2:
                    try:
                        date_str = parts[1]
                        signal['date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    except:
                        # Use file modification time if parsing fails
                        signal['date'] = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d')
                else:
                    signal['date'] = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d')
                
                signals.append(signal)
            except Exception as e:
                print(f"Error loading signal file {file_path}: {e}")
    
    return signals

def get_signals_summary(signals):
    """
    Generate a summary of trading signals.
    
    Args:
        signals (list): List of signal dictionaries
    
    Returns:
        dict: Summary statistics
    """
    summary = {
        'total_signals': len(signals),
        'buy_signals': 0,
        'sell_signals': 0,
        'hold_signals': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'by_symbol': {},
        'recent_signals': []
    }
    
    for signal in signals:
        # Count by action
        action = signal.get('suggested_action', '').lower()
        if action == 'buy':
            summary['buy_signals'] += 1
        elif action == 'sell':
            summary['sell_signals'] += 1
        elif action == 'hold':
            summary['hold_signals'] += 1
        
        # Count by confidence
        confidence = signal.get('pattern_confidence', '').lower()
        if confidence == 'high':
            summary['high_confidence'] += 1
        elif confidence == 'medium':
            summary['medium_confidence'] += 1
        elif confidence == 'low':
            summary['low_confidence'] += 1
        
        # Count by symbol
        symbol = signal.get('symbol', 'unknown')
        if symbol not in summary['by_symbol']:
            summary['by_symbol'][symbol] = {
                'total': 0,
                'buy': 0,
                'sell': 0,
                'hold': 0
            }
        
        summary['by_symbol'][symbol]['total'] += 1
        if action == 'buy':
            summary['by_symbol'][symbol]['buy'] += 1
        elif action == 'sell':
            summary['by_symbol'][symbol]['sell'] += 1
        elif action == 'hold':
            summary['by_symbol'][symbol]['hold'] += 1
    
    # Get the most recent signals
    recent = sorted(signals, key=lambda x: x.get('date', ''), reverse=True)[:5]
    summary['recent_signals'] = recent
    
    return summary

@app.route('/')
def index():
    """Dashboard home page."""
    days = request.args.get('days', default=7, type=int)
    symbol = request.args.get('symbol', default=None)
    
    signals = load_signals(days_back=days, symbol=symbol)
    summary = get_signals_summary(signals)
    
    return render_template(
        'index.html',
        summary=summary,
        signals=signals,
        days=days,
        symbols=DEFAULT_SYMBOLS,
        selected_symbol=symbol
    )

@app.route('/signals')
def get_signals():
    """API endpoint to get signals as JSON."""
    days = request.args.get('days', default=7, type=int)
    symbol = request.args.get('symbol', default=None)
    
    signals = load_signals(days_back=days, symbol=symbol)
    return jsonify(signals)

@app.route('/signals/<symbol>')
def get_symbol_signals(symbol):
    """Page to view signals for a specific symbol."""
    days = request.args.get('days', default=7, type=int)
    
    signals = load_signals(days_back=days, symbol=symbol)
    summary = get_signals_summary(signals)
    
    return render_template(
        'symbol.html',
        summary=summary,
        signals=signals,
        days=days,
        symbol=symbol,
        symbols=DEFAULT_SYMBOLS
    )

@app.route('/chart')
def chart():
    """Page with interactive charts."""
    days = request.args.get('days', default=30, type=int)
    
    signals = load_signals(days_back=days)
    
    # Prepare data for charts
    df = pd.DataFrame(signals)
    
    # Create a date index if possible
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Daily signal counts
        daily_counts = df.groupby([df['date'].dt.date, 'suggested_action']).size().unstack().fillna(0)
        
        # Convert to chart data format
        chart_data = {
            'dates': [d.strftime('%Y-%m-%d') for d in daily_counts.index],
            'buy': daily_counts['buy'].tolist() if 'buy' in daily_counts.columns else [],
            'sell': daily_counts['sell'].tolist() if 'sell' in daily_counts.columns else [],
            'hold': daily_counts['hold'].tolist() if 'hold' in daily_counts.columns else []
        }
    else:
        chart_data = {'dates': [], 'buy': [], 'sell': [], 'hold': []}
    
    return render_template(
        'chart.html',
        chart_data=json.dumps(chart_data),
        days=days
    )

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    """Run a scan for new signals."""
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        interval = request.form.get('interval', '15m')
        
        # Import and run the signal generator
        try:
            from main import process_symbol
            
            result = process_symbol(symbol, interval)
            if result:
                return redirect(url_for('get_symbol_signals', symbol=symbol))
            else:
                return render_template('scan.html', error=f"Failed to generate signal for {symbol}", symbols=DEFAULT_SYMBOLS)
        except Exception as e:
            return render_template('scan.html', error=f"Error running scan: {e}", symbols=DEFAULT_SYMBOLS)
    
    return render_template('scan.html', symbols=DEFAULT_SYMBOLS)

@app.template_filter('format_date')
def format_date(value):
    """Format date for display."""
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.strftime('%b %d, %Y')
        except:
            return value
    return value

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Trading Signals Dashboard')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting Trading Signals Dashboard on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)