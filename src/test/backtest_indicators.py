#!/usr/bin/env python3
"""
Backtest utility for technical indicators on historical data.
This module uses existing src.analysis modules to validate indicator reliability.
"""
import os
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import glob

# Import existing project modules
from src.data.yahoo_fetcher import fetch_yahoo_data
from src.analysis.technical import calculate_technical_indicators, extract_price_summary
from src.analysis.patterns import detect_candlestick_patterns, analyze_trend, analyze_support_resistance
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
# PATTERN ANALYSIS FUNCTIONS
# =====================================================================

def prepare_data_for_backtest(data):
    """
    Process data with all technical indicators for backtesting.
    
    Args:
        data (dict): Raw price data
        
    Returns:
        dict: Processed data with all indicators
    """
    # Calculate technical indicators using the existing module
    data_with_indicators = calculate_technical_indicators(data)
    return data_with_indicators

def analyze_pattern_performance(df, pattern_indices, pattern_name, threshold_periods, expected_direction=True):
    """
    Analyze how well a pattern predicted future price movement.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        pattern_indices (list): Indices where pattern occurred
        pattern_name (str): Name of the pattern
        threshold_periods (int): Number of periods to check forward
        expected_direction (bool): True for bullish (expecting price rise)
        
    Returns:
        dict: Performance metrics for the pattern
    """
    # Skip if no instances found
    if not pattern_indices:
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
        
        # Determine if pattern led to expected outcome
        if expected_direction:  # Bullish pattern
            success = price_return > 0
        else:  # Bearish pattern
            success = price_return < 0
            
        if success:
            success_count += 1
        
        total_return += price_return
        
        # Record this occurrence
        occurrences.append({
            'date': df['t'].iloc[idx] if 't' in df.columns else str(idx),
            'pattern_price': float(pattern_price),
            'future_price': float(future_price),
            'return': float(price_return),
            'success': bool(success)  # Ensure it's a Python bool
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

def identify_bullish_patterns(data, threshold_periods=10):
    """
    Identify bullish patterns in the historical data and check if they led to price increases.
    
    Args:
        data (dict): Data with technical indicators
        threshold_periods (int): Number of periods to check after pattern
        
    Returns:
        dict: Analysis of bullish patterns and their success rates
    """
    if not data or 'bars' not in data or not data['bars']:
        return None
    
    symbol = data.get('symbol', 'Unknown')
    main_logger.info(f"Analyzing bullish patterns for {symbol}...")
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Use detect_candlestick_patterns from the existing module
    # This requires original data format, not dataframe
    patterns_detected = detect_candlestick_patterns(data['bars'])
    
    # We'll also analyze technical indicator signals
    pattern_analysis = {
        'symbol': symbol,
        'total_bars': len(df),
        'patterns': {}
    }
    
    # Extract bullish patterns from detected patterns
    bullish_patterns = {}
    for pattern_name, description in patterns_detected.items():
        if 'bullish' in pattern_name.lower():
            # Find where this pattern was detected
            # This is an approximation since we don't have the exact indices
            pattern_indices = []
            # Use the most recent 2/3 of data for pattern detection to match with TA-Lib lookback
            start_idx = len(df) // 3
            pattern_str = pattern_name.lower()
            
            # Look for specific bullish patterns in the data
            # Simplified detection based on general pattern characteristics
            if 'engulfing' in pattern_str:
                for i in range(start_idx+1, len(df)):
                    if (df['c'].iloc[i] > df['o'].iloc[i] and  # Bullish candle
                        df['c'].iloc[i-1] < df['o'].iloc[i-1] and  # Previous bearish candle
                        df['c'].iloc[i] > df['o'].iloc[i-1] and  # Current close > prev open
                        df['o'].iloc[i] < df['c'].iloc[i-1]):  # Current open < prev close
                        pattern_indices.append(i)
            
            elif 'hammer' in pattern_str:
                for i in range(start_idx, len(df)):
                    body_size = abs(df['c'].iloc[i] - df['o'].iloc[i])
                    lower_shadow = min(df['c'].iloc[i], df['o'].iloc[i]) - df['l'].iloc[i]
                    if (lower_shadow > 2 * body_size and  # Long lower shadow
                        body_size > 0):  # Non-zero body
                        pattern_indices.append(i)
            
            # Analyze pattern performance
            performance = analyze_pattern_performance(df, pattern_indices, pattern_name, threshold_periods, True)
            if performance:
                bullish_patterns[pattern_name] = performance
    
    # Add technical indicator signals analysis
    # RSI Oversold
    if 'rsi' in df.columns:
        rsi_oversold_indices = list(np.where(df['rsi'] < 30)[0])
        rsi_analysis = analyze_pattern_performance(df, rsi_oversold_indices, "RSI Oversold", threshold_periods, True)
        if rsi_analysis:
            bullish_patterns["RSI_Oversold"] = rsi_analysis
    
    # MACD Bullish Cross
    if all(col in df.columns for col in ['macd', 'macd_signal']):
        macd_cross_indices = []
        for i in range(1, len(df)):
            if (df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and 
                df['macd'].iloc[i] > df['macd_signal'].iloc[i]):
                macd_cross_indices.append(i)
        
        macd_analysis = analyze_pattern_performance(df, macd_cross_indices, "MACD Bullish Cross", threshold_periods, True)
        if macd_analysis:
            bullish_patterns["MACD_Bullish_Cross"] = macd_analysis
    
    # Golden Cross (SMA)
    if all(col in df.columns for col in ['sma_50', 'sma_200']):
        golden_cross_indices = []
        for i in range(1, len(df)):
            if (df['sma_50'].iloc[i-1] <= df['sma_200'].iloc[i-1] and 
                df['sma_50'].iloc[i] > df['sma_200'].iloc[i]):
                golden_cross_indices.append(i)
        
        gc_analysis = analyze_pattern_performance(df, golden_cross_indices, "Golden Cross", threshold_periods, True)
        if gc_analysis:
            bullish_patterns["Golden_Cross"] = gc_analysis
    
    # Bollinger Band Bounce
    if all(col in df.columns for col in ['bb_lower', 'c']):
        bb_bounce_indices = []
        for i in range(1, len(df)):
            if (df['c'].iloc[i-1] <= df['bb_lower'].iloc[i-1] and 
                df['c'].iloc[i] > df['bb_lower'].iloc[i]):
                bb_bounce_indices.append(i)
        
        bb_analysis = analyze_pattern_performance(df, bb_bounce_indices, "BB Bounce", threshold_periods, True)
        if bb_analysis:
            bullish_patterns["BB_Lower_Bounce"] = bb_analysis
    
    # Add all patterns to the analysis
    pattern_analysis['patterns'] = bullish_patterns
    
    return pattern_analysis

def identify_bearish_patterns(data, threshold_periods=10):
    """
    Identify bearish patterns in the historical data and check if they led to price decreases.
    
    Args:
        data (dict): Data with technical indicators
        threshold_periods (int): Number of periods to check after pattern
        
    Returns:
        dict: Analysis of bearish patterns and their success rates
    """
    if not data or 'bars' not in data or not data['bars']:
        return None
    
    symbol = data.get('symbol', 'Unknown')
    main_logger.info(f"Analyzing bearish patterns for {symbol}...")
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Use detect_candlestick_patterns from the existing module
    patterns_detected = detect_candlestick_patterns(data['bars'])
    
    # We'll also analyze technical indicator signals
    pattern_analysis = {
        'symbol': symbol,
        'total_bars': len(df),
        'patterns': {}
    }
    
    # Extract bearish patterns from detected patterns
    bearish_patterns = {}
    for pattern_name, description in patterns_detected.items():
        if 'bearish' in pattern_name.lower():
            # Find where this pattern was detected
            pattern_indices = []
            # Use the most recent 2/3 of data for pattern detection
            start_idx = len(df) // 3
            pattern_str = pattern_name.lower()
            
            # Look for specific bearish patterns in the data
            if 'engulfing' in pattern_str:
                for i in range(start_idx+1, len(df)):
                    if (df['c'].iloc[i] < df['o'].iloc[i] and  # Bearish candle
                        df['c'].iloc[i-1] > df['o'].iloc[i-1] and  # Previous bullish candle
                        df['o'].iloc[i] > df['c'].iloc[i-1] and  # Current open > prev close
                        df['c'].iloc[i] < df['o'].iloc[i-1]):  # Current close < prev open
                        pattern_indices.append(i)
            
            elif 'evening star' in pattern_str:
                for i in range(start_idx+2, len(df)):
                    if (df['c'].iloc[i-2] > df['o'].iloc[i-2] and  # First day bullish
                        abs(df['c'].iloc[i-1] - df['o'].iloc[i-1]) < 0.3 * abs(df['c'].iloc[i-2] - df['o'].iloc[i-2]) and  # Second day small body
                        df['c'].iloc[i] < df['o'].iloc[i] and  # Third day bearish
                        df['c'].iloc[i] < (df['o'].iloc[i-2] + df['c'].iloc[i-2])/2):  # Third day closes below midpoint of first day
                        pattern_indices.append(i)
            
            # Analyze pattern performance
            performance = analyze_pattern_performance(df, pattern_indices, pattern_name, threshold_periods, False)
            if performance:
                bearish_patterns[pattern_name] = performance
    
    # Add technical indicator signals analysis
    # RSI Overbought
    if 'rsi' in df.columns:
        rsi_overbought_indices = list(np.where(df['rsi'] > 70)[0])
        rsi_analysis = analyze_pattern_performance(df, rsi_overbought_indices, "RSI Overbought", threshold_periods, False)
        if rsi_analysis:
            bearish_patterns["RSI_Overbought"] = rsi_analysis
    
    # MACD Bearish Cross
    if all(col in df.columns for col in ['macd', 'macd_signal']):
        macd_cross_indices = []
        for i in range(1, len(df)):
            if (df['macd'].iloc[i-1] > df['macd_signal'].iloc[i-1] and 
                df['macd'].iloc[i] < df['macd_signal'].iloc[i]):
                macd_cross_indices.append(i)
        
        macd_analysis = analyze_pattern_performance(df, macd_cross_indices, "MACD Bearish Cross", threshold_periods, False)
        if macd_analysis:
            bearish_patterns["MACD_Bearish_Cross"] = macd_analysis
    
    # Death Cross (SMA)
    if all(col in df.columns for col in ['sma_50', 'sma_200']):
        death_cross_indices = []
        for i in range(1, len(df)):
            if (df['sma_50'].iloc[i-1] >= df['sma_200'].iloc[i-1] and 
                df['sma_50'].iloc[i] < df['sma_200'].iloc[i]):
                death_cross_indices.append(i)
        
        dc_analysis = analyze_pattern_performance(df, death_cross_indices, "Death Cross", threshold_periods, False)
        if dc_analysis:
            bearish_patterns["Death_Cross"] = dc_analysis
    
    # Bollinger Band Break
    if all(col in df.columns for col in ['bb_upper', 'c']):
        bb_break_indices = []
        for i in range(1, len(df)):
            if (df['c'].iloc[i-1] >= df['bb_upper'].iloc[i-1] and 
                df['c'].iloc[i] < df['bb_upper'].iloc[i]):
                bb_break_indices.append(i)
        
        bb_analysis = analyze_pattern_performance(df, bb_break_indices, "BB Upper Break", threshold_periods, False)
        if bb_analysis:
            bearish_patterns["BB_Upper_Break"] = bb_analysis
    
    # Add all patterns to the analysis
    pattern_analysis['patterns'] = bearish_patterns
    
    return pattern_analysis

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
        
        # Process data with technical indicators
        processed_data = prepare_data_for_backtest(data)
        
        # For each period to check
        for period in periods_to_check:
            main_logger.info(f"\nAnalyzing with {period}-day forward period:")
            
            # Analyze bullish patterns
            bullish_analysis = identify_bullish_patterns(processed_data, threshold_periods=period)
            if bullish_analysis:
                # Save to file
                save_analysis_results(bullish_analysis, symbol, "bullish", period, output_dir)
                
                # Visualize
                visualize_pattern_effectiveness(bullish_analysis, "bullish", output_dir)
            
            # Analyze bearish patterns
            bearish_analysis = identify_bearish_patterns(processed_data, threshold_periods=period)
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
    
    print("Technical Analysis Backtest Utility")
    print("==================================\n")
    
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