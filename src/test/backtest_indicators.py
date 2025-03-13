#!/usr/bin/env python3
"""
Backtest utility for TA-Lib indicators on historical data.
This script validates whether technical indicators correctly identify patterns
on historical data where the outcomes are known.
"""
import os
import json
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import glob

from src.data.yahoo_fetcher import fetch_yahoo_data
from src.analysis.technical import calculate_technical_indicators
from src.analysis.patterns import detect_candlestick_patterns, analyze_trend
from src.utils.logger import main_logger
from src.utils.config import RAW_DATA_DIR, OUTPUTS_DIR


def load_historical_data(symbol=None, use_existing=True):
    """
    Load historical data for backtesting.
    
    Args:
        symbol (str): Symbol to load data for, or None to load all available
        use_existing (bool): Whether to use existing data files or fetch new data
        
    Returns:
        dict: Dictionary mapping symbols to their data
    """
    data_dict = {}
    
    # If a specific symbol is requested
    if symbol:
        if use_existing:
            # Try to find existing data files for this symbol
            pattern = f"{symbol}_*.json"
            files = glob.glob(os.path.join(RAW_DATA_DIR, pattern))
            
            if files:
                # Sort by modification time (newest first)
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Load the newest file
                with open(files[0], 'r') as f:
                    print(f"Loading existing data from {files[0]}")
                    data_dict[symbol] = json.load(f)
            else:
                # No existing files, fetch new data
                print(f"No existing data found for {symbol}, fetching new data...")
                data = fetch_yahoo_data(symbol, interval='1d', period='1y')
                if data:
                    data_dict[symbol] = data
        else:
            # Fetch new data
            print(f"Fetching new data for {symbol}...")
            data = fetch_yahoo_data(symbol, interval='1d', period='1y')
            if data:
                data_dict[symbol] = data
    else:
        # Load all available data files
        if use_existing:
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
                    print(f"Loading existing data from {sym_files[0]}")
                    data_dict[sym] = json.load(f)
        else:
            # Fetch new data for default symbols
            default_symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
            for sym in default_symbols:
                print(f"Fetching new data for {sym}...")
                data = fetch_yahoo_data(sym, interval='1d', period='1y')
                if data:
                    data_dict[sym] = data
    
    return data_dict


# Update the identify_bullish_patterns function to properly convert array types
def identify_bullish_patterns(data, threshold_periods=10):
    """
    Identify bullish patterns in the historical data and check if they led to price increases.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        threshold_periods (int): Number of periods to check for price increase after pattern
        
    Returns:
        dict: Analysis of bullish patterns and their success rates
    """
    if not data or 'bars' not in data or not data['bars']:
        return None
    
    symbol = data.get('symbol', 'Unknown')
    print(f"Analyzing bullish patterns for {symbol}...")
    
    # Calculate indicators first
    data_with_indicators = calculate_technical_indicators(data)
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(data_with_indicators['bars'])
    
    # Make sure columns are numeric and explicitly convert to float64 (double)
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
    
    # Convert columns to numpy arrays for TA-Lib, explicitly as float64
    open_prices = np.array(df['o'], dtype=np.float64)
    high = np.array(df['h'], dtype=np.float64)
    low = np.array(df['l'], dtype=np.float64)
    close = np.array(df['c'], dtype=np.float64)
    volume = np.array(df['v'], dtype=np.float64)
    
    # Dictionary to store patterns and their success rates
    pattern_analysis = {
        'symbol': symbol,
        'total_bars': len(df),
        'patterns': {}
    }
    
    # Dictionary to store patterns and their success rates
    pattern_analysis = {
        'symbol': symbol,
        'total_bars': len(df),
        'patterns': {}
    }
    
    # Dictionary of bullish patterns to check
    bullish_patterns = {
        'Bullish Engulfing': ta.CDLENGULFING,
        'Hammer': ta.CDLHAMMER,
        'Morning Star': ta.CDLMORNINGSTAR,
        'Three White Soldiers': ta.CDL3WHITESOLDIERS,
        'Bullish Harami': ta.CDLHARAMI,
        'Piercing Line': ta.CDLPIERCING,
        'Bullish Doji Star': ta.CDLDOJISTAR,
        'Dragonfly Doji': ta.CDLDRAGONFLYDOJI,
        'Bullish Kicking': ta.CDLKICKING,
    }
    
    # Bullish indicator combinations to check
    indicator_combinations = [
        {
            'name': 'RSI Oversold Reversal',
            'condition': lambda row: row['rsi'] < 30,
            'confirmation': lambda i, df: df['rsi'].iloc[i+1] > df['rsi'].iloc[i] and df['c'].iloc[i+1] > df['c'].iloc[i]
        },
        {
            'name': 'MACD Bullish Crossover',
            'condition': lambda row: row['macd'] < row['macd_signal'] and row['macd_hist'] > 0,
            'confirmation': lambda i, df: df['macd'].iloc[i] > df['macd_signal'].iloc[i]
        },
        {
            'name': 'Golden Cross (SMA)',
            'condition': lambda row: (row['sma_20'] > row['sma_50']) and (pd.Series(df['sma_20']).shift(1).iloc[i] <= pd.Series(df['sma_50']).shift(1).iloc[i]),
            'confirmation': lambda i, df: df['c'].iloc[i] > df['sma_20'].iloc[i]
        },
        {
            'name': 'Bollinger Band Bounce',
            'condition': lambda row: row['c'] <= row['bb_lower'],
            'confirmation': lambda i, df: df['c'].iloc[i+1] > df['c'].iloc[i] and df['c'].iloc[i+1] > df['bb_lower'].iloc[i]
        },
        {
            'name': 'Stochastic Oversold Reversal',
            'condition': lambda row: 'stoch_k' in row and row['stoch_k'] < 20 and row['stoch_d'] < 20,
            'confirmation': lambda i, df: 'stoch_k' in df.columns and df['stoch_k'].iloc[i+1] > df['stoch_k'].iloc[i] and df['stoch_k'].iloc[i+1] > df['stoch_d'].iloc[i+1]
        }
    ]
    
    # Check candlestick patterns
    for pattern_name, pattern_func in bullish_patterns.items():
        # Apply the TA-Lib pattern function
        pattern_result = pattern_func(open_prices, high, low, close)
        
        # Find all instances where the pattern was detected (positive values for bullish)
        pattern_indices = np.where(pattern_result > 0)[0]
        
        # Skip if no instances found
        if len(pattern_indices) == 0:
            continue
        
        # Track pattern occurrences and success rates
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
            
            # Determine if pattern led to a price increase
            success = price_return > 0
            if success:
                success_count += 1
            
            total_return += price_return
            
            # Record this occurrence
            occurrences.append({
                'date': df['t'].iloc[idx],
                'pattern_price': float(pattern_price),
                'future_price': float(future_price),
                'return': float(price_return),
                'success': success
            })
        
        # Calculate statistics
        if occurrences:
            success_rate = success_count / len(occurrences) * 100
            avg_return = total_return / len(occurrences)
            
            pattern_analysis['patterns'][pattern_name] = {
                'occurrences': len(occurrences),
                'success_rate': float(success_rate),
                'avg_return': float(avg_return),
                'details': occurrences
            }
            
            print(f"  {pattern_name}: {len(occurrences)} occurrences, {success_rate:.1f}% success, {avg_return:.2f}% avg return")
    
    # Check indicator combinations
    for combo in indicator_combinations:
        combo_name = combo['name']
        condition_func = combo['condition']
        confirmation_func = combo['confirmation']
        
        # Convert DataFrame to dict for each row
        occurrences = []
        success_count = 0
        total_return = 0
        
        for i in range(len(df) - threshold_periods):
            row = df.iloc[i].to_dict()
            
            try:
                # Check if this row meets the condition
                if condition_func(row):
                    # Check for confirmation in the next bar if possible
                    if i + 1 < len(df) and confirmation_func(i, df):
                        # Get prices at pattern and after threshold
                        pattern_price = df['c'].iloc[i]
                        future_price = df['c'].iloc[i + threshold_periods]
                        
                        # Calculate return
                        price_return = (future_price - pattern_price) / pattern_price * 100
                        
                        # Determine if pattern led to a price increase
                        success = price_return > 0
                        if success:
                            success_count += 1
                        
                        total_return += price_return
                        
                        # Record this occurrence
                        occurrences.append({
                            'date': df['t'].iloc[i],
                            'pattern_price': float(pattern_price),
                            'future_price': float(future_price),
                            'return': float(price_return),
                            'success': success
                        })
            except (KeyError, IndexError) as e:
                # Skip if required fields are missing
                continue
        
        # Calculate statistics
        if occurrences:
            success_rate = success_count / len(occurrences) * 100
            avg_return = total_return / len(occurrences)
            
            pattern_analysis['patterns'][combo_name] = {
                'occurrences': len(occurrences),
                'success_rate': float(success_rate),
                'avg_return': float(avg_return),
                'details': occurrences
            }
            
            print(f"  {combo_name}: {len(occurrences)} occurrences, {success_rate:.1f}% success, {avg_return:.2f}% avg return")
    
    return pattern_analysis


def identify_bearish_patterns(data, threshold_periods=10):
    """
    Identify bearish patterns in the historical data and check if they led to price decreases.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        threshold_periods (int): Number of periods to check for price decrease after pattern
        
    Returns:
        dict: Analysis of bearish patterns and their success rates
    """
    if not data or 'bars' not in data or not data['bars']:
        return None
    
    symbol = data.get('symbol', 'Unknown')
    print(f"Analyzing bearish patterns for {symbol}...")
    
    # Calculate indicators first
    data_with_indicators = calculate_technical_indicators(data)
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(data_with_indicators['bars'])
    
    # Make sure columns are numeric and explicitly convert to float64 (double)
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
    
    # Convert columns to numpy arrays for TA-Lib, explicitly as float64
    open_prices = np.array(df['o'], dtype=np.float64)
    high = np.array(df['h'], dtype=np.float64)
    low = np.array(df['l'], dtype=np.float64)
    close = np.array(df['c'], dtype=np.float64)
    volume = np.array(df['v'], dtype=np.float64)
    
    # Dictionary to store patterns and their success rates
    pattern_analysis = {
        'symbol': symbol,
        'total_bars': len(df),
        'patterns': {}
    }
    
    # Dictionary of bearish patterns to check
    bearish_patterns = {
        'Bearish Engulfing': ta.CDLENGULFING,
        'Hanging Man': ta.CDLHANGINGMAN,
        'Evening Star': ta.CDLEVENINGSTAR,
        'Three Black Crows': ta.CDL3BLACKCROWS,
        'Bearish Harami': ta.CDLHARAMI,
        'Dark Cloud Cover': ta.CDLDARKCLOUDCOVER,
        'Shooting Star': ta.CDLSHOOTINGSTAR,
        'Bearish Doji Star': ta.CDLDOJISTAR,
        'Gravestone Doji': ta.CDLGRAVESTONEDOJI,
        'Bearish Kicking': ta.CDLKICKING,
    }
    
    # Bearish indicator combinations to check
    indicator_combinations = [
        {
            'name': 'RSI Overbought Reversal',
            'condition': lambda row: row['rsi'] > 70,
            'confirmation': lambda i, df: df['rsi'].iloc[i+1] < df['rsi'].iloc[i] and df['c'].iloc[i+1] < df['c'].iloc[i]
        },
        {
            'name': 'MACD Bearish Crossover',
            'condition': lambda row: row['macd'] > row['macd_signal'] and row['macd_hist'] < 0,
            'confirmation': lambda i, df: df['macd'].iloc[i] < df['macd_signal'].iloc[i]
        },
        {
            'name': 'Death Cross (SMA)',
            'condition': lambda row: (row['sma_20'] < row['sma_50']) and (pd.Series(df['sma_20']).shift(1).iloc[i] >= pd.Series(df['sma_50']).shift(1).iloc[i]),
            'confirmation': lambda i, df: df['c'].iloc[i] < df['sma_20'].iloc[i]
        },
        {
            'name': 'Bollinger Band Breakdown',
            'condition': lambda row: row['c'] >= row['bb_upper'],
            'confirmation': lambda i, df: df['c'].iloc[i+1] < df['c'].iloc[i] and df['c'].iloc[i+1] < df['bb_upper'].iloc[i]
        },
        {
            'name': 'Stochastic Overbought Reversal',
            'condition': lambda row: 'stoch_k' in row and row['stoch_k'] > 80 and row['stoch_d'] > 80,
            'confirmation': lambda i, df: 'stoch_k' in df.columns and df['stoch_k'].iloc[i+1] < df['stoch_k'].iloc[i] and df['stoch_k'].iloc[i+1] < df['stoch_d'].iloc[i+1]
        }
    ]
    
    # Check candlestick patterns
    for pattern_name, pattern_func in bearish_patterns.items():
        # Apply the TA-Lib pattern function
        pattern_result = pattern_func(open_prices, high, low, close)
        
        # Find all instances where the pattern was detected (negative values for bearish)
        pattern_indices = np.where(pattern_result < 0)[0]
        
        # Skip if no instances found
        if len(pattern_indices) == 0:
            continue
        
        # Track pattern occurrences and success rates
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
            
            # Calculate return (negative is good for bearish patterns)
            price_return = (future_price - pattern_price) / pattern_price * 100
            
            # Determine if pattern led to a price decrease
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
                'success': success
            })
        
        # Calculate statistics
        if occurrences:
            success_rate = success_count / len(occurrences) * 100
            avg_return = total_return / len(occurrences)
            
            pattern_analysis['patterns'][pattern_name] = {
                'occurrences': len(occurrences),
                'success_rate': float(success_rate),
                'avg_return': float(avg_return),
                'details': occurrences
            }
            
            print(f"  {pattern_name}: {len(occurrences)} occurrences, {success_rate:.1f}% success, {avg_return:.2f}% avg return")
    
    # Check indicator combinations
    for combo in indicator_combinations:
        combo_name = combo['name']
        condition_func = combo['condition']
        confirmation_func = combo['confirmation']
        
        # Convert DataFrame to dict for each row
        occurrences = []
        success_count = 0
        total_return = 0
        
        for i in range(len(df) - threshold_periods):
            row = df.iloc[i].to_dict()
            
            try:
                # Check if this row meets the condition
                if condition_func(row):
                    # Check for confirmation in the next bar if possible
                    if i + 1 < len(df) and confirmation_func(i, df):
                        # Get prices at pattern and after threshold
                        pattern_price = df['c'].iloc[i]
                        future_price = df['c'].iloc[i + threshold_periods]
                        
                        # Calculate return (negative is good for bearish patterns)
                        price_return = (future_price - pattern_price) / pattern_price * 100
                        
                        # Determine if pattern led to a price decrease
                        success = price_return < 0
                        if success:
                            success_count += 1
                        
                        total_return += price_return
                        
                        # Record this occurrence
                        occurrences.append({
                            'date': df['t'].iloc[i],
                            'pattern_price': float(pattern_price),
                            'future_price': float(future_price),
                            'return': float(price_return),
                            'success': success
                        })
            except (KeyError, IndexError) as e:
                # Skip if required fields are missing
                continue
        
        # Calculate statistics
        if occurrences:
            success_rate = success_count / len(occurrences) * 100
            avg_return = total_return / len(occurrences)
            
            pattern_analysis['patterns'][combo_name] = {
                'occurrences': len(occurrences),
                'success_rate': float(success_rate),
                'avg_return': float(avg_return),
                'details': occurrences
            }
            
            print(f"  {combo_name}: {len(occurrences)} occurrences, {success_rate:.1f}% success, {avg_return:.2f}% avg return")
    
    return pattern_analysis


def visualize_pattern_effectiveness(analysis, pattern_type="bullish"):
    """
    Visualize the effectiveness of patterns.
    
    Args:
        analysis (dict): Pattern analysis data
        pattern_type (str): 'bullish' or 'bearish'
    """
    if not analysis or 'patterns' not in analysis or not analysis['patterns']:
        print(f"No {pattern_type} patterns to visualize")
        return
    
    # Extract pattern names, success rates, and average returns
    pattern_names = []
    success_rates = []
    avg_returns = []
    occurrences = []
    
    for name, data in analysis['patterns'].items():
        pattern_names.append(name)
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
    plt.savefig(f"{symbol}_{pattern_type}_pattern_analysis.png")
    plt.close()
    
    print(f"Saved {pattern_type} pattern visualization to {symbol}_{pattern_type}_pattern_analysis.png")


def run_backtest(symbols=None, periods_to_check=[5, 10, 20], use_existing_data=True):
    """
    Run backtest on symbols.
    
    Args:
        symbols (list): List of symbols to test, or None to use all available
        periods_to_check (list): List of periods to check after pattern
        use_existing_data (bool): Whether to use existing data files or fetch new data
    """
    # Load data
    if symbols:
        data_dict = {}
        for symbol in symbols:
            data = load_historical_data(symbol, use_existing=use_existing_data)
            if data and symbol in data:
                data_dict[symbol] = data[symbol]
    else:
        data_dict = load_historical_data(use_existing=use_existing_data)
    
    # Process each symbol
    for symbol, data in data_dict.items():
        print(f"\nBacktesting {symbol}...")
        
        # For each period to check
        for period in periods_to_check:
            print(f"\nAnalyzing with {period}-day forward period:")
            
            # Analyze bullish patterns
            bullish_analysis = identify_bullish_patterns(data, threshold_periods=period)
            if bullish_analysis:
                # Save to file
                with open(f"{symbol}_bullish_p{period}_analysis.json", "w") as f:
                    json.dump(bullish_analysis, f, indent=2)
                
                # Visualize
                visualize_pattern_effectiveness(bullish_analysis, "bullish")
            
            # Analyze bearish patterns
            bearish_analysis = identify_bearish_patterns(data, threshold_periods=period)
            if bearish_analysis:
                # Save to file
                with open(f"{symbol}_bearish_p{period}_analysis.json", "w") as f:
                    json.dump(bearish_analysis, f, indent=2)
                
                # Visualize
                visualize_pattern_effectiveness(bearish_analysis, "bearish")
        
        print(f"Completed backtest for {symbol}")


if __name__ == "__main__":
    print("TA-Lib Backtest Utility")
    print("======================\n")
    
    # Define symbols to test
    test_symbols = ["AAPL", "MSFT", "AMZN", "TSLA", "GOOGL"]
    
    # Define periods to check after pattern
    periods = [5, 10, 20]  # 5-day, 10-day, and 20-day forward periods
    
    # Run backtest
    run_backtest(symbols=["AAPL"], periods_to_check=periods, use_existing_data=True)
    
    print("\nBacktest completed. Check the output files for results.")