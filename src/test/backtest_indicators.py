#!/usr/bin/env python3
"""
Backtest utility for technical indicators on historical data.
This module validates whether indicators correctly identify patterns
on historical data where outcomes are known.
"""
import os
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Import existing project modules
from src.data.yahoo_fetcher import fetch_yahoo_data
from src.analysis.technical import calculate_technical_indicators
from src.analysis.patterns import detect_candlestick_patterns, analyze_trend
from src.utils.logger import main_logger
from src.utils.config import RAW_DATA_DIR, OUTPUTS_DIR, PROCESSED_DATA_DIR
from src.utils.file_utils import create_directories, save_to_json

# Create required directories
create_directories()

# =====================================================================
# DATA LOADING FUNCTIONS
# =====================================================================

def load_historical_data(symbol=None, use_existing=True):
    """
    Load historical data for backtesting.
    
    Args:
        symbol (str): Symbol to load data for, or None to load all available
        use_existing (bool): Whether to use existing data files or fetch new data
        
    Returns:
        dict: Dictionary mapping symbols to their data
    """
    main_logger.info(f"Loading historical data for {symbol if symbol else 'all symbols'}")
    data_dict = {}
    
    # If a specific symbol is requested
    if symbol:
        if use_existing:
            # Try to find existing data files for this symbol
            pattern = os.path.join(RAW_DATA_DIR, f"{symbol}_*.json")
            files = []
            
            # Handle case where directory might not exist yet
            if os.path.exists(RAW_DATA_DIR):
                import glob
                files = glob.glob(pattern)
            
            if files:
                # Sort by modification time (newest first)
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Load the newest file
                with open(files[0], 'r') as f:
                    main_logger.info(f"Loading existing data from {files[0]}")
                    data_dict[symbol] = json.load(f)
            else:
                # No existing files, fetch new data
                main_logger.info(f"No existing data found for {symbol}, fetching new data...")
                data = fetch_yahoo_data(symbol, interval='1d', period='1y')
                if data:
                    data_dict[symbol] = data
        else:
            # Fetch new data
            main_logger.info(f"Fetching new data for {symbol}...")
            data = fetch_yahoo_data(symbol, interval='1d', period='1y')
            if data:
                data_dict[symbol] = data
    else:
        # Load all available data files or default symbols
        if use_existing and os.path.exists(RAW_DATA_DIR):
            import glob
            # Get all json files in the raw data directory
            files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
            
            # Group by symbol
            symbol_files = {}
            for file in files:
                base = os.path.basename(file)
                # Extract symbol from filename (assuming format like AAPL_5m_20250312.json)
                parts = base.split('_')
                if len(parts) >= 1:
                    sym = parts[0]
                    if sym not in symbol_files:
                        symbol_files[sym] = []
                    symbol_files[sym].append(file)
            
            # Load the newest file for each symbol
            for sym, sym_files in symbol_files.items():
                # Sort by modification time (newest first)
                sym_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Load the newest file
                with open(sym_files[0], 'r') as f:
                    main_logger.info(f"Loading existing data from {sym_files[0]}")
                    data_dict[sym] = json.load(f)
        else:
            # Fetch new data for default symbols
            default_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
            for sym in default_symbols:
                main_logger.info(f"Fetching new data for {sym}...")
                data = fetch_yahoo_data(sym, interval='1d', period='1y')
                if data:
                    data_dict[sym] = data
    
    return data_dict

# =====================================================================
# PATTERN DETECTION FUNCTIONS
# =====================================================================

def identify_patterns(data, pattern_type="bullish", threshold_periods=10):
    """
    Identify bullish or bearish patterns in the historical data and check 
    if they led to price movements in the expected direction.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        pattern_type (str): "bullish" or "bearish" to determine pattern type
        threshold_periods (int): Number of periods to check for price movement
        
    Returns:
        dict: Analysis of patterns and their success rates
    """
    if not data or 'bars' not in data or not data['bars']:
        return None
    
    symbol = data.get('symbol', 'Unknown')
    main_logger.info(f"Analyzing {pattern_type} patterns for {symbol}...")
    
    # Calculate indicators first using existing project module
    data_with_indicators = calculate_technical_indicators(data)
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(data_with_indicators['bars'])
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Dictionary to store patterns and their success rates
    pattern_analysis = {
        'symbol': symbol,
        'total_bars': len(df),
        'patterns': {}
    }
    
    # Dictionary of patterns to check
    pattern_types = {
        'bullish': [
            'bullish_engulfing', 'hammer', 'morning_star', 'three_white_soldiers',
            'bullish_harami', 'piercing', 'bullish_doji_star', 'dragonfly_doji'
        ],
        'bearish': [
            'bearish_engulfing', 'hanging_man', 'evening_star', 'three_black_crows',
            'bearish_harami', 'dark_cloud_cover', 'shooting_star', 'gravestone_doji'
        ]
    }
    
    # Get patterns using patterns module or retrieve from indicators
    # First check if patterns were already detected
    pattern_flags = {}
    
    for pattern in pattern_types[pattern_type]:
        if pattern in df.columns:
            # Pattern data already exists in DataFrame
            pattern_flags[pattern] = df[pattern].values
        else:
            # Mark pattern not found
            pattern_flags[pattern] = np.zeros(len(df))
            main_logger.debug(f"Pattern {pattern} not found in data")
    
    # Indicator combinations to check (like RSI oversold, MACD crossing, etc.)
    if pattern_type == "bullish":
        indicator_signals = analyze_bullish_indicator_signals(df)
    else:
        indicator_signals = analyze_bearish_indicator_signals(df)
    
    # Combine pattern and indicator analysis
    for name, signal_array in pattern_flags.items():
        occurrences = analyze_pattern_performance(
            df, signal_array, name, threshold_periods, 
            expected_direction=(pattern_type == "bullish")
        )
        
        if occurrences:
            pattern_analysis['patterns'][name] = occurrences
    
    # Add indicator signals to the patterns dictionary
    for name, signal_info in indicator_signals.items():
        if signal_info['occurrences']:
            pattern_analysis['patterns'][name] = signal_info
    
    return pattern_analysis

def analyze_pattern_performance(df, pattern_array, pattern_name, threshold_periods, expected_direction=True):
    """
    Analyze the performance of a detected pattern by checking future price movement.
    
    Args:
        df (DataFrame): DataFrame with price data
        pattern_array (ndarray): Array indicating where pattern was detected
        pattern_name (str): Name of the pattern
        threshold_periods (int): How many periods forward to check
        expected_direction (bool): True if expecting upward movement, False for downward
        
    Returns:
        dict: Performance analysis of the pattern
    """
    # Find pattern occurrences (non-zero values)
    pattern_indices = np.where(pattern_array > 0)[0]
    
    # If no occurrences, return None
    if len(pattern_indices) == 0:
        return None
    
    # Track pattern performance
    occurrences = []
    success_count = 0
    total_return = 0
    
    for idx in pattern_indices:
        # Skip if we don't have enough data after this index
        if idx + threshold_periods >= len(df):
            continue
        
        # Get prices at pattern and after threshold
        pattern_price = df['c'].iloc[idx]
        future_price = df['c'].iloc[idx + threshold_periods]
        
        # Calculate return
        price_return = (future_price - pattern_price) / pattern_price * 100
        
        # Determine if pattern was successful based on expected direction
        if expected_direction:  # Bullish pattern
            success = price_return > 0
        else:  # Bearish pattern
            success = price_return < 0
            
        if success:
            success_count += 1
        
        total_return += price_return
        
        # Record this occurrence
        occurrences.append({
            'date': df['t'].iloc[idx],
            'pattern_price': float(pattern_price),
            'future_price': float(future_price),
            'return': float(price_return),
            'success': bool(success)
        })
    
    # Calculate statistics
    if occurrences:
        success_rate = (success_count / len(occurrences)) * 100
        avg_return = total_return / len(occurrences)
        
        main_logger.info(f"  {pattern_name}: {len(occurrences)} occurrences, "
                        f"{success_rate:.1f}% success, {avg_return:.2f}% avg return")
        
        return {
            'occurrences': len(occurrences),
            'success_rate': float(success_rate),
            'avg_return': float(avg_return),
            'details': occurrences
        }
    
    return None

def analyze_indicator_signal(df, condition, confirmation, bullish=True, threshold_periods=10):
    """
    Generic function to analyze indicator signals.
    
    Args:
        df (DataFrame): DataFrame with price and indicator data
        condition (function): Function to check if the row meets the condition. Now expects (i, row)
        confirmation (function): Function to check for confirmation in next bar. Expects (i, df)
        bullish (bool): If True, expect price to rise after signal
        threshold_periods (int): How many periods to check for price movement
    
    Returns:
        dict: Analysis results
    """
    occurrences = []
    success_count = 0
    total_return = 0
    
    for i in range(len(df) - threshold_periods):
        row = df.iloc[i].to_dict()
        
        try:
            # Check if this row meets the condition
            if condition(i, row):
                # Check if we have confirmation
                if confirmation(i, df):
                    # Calculate performance
                    pattern_price = df['c'].iloc[i+1]  # Entry on confirmation bar
                    future_price = df['c'].iloc[i+1+threshold_periods]
                    
                    # Calculate price return
                    price_return = (future_price - pattern_price) / pattern_price * 100
                    
                    # Determine success based on expected direction
                    success = price_return > 0 if bullish else price_return < 0
                    if success:
                        success_count += 1
                    
                    total_return += price_return
                    
                    # Record this occurrence
                    occurrences.append({
                        'date': df['t'].iloc[i+1],
                        'pattern_price': float(pattern_price),
                        'future_price': float(future_price),
                        'return': float(price_return),
                        'success': bool(success)
                    })
        except (KeyError, IndexError) as e:
            # Skip if required fields are missing
            pass
    
    # Calculate statistics
    if occurrences:
        success_rate = (success_count / len(occurrences)) * 100
        avg_return = total_return / len(occurrences)
        
        main_logger.info(f"  Pattern: {len(occurrences)} occurrences, {success_rate:.1f}% success, {avg_return:.2f}% avg return")
        
        return {
            'occurrences': len(occurrences),
            'success_rate': float(success_rate),
            'avg_return': float(avg_return),
            'details': occurrences
        }
    
    return {'occurrences': 0, 'success_rate': 0, 'avg_return': 0, 'details': []}

def analyze_bullish_indicator_signals(df):
    """
    Analyze bullish signals from technical indicators.
    
    Args:
        df (DataFrame): DataFrame with price and indicator data
        
    Returns:
        dict: Dictionary of indicator signals and their details
    """
    signals = {}
    
    # RSI Oversold Reversal
    if 'rsi' in df.columns:
        signals['RSI_Oversold_Reversal'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: row['rsi'] < 30 if 'rsi' in row else False,
            confirmation=lambda i, df: (
                i+1 < len(df) and 
                'rsi' in df.columns and 
                df['rsi'].iloc[i+1] > df['rsi'].iloc[i] and 
                df['c'].iloc[i+1] > df['c'].iloc[i]
            ),
            bullish=True
        )
    
    # MACD Bullish Crossover
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        signals['MACD_Bullish_Crossover'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: (
                'macd' in row and 'macd_signal' in row and
                row['macd'] < row['macd_signal'] and
                'macd_hist' in row and row['macd_hist'] > 0
            ),
            confirmation=lambda i, df: (
                i+1 < len(df) and
                'macd' in df.columns and 'macd_signal' in df.columns and
                df['macd'].iloc[i+1] > df['macd_signal'].iloc[i+1]
            ),
            bullish=True
        )
    
    # Golden Cross (SMA)
    if 'sma_20' in df.columns and 'sma_50' in df.columns:
        signals['Golden_Cross_SMA'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: (
                row['sma_20'] > row['sma_50'] and i > 0 and 
                df['sma_20'].iloc[i - 1] <= df['sma_50'].iloc[i - 1]
            ),
            confirmation=lambda i, df: (
                i + 1 < len(df) and 'c' in df.columns and
                df['c'].iloc[i + 1] > df['sma_20'].iloc[i + 1]
            ),
            bullish=True
        )

    # Bollinger Band Bounce
    if 'bb_lower' in df.columns:
        signals['Bollinger_Band_Bounce'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: 'c' in row and 'bb_lower' in row and row['c'] <= row['bb_lower'],
            confirmation=lambda i, df: (
                i+1 < len(df) and 'c' in df.columns and 'bb_lower' in df.columns and
                df['c'].iloc[i+1] > df['c'].iloc[i] and
                df['c'].iloc[i+1] > df['bb_lower'].iloc[i+1]
            ),
            bullish=True
        )
    
    return signals

def analyze_bearish_indicator_signals(df):
    """
    Analyze bearish signals from technical indicators.
    
    Args:
        df (DataFrame): DataFrame with price and indicator data
        
    Returns:
        dict: Dictionary of indicator signals and their details
    """
    signals = {}
    
    # RSI Overbought Reversal
    if 'rsi' in df.columns:
        signals['RSI_Overbought_Reversal'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: row['rsi'] > 70 if 'rsi' in row else False,
            confirmation=lambda i, df: (
                i+1 < len(df) and 
                'rsi' in df.columns and 
                df['rsi'].iloc[i+1] < df['rsi'].iloc[i] and 
                df['c'].iloc[i+1] < df['c'].iloc[i]
            ),
            bullish=False
        )
    
    # MACD Bearish Crossover
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        signals['MACD_Bearish_Crossover'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: (
                'macd' in row and 'macd_signal' in row and
                row['macd'] > row['macd_signal'] and
                'macd_hist' in row and row['macd_hist'] < 0
            ),
            confirmation=lambda i, df: (
                i+1 < len(df) and
                'macd' in df.columns and 'macd_signal' in df.columns and
                df['macd'].iloc[i+1] < df['macd_signal'].iloc[i+1]
            ),
            bullish=False
        )
    
    # Death Cross (SMA)
    if 'sma_20' in df.columns and 'sma_50' in df.columns:
        signals['Death_Cross_SMA'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: (
                'sma_20' in row and 'sma_50' in row and
                row['sma_20'] < row['sma_50'] and
                i > 0 and df['sma_20'].iloc[i-1] >= df['sma_50'].iloc[i-1]
            ),
            confirmation=lambda i, df: (
                i+1 < len(df) and 'c' in df.columns and 'sma_20' in df.columns and
                df['c'].iloc[i+1] < df['sma_20'].iloc[i+1]
            ),
            bullish=False
        )
    
    # Bollinger Band Breakdown
    if 'bb_upper' in df.columns:
        signals['Bollinger_Band_Breakdown'] = analyze_indicator_signal(
            df,
            condition=lambda i, row: 'c' in row and 'bb_upper' in row and row['c'] >= row['bb_upper'],
            confirmation=lambda i, df: (
                i+1 < len(df) and 'c' in df.columns and 'bb_upper' in df.columns and
                df['c'].iloc[i+1] < df['c'].iloc[i] and
                df['c'].iloc[i+1] < df['bb_upper'].iloc[i+1]
            ),
            bullish=False
        )
    
    return signals

# =====================================================================
# VISUALIZATION FUNCTIONS
# =====================================================================

def visualize_pattern_effectiveness(analysis, pattern_type="bullish", output_dir="backtest_results"):
    """
    Visualize the effectiveness of patterns.
    
    Args:
        analysis (dict): Pattern analysis data
        pattern_type (str): 'bullish' or 'bearish'
        output_dir (str): Directory to save visualization files
    """
    if not analysis or 'patterns' not in analysis or not analysis['patterns']:
        main_logger.info(f"No {pattern_type} patterns to visualize")
        return
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Extract pattern names, success rates, and average returns
    pattern_names = []
    success_rates = []
    avg_returns = []
    occurrences = []
    
    for name, data in analysis['patterns'].items():
        pattern_names.append(name.replace('_', ' ').title())
        success_rates.append(data['success_rate'])
        avg_returns.append(data['avg_return'])
        occurrences.append(data['occurrences'])
    
    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
    
    # Sort by success rate
    sorted_indices = np.argsort(success_rates)
    sorted_names = [pattern_names[i] for i in sorted_indices]
    sorted_rates = [success_rates[i] for i in sorted_indices]
    sorted_returns = [avg_returns[i] for i in sorted_indices]
    sorted_occurrences = [occurrences[i] for i in sorted_indices]
    
    # Success rate bar chart
    bars = ax1.barh(sorted_names, sorted_rates, color='skyblue')
    ax1.set_xlabel('Success Rate (%)')
    ax1.set_title(f'{pattern_type.capitalize()} Pattern Success Rate')
    ax1.axvline(x=50, color='red', linestyle='--', alpha=0.5)  # 50% reference line
    
    # Add percentage labels
    for i, bar in enumerate(bars):
        ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                 f'{sorted_rates[i]:.1f}% ({sorted_occurrences[i]})', 
                 va='center')
    
    # Average return bar chart
    bars = ax2.barh(sorted_names, sorted_returns, 
                    color=['green' if x > 0 else 'red' for x in sorted_returns])
    ax2.set_xlabel('Average Return (%)')
    ax2.set_title(f'{pattern_type.capitalize()} Pattern Average Return')
    ax2.axvline(x=0, color='black', linestyle='-', alpha=0.5)  # Zero reference line
    
    # Add percentage labels
    for i, bar in enumerate(bars):
        ax2.text(bar.get_width() + 0.1 if sorted_returns[i] > 0 else bar.get_width() - 0.1, 
                 bar.get_y() + bar.get_height()/2, 
                 f'{sorted_returns[i]:.2f}%', 
                 va='center', ha='left' if sorted_returns[i] > 0 else 'right')
    
    plt.tight_layout()
    
    # Save the figure
    symbol = analysis.get('symbol', 'market')
    filename = f"{symbol}_{pattern_type}_pattern_analysis.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath)
    plt.close()
    
    main_logger.info(f"Saved {pattern_type} pattern visualization to {filepath}")

# =====================================================================
# SERIALIZATION HELPER
# =====================================================================

class NpEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp, pd.Period)):
            return str(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NpEncoder, self).default(obj)

def save_analysis_results(analysis, symbol, pattern_type, period, output_dir="backtest_results"):
    """
    Save analysis results to a JSON file with proper serialization.
    
    Args:
        analysis (dict): Analysis results to save
        symbol (str): Symbol being analyzed
        pattern_type (str): 'bullish' or 'bearish'
        period (int): Period used for the analysis
        output_dir (str): Directory to save the results
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Create filename
    filename = f"{symbol}_{pattern_type}_p{period}_analysis.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to file using custom encoder
    try:
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2, cls=NpEncoder)
        main_logger.info(f"Successfully saved analysis to {filepath}")
        return filepath
    except Exception as e:
        main_logger.error(f"Error saving analysis to {filepath}: {e}")
        return None

# =====================================================================
# MAIN FUNCTIONS
# =====================================================================

def run_backtest(symbols=None, periods_to_check=None, use_existing_data=True, output_dir="backtest_results"):
    """
    Run backtest on symbols.
    
    Args:
        symbols (list): List of symbols to test, or None to use all available
        periods_to_check (list): List of periods to check after pattern
        use_existing_data (bool): Whether to use existing data files or fetch new data
        output_dir (str): Directory to save results
    """
    if periods_to_check is None:
        periods_to_check = [5, 10, 20]
        
    # Load data
    if symbols:
        data_dict = {}
        for symbol in symbols:
            data = load_historical_data(symbol, use_existing=use_existing_data)
            if data and symbol in data:
                data_dict[symbol] = data[symbol]
    else:
        data_dict = load_historical_data(use_existing=use_existing_data)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process each symbol
    for symbol, data in data_dict.items():
        main_logger.info(f"\nBacktesting {symbol}...")
        
        # For each period to check
        for period in periods_to_check:
            main_logger.info(f"\nAnalyzing with {period}-day forward period:")
            
            # Analyze bullish patterns
            bullish_analysis = identify_patterns(data, pattern_type="bullish", threshold_periods=period)
            if bullish_analysis:
                # Save to file
                save_analysis_results(bullish_analysis, symbol, "bullish", period, output_dir)
                
                # Visualize
                visualize_pattern_effectiveness(bullish_analysis, "bullish", output_dir)
            
            # Analyze bearish patterns
            bearish_analysis = identify_patterns(data, pattern_type="bearish", threshold_periods=period)
            if bearish_analysis:
                # Save to file
                save_analysis_results(bearish_analysis, symbol, "bearish", period, output_dir)
                
                # Visualize
                visualize_pattern_effectiveness(bearish_analysis, "bearish", output_dir)
        
        main_logger.info(f"Completed backtest for {symbol}")

def main():
    """Main function to parse arguments and run backtest."""
    parser = argparse.ArgumentParser(description='TA-Lib Backtest Utility')
    
    parser.add_argument('--symbols', nargs='+', default=["AAPL"],
                        help='Stock symbols to analyze (default: AAPL)')
    
    parser.add_argument('--periods', nargs='+', type=int, default=[5, 10, 20],
                        help='Periods to check after pattern (default: 5 10 20)')
    
    parser.add_argument('--use-existing', action='store_true', default=True,
                        help='Use existing data files instead of fetching new ones')
    
    parser.add_argument('--output-dir', type=str, default="backtest_results",
                        help='Directory to save output files (default: backtest_results)')
    
    args = parser.parse_args()
    
    print("TA-Lib Backtest Utility")
    print("======================\n")
    
    # Run backtest
    run_backtest(
        symbols=args.symbols,
        periods_to_check=args.periods,
        use_existing_data=args.use_existing,
        output_dir=args.output_dir
    )
    
    print("\nBacktest completed. Check the output files for results.")

if __name__ == "__main__":
    main()
