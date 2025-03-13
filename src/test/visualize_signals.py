#!/usr/bin/env python3
"""
Visualization tool for verifying trading signals on price charts.
This script loads historical data, applies TA-Lib indicators,
and creates charts that highlight where signals are triggered.
"""
import os
import json
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import glob
from matplotlib.patches import Rectangle

def load_data_file(file_path):
    """Load a JSON data file and return the data."""
    with open(file_path, 'r') as f:
        return json.load(f)

def find_data_files(symbol, data_dir="data/raw"):
    """Find data files for a given symbol."""
    pattern = f"{symbol}_*.json"
    return glob.glob(os.path.join(data_dir, pattern))

def prepare_dataframe(data):
    """Convert data to DataFrame and prepare for analysis."""
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Make sure columns are numeric and explicitly convert to float64
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['t'])
    
    return df

def calculate_indicators(df):
    """Calculate technical indicators using TA-Lib."""
    # Extract arrays for TA-Lib
    close = np.array(df['c'], dtype=np.float64)
    high = np.array(df['h'], dtype=np.float64)
    low = np.array(df['l'], dtype=np.float64)
    open_prices = np.array(df['o'], dtype=np.float64)
    volume = np.array(df['v'], dtype=np.float64)
    
    # Calculate SMA indicators
    df['sma_20'] = ta.SMA(close, timeperiod=20)
    df['sma_50'] = ta.SMA(close, timeperiod=50)
    df['sma_200'] = ta.SMA(close, timeperiod=200)
    
    # Calculate EMA indicators
    df['ema_12'] = ta.EMA(close, timeperiod=12)
    df['ema_26'] = ta.EMA(close, timeperiod=26)
    
    # Calculate MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = ta.MACD(
        close, fastperiod=12, slowperiod=26, signalperiod=9
    )
    
    # Calculate RSI
    df['rsi'] = ta.RSI(close, timeperiod=14)
    
    # Calculate Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(
        close, timeperiod=20, nbdevup=2, nbdevdn=2
    )
    
    # Calculate Stochastic Oscillator
    df['stoch_k'], df['stoch_d'] = ta.STOCH(
        high, low, close, fastk_period=14, slowk_period=3, slowd_period=3
    )
    
    # Calculate ATR
    df['atr'] = ta.ATR(high, low, close, timeperiod=14)
    
    # Calculate ADX
    df['adx'] = ta.ADX(high, low, close, timeperiod=14)
    
    # On-Balance Volume
    df['obv'] = ta.OBV(close, volume)
    
    return df

def detect_candlestick_patterns(df):
    """Detect candlestick patterns using TA-Lib."""
    # Extract arrays for TA-Lib
    open_arr = np.array(df['o'], dtype=np.float64)
    high = np.array(df['h'], dtype=np.float64)
    low = np.array(df['l'], dtype=np.float64)
    close = np.array(df['c'], dtype=np.float64)
    
    # Dictionary to store pattern results
    patterns = {}
    
    # Bullish patterns
    patterns['bullish_engulfing'] = ta.CDLENGULFING(open_arr, high, low, close)
    patterns['hammer'] = ta.CDLHAMMER(open_arr, high, low, close)
    patterns['morning_star'] = ta.CDLMORNINGSTAR(open_arr, high, low, close)
    patterns['three_white_soldiers'] = ta.CDL3WHITESOLDIERS(open_arr, high, low, close)
    patterns['piercing'] = ta.CDLPIERCING(open_arr, high, low, close)
    patterns['doji_star'] = ta.CDLDOJISTAR(open_arr, high, low, close)
    
    # Bearish patterns
    patterns['bearish_engulfing'] = ta.CDLENGULFING(open_arr, high, low, close) * -1  # Reverse sign to identify bearish
    patterns['hanging_man'] = ta.CDLHANGINGMAN(open_arr, high, low, close)
    patterns['evening_star'] = ta.CDLEVENINGSTAR(open_arr, high, low, close)
    patterns['three_black_crows'] = ta.CDL3BLACKCROWS(open_arr, high, low, close)
    patterns['dark_cloud_cover'] = ta.CDLDARKCLOUDCOVER(open_arr, high, low, close)
    patterns['shooting_star'] = ta.CDLSHOOTINGSTAR(open_arr, high, low, close)
    
    # Add pattern columns to the dataframe
    for pattern_name, pattern_values in patterns.items():
        df[pattern_name] = pattern_values
    
    return df

def detect_indicator_signals(df):
    """Detect technical indicator signals."""
    # Initialize columns for signals
    df['rsi_oversold'] = 0
    df['rsi_overbought'] = 0
    df['macd_bullish_cross'] = 0
    df['macd_bearish_cross'] = 0
    df['bb_lower_touch'] = 0
    df['bb_upper_touch'] = 0
    df['golden_cross'] = 0
    df['death_cross'] = 0
    df['stoch_oversold'] = 0
    df['stoch_overbought'] = 0
    
    # RSI signals (oversold < 30, overbought > 70)
    df.loc[df['rsi'] < 30, 'rsi_oversold'] = 100
    df.loc[df['rsi'] > 70, 'rsi_overbought'] = 100
    
    # MACD cross signals
    # Previous MACD below signal line, current MACD above signal line = bullish cross
    df['macd_bullish_cross'] = np.where(
        (df['macd'].shift(1) < df['macd_signal'].shift(1)) & 
        (df['macd'] > df['macd_signal']),
        100, 0
    )
    
    # Previous MACD above signal line, current MACD below signal line = bearish cross
    df['macd_bearish_cross'] = np.where(
        (df['macd'].shift(1) > df['macd_signal'].shift(1)) & 
        (df['macd'] < df['macd_signal']),
        100, 0
    )
    
    # Bollinger Band signals
    df['bb_lower_touch'] = np.where(df['l'] <= df['bb_lower'], 100, 0)
    df['bb_upper_touch'] = np.where(df['h'] >= df['bb_upper'], 100, 0)
    
    # Golden Cross (SMA 50 crosses above SMA 200)
    df['golden_cross'] = np.where(
        (df['sma_50'].shift(1) <= df['sma_200'].shift(1)) & 
        (df['sma_50'] > df['sma_200']),
        100, 0
    )
    
    # Death Cross (SMA 50 crosses below SMA 200)
    df['death_cross'] = np.where(
        (df['sma_50'].shift(1) >= df['sma_200'].shift(1)) & 
        (df['sma_50'] < df['sma_200']),
        100, 0
    )
    
    # Stochastic signals
    df['stoch_oversold'] = np.where(
        (df['stoch_k'] < 20) & (df['stoch_d'] < 20),
        100, 0
    )
    
    df['stoch_overbought'] = np.where(
        (df['stoch_k'] > 80) & (df['stoch_d'] > 80),
        100, 0
    )
    
    return df

def plot_price_with_signals(df, symbol, output_dir="signal_charts"):
    """Create a chart with price and indicators, highlighting signals."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a figure with subplots
    fig = plt.figure(figsize=(18, 12))
    
    # Define grid for subplots
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.1)
    
    # Price chart with signals
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    
    # Plot price data
    ax1.plot(df['datetime'], df['c'], label='Close', color='black', linewidth=1.5)
    
    # Plot moving averages
    if 'sma_20' in df.columns and not df['sma_20'].isna().all():
        ax1.plot(df['datetime'], df['sma_20'], label='SMA 20', color='blue', linewidth=1)
    if 'sma_50' in df.columns and not df['sma_50'].isna().all():
        ax1.plot(df['datetime'], df['sma_50'], label='SMA 50', color='green', linewidth=1)
    if 'ema_12' in df.columns and not df['ema_12'].isna().all():
        ax1.plot(df['datetime'], df['ema_12'], label='EMA 12', color='orange', linewidth=1, linestyle='--')
    if 'ema_26' in df.columns and not df['ema_26'].isna().all():
        ax1.plot(df['datetime'], df['ema_26'], label='EMA 26', color='purple', linewidth=1, linestyle='--')
    
    # Plot Bollinger Bands
    if 'bb_upper' in df.columns and not df['bb_upper'].isna().all():
        ax1.plot(df['datetime'], df['bb_upper'], color='gray', linewidth=1, linestyle='-', alpha=0.7)
        ax1.plot(df['datetime'], df['bb_lower'], color='gray', linewidth=1, linestyle='-', alpha=0.7)
        ax1.fill_between(df['datetime'], df['bb_upper'], df['bb_lower'], color='gray', alpha=0.1)
    
    # Plot candlestick patterns (bullish)
    bullish_patterns = ['bullish_engulfing', 'hammer', 'morning_star', 'three_white_soldiers', 'piercing', 'doji_star']
    for pattern in bullish_patterns:
        if pattern in df.columns:
            # Find where pattern is detected (value > 0)
            pattern_indices = df[df[pattern] > 0].index
            for idx in pattern_indices:
                # Mark the pattern on the chart
                ax1.scatter(df['datetime'].iloc[idx], df['l'].iloc[idx] * 0.99, marker='^', color='green', s=100, alpha=0.7)
                # Add pattern name as text
                ax1.text(df['datetime'].iloc[idx], df['l'].iloc[idx] * 0.98, pattern.replace('_', ' '), 
                         fontsize=8, color='green', ha='center', rotation=45)
    
    # Plot candlestick patterns (bearish)
    bearish_patterns = ['bearish_engulfing', 'hanging_man', 'evening_star', 'three_black_crows', 'dark_cloud_cover', 'shooting_star']
    for pattern in bearish_patterns:
        if pattern in df.columns:
            # Find where pattern is detected (value > 0)
            pattern_indices = df[df[pattern] > 0].index
            for idx in pattern_indices:
                # Mark the pattern on the chart
                ax1.scatter(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.01, marker='v', color='red', s=100, alpha=0.7)
                # Add pattern name as text
                ax1.text(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.02, pattern.replace('_', ' '), 
                         fontsize=8, color='red', ha='center', rotation=45)
    
    # Plot indicator signals
    # RSI signals
    if 'rsi_oversold' in df.columns:
        oversold_indices = df[df['rsi_oversold'] > 0].index
        for idx in oversold_indices:
            ax1.scatter(df['datetime'].iloc[idx], df['l'].iloc[idx] * 0.99, marker='*', color='blue', s=150, alpha=0.7)
            ax1.text(df['datetime'].iloc[idx], df['l'].iloc[idx] * 0.98, 'RSI Oversold', 
                     fontsize=8, color='blue', ha='center')
    
    if 'rsi_overbought' in df.columns:
        overbought_indices = df[df['rsi_overbought'] > 0].index
        for idx in overbought_indices:
            ax1.scatter(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.01, marker='*', color='purple', s=150, alpha=0.7)
            ax1.text(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.02, 'RSI Overbought', 
                     fontsize=8, color='purple', ha='center')
    
    # MACD signals
    if 'macd_bullish_cross' in df.columns:
        bullish_cross_indices = df[df['macd_bullish_cross'] > 0].index
        for idx in bullish_cross_indices:
            ax1.scatter(df['datetime'].iloc[idx], df['l'].iloc[idx] * 0.99, marker='o', color='lime', s=120, alpha=0.7)
            ax1.text(df['datetime'].iloc[idx], df['l'].iloc[idx] * 0.98, 'MACD Bullish', 
                     fontsize=8, color='lime', ha='center')
    
    if 'macd_bearish_cross' in df.columns:
        bearish_cross_indices = df[df['macd_bearish_cross'] > 0].index
        for idx in bearish_cross_indices:
            ax1.scatter(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.01, marker='o', color='orange', s=120, alpha=0.7)
            ax1.text(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.02, 'MACD Bearish', 
                     fontsize=8, color='orange', ha='center')
    
    # Golden/Death Cross signals
    if 'golden_cross' in df.columns:
        golden_indices = df[df['golden_cross'] > 0].index
        for idx in golden_indices:
            ax1.axvline(x=df['datetime'].iloc[idx], color='gold', linestyle='--', alpha=0.5)
            ax1.text(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.05, 'Golden Cross', 
                     fontsize=10, color='gold', ha='center')
    
    if 'death_cross' in df.columns:
        death_indices = df[df['death_cross'] > 0].index
        for idx in death_indices:
            ax1.axvline(x=df['datetime'].iloc[idx], color='black', linestyle='--', alpha=0.5)
            ax1.text(df['datetime'].iloc[idx], df['h'].iloc[idx] * 1.05, 'Death Cross', 
                     fontsize=10, color='black', ha='center')
    
    # Add RSI in subplot
    if 'rsi' in df.columns:
        ax2.plot(df['datetime'], df['rsi'], color='purple', linewidth=1)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.3)
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.3)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('RSI')
        ax2.grid(True, alpha=0.3)
    
    # Add MACD in subplot
    if 'macd' in df.columns and 'macd_signal' in df.columns and 'macd_hist' in df.columns:
        ax3.plot(df['datetime'], df['macd'], color='blue', linewidth=1, label='MACD')
        ax3.plot(df['datetime'], df['macd_signal'], color='red', linewidth=1, label='Signal')
        
        # Color MACD histogram based on positive/negative values
        pos = df['macd_hist'] > 0
        neg = df['macd_hist'] <= 0
        
        if not pos.empty and any(pos):
            ax3.bar(df.loc[pos, 'datetime'], df.loc[pos, 'macd_hist'], color='green', alpha=0.5, width=0.7)
        if not neg.empty and any(neg):
            ax3.bar(df.loc[neg, 'datetime'], df.loc[neg, 'macd_hist'], color='red', alpha=0.5, width=0.7)
            
        ax3.set_ylabel('MACD')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='k', linestyle='-', alpha=0.2)
    
    # Add titles and labels
    ax1.set_title(f"{symbol} with Technical Indicators and Signals", fontsize=16)
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # Format x-axis to show dates clearly
    plt.gcf().autofmt_xdate()
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax1.xaxis.set_major_formatter(date_format)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    output_file = os.path.join(output_dir, f"{symbol}_signals.png")
    plt.savefig(output_file, dpi=150)
    print(f"Chart saved to {output_file}")
    
    # Close the figure to free memory
    plt.close()
    
    return output_file

def process_symbol(symbol, data_dir="data/raw", output_dir="signal_charts"):
    """Process a symbol to detect and visualize signals."""
    print(f"Processing {symbol}...")
    
    # Find data files
    files = find_data_files(symbol, data_dir)
    
    if not files:
        print(f"No data files found for {symbol}")
        return None
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Load the newest file
    data = load_data_file(files[0])
    print(f"Loaded data from {files[0]}")
    
    # Prepare data
    df = prepare_dataframe(data)
    print(f"Prepared dataframe with {len(df)} rows")
    
    # Calculate indicators
    df = calculate_indicators(df)
    print("Calculated technical indicators")
    
    # Detect candlestick patterns
    df = detect_candlestick_patterns(df)
    print("Detected candlestick patterns")
    
    # Detect indicator signals
    df = detect_indicator_signals(df)
    print("Detected indicator signals")
    
    # Create visualization
    chart_path = plot_price_with_signals(df, symbol, output_dir)
    print(f"Created visualization at {chart_path}")
    
    return chart_path

if __name__ == "__main__":
    print("Technical Indicator Signal Visualization Tool")
    print("============================================\n")
    
    # Define symbols to process
    symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
    
    # Process each symbol
    for symbol in symbols:
        process_symbol(symbol)
    
    print("\nVisualization completed. Check the signal_charts directory for results.")