"""
Alpaca trading execution module.
"""
import os
import time
import requests
from datetime import datetime

from src.utils.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, RISK_PER_TRADE
from src.utils.logger import execution_logger

# Determine if we're using paper trading or live trading
PAPER_TRADING = True  # Set to False for live trading

ALPACA_BASE_URL = "https://paper-api.alpaca.markets" if PAPER_TRADING else "https://api.alpaca.markets"

# Set up headers for Alpaca API
HEADERS = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

def check_account_status():
    """
    Check the status of the Alpaca trading account.
    
    Returns:
        dict: Account information or None if error
    """
    url = f"{ALPACA_BASE_URL}/v2/account"
    
    try:
        execution_logger.info("Checking Alpaca account status")
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            account_info = response.json()
            
            execution_logger.info(f"Account ID: {account_info.get('id')}")
            execution_logger.info(f"Account Status: {account_info.get('status')}")
            execution_logger.info(f"Portfolio Value: ${account_info.get('portfolio_value')}")
            execution_logger.info(f"Buying Power: ${account_info.get('buying_power')}")
            
            return account_info
        else:
            execution_logger.error(f"Error checking account: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception checking account: {e}")
        return None

def get_positions():
    """
    Get current positions in the account.
    
    Returns:
        list: Current positions or None if error
    """
    url = f"{ALPACA_BASE_URL}/v2/positions"
    
    try:
        execution_logger.info("Getting current positions")
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            positions = response.json()
            
            if positions:
                execution_logger.info(f"Found {len(positions)} open positions")
                
                for position in positions:
                    symbol = position.get('symbol')
                    qty = position.get('qty')
                    entry_price = position.get('avg_entry_price')
                    current_price = position.get('current_price')
                    unrealized_pl = position.get('unrealized_pl')
                    unrealized_plpc = position.get('unrealized_plpc')
                    
                    execution_logger.info(f"{symbol}: {qty} shares @ ${entry_price} (P&L: ${unrealized_pl})")
            else:
                execution_logger.info("No open positions found")
            
            return positions
        else:
            execution_logger.error(f"Error getting positions: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception getting positions: {e}")
        return None

def get_open_orders():
    """
    Get open orders in the account.
    
    Returns:
        list: Open orders or None if error
    """
    url = f"{ALPACA_BASE_URL}/v2/orders"
    params = {
        'status': 'open'
    }
    
    try:
        execution_logger.info("Getting open orders")
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            orders = response.json()
            
            if orders:
                execution_logger.info(f"Found {len(orders)} open orders")
                
                for order in orders:
                    order_id = order.get('id')
                    symbol = order.get('symbol')
                    side = order.get('side')
                    qty = order.get('qty')
                    order_type = order.get('type')
                    
                    execution_logger.info(f"Order {order_id}: {side.upper()} {qty} {symbol} ({order_type.upper()})")
            else:
                execution_logger.info("No open orders found")
            
            return orders
        else:
            execution_logger.error(f"Error getting orders: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception getting orders: {e}")
        return None

def place_order(symbol, qty, side, order_type='market', time_in_force='day', 
                limit_price=None, stop_price=None, take_profit=None, stop_loss=None):
    """
    Place an order with Alpaca.
    
    Args:
        symbol (str): Symbol to trade
        qty (float): Quantity to trade
        side (str): 'buy' or 'sell'
        order_type (str): 'market', 'limit', 'stop', 'stop_limit'
        time_in_force (str): 'day', 'gtc', 'opg', 'cls', 'ioc', 'fok'
        limit_price (float): Limit price for limit and stop-limit orders
        stop_price (float): Stop price for stop and stop-limit orders
        take_profit (dict): Take profit details (e.g. {'limit_price': 123.45})
        stop_loss (dict): Stop loss details (e.g. {'stop_price': 123.45, 'limit_price': 123.45})
    
    Returns:
        dict: Order details or None if error
    """
    url = f"{ALPACA_BASE_URL}/v2/orders"
    
    # Prepare order data
    order_data = {
        'symbol': symbol,
        'qty': str(qty),
        'side': side,
        'type': order_type,
        'time_in_force': time_in_force
    }
    
    # Add optional parameters if provided
    if limit_price is not None and order_type in ['limit', 'stop_limit']:
        order_data['limit_price'] = str(limit_price)
    
    if stop_price is not None and order_type in ['stop', 'stop_limit']:
        order_data['stop_price'] = str(stop_price)
    
    # Add brackets if provided
    if take_profit is not None:
        order_data['take_profit'] = take_profit
    
    if stop_loss is not None:
        order_data['stop_loss'] = stop_loss
    
    try:
        execution_logger.info(f"Placing {side.upper()} order for {qty} {symbol} ({order_type.upper()})")
        
        if limit_price is not None:
            execution_logger.info(f"Limit Price: ${limit_price}")
        
        if stop_price is not None:
            execution_logger.info(f"Stop Price: ${stop_price}")
        
        if take_profit is not None:
            execution_logger.info(f"Take Profit: ${take_profit.get('limit_price')}")
        
        if stop_loss is not None:
            execution_logger.info(f"Stop Loss: ${stop_loss.get('stop_price')}")
        
        response = requests.post(url, headers=HEADERS, json=order_data)
        
        if response.status_code == 200:
            order = response.json()
            
            execution_logger.info(f"Order placed successfully!")
            execution_logger.info(f"Order ID: {order.get('id')}")
            execution_logger.info(f"Status: {order.get('status')}")
            
            return order
        else:
            execution_logger.error(f"Error placing order: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception placing order: {e}")
        return None

def execute_trading_signal(signal, symbol, risk_percentage=RISK_PER_TRADE):
    """
    Execute a trading signal by placing an order with Alpaca.
    
    Args:
        signal (dict): Trading signal
        symbol (str): Symbol to trade
        risk_percentage (float): Percentage of portfolio to risk per trade
    
    Returns:
        dict: Order details or None if error
    """
    try:
        execution_logger.info(f"Executing trading signal for {symbol}")
        
        # Extract key information from the signal
        action = signal.get('suggested_action', '').lower()
        
        # Skip if no action or hold
        if not action or action == 'hold':
            execution_logger.info(f"No action needed for {symbol} (Signal: {action})")
            return None
        
        # Convert price targets to float
        entry_price = None
        stop_loss_price = None
        take_profit_price = None
        
        try:
            entry_price_str = signal.get('entry_price', '')
            if entry_price_str and isinstance(entry_price_str, str):
                entry_price = float(entry_price_str.replace('$', '').strip())
            
            stop_loss_str = signal.get('stop_loss', '')
            if stop_loss_str and isinstance(stop_loss_str, str):
                stop_loss_price = float(stop_loss_str.replace('$', '').strip())
            
            take_profit_str = signal.get('take_profit', '')
            if take_profit_str and isinstance(take_profit_str, str):
                take_profit_price = float(take_profit_str.replace('$', '').strip())
        except ValueError as e:
            execution_logger.error(f"Error converting price targets to float: {e}")
            # Continue with None values if conversion fails
        
        # Get account information for risk management
        account = check_account_status()
        
        if not account:
            execution_logger.error("Could not get account information. Aborting trade.")
            return None
        
        portfolio_value = float(account.get('portfolio_value', 0))
        risk_amount = portfolio_value * risk_percentage
        
        # Get current price if entry price is not specified
        if not entry_price:
            # Fetch the latest quote
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 200:
                quote = response.json()
                if 'quote' in quote:
                    bid_price = float(quote['quote'].get('bp', 0))
                    ask_price = float(quote['quote'].get('ap', 0))
                    
                    if bid_price > 0 and ask_price > 0:
                        entry_price = (bid_price + ask_price) / 2
                        execution_logger.info(f"Using current market price: ${entry_price:.2f}")
            
            if not entry_price:
                execution_logger.error(f"Could not determine entry price for {symbol}. Aborting trade.")
                return None
        
        # Calculate stop loss if not provided
        if not stop_loss_price:
            if action == 'buy':
                stop_loss_price = entry_price * 0.95  # 5% below entry for long positions
            else:
                stop_loss_price = entry_price * 1.05  # 5% above entry for short positions
            execution_logger.info(f"Using calculated stop loss: ${stop_loss_price:.2f}")
        
        # Calculate take profit if not provided
        if not take_profit_price:
            if action == 'buy':
                take_profit_price = entry_price * 1.15  # 15% above entry for long positions
            else:
                take_profit_price = entry_price * 0.85  # 15% below entry for short positions
            execution_logger.info(f"Using calculated take profit: ${take_profit_price:.2f}")
        
        # Calculate position size based on risk
        if action == 'buy':
            risk_per_share = entry_price - stop_loss_price
        else:
            risk_per_share = stop_loss_price - entry_price
        
        if risk_per_share <= 0:
            execution_logger.error(f"Invalid risk calculation for {symbol}. Entry: ${entry_price}, Stop: ${stop_loss_price}")
            return None
        
        # Calculate number of shares based on risk
        qty = int(risk_amount / risk_per_share)
        
        if qty <= 0:
            execution_logger.warning(f"Calculated quantity is too small for {symbol}. Using minimum quantity of 1.")
            qty = 1
        
        execution_logger.info(f"Position size: {qty} shares (risking ${risk_amount:.2f})")
        
        # Prepare take profit and stop loss orders
        take_profit_order = {
            'limit_price': str(take_profit_price)
        }
        
        stop_loss_order = {
            'stop_price': str(stop_loss_price)
        }
        
        # Place the order
        order_type = 'market'  # Use market order by default
        side = action
        
        if side not in ['buy', 'sell']:
            execution_logger.error(f"Invalid action: {action}. Must be 'buy' or 'sell'. Aborting trade.")
            return None
        
        order = place_order(
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            time_in_force='day',
            take_profit=take_profit_order,
            stop_loss=stop_loss_order
        )
        
        if order:
            execution_logger.info(f"Successfully executed trading signal for {symbol}")
        
        return order
    
    except Exception as e:
        execution_logger.error(f"Exception executing trading signal for {symbol}: {e}")
        return None

def process_signals_batch(signals_dict, risk_per_trade=RISK_PER_TRADE):
    """
    Process a batch of trading signals.
    
    Args:
        signals_dict (dict): Dictionary mapping symbols to their trading signals
        risk_per_trade (float): Percentage of portfolio to risk per trade
    
    Returns:
        dict: Dictionary mapping symbols to their order results
    """
    execution_logger.info(f"Processing batch of {len(signals_dict)} trading signals")
    
    # Check if we're in paper trading mode
    if not PAPER_TRADING:
        confirm = input(f"WARNING: You are about to place REAL orders for {len(signals_dict)} symbols. Continue? (y/n): ")
        if confirm.lower() != 'y':
            execution_logger.warning("User aborted live trading batch processing")
            return {}
    
    orders = {}
    for symbol, signal in signals_dict.items():
        # Add a small delay between orders to avoid rate limits
        if orders:  # Not the first order
            time.sleep(1)
        
        order = execute_trading_signal(signal, symbol, risk_per_trade)
        if order:
            orders[symbol] = order
    
    execution_logger.info(f"Successfully executed {len(orders)} out of {len(signals_dict)} trading signals")
    return orders

def close_position(symbol):
    """
    Close an existing position.
    
    Args:
        symbol (str): Symbol to close
    
    Returns:
        dict: Order details or None if error
    """
    url = f"{ALPACA_BASE_URL}/v2/positions/{symbol}"
    
    try:
        execution_logger.info(f"Closing position for {symbol}")
        response = requests.delete(url, headers=HEADERS)
        
        if response.status_code == 200:
            order = response.json()
            
            execution_logger.info(f"Successfully closed position for {symbol}")
            execution_logger.info(f"Order ID: {order.get('id')}")
            
            return order
        else:
            execution_logger.error(f"Error closing position for {symbol}: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception closing position for {symbol}: {e}")
        return None

def close_all_positions():
    """
    Close all open positions.
    
    Returns:
        dict: Dictionary mapping symbols to their order results
    """
    url = f"{ALPACA_BASE_URL}/v2/positions"
    
    try:
        execution_logger.info("Closing all positions")
        
        # Check if we're in paper trading mode
        if not PAPER_TRADING:
            confirm = input("WARNING: You are about to close ALL REAL positions. Continue? (y/n): ")
            if confirm.lower() != 'y':
                execution_logger.warning("User aborted closing all positions")
                return {}
        
        response = requests.delete(url, headers=HEADERS)
        
        if response.status_code == 200:
            orders = response.json()
            
            execution_logger.info(f"Successfully closed all positions")
            
            results = {}
            for order in orders:
                symbol = order.get('symbol')
                if symbol:
                    results[symbol] = order
            
            return results
        else:
            execution_logger.error(f"Error closing all positions: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception closing all positions: {e}")
        return None

def cancel_all_orders():
    """
    Cancel all open orders.
    
    Returns:
        list: Cancelled orders or None if error
    """
    url = f"{ALPACA_BASE_URL}/v2/orders"
    
    try:
        execution_logger.info("Cancelling all orders")
        response = requests.delete(url, headers=HEADERS)
        
        if response.status_code == 200:
            orders = response.json()
            
            execution_logger.info(f"Successfully cancelled {len(orders)} orders")
            return orders
        else:
            execution_logger.error(f"Error cancelling orders: {response.status_code}")
            execution_logger.debug(response.text)
            return None
    
    except Exception as e:
        execution_logger.error(f"Exception cancelling orders: {e}")
        return None