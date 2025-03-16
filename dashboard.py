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

@app.route('/signal/<symbol>/<signal_id>')
def view_signal_detail(symbol, signal_id):
    """
    View detailed information about a specific trading signal with interactive chart.
    
    Args:
        symbol (str): The stock symbol
        signal_id (str): The signal ID or timestamp
    """
    try:
        # Find the signal file based on the ID
        signal_file = None
        if os.path.exists(os.path.join(OUTPUTS_DIR, f"{symbol}_{signal_id}_signal.json")):
            signal_file = os.path.join(OUTPUTS_DIR, f"{symbol}_{signal_id}_signal.json")
        else:
            # Search for files matching the pattern
            pattern = os.path.join(OUTPUTS_DIR, f"{symbol}_*{signal_id}*.json")
            matching_files = glob.glob(pattern)
            if matching_files:
                signal_file = matching_files[0]
        
        if not signal_file or not os.path.exists(signal_file):
            flash(f"Signal not found for {symbol}", "danger")
            return redirect(url_for('get_symbol_signals', symbol=symbol))
        
        # Load the signal
        with open(signal_file, 'r') as f:
            signal = json.load(f)
        
        # Get chart data for this symbol
        chart_data = prepare_chart_data(symbol)
        
        # Extract technical analysis data from the signal if available
        technical_data = None
        if 'technical_analysis' in signal:
            technical_data = signal['technical_analysis']
        
        # Prepare data for signal markers
        if chart_data and 'datetime' in chart_data:
            # If the chart data doesn't already have signals, add them
            if 'signals' not in chart_data:
                chart_data['signals'] = {
                    'buySellPoints': []
                }
            
            # Try to match the signal to a specific timestamp
            signal_time = None
            if 'metadata' in signal and 'generated_at' in signal['metadata']:
                signal_time = signal['metadata']['generated_at']
            elif 'date' in signal:
                signal_time = signal['date']
            
            # If we found a time, add the signal marker
            if signal_time:
                # Find the closest timestamp in the chart data
                # This is a simplification - in reality you'd want a more sophisticated matching
                closest_time = chart_data['datetime'][-1]  # Default to last timestamp
                
                chart_data['signals']['buySellPoints'].append({
                    'time': closest_time,
                    'action': signal['suggested_action'],
                    'price': signal['entry_price'] if 'entry_price' in signal else chart_data['price']['close'][-1]
                })
        
        # Render the signal detail template
        return render_template(
            'signal_detail.html',
            symbol=symbol,
            signal=signal,
            chart_data=chart_data,
            technical_data=technical_data,
            interval=signal.get('metadata', {}).get('interval', '15m')
        )
    except Exception as e:
        app.logger.error(f"Error viewing signal detail: {e}")
        flash(f"Error viewing signal detail: {str(e)}", "danger")
        return redirect(url_for('get_symbol_signals', symbol=symbol))

def prepare_chart_data(symbol, days_back=7):
    """
    Prepare chart data for a symbol.
    
    Args:
        symbol (str): The stock symbol
        days_back (int): Number of days of data to include
    
    Returns:
        dict: Chart data formatted for Plotly
    """
    try:
        # Find the latest processed data file for this symbol
        pattern = os.path.join(PROCESSED_DATA_DIR, f"{symbol}_*_processed*.json")
        files = glob.glob(pattern)
        
        if not files:
            # If no processed data, try raw data
            pattern = os.path.join(RAW_DATA_DIR, f"{symbol}_*.json")
            files = glob.glob(pattern)
        
        if not files:
            return None
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Load the most recent file
        with open(files[0], 'r') as f:
            data = json.load(f)
        
        if not data or 'bars' not in data or not data['bars']:
            return None
        
        # Calculate cutoff date
        cutoff = datetime.now() - timedelta(days=days_back)
        
        # Convert to DataFrame for easier filtering
        df = pd.DataFrame(data['bars'])
        
        # Convert timestamp to datetime for filtering
        df['datetime'] = pd.to_datetime(df['t'])
        
        # Filter by date
        recent_df = df[df['datetime'] >= cutoff]
        
        if recent_df.empty:
            # If filtering results in empty dataframe, use all data
            recent_df = df
        
        # Convert back to format suitable for Plotly
        chart_data = {
            'datetime': recent_df['t'].tolist(),
            'price': {
                'open': recent_df['o'].tolist(),
                'high': recent_df['h'].tolist(),
                'low': recent_df['l'].tolist(),
                'close': recent_df['c'].tolist(),
                'volume': recent_df['v'].tolist() if 'v' in recent_df.columns else []
            },
            'indicators': {}
        }
        
        # Add technical indicators if available
        indicator_columns = [col for col in recent_df.columns if col.startswith(('sma_', 'ema_', 'bb_', 'rsi', 'macd', 'stoch_'))]
        for col in indicator_columns:
            chart_data['indicators'][col] = recent_df[col].tolist()
        
        return chart_data
        
    except Exception as e:
        app.logger.error(f"Error preparing chart data: {e}")
        return None

@app.route('/generate/<trading_style>')
def generate_styled_signal(trading_style):
    """
    Generate a trading signal with a specific trading style.
    
    Args:
        trading_style (str): 'short_term', 'medium_term', or 'long_term'
    """
    symbol = request.args.get('symbol')
    interval = request.args.get('interval', '15m')
    period = request.args.get('period', '5d')
    
    if not symbol:
        flash("Please provide a symbol", "danger")
        return redirect(url_for('scan'))
    
    try:
        # Import the appropriate prompt generator based on trading style
        if trading_style == 'short_term':
            from prompts.intraday_prompt import prepare_short_term_prompt as prepare_prompt
        elif trading_style == 'long_term':
            from prompts.intraday_prompt import prepare_long_term_prompt as prepare_prompt
        else:
            # Default to medium term
            from prompts.intraday_prompt import prepare_medium_term_prompt as prepare_prompt
        
        # Import other required functions
        from data.tradingview import fetch_intraday_data
        from signals.llm_signals import get_trading_signal
        from src.analysis.technical import calculate_technical_indicators, get_timeframe_adjusted_settings
        
        # Get timeframe-adjusted settings
        indicator_settings = get_timeframe_adjusted_settings(interval)
        
        # Fetch and process data
        data = fetch_intraday_data(symbol, interval, period)
        if not data:
            flash(f"Failed to fetch data for {symbol}", "danger")
            return redirect(url_for('scan'))
        
        # Calculate technical indicators
        data = calculate_technical_indicators(data, indicator_settings)
        
        # Prepare the prompt using the specific trading style
        prompt = prepare_prompt(data, symbol, interval)
        if not prompt:
            flash(f"Failed to prepare prompt for {symbol}", "danger")
            return redirect(url_for('scan'))
        
        # Get trading signal
        trading_signal = get_trading_signal(prompt)
        if not trading_signal:
            flash(f"Failed to generate signal for {symbol}", "danger")
            return redirect(url_for('scan'))
        
        # Add trading style to metadata
        if isinstance(trading_signal, dict):
            if 'metadata' not in trading_signal:
                trading_signal['metadata'] = {}
            trading_signal['metadata']['trading_style'] = trading_style
            trading_signal['metadata']['interval'] = interval
            trading_signal['metadata']['period'] = period
        
        # Save the signal
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(OUTPUTS_DIR, f"{symbol}_{timestamp}_signal.json")
        with open(file_path, 'w') as f:
            json.dump(trading_signal, f, indent=2)
        
        # Extract signal ID from file path
        signal_id = timestamp
        
        # Redirect to the signal detail page
        return redirect(url_for('view_signal_detail', symbol=symbol, signal_id=signal_id))
        
    except Exception as e:
        app.logger.error(f"Error generating styled signal: {e}")
        flash(f"Error generating signal: {str(e)}", "danger")
        return redirect(url_for('scan'))

# Update the /scan route with the enhanced function
@app.route('/scan', methods=['GET', 'POST'])
def scan():
    """Run a scan for new signals with custom timeframe and indicator settings."""
    if request.method == 'POST':
        try:
            # Get form data
            symbol = request.form.get('symbol')
            interval = request.form.get('interval', '15m')
            period = request.form.get('period', '5d')
            
            # Check for custom symbol
            if symbol == 'custom':
                symbol = request.form.get('customSymbol', '').strip().upper()
                if not symbol:
                    return render_template('scan.html', error="Custom symbol cannot be empty", symbols=DEFAULT_SYMBOLS)
            
            # Check if technical analysis should be included
            with_technical = request.form.get('technical') == 'on'
            
            # Get advanced indicator settings if provided
            indicator_settings = None
            if request.form.get('showAdvancedSettings') == 'on':
                indicator_settings = {
                    'sma': [
                        int(request.form.get('sma1', 20)),
                        int(request.form.get('sma2', 50)),
                        int(request.form.get('sma3', 200))
                    ],
                    'ema': [
                        int(request.form.get('ema1', 12)),
                        int(request.form.get('ema2', 26))
                    ],
                    'rsi': int(request.form.get('rsi', 14)),
                    'macd': {
                        'fast': int(request.form.get('macd_fast', 12)),
                        'slow': int(request.form.get('macd_slow', 26)),
                        'signal': int(request.form.get('macd_signal', 9))
                    },
                    'bollinger': {
                        'period': int(request.form.get('bb_period', 20)),
                        'std_dev': 2  # Default
                    },
                    'atr': 14  # Default
                }
            elif with_technical:
                # Use timeframe-adjusted settings based on the interval
                from src.analysis.technical import get_timeframe_adjusted_settings
                indicator_settings = get_timeframe_adjusted_settings(interval)
            
            # Import and run the signal generator
            try:
                from main import process_symbol
                
                # Log the settings being used
                app.logger.info(f"Running scan for {symbol} using {interval} interval for {period} period")
                if indicator_settings:
                    app.logger.info(f"Using custom indicator settings: {indicator_settings}")
                
                # Process the symbol
                result = process_symbol(
                    symbol, 
                    interval=interval,
                    period=period,
                    with_technical=with_technical,
                    indicator_settings=indicator_settings
                )
                
                if result:
                    # If we have a signal ID in the metadata, use that
                    signal_id = result.get('metadata', {}).get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
                    
                    # Redirect to the signal detail page
                    return redirect(url_for('view_signal_detail', symbol=symbol, signal_id=signal_id))
                else:
                    return render_template(
                        'scan.html', 
                        error=f"Failed to generate signal for {symbol}", 
                        symbols=DEFAULT_SYMBOLS
                    )
            except Exception as e:
                app.logger.error(f"Error processing symbol: {e}")
                return render_template(
                    'scan.html', 
                    error=f"Error running scan: {str(e)}", 
                    symbols=DEFAULT_SYMBOLS
                )
        except Exception as e:
            app.logger.error(f"Error processing form data: {e}")
            return render_template(
                'scan.html', 
                error=f"Error processing request: {str(e)}", 
                symbols=DEFAULT_SYMBOLS
            )
    
    # GET request
    return render_template('scan.html', symbols=DEFAULT_SYMBOLS)

# Add some filters needed for the templates
@app.template_filter('tojson')
def tojson_filter(obj):
    return json.dumps(obj)

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