#!/usr/bin/env python3
"""
Interactive web dashboard for verifying trading signals on price charts.
Uses the shared signal_visualization module for core functionality
while maintaining a rich, interactive interface.
"""
import os
import argparse
import json
import math
import glob
from flask import Flask, render_template, request, jsonify, send_from_directory

# Import the shared visualization module
from src.utils.signal_visualization import (
    load_symbol_data,
    prepare_data_for_visualization,
    prepare_web_visualization_data,
    save_visualization_data
)
from src.utils.config import RAW_DATA_DIR
from src.utils.logger import main_logger
from src.utils.file_utils import create_directories

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
for directory in [ANALYSIS_DIR, TEMPLATE_DIR, STATIC_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Create static directories if needed
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

def find_available_symbols(data_dir=RAW_DATA_DIR):
    """Find all available symbols in the data directory."""
    if not os.path.exists(data_dir):
        return ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
        
    all_files = glob.glob(os.path.join(data_dir, "*.json"))
    symbols = set()
    for file_path in all_files:
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        if parts:
            symbols.add(parts[0])
    
    return sorted(list(symbols)) if symbols else ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]

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
            
        main_logger.info(f"Loading data for {ticker}")
        
        # Load and process data using shared modules
        raw_data = load_symbol_data(ticker, interval='1d', period='1y')
        if not raw_data:
            return jsonify({'error': f'No data found for {ticker}'}), 404
            
        processed_data = prepare_data_for_visualization(raw_data)
        if not processed_data:
            return jsonify({'error': f'Error processing data for {ticker}'}), 500
            
        viz_data = prepare_web_visualization_data(processed_data)
        
        return jsonify(viz_data)
        
    except Exception as e:
        main_logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/data/<symbol>')
def get_symbol_data(symbol):
    """API endpoint for symbol data."""
    try:
        # Check if analysis already exists
        analysis_file = os.path.join(ANALYSIS_DIR, f"{symbol}_analysis.json")
        
        if os.path.exists(analysis_file):
            # Load existing analysis
            with open(analysis_file, 'r') as f:
                return jsonify(json.load(f))
        
        # Load raw data
        data = load_symbol_data(symbol, interval='1d', period='1y')
        if not data:
            return jsonify({"error": f"No data found for symbol {symbol}"}), 404
            
        # Process data with indicators and signals
        processed_data = prepare_data_for_visualization(data)
        if not processed_data:
            return jsonify({"error": f"Error processing data for {symbol}"}), 500
            
        # Prepare data for web visualization
        viz_data = prepare_web_visualization_data(processed_data)
        
        # Save processed data
        file_path = save_visualization_data(viz_data, ANALYSIS_DIR, f"{symbol}_analysis")
        main_logger.info(f"Saved processed data for {symbol} to {file_path}")
        
        return jsonify(viz_data)
    except Exception as e:
        main_logger.error(f"Error processing {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

def replace_nan_with_none(obj):
    """Recursively replace NaN values in a dict or list with None."""
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(item) for item in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj

@app.route('/')
def index():
    """Home page route."""
    # Get list of available symbols
    symbols = find_available_symbols()
    
    # Load index.html content from file
    index_html_path = os.path.join(TEMPLATE_DIR, 'index.html')
    if os.path.exists(index_html_path):
        with open(index_html_path, 'r') as f:
            index_html_content = f.read()
            # If the content is wrapped in a variable assignment, extract it
            if index_html_content.startswith('index_html = """') and index_html_content.endswith('"""'):
                index_html_content = index_html_content[15:-3]  # Extract the HTML content
    else:
        # Use the template directly
        return render_template("index.html", symbols=symbols)
        
    # Render template with symbols
    from flask import render_template_string
    return render_template_string(index_html_content, symbols=symbols)

def create_templates():
    """Create template files if they don't exist."""
    # Create CSS file
    css_dir = os.path.join(STATIC_DIR, "css")
    css_path = os.path.join(css_dir, "style.css")
    
    # Only create CSS file if it doesn't exist
    if not os.path.exists(css_path):
        css_content_path = os.path.join(TEMPLATE_DIR, 'static', 'style.css')
        if os.path.exists(css_content_path):
            # Copy from style.css if it exists
            with open(css_content_path, 'r') as src, open(css_path, 'w') as dest:
                dest.write(src.read())
    
    # Create JS file
    js_dir = os.path.join(STATIC_DIR, "js")
    js_path = os.path.join(js_dir, "dashboard.js")
    
    # Only create JS file if it doesn't exist
    if not os.path.exists(js_path):
        js_content_path = os.path.join(TEMPLATE_DIR, 'static', 'js', 'dashboard.js')
        if os.path.exists(js_content_path):
            # Copy from dashboard.js if it exists
            with open(js_content_path, 'r') as src, open(js_path, 'w') as dest:
                dest.write(src.read())
    
    main_logger.info(f"Templates directory: {TEMPLATE_DIR}")
    main_logger.info(f"Static directory: {STATIC_DIR}")

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
    create_directories()
    
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