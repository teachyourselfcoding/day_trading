#!/usr/bin/env python3
"""
Simplified visualization tool for verifying trading signals on price charts.
Uses the shared signal_visualization module for core functionality.
"""
import os
import argparse
from datetime import datetime

# Import the shared visualization module
from src.utils.signal_visualization import (
    load_symbol_data,
    prepare_data_for_visualization,
    create_mpl_visualization
)
from src.utils.logger import main_logger

def process_symbol(symbol, output_dir="signal_charts", interval="1d", period="1y"):
    """
    Process a symbol to visualize signals.
    
    Args:
        symbol (str): Symbol to process
        output_dir (str): Directory to save visualizations
        interval (str): Time interval for data
        period (str): Historical period to analyze
        
    Returns:
        str: Path to visualization file or None if error
    """
    main_logger.info(f"Processing {symbol}...")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load data
    data = load_symbol_data(symbol, interval=interval, period=period)
    if not data:
        main_logger.error(f"No data found for {symbol}")
        return None
    
    # Prepare data with indicators and signals
    viz_data = prepare_data_for_visualization(data)
    if not viz_data:
        main_logger.error(f"Error preparing data for {symbol}")
        return None
    
    # Create visualization
    output_path = os.path.join(output_dir, f"{symbol}_signals.png")
    viz_path = create_mpl_visualization(viz_data, output_path)
    
    return viz_path

def main():
    """Main function to parse arguments and process symbols."""
    parser = argparse.ArgumentParser(description='Trading Signal Visualization Tool')
    
    parser.add_argument('--symbols', nargs='+', default=["AAPL", "MSFT", "AMZN", "GOOGL", "META"],
                        help='Stock symbols to visualize (default: AAPL MSFT AMZN GOOGL META)')
    
    parser.add_argument('--interval', type=str, default="1d",
                        help='Time interval for data (default: 1d)')
    
    parser.add_argument('--period', type=str, default="1y",
                        help='Historical period to analyze (default: 1y)')
    
    parser.add_argument('--output-dir', type=str, default="signal_charts",
                        help='Directory to save visualizations (default: signal_charts)')
    
    args = parser.parse_args()
    
    print("Trading Signal Visualization Tool")
    print("================================\n")
    
    # Process each symbol
    for symbol in args.symbols:
        viz_path = process_symbol(
            symbol, 
            output_dir=args.output_dir, 
            interval=args.interval, 
            period=args.period
        )
        
        if viz_path:
            print(f"Created visualization for {symbol} at {viz_path}")
    
    print("\nVisualization completed. Check the output directory for results.")

if __name__ == "__main__":
    main()