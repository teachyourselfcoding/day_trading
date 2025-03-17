#!/usr/bin/env python3
"""
Trading Signals Project - Main Script

This script fetches market data, analyzes it, and generates trading signals.
It can be run with command-line arguments for different symbols, intervals, periods,
and custom indicator settings.
"""
import os
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

from data.tradingview import fetch_intraday_data
from prompts.intraday_prompt import prepare_medium_term_prompt
from signals.llm_signals import get_trading_signal
from src.utils.file_utils import create_directories
from src.utils.logger import main_logger
from src.analysis.technical import calculate_technical_indicators, get_timeframe_adjusted_settings
from src.utils.config import DEFAULT_SYMBOLS, DEFAULT_INTERVAL, DEFAULT_PERIOD
from src.utils.config import TECHNICAL_SETTINGS, OUTPUTS_DIR

# Ensure all directories exist
create_directories()

# Load environment variables
load_dotenv()

def process_symbol(symbol, interval=DEFAULT_INTERVAL, period=DEFAULT_PERIOD, 
                  with_technical=True, execute=False, indicator_settings=None, trading_style="medium_term"):
    """
    Process a single symbol to generate trading signals.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        interval (str): Time interval for data
        period (str): Historical period to fetch
        with_technical (bool): Whether to include technical analysis
        execute (bool): Whether to execute trades based on signals
        indicator_settings (dict): Custom technical indicator settings
        trading_style (str): 'short_term', 'medium_term', or 'long_term'
    
    Returns:
        dict: Generated trading signal or None if error
    """
    try:
        main_logger.info(f"Processing {symbol} at {interval} interval for {period} period with {trading_style} style")
        
        # Step 1: Fetch data
        data = fetch_intraday_data(symbol, interval, period)
        if not data:
            main_logger.error(f"Failed to fetch data for {symbol}")
            return None
        
        # Step 2: Perform technical analysis if requested
        if with_technical:
            main_logger.info(f"Calculating technical indicators for {symbol}")
            
            # Use custom indicator settings if provided or get timeframe-adjusted settings
            if indicator_settings:
                settings_to_use = indicator_settings
            else:
                settings_to_use = get_timeframe_adjusted_settings(interval)
                
            data = calculate_technical_indicators(data, settings_to_use)
        
        # Step 3: Prepare LLM prompt based on trading style
        if trading_style == "short_term":
            prompt = prepare_short_term_prompt(data, symbol, interval)
        elif trading_style == "long_term":
            prompt = prepare_long_term_prompt(data, symbol, interval)
        else:
            # Default to medium term
            prompt = prepare_medium_term_prompt(data, symbol, interval)
            
        if not prompt:
            main_logger.error(f"Failed to prepare prompt for {symbol}")
            return None
        
        # Step 4: Get trading signal
        trading_signal = get_trading_signal(prompt)
        
        if trading_signal:
            main_logger.info(f"Generated trading signal for {symbol}")
            main_logger.info(f"Action: {trading_signal.get('suggested_action', 'unknown')}")
            
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if isinstance(trading_signal, dict):
                trading_signal.setdefault('metadata', {}).update({
                    'interval': interval,
                    'period': period,
                    'indicator_settings': settings_to_use if indicator_settings else "timeframe_adjusted",
                    'trading_style': trading_style,
                    'timestamp': timestamp  # Add timestamp for referencing this specific signal
                })
                
                # Log the saved file path but don't save again
                main_logger.info(f"Trading signal metadata updated for {symbol}")
            
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

def process_multiple_symbols(symbols, interval=DEFAULT_INTERVAL, period=DEFAULT_PERIOD, 
                           with_technical=True, execute=False, indicator_settings=None, trading_style="medium_term"):
    """
    Process multiple symbols to generate trading signals.
    
    Args:
        symbols (list): List of stock symbols
        interval (str): Time interval for data
        period (str): Historical period to fetch
        with_technical (bool): Whether to include technical analysis
        execute (bool): Whether to execute trades based on signals
        indicator_settings (dict): Custom technical indicator settings
        trading_style (str): 'short_term', 'medium_term', or 'long_term'
    
    Returns:
        dict: Dictionary mapping symbols to their trading signals
    """
    results = {}
    for symbol in symbols:
        signal = process_symbol(symbol, interval, period, with_technical, execute, indicator_settings, trading_style)
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
            "period": period,
            "trading_style": trading_style,
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

def parse_indicator_settings(args):
    """
    Parse command line arguments into indicator settings dict.
    
    Args:
        args: Command line arguments from argparse
        
    Returns:
        dict: Custom indicator settings or None if using defaults
    """
    # Check if any custom indicator settings were provided
    has_custom_settings = (
        args.sma is not None or 
        args.ema is not None or 
        args.rsi is not None or 
        args.macd_fast is not None or
        args.macd_slow is not None or
        args.macd_signal is not None or
        args.bb_period is not None or
        args.bb_std is not None or
        args.atr is not None
    )
    
    if not has_custom_settings:
        return None
    
    # Start with the default settings
    settings = TECHNICAL_SETTINGS.copy()
    
    # Update with custom values
    if args.sma is not None:
        settings['sma'] = args.sma
    
    if args.ema is not None:
        settings['ema'] = args.ema
    
    if args.rsi is not None:
        settings['rsi'] = args.rsi
    
    if args.macd_fast is not None or args.macd_slow is not None or args.macd_signal is not None:
        macd_settings = settings['macd'].copy()
        if args.macd_fast is not None:
            macd_settings['fast'] = args.macd_fast
        if args.macd_slow is not None:
            macd_settings['slow'] = args.macd_slow
        if args.macd_signal is not None:
            macd_settings['signal'] = args.macd_signal
        settings['macd'] = macd_settings
    
    if args.bb_period is not None or args.bb_std is not None:
        bb_settings = settings['bollinger'].copy()
        if args.bb_period is not None:
            bb_settings['period'] = args.bb_period
        if args.bb_std is not None:
            bb_settings['std_dev'] = args.bb_std
        settings['bollinger'] = bb_settings
    
    if args.atr is not None:
        settings['atr'] = args.atr
    
    return settings

def main():
    """Main function to parse arguments and run the appropriate process."""
    parser = argparse.ArgumentParser(description='Trading Signals Generator')
    
    parser.add_argument('--symbols', nargs='+', default=DEFAULT_SYMBOLS,
                        help='Stock symbols to analyze (default: AAPL MSFT AMZN GOOGL META)')
    
    parser.add_argument('--interval', type=str, default=DEFAULT_INTERVAL,
                        help='Time interval for data (default: 5m)')
    
    parser.add_argument('--period', type=str, default=DEFAULT_PERIOD,
                        help='Historical period to fetch (default: 5d)')
    
    parser.add_argument('--skip-technical', action='store_true',
                        help='Skip technical indicator calculations')
    
    parser.add_argument('--execute', action='store_true',
                        help='Execute trades based on signals (use with caution!)')
    
    parser.add_argument('--symbol', type=str,
                        help='Single symbol to analyze (overrides --symbols)')
    
    parser.add_argument('--trading-style', type=str, default='medium_term',
                        choices=['short_term', 'medium_term', 'long_term'],
                        help='Trading style to use (short_term, medium_term, or long_term)')
    
    # Add custom indicator settings
    parser.add_argument('--sma', nargs='+', type=int,
                        help='Custom SMA periods (e.g., --sma 20 50 200)')
    
    parser.add_argument('--ema', nargs='+', type=int,
                        help='Custom EMA periods (e.g., --ema 12 26)')
    
    parser.add_argument('--rsi', type=int,
                        help='Custom RSI period (e.g., --rsi 14)')
    
    parser.add_argument('--macd-fast', type=int,
                        help='Custom MACD fast period (e.g., --macd-fast 12)')
    
    parser.add_argument('--macd-slow', type=int,
                        help='Custom MACD slow period (e.g., --macd-slow 26)')
    
    parser.add_argument('--macd-signal', type=int,
                        help='Custom MACD signal period (e.g., --macd-signal 9)')
    
    parser.add_argument('--bb-period', type=int,
                        help='Custom Bollinger Bands period (e.g., --bb-period 20)')
    
    parser.add_argument('--bb-std', type=float,
                        help='Custom Bollinger Bands standard deviation (e.g., --bb-std 2.0)')
    
    parser.add_argument('--atr', type=int,
                        help='Custom ATR period (e.g., --atr 14)')
    
    args = parser.parse_args()
    
    # Parse custom indicator settings
    indicator_settings = parse_indicator_settings(args)
    
    # Log the starting configuration
    main_logger.info(f"Starting Trading Signals Generator")
    main_logger.info(f"Using interval: {args.interval}, period: {args.period}, trading style: {args.trading_style}")
    if indicator_settings:
        main_logger.info(f"Using custom indicator settings")
    
    # Process a single symbol if specified
    if args.symbol:
        main_logger.info(f"Processing single symbol: {args.symbol}")
        signal = process_symbol(
            args.symbol, 
            args.interval,
            args.period,
            not args.skip_technical,
            args.execute,
            indicator_settings,
            args.trading_style
        )
        if signal:
            print(f"\nTrading Signal for {args.symbol}:")
            print(f"Action: {signal.get('suggested_action', 'unknown')}")
            print(f"Pattern: {signal.get('pattern_identified', 'unknown')} ({signal.get('pattern_confidence', 'unknown')})")
            print(f"Entry: {signal.get('entry_price', 'N/A')}")
            print(f"Stop Loss: {signal.get('stop_loss', 'N/A')}")
            print(f"Take Profit: {signal.get('take_profit', 'N/A')}")
            print(f"Timeframe: {args.interval} chart with {args.period} history")
            print(f"Trading Style: {args.trading_style}")
    else:
        # Process multiple symbols
        main_logger.info(f"Processing {len(args.symbols)} symbols: {', '.join(args.symbols)}")
        signals = process_multiple_symbols(
            args.symbols, 
            args.interval,
            args.period,
            not args.skip_technical,
            args.execute,
            indicator_settings,
            args.trading_style
        )
        
        # Print a simple summary to the console
        print(f"\nProcessed {len(args.symbols)} symbols, generated {len(signals)} signals")
        print(f"Timeframe: {args.interval} chart with {args.period} history")
        print(f"Trading Style: {args.trading_style}")
        for symbol, signal in signals.items():
            print(f"{symbol}: {signal.get('suggested_action', 'unknown')} ({signal.get('pattern_confidence', 'unknown')})")
    
    main_logger.info("Trading Signals Generator completed")

if __name__ == "__main__":
    main()