"""
Shared signal visualization module for trading signals project.
This module provides visualization tools that can be used by both
static visualization scripts and interactive web dashboards.
"""
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Import existing project analysis modules
from src.analysis.technical import calculate_technical_indicators, extract_price_summary
from src.analysis.patterns import detect_candlestick_patterns, analyze_trend, analyze_support_resistance
from src.utils.logger import analysis_logger
from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

def load_symbol_data(symbol, interval='1d', period='1y', use_existing=True):
    """
    Load data for a symbol, either from existing files or by fetching new data.
    
    Args:
        symbol (str): Stock symbol to load
        interval (str): Time interval for data (e.g., '1d', '1h')
        period (str): Historical period to fetch (e.g., '1y', '6mo')
        use_existing (bool): Whether to use existing files first
        
    Returns:
        dict: Data dictionary with price bars and metadata
    """
    import glob
    from src.data.yahoo_fetcher import fetch_yahoo_data
    
    data = None
    
    # Try to find existing data files
    if use_existing:
        pattern = os.path.join(RAW_DATA_DIR, f"{symbol}_*.json")
        files = []
        
        if os.path.exists(RAW_DATA_DIR):
            files = glob.glob(pattern)
        
        if files:
            # Sort by modification time (newest first)
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Load the newest file
            with open(files[0], 'r') as f:
                analysis_logger.info(f"Loading existing data from {files[0]}")
                data = json.load(f)
    
    # Fetch new data if needed
    if data is None:
        analysis_logger.info(f"Fetching new data for {symbol}...")
        data = fetch_yahoo_data(symbol, interval=interval, period=period)
    
    return data

def prepare_data_for_visualization(data):
    """
    Process raw data and add technical indicators and patterns for visualization.
    
    Args:
        data (dict): Raw price data dictionary
        
    Returns:
        dict: Enhanced data with indicators and detected patterns
    """
    if not data or 'bars' not in data or not data['bars']:
        analysis_logger.error("No bars in data for visualization")
        return None
    
    # Calculate technical indicators using existing module
    data_with_indicators = calculate_technical_indicators(data)
    
    # Convert to pandas DataFrame for easier processing
    df = pd.DataFrame(data_with_indicators['bars'])
    
    # Make sure datetime information is available
    if 't' in df.columns:
        df['datetime'] = pd.to_datetime(df['t'])
    
    # Detect indicator signals
    signals = detect_signals(df)
    
    # Add signals to the data dictionary
    data_with_indicators['signals'] = signals
    
    # Add patterns to the data dictionary
    patterns = categorize_patterns(df)
    data_with_indicators['patterns'] = patterns
    
    analysis_logger.info(f"Prepared data for {data.get('symbol', 'unknown')} with indicators and patterns")
    return data_with_indicators

def detect_signals(df):
    """
    Detect technical indicator signals from DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price and indicator data
        
    Returns:
        dict: Dictionary of detected signals
    """
    signals = {
        'rsi_oversold': np.zeros(len(df)),
        'rsi_overbought': np.zeros(len(df)),
        'macd_bullish_cross': np.zeros(len(df)),
        'macd_bearish_cross': np.zeros(len(df)),
        'bb_lower_touch': np.zeros(len(df)),
        'bb_upper_touch': np.zeros(len(df)),
        'golden_cross': np.zeros(len(df)),
        'death_cross': np.zeros(len(df)),
        'stoch_oversold': np.zeros(len(df)),
        'stoch_overbought': np.zeros(len(df))
    }
    
    # RSI signals (oversold < 30, overbought > 70)
    if 'rsi' in df.columns:
        signals['rsi_oversold'] = np.where(df['rsi'] < 30, 100, 0)
        signals['rsi_overbought'] = np.where(df['rsi'] > 70, 100, 0)
    
    # MACD cross signals
    if all(col in df.columns for col in ['macd', 'macd_signal']):
        # Bullish cross: MACD crosses above signal line
        signals['macd_bullish_cross'] = np.where(
            (df['macd'].shift(1) < df['macd_signal'].shift(1)) & 
            (df['macd'] > df['macd_signal']),
            100, 0
        )
        
        # Bearish cross: MACD crosses below signal line
        signals['macd_bearish_cross'] = np.where(
            (df['macd'].shift(1) > df['macd_signal'].shift(1)) & 
            (df['macd'] < df['macd_signal']),
            100, 0
        )
    
    # Bollinger Band signals
    if all(col in df.columns for col in ['bb_lower', 'bb_upper']):
        signals['bb_lower_touch'] = np.where(df['l'] <= df['bb_lower'], 100, 0)
        signals['bb_upper_touch'] = np.where(df['h'] >= df['bb_upper'], 100, 0)
    
    # Golden/Death Cross
    if all(col in df.columns for col in ['sma_50', 'sma_200']):
        # Golden Cross: 50-day SMA crosses above 200-day SMA
        signals['golden_cross'] = np.where(
            (df['sma_50'].shift(1) <= df['sma_200'].shift(1)) & 
            (df['sma_50'] > df['sma_200']),
            100, 0
        )
        
        # Death Cross: 50-day SMA crosses below 200-day SMA
        signals['death_cross'] = np.where(
            (df['sma_50'].shift(1) >= df['sma_200'].shift(1)) & 
            (df['sma_50'] < df['sma_200']),
            100, 0
        )
    
    # Stochastic signals
    if all(col in df.columns for col in ['stoch_k', 'stoch_d']):
        signals['stoch_oversold'] = np.where(
            (df['stoch_k'] < 20) & (df['stoch_d'] < 20),
            100, 0
        )
        signals['stoch_overbought'] = np.where(
            (df['stoch_k'] > 80) & (df['stoch_d'] > 80),
            100, 0
        )
    
    # Convert numpy arrays to lists for JSON serialization
    return {k: v.tolist() for k, v in signals.items()}

def categorize_patterns(df):
    """
    Extract and categorize candlestick patterns from DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        
    Returns:
        dict: Dictionary with bullish and bearish patterns
    """
    # Use the existing project's pattern detection function if possible
    # If the DataFrame doesn't already have pattern columns, detect them
    pattern_columns = [col for col in df.columns if 'cdl' in col.lower()]
    
    if not pattern_columns:
        # Use existing pattern detection from your project
        # This assumes we have OHLC data to work with
        try:
            # Extract arrays for TA-Lib
            open_arr = np.array(df['o'], dtype=np.float64)
            high = np.array(df['h'], dtype=np.float64)
            low = np.array(df['l'], dtype=np.float64)
            close = np.array(df['c'], dtype=np.float64)
            
            import talib as ta
            
            # Define pattern functions to check
            bullish_patterns = {
                'bullish_engulfing': ta.CDLENGULFING,
                'hammer': ta.CDLHAMMER,
                'morning_star': ta.CDLMORNINGSTAR,
                'three_white_soldiers': ta.CDL3WHITESOLDIERS,
                'piercing': ta.CDLPIERCING,
                'doji_star': ta.CDLDOJISTAR
            }
            
            bearish_patterns = {
                'bearish_engulfing': lambda o, h, l, c: ta.CDLENGULFING(o, h, l, c) * -1,
                'hanging_man': ta.CDLHANGINGMAN,
                'evening_star': ta.CDLEVENINGSTAR,
                'three_black_crows': ta.CDL3BLACKCROWS,
                'dark_cloud_cover': ta.CDLDARKCLOUDCOVER,
                'shooting_star': ta.CDLSHOOTINGSTAR
            }
            
            patterns_result = {'bullish': {}, 'bearish': {}}
            
            # Detect bullish patterns
            for name, func in bullish_patterns.items():
                result = func(open_arr, high, low, close)
                # Only include bullish signals (value > 0)
                patterns_result['bullish'][name] = result.tolist()
            
            # Detect bearish patterns
            for name, func in bearish_patterns.items():
                result = func(open_arr, high, low, close)
                # Only include bearish signals (value < 0 for some functions)
                patterns_result['bearish'][name] = result.tolist()
                
            return patterns_result
                
        except Exception as e:
            analysis_logger.error(f"Error detecting patterns: {e}")
            return {'bullish': {}, 'bearish': {}}
    else:
        # Patterns are already detected, organize them
        bullish = {}
        bearish = {}
        
        for col in pattern_columns:
            pattern_name = col.lower()
            if 'bull' in pattern_name or any(p in pattern_name for p in ['hammer', 'morn', 'pierc', 'white']):
                bullish[pattern_name] = df[col].tolist()
            else:
                bearish[pattern_name] = df[col].tolist()
        
        return {'bullish': bullish, 'bearish': bearish}

def create_mpl_visualization(data, output_path, show_signals=True, show_volume=True):
    """
    Create a static visualization using matplotlib.
    
    Args:
        data (dict): Processed data with indicators and signals
        output_path (str): Path to save the visualization
        show_signals (bool): Whether to display signal markers
        show_volume (bool): Whether to display volume bars
        
    Returns:
        str: Path to the saved visualization file
    """
    # Convert to DataFrame for easier handling
    df = pd.DataFrame(data['bars'])
    
    # Make sure datetime information is available
    if 't' in df.columns:
        df['datetime'] = pd.to_datetime(df['t'])
    
    # Create figure with two subplots
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    
    # Plot price data
    ax1.plot(df['datetime'], df['c'], label='Close', color='black', linewidth=1.5)
    
    # Plot additional indicators if available
    if 'sma_20' in df.columns:
        ax1.plot(df['datetime'], df['sma_20'], label='SMA 20', color='blue', linewidth=1)
    if 'sma_50' in df.columns:
        ax1.plot(df['datetime'], df['sma_50'], label='SMA 50', color='green', linewidth=1)
    if 'sma_200' in df.columns:
        ax1.plot(df['datetime'], df['sma_200'], label='SMA 200', color='red', linewidth=1)
    if 'ema_12' in df.columns:
        ax1.plot(df['datetime'], df['ema_12'], label='EMA 12', color='purple', linewidth=1, linestyle='--')
    if 'ema_26' in df.columns:
        ax1.plot(df['datetime'], df['ema_26'], label='EMA 26', color='orange', linewidth=1, linestyle='--')
    
    # Plot Bollinger Bands if available
    if all(col in df.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
        ax1.plot(df['datetime'], df['bb_upper'], color='gray', linestyle='-', alpha=0.5)
        ax1.plot(df['datetime'], df['bb_middle'], color='gray', linestyle='--', alpha=0.5)
        ax1.plot(df['datetime'], df['bb_lower'], color='gray', linestyle='-', alpha=0.5)
        ax1.fill_between(df['datetime'], df['bb_upper'], df['bb_lower'], color='gray', alpha=0.1)
    
    # Add signal markers if requested
    if show_signals and 'signals' in data:
        # RSI Signals
        if 'rsi_oversold' in data['signals']:
            oversold_indices = [i for i, val in enumerate(data['signals']['rsi_oversold']) if val > 0]
            if oversold_indices:
                oversold_x = [df['datetime'].iloc[i] for i in oversold_indices]
                oversold_y = [df['l'].iloc[i] * 0.99 for i in oversold_indices]
                ax1.scatter(oversold_x, oversold_y, marker='^', color='green', s=100, alpha=0.7, label='RSI Oversold')
        
        if 'rsi_overbought' in data['signals']:
            overbought_indices = [i for i, val in enumerate(data['signals']['rsi_overbought']) if val > 0]
            if overbought_indices:
                overbought_x = [df['datetime'].iloc[i] for i in overbought_indices]
                overbought_y = [df['h'].iloc[i] * 1.01 for i in overbought_indices]
                ax1.scatter(overbought_x, overbought_y, marker='v', color='red', s=100, alpha=0.7, label='RSI Overbought')
        
        # MACD Signals
        if 'macd_bullish_cross' in data['signals']:
            macd_bull_indices = [i for i, val in enumerate(data['signals']['macd_bullish_cross']) if val > 0]
            if macd_bull_indices:
                macd_bull_x = [df['datetime'].iloc[i] for i in macd_bull_indices]
                macd_bull_y = [df['l'].iloc[i] * 0.98 for i in macd_bull_indices]
                ax1.scatter(macd_bull_x, macd_bull_y, marker='*', color='lime', s=120, alpha=0.7, label='MACD Bullish')
        
        if 'macd_bearish_cross' in data['signals']:
            macd_bear_indices = [i for i, val in enumerate(data['signals']['macd_bearish_cross']) if val > 0]
            if macd_bear_indices:
                macd_bear_x = [df['datetime'].iloc[i] for i in macd_bear_indices]
                macd_bear_y = [df['h'].iloc[i] * 1.02 for i in macd_bear_indices]
                ax1.scatter(macd_bear_x, macd_bear_y, marker='*', color='orange', s=120, alpha=0.7, label='MACD Bearish')
    
    # Plot pattern markers if available
    if 'patterns' in data:
        # Bullish patterns
        if 'bullish' in data['patterns']:
            for pattern_name, pattern_values in data['patterns']['bullish'].items():
                pattern_indices = [i for i, val in enumerate(pattern_values) if val > 0]
                if pattern_indices:
                    pattern_x = [df['datetime'].iloc[i] for i in pattern_indices]
                    pattern_y = [df['l'].iloc[i] * 0.99 for i in pattern_indices]
                    ax1.scatter(pattern_x, pattern_y, marker='^', color='green', s=80, alpha=0.7)
                    for i, idx in enumerate(pattern_indices):
                        ax1.annotate(pattern_name.replace('_', ' '), 
                                   (pattern_x[i], pattern_y[i]),
                                   xytext=(0, -15), textcoords='offset points',
                                   ha='center', va='top', fontsize=8, rotation=45)
        
        # Bearish patterns
        if 'bearish' in data['patterns']:
            for pattern_name, pattern_values in data['patterns']['bearish'].items():
                pattern_indices = [i for i, val in enumerate(pattern_values) if val > 0]
                if pattern_indices:
                    pattern_x = [df['datetime'].iloc[i] for i in pattern_indices]
                    pattern_y = [df['h'].iloc[i] * 1.01 for i in pattern_indices]
                    ax1.scatter(pattern_x, pattern_y, marker='v', color='red', s=80, alpha=0.7)
                    for i, idx in enumerate(pattern_indices):
                        ax1.annotate(pattern_name.replace('_', ' '), 
                                   (pattern_x[i], pattern_y[i]),
                                   xytext=(0, 15), textcoords='offset points',
                                   ha='center', va='bottom', fontsize=8, rotation=45)
    
    # Add volume subplot if requested
    if show_volume and 'v' in df.columns:
        ax2.bar(df['datetime'], df['v'], color='gray', alpha=0.5)
        ax2.set_ylabel('Volume')
    else:
        # If no volume, show RSI instead
        if 'rsi' in df.columns:
            ax2.plot(df['datetime'], df['rsi'], color='purple')
            ax2.axhline(y=70, color='r', linestyle='--', alpha=0.3)
            ax2.axhline(y=30, color='g', linestyle='--', alpha=0.3)
            ax2.set_ylim(0, 100)
            ax2.set_ylabel('RSI')
    
    # Add labels and title
    symbol = data.get('symbol', 'Unknown')
    ax1.set_title(f"{symbol} with Technical Indicators and Signals")
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # Format dates on x-axis
    import matplotlib.dates as mdates
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax1.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    analysis_logger.info(f"Saved visualization to {output_path}")
    return output_path

def prepare_web_visualization_data(data):
    """
    Prepare data structure for web-based visualization (Plotly/Chart.js).
    
    Args:
        data (dict): Processed data with indicators and signals
        
    Returns:
        dict: Formatted data ready for web visualization
    """
    # Make sure we have data to work with
    if not data or 'bars' not in data or not data['bars']:
        return None
    
    df = pd.DataFrame(data['bars'])
    
    # Format data for web visualization
    chart_data = {
        'symbol': data.get('symbol', 'unknown'),
        'datetime': df['t'].tolist() if 't' in df.columns else [],
        'price': {
            'open': df['o'].tolist() if 'o' in df.columns else [],
            'high': df['h'].tolist() if 'h' in df.columns else [],
            'low': df['l'].tolist() if 'l' in df.columns else [],
            'close': df['c'].tolist() if 'c' in df.columns else [],
            'volume': df['v'].tolist() if 'v' in df.columns else []
        },
        'indicators': {}
    }
    
    # Add available indicators
    indicator_columns = [col for col in df.columns if col not in ['t', 'o', 'h', 'l', 'c', 'v', 'datetime']]
    for col in indicator_columns:
        chart_data['indicators'][col] = df[col].tolist()
    
    # Add signals if available
    if 'signals' in data:
        chart_data['signals'] = data['signals']
    
    # Add patterns if available
    if 'patterns' in data:
        chart_data['patterns'] = data['patterns']
    
    # Replace NaN values with None for JSON compatibility
    import math
    
    def replace_nan(obj):
        if isinstance(obj, dict):
            return {k: replace_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_nan(item) for item in obj]
        elif isinstance(obj, float) and math.isnan(obj):
            return None
        else:
            return obj
    
    return replace_nan(chart_data)

class NpEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types."""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NpEncoder, self).default(obj)

def save_visualization_data(data, output_dir, filename_prefix):
    """
    Save visualization data to JSON file.
    
    Args:
        data (dict): Visualization data
        output_dir (str): Directory to save to
        filename_prefix (str): Prefix for the filename
        
    Returns:
        str: Path to the saved file
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to file using custom encoder
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, cls=NpEncoder)
    
    analysis_logger.info(f"Saved visualization data to {filepath}")
    return filepath