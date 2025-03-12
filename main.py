#!/usr/bin/env python3
"""
Trading Signals Project - Main Script

This script fetches market data, analyzes it, and generates trading signals.
It can be run with command-line arguments for different symbols, intervals, and modes.
"""
import os
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

from data.tradingview import fetch_intraday_data
from prompts.intraday_prompt import prepare_llm_prompt
from signals.llm_signals import get_trading_signal
from src.utils.file_utils import create_directories
from src.utils.logger import main_logger
from src.analysis.technical import calculate_technical_indicators
from src.utils.config import DEFAULT_SYMBOLS, DEFAULT_INTERVAL, OUTPUTS_DIR

# Ensure all directories exist
create_directories()

# Load environment variables
load_dotenv()

def process_symbol(symbol, interval=DEFAULT_INTERVAL, with_technical=True, execute=False):
    """
    Process a single symbol to generate trading signals.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        interval (str): Time interval for data
        with_technical (bool): Whether to include technical analysis
        execute (bool): Whether to execute trades based on signals
    
    Returns:
        dict: Generated trading signal or None if error
    """
    try:
        main_logger.info(f"Processing {symbol} at {interval} interval")
        
        # Step 1: Fetch data
        data = fetch_intraday_data(symbol, interval)
        if not data:
            main_logger.error(f"Failed to fetch data for {symbol}")
            return None
        
        # Step 2: Perform technical analysis if requested
        if with_technical:
            main_logger.info(f"Calculating technical indicators for {symbol}")
            data = calculate_technical_indicators(data)
        
        # Step 3: Prepare LLM prompt
        prompt = prepare_llm_prompt(data, symbol, interval)
        if not prompt:
            main_logger.error(f"Failed to prepare prompt for {symbol}")
            return None
        
        # Step 4: Get trading signal
        trading_signal = get_trading_signal(prompt)
        
        if trading_signal:
            main_logger.info(f"Generated trading signal for {symbol}")
            main_logger.info(f"Action: {trading_signal.get('suggested_action', 'unknown')}")
            
            # Save to a more user-friendly file name
            timestamp = datetime.now().strftime('%Y%m%d')
            file_path = os.path.join(OUTPUTS_DIR, f"{symbol}_{timestamp}_signal.json")
            with open(file_path, 'w') as f:
                json.dump(trading_signal, f, indent=2)
            
            # Step 5: Execute trade if requested (and implemented)
            if execute:
                main_logger.warning("Trade execution is not yet implemented")
                # Future: Import and call the trade execution function
                # from src.execution.alpaca_executor import execute_trading_signal
                # order = execute_trading_signal(trading_signal, symbol)
        
        return trading_signal
    
    except Exception as e:
        main_logger.error(f"Error processing {symbol}: {e}")
        return None

def process_multiple_symbols(symbols, interval=DEFAULT_INTERVAL, with_technical=True, execute=False):
    """
    Process multiple symbols to generate trading signals.
    
    Args:
        symbols (list): List of stock symbols
        interval (str): Time interval for data
        with_technical (bool): Whether to include technical analysis
        execute (bool): Whether to execute trades based on signals
    
    Returns:
        dict: Dictionary mapping symbols to their trading signals
    """
    results = {}
    for symbol in symbols:
        signal = process_symbol(symbol, interval, with_technical, execute)
        if signal:
            results[symbol] = signal
    
    # If we processed multiple symbols, save a summary file
    if len(results) > 1:
        timestamp = datetime.now().strftime('%Y%m%d')
        summary = {
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "symbols_processed": len(symbols),
            "signals_generated": len(results),
            "interval": interval,
            "signals_summary": {}
        }
        
        # Create a condensed summary of each signal
        for symbol, signal in results.items():
            summary["signals_summary"][symbol] = {
                "action": signal.get("suggested_action", "unknown"),
                "confidence": signal.get("pattern_confidence", "unknown"),
                "pattern": signal.get("pattern_identified", "unknown")
            }
        
        # Save the summary
        file_path = os.path.join(OUTPUTS_DIR, f"summary_{timestamp}.json")
        with open(file_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        main_logger.info(f"Saved summary for {len(results)} signals to {file_path}")
    
    return results

def main():
    """Main function to parse arguments and run the appropriate process."""
    parser = argparse.ArgumentParser(description='Trading Signals Generator')
    
    parser.add_argument('--symbols', nargs='+', default=DEFAULT_SYMBOLS,
                        help='Stock symbols to analyze (default: AAPL MSFT AMZN GOOGL META)')
    
    parser.add_argument('--interval', type=str, default=DEFAULT_INTERVAL,
                        help='Time interval for data (default: 5m)')
    
    parser.add_argument('--skip-technical', action='store_true',
                        help='Skip technical indicator calculations')
    
    parser.add_argument('--execute', action='store_true',
                        help='Execute trades based on signals (use with caution!)')
    
    parser.add_argument('--symbol', type=str,
                        help='Single symbol to analyze (overrides --symbols)')
    
    args = parser.parse_args()
    
    # Log the starting configuration
    main_logger.info(f"Starting Trading Signals Generator")
    main_logger.info(f"Using interval: {args.interval}")
    
    # Process a single symbol if specified
    if args.symbol:
        main_logger.info(f"Processing single symbol: {args.symbol}")
        signal = process_symbol(
            args.symbol, 
            args.interval, 
            not args.skip_technical,
            args.execute
        )
        if signal:
            print(f"\nTrading Signal for {args.symbol}:")
            print(f"Action: {signal.get('suggested_action', 'unknown')}")
            print(f"Pattern: {signal.get('pattern_identified', 'unknown')} ({signal.get('pattern_confidence', 'unknown')})")
            print(f"Entry: {signal.get('entry_price', 'N/A')}")
            print(f"Stop Loss: {signal.get('stop_loss', 'N/A')}")
            print(f"Take Profit: {signal.get('take_profit', 'N/A')}")
    else:
        # Process multiple symbols
        main_logger.info(f"Processing {len(args.symbols)} symbols: {', '.join(args.symbols)}")
        signals = process_multiple_symbols(
            args.symbols, 
            args.interval, 
            not args.skip_technical,
            args.execute
        )
        
        # Print a simple summary to the console
        print(f"\nProcessed {len(args.symbols)} symbols, generated {len(signals)} signals")
        for symbol, signal in signals.items():
            print(f"{symbol}: {signal.get('suggested_action', 'unknown')} ({signal.get('pattern_confidence', 'unknown')})")
    
    main_logger.info("Trading Signals Generator completed")

if __name__ == "__main__":
    main()