#!/usr/bin/env python3
"""
Simplified web dashboard for trading signal verification.
Uses the shared signal_visualization module for core functionality.
"""
import os
import argparse
import json
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

# Set the template directory (ensure your dashboard.html is located here)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(CURRENT_DIR, "templates")

# Create Flask app and set the template folder
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['SECRET_KEY'] = os.urandom(24)

# Configuration
ANALYSIS_DIR = "analysis_results"

# Create directories if they don't exist
if not os.path.exists(ANALYSIS_DIR):
    os.makedirs(ANALYSIS_DIR)
        
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
        
        # Save data for future use
        save_visualization_data(viz_data, ANALYSIS_DIR, f"{symbol}_analysis")
        
        return jsonify(viz_data)
    except Exception as e:
        main_logger.error(f"Error fetching data for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

def find_available_symbols(data_dir=RAW_DATA_DIR):
    """Find all available symbols in the data directory."""
    import glob
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

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    static_dir = os.path.join(TEMPLATE_DIR, 'static')
    return send_from_directory(static_dir, path)

@app.route('/')
def index():
    """Home page route."""
    # Get list of available symbols
    symbols = find_available_symbols()
    # Render the dashboard.html template from your templates folder
    return render_template("dashboard.html", symbols=symbols)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trading Signal Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", default=8080, type=int, help="Port number")
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port)
