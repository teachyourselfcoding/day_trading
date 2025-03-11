"""
File utilities for managing data storage and retrieval.
"""
import os
import json
from datetime import datetime
from src.utils.config import DIRS_TO_CREATE

def create_directories():
    """Create the necessary directory structure for the project."""
    for directory in DIRS_TO_CREATE:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def save_to_json(data, directory, filename_prefix, include_timestamp=True):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        directory: Directory to save to
        filename_prefix: Prefix for the filename
        include_timestamp: Whether to include a timestamp in the filename
    
    Returns:
        str: Path to the saved file
    """
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate filename with timestamp if needed
    if include_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.json"
    else:
        filename = f"{filename_prefix}.json"
    
    filepath = os.path.join(directory, filename)
    
    # Save the data
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath

def load_from_json(filepath):
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
    
    Returns:
        The loaded data or None if the file doesn't exist
    """
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return data

def get_latest_file(directory, prefix=None, extension='.json'):
    """
    Get the latest file in a directory with an optional prefix and extension.
    
    Args:
        directory: Directory to search in
        prefix: Prefix to filter by (optional)
        extension: File extension to filter by
    
    Returns:
        str: Path to the latest file or None if no files found
    """
    if not os.path.exists(directory):
        return None
    
    files = os.listdir(directory)
    
    # Filter by prefix and extension
    if prefix:
        files = [f for f in files if f.startswith(prefix) and f.endswith(extension)]
    else:
        files = [f for f in files if f.endswith(extension)]
    
    if not files:
        return None
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
    
    return os.path.join(directory, files[0])

def list_signals(directory, symbol=None):
    """
    List all signal files for a symbol or all symbols.
    
    Args:
        directory: Directory to search in
        symbol: Symbol to filter by (optional)
    
    Returns:
        list: List of signal files
    """
    if not os.path.exists(directory):
        return []
    
    files = os.listdir(directory)
    
    # Filter by symbol if provided
    if symbol:
        files = [f for f in files if f.startswith(f"{symbol}_signal")]
    else:
        files = [f for f in files if "_signal_" in f]
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
    
    return [os.path.join(directory, f) for f in files]