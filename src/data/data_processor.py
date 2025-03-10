"""
Data processing module for handling and preparing market data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.utils.config import PROCESSED_DATA_DIR
from src.utils.file_utils import save_to_json
from src.utils.logger import data_logger

def resample_data(data, target_interval):
    """
    Resample data to a different interval.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        target_interval (str): Target interval (e.g., '5Min', '15Min', '1H', '1D')
    
    Returns:
        dict: Resampled data
    """
    if not data or 'bars' not in data or not data['bars']:
        data_logger.error("No bars in data for resampling")
        return data
    
    symbol = data['symbol']
    data_logger.info(f"Resampling data for {symbol} to {target_interval}")
    
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['t'])
    df.set_index('datetime', inplace=True)
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Map interval string to pandas offset string
    interval_map = {
        '1Min': '1min',
        '5Min': '5min',
        '15Min': '15min',
        '30Min': '30min',
        '1H': '1H',
        '4H': '4H',
        '1D': '1D'
    }
    
    pandas_interval = interval_map.get(target_interval, '5min')
    
    # Resample data
    resampled = pd.DataFrame()
    resampled['o'] = df['o'].resample(pandas_interval).first()
    resampled['h'] = df['h'].resample(pandas_interval).max()
    resampled['l'] = df['l'].resample(pandas_interval).min()
    resampled['c'] = df['c'].resample(pandas_interval).last()
    resampled['v'] = df['v'].resample(pandas_interval).sum()
    
    # Drop rows with NaN values
    resampled.dropna(inplace=True)
    
    # Reset index and convert datetime back to string
    resampled.reset_index(inplace=True)
    resampled['t'] = resampled['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    resampled.drop('datetime', axis=1, inplace=True)
    
    # Convert to dictionary
    resampled_data = {
        'bars': resampled.to_dict('records'),
        'symbol': symbol,
        'metadata': {
            'interval': target_interval,
            'original_interval': data.get('metadata', {}).get('interval', 'unknown'),
            'resampled_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    }
    
    # Save resampled data
    file_path = save_to_json(
        resampled_data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_{target_interval}_resampled"
    )
    data_logger.info(f"Saved resampled data to {file_path}")
    
    return resampled_data

def filter_market_hours(data, market_open='09:30:00', market_close='16:00:00', timezone='US/Eastern'):
    """
    Filter data to include only market hours.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        market_open (str): Market open time (HH:MM:SS)
        market_close (str): Market close time (HH:MM:SS)
        timezone (str): Timezone for market hours
    
    Returns:
        dict: Filtered data
    """
    if not data or 'bars' not in data or not data['bars']:
        data_logger.error("No bars in data for filtering market hours")
        return data
    
    symbol = data['symbol']
    data_logger.info(f"Filtering market hours for {symbol}")
    
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['t'])
    
    # Extract time component
    df['time'] = df['datetime'].dt.strftime('%H:%M:%S')
    
    # Filter by market hours
    filtered_df = df[(df['time'] >= market_open) & (df['time'] <= market_close)]
    
    # Drop temporary columns
    filtered_df.drop(['datetime', 'time'], axis=1, inplace=True)
    
    # Check if we have data left
    if filtered_df.empty:
        data_logger.warning(f"No data left after filtering market hours for {symbol}")
        return data
    
    # Convert to dictionary
    filtered_data = {
        'bars': filtered_df.to_dict('records'),
        'symbol': symbol,
        'metadata': {
            'interval': data.get('metadata', {}).get('interval', 'unknown'),
            'market_hours_only': True,
            'market_open': market_open,
            'market_close': market_close,
            'filtered_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    }
    
    # Save filtered data
    file_path = save_to_json(
        filtered_data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_market_hours_only"
    )
    data_logger.info(f"Saved market hours filtered data to {file_path}")
    
    return filtered_data

def merge_data_sources(data_list, symbol):
    """
    Merge data from multiple sources for the same symbol.
    
    Args:
        data_list (list): List of data dictionaries with 'bars' key
        symbol (str): Symbol to merge data for
    
    Returns:
        dict: Merged data
    """
    if not data_list:
        data_logger.error("No data sources to merge")
        return None
    
    data_logger.info(f"Merging {len(data_list)} data sources for {symbol}")
    
    # Combine all bars
    all_bars = []
    for data in data_list:
        if 'bars' in data and data['bars']:
            all_bars.extend(data['bars'])
    
    if not all_bars:
        data_logger.error(f"No bars found in any data source for {symbol}")
        return None
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(all_bars)
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['t'])
    
    # Sort by datetime
    df.sort_values('datetime', inplace=True)
    
    # Remove duplicates based on timestamp
    df.drop_duplicates(subset=['datetime'], keep='first', inplace=True)
    
    # Convert datetime back to string
    df['t'] = df['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    df.drop('datetime', axis=1, inplace=True)
    
    # Convert to dictionary
    merged_data = {
        'bars': df.to_dict('records'),
        'symbol': symbol,
        'metadata': {
            'merged_sources': len(data_list),
            'merged_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    }
    
    # Save merged data
    file_path = save_to_json(
        merged_data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_merged"
    )
    data_logger.info(f"Saved merged data to {file_path}")
    
    return merged_data

def fill_missing_data(data, method='linear'):
    """
    Fill missing data points in a time series.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        method (str): Interpolation method ('linear', 'ffill', 'bfill')
    
    Returns:
        dict: Data with missing points filled
    """
    if not data or 'bars' not in data or not data['bars']:
        data_logger.error("No bars in data for filling missing points")
        return data
    
    symbol = data['symbol']
    data_logger.info(f"Filling missing data points for {symbol} using {method} method")
    
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['t'])
    df.set_index('datetime', inplace=True)
    
    # Make sure columns are numeric
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])
    
    # Determine the interval
    if len(df) > 1:
        time_diffs = df.index.to_series().diff().dropna()
        most_common_diff = time_diffs.mode()[0]
        interval = most_common_diff
    else:
        data_logger.warning(f"Not enough data points to determine interval for {symbol}")
        return data
    
    # Create a full date range
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=interval)
    
    # Reindex to include all time points
    df_reindexed = df.reindex(full_range)
    
    # Fill missing values
    if method == 'ffill':
        df_filled = df_reindexed.fillna(method='ffill')
    elif method == 'bfill':
        df_filled = df_reindexed.fillna(method='bfill')
    else:  # Linear interpolation (default)
        df_filled = df_reindexed.interpolate(method='linear')
    
    # For volume, use 0 for missing values instead of interpolation
    if 'v' in df_filled.columns:
        df_filled['v'] = df_filled['v'].fillna(0)
    
    # Reset index and convert datetime back to string
    df_filled.reset_index(inplace=True)
    df_filled['t'] = df_filled['index'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    df_filled.drop('index', axis=1, inplace=True)
    
    # Convert to dictionary
    filled_data = {
        'bars': df_filled.to_dict('records'),
        'symbol': symbol,
        'metadata': {
            'interval': data.get('metadata', {}).get('interval', 'unknown'),
            'fill_method': method,
            'filled_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    }
    
    # Save filled data
    file_path = save_to_json(
        filled_data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_{method}_filled"
    )
    data_logger.info(f"Saved filled data to {file_path}")
    
    return filled_data

def normalize_volume(data, method='z-score'):
    """
    Normalize volume data to make it comparable across different symbols.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        method (str): Normalization method ('z-score', 'min-max', 'log')
    
    Returns:
        dict: Data with normalized volume
    """
    if not data or 'bars' not in data or not data['bars']:
        data_logger.error("No bars in data for volume normalization")
        return data
    
    symbol = data['symbol']
    data_logger.info(f"Normalizing volume for {symbol} using {method} method")
    
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Make sure volume is numeric
    df['v'] = pd.to_numeric(df['v'])
    
    # Apply normalization
    if method == 'z-score':
        mean_vol = df['v'].mean()
        std_vol = df['v'].std()
        if std_vol > 0:  # Avoid division by zero
            df['v_normalized'] = (df['v'] - mean_vol) / std_vol
        else:
            df['v_normalized'] = 0
    elif method == 'min-max':
        min_vol = df['v'].min()
        max_vol = df['v'].max()
        if max_vol > min_vol:  # Avoid division by zero
            df['v_normalized'] = (df['v'] - min_vol) / (max_vol - min_vol)
        else:
            df['v_normalized'] = 0
    elif method == 'log':
        # Add 1 to avoid log(0)
        df['v_normalized'] = np.log1p(df['v'])
    else:
        data_logger.warning(f"Unknown normalization method: {method}")
        return data
    
    # Keep the original volume
    df['v_original'] = df['v']
    
    # Replace volume with normalized volume
    df['v'] = df['v_normalized']
    
    # Drop the temporary column
    df.drop('v_normalized', axis=1, inplace=True)
    
    # Convert to dictionary
    normalized_data = {
        'bars': df.to_dict('records'),
        'symbol': symbol,
        'metadata': {
            'interval': data.get('metadata', {}).get('interval', 'unknown'),
            'volume_normalization': method,
            'normalized_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    }
    
    # Save normalized data
    file_path = save_to_json(
        normalized_data, 
        PROCESSED_DATA_DIR, 
        f"{symbol}_{method}_normalized"
    )
    data_logger.info(f"Saved volume normalized data to {file_path}")
    
    return normalized_data