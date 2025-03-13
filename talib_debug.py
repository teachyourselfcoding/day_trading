#!/usr/bin/env python3
"""
Simple test script to debug TA-Lib compatibility issues.
"""
import os
import json
import pandas as pd
import numpy as np
import talib as ta
import matplotlib.pyplot as plt

def load_data_file(file_path):
    """Load a JSON data file and return the data."""
    with open(file_path, 'r') as f:
        return json.load(f)

def test_talib_with_file(file_path):
    """Test TA-Lib with a specific data file."""
    print(f"Testing TA-Lib with file: {file_path}")
    
    # Load the data
    data = load_data_file(file_path)
    
    if not data or 'bars' not in data or not data['bars']:
        print("No bars data in file")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(data['bars'])
    
    # Print column names and sample data
    print(f"Columns: {df.columns.tolist()}")
    print(f"Sample data types: {df.dtypes}")
    print(f"First row: {df.iloc[0].to_dict()}")
    
    # Make sure columns are numeric and explicitly convert to float64 (double)
    for col in ['o', 'h', 'l', 'c', 'v']:
        if col in df.columns:
            # Print original values for debugging
            print(f"Original {col} type: {df[col].dtype}")
            print(f"Sample original {col} values: {df[col].head().tolist()}")
            
            # Convert to numeric and ensure float64
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float64)
            
            # Print converted values
            print(f"Converted {col} type: {df[col].dtype}")
            print(f"Sample converted {col} values: {df[col].head().tolist()}")
    
    # Convert columns to numpy arrays for TA-Lib
    try:
        close = np.array(df['c'], dtype=np.float64)
        high = np.array(df['h'], dtype=np.float64)
        low = np.array(df['l'], dtype=np.float64)
        open_prices = np.array(df['o'], dtype=np.float64)
        volume = np.array(df['v'], dtype=np.float64)
        
        print("Arrays created successfully")
        print(f"Close array type: {close.dtype}")
        print(f"Volume array type: {volume.dtype}")
        
        # Try to calculate some basic indicators
        print("Attempting to calculate SMA...")
        sma = ta.SMA(close, timeperiod=5)
        print(f"SMA calculated successfully: {sma[-5:]}")
        
        print("Attempting to calculate OBV...")
        obv = ta.OBV(close, volume)
        print(f"OBV calculated successfully: {obv[-5:]}")
        
        print("Attempting to calculate RSI...")
        rsi = ta.RSI(close, timeperiod=14)
        print(f"RSI calculated successfully: {rsi[-5:]}")
        
        print("Attempting to calculate MACD...")
        macd, macd_signal, macd_hist = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        print(f"MACD calculated successfully")
        
        return True
    
    except Exception as e:
        print(f"Error in TA-Lib calculation: {e}")
        return False

if __name__ == "__main__":
    print("TA-Lib Debug Utility")
    print("===================\n")
    
    # Find JSON files in the raw data directory
    data_dir = "data/raw"  # Adjust this path if needed
    json_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"No JSON files found in {data_dir}")
    else:
        # Test with the first file
        print(f"Found {len(json_files)} JSON files")
        test_file = json_files[0]
        test_talib_with_file(test_file)