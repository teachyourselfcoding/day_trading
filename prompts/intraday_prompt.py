"""
Enhanced prompt generator with improved modularity for different timeframes.
"""
import json
from datetime import datetime
from src.utils.logger import signals_logger
from src.analysis.patterns import (
    analyze_trend,
    analyze_support_resistance,
    detect_breakouts,
    generate_market_context
)
from src.analysis.technical import (
    extract_price_summary,
    analyze_volume,
    generate_overall_summary
)

def prepare_medium_term_prompt(data, symbol, interval):
    """
    Prepare a prompt for medium-term trading analysis.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    try:
        # First, make sure we have data to work with
        if not data or 'bars' not in data or not data['bars']:
            signals_logger.error(f"No bars in data for prompt generation for {symbol}")
            return None
            
        signals_logger.info(f"Preparing medium_term prompt for {symbol}")
        
        # Define the LLM's role and approach
        role_definition = {
            "role": "Experienced Technical Analyst",
            "expertise": "Medium-term market analysis focusing on swing trading opportunities",
            "approach": "Balanced analysis of technical indicators, price action, and market structure",
            "time_horizon": "5-20 days holding period",
            "risk_management": "Emphasis on favorable risk-reward ratios with clear stop loss levels",
            "analysis_style": "Objective, data-driven with focus on probability rather than certainty"
        }
        
        # Extract key market data
        price_summary = extract_price_summary(data)
        
        # Prepare the prompt structure
        prompt = {
            "role_definition": role_definition,
            "task": f"Analyze market data and technical indicators to generate medium term trading signals for {symbol}.",
            "symbol": symbol,
            "interval": interval,
            "market_data": price_summary,
            "technical_analysis": {},
            "trading_style": "medium_term",
            "expected_response_format": {
                "pattern_identified": "<pattern_name>",
                "pattern_confidence": "<low/medium/high>",
                "suggested_action": "<buy/sell/hold>",
                "entry_price": "<calculated_entry_price>",
                "stop_loss": "<calculated_stop_loss>",
                "take_profit": "<calculated_take_profit>",
                "risk_reward_ratio": "<calculated_ratio>",
                "reasoning": "<evidence-based_reasoning_for_decision>",
                "alternative_scenario": "<conditions_which_invalidate_the_analysis>",
                "timeframe": "<expected_holding_period>"
            },
            "response_instructions": {
                "format": "Please provide your analysis as a valid JSON object that matches the expected_response_format exactly.",
                "requirements": "Ensure all fields are included in your response, including the symbol, pattern_identified, pattern_confidence, and suggested_action.",
                "example": {
                    "pattern_identified": "Uptrend Continuation",
                    "pattern_confidence": "medium",
                    "suggested_action": "buy",
                    "entry_price": "388.50",
                    "stop_loss": "382.34",
                    "take_profit": "394.00",
                    "risk_reward_ratio": "1:1.1",
                    "reasoning": "Price is in an uptrend with bullish signals from the SMA 20, SMA 50, and MACD.",
                    "alternative_scenario": "If price falls below 382.34, analysis is invalidated.",
                    "timeframe": "5-20 days"
                },
                "important_note": "Respond ONLY with the JSON object. Do not include any additional text, explanations, or markdown formatting outside the JSON structure."
            }
        }
        
        # Add trend analysis
        trend_analysis = analyze_trend(data, focus="medium_term")
        prompt["technical_analysis"]["trend_analysis"] = trend_analysis
        
        # Add support and resistance levels
        support_resistance = analyze_support_resistance(data)
        prompt["technical_analysis"]["support_resistance"] = support_resistance
        
        # Add volume analysis
        volume_analysis = analyze_volume(data)
        if volume_analysis:
            prompt["technical_analysis"]["volume_analysis"] = volume_analysis
        
        # Add breakout detection
        breakouts = detect_breakouts(data, support_resistance)
        if breakouts:
            prompt["technical_analysis"]["breakouts"] = breakouts
        
        # Generate market context
        market_context = generate_market_context(data)
        prompt["market_context"] = market_context
        
        # Generate an overall summary
        summary = generate_overall_summary(data, trend_analysis, breakouts)
        prompt["technical_analysis"]["overall_summary"] = summary

        # Add additional guidelines for the LLM to improve the analysis
        prompt["analysis_guidelines"] = {
            "entry_stop_tp": "Calculate a specific entry price using technical levels and recent volatility instead of simply using the current price. Likewise, determine stop loss and take profit levels based on a defined risk-reward ratio.",
            "bearish_pressure": "Explain bearish pressure clearly by discussing its impact on trend strength and how it might conflict with bullish signals, including the implications for the trade setup.",
            "resistance_breakout": "If the current price exceeds identified resistance levels, explicitly state that a resistance breakout has occurred, differentiating between a true breakout and a potential fakeout.",
            "alternative_scenario": "Detail alternative scenarios by explaining that a break below the calculated stop loss would invalidate the analysis, thus requiring re-assessment of the trade.",
            "risk_reward": "Provide refined risk-reward calculations by explicitly computing the ratio based on the differences between the calculated entry price, stop loss, and take profit levels."
        }
        
        # Convert to JSON string
        return json.dumps(prompt, indent=2)
    
    except Exception as e:
        signals_logger.error(f"Error preparing medium_term prompt for {symbol}: {e}")
        return None

    
def prepare_short_term_prompt(data, symbol, interval):
    """
    Prepare a prompt for short-term trading analysis.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    try:
        # First, make sure we have data to work with
        if not data or 'bars' not in data or not data['bars']:
            signals_logger.error(f"No bars in data for prompt generation for {symbol}")
            return None
            
        signals_logger.info(f"Preparing short_term prompt for {symbol}")
        
        # Define the LLM's role and approach
        role_definition = {
            "role": "Day Trader and Technical Analyst",
            "expertise": "Short-term market analysis focusing on intraday and multi-day opportunities",
            "approach": "Emphasis on momentum, volatility, and quick price movements",
            "time_horizon": "Hours to 5 days holding period",
            "risk_management": "Tight stop losses and quick profit taking",
            "analysis_style": "Reactive to price action and volume with emphasis on entry/exit timing"
        }
        
        # Extract key market data
        price_summary = extract_price_summary(data)
        
        # Prepare the prompt structure
        prompt = {
            "role_definition": role_definition,
            "task": f"Analyze market data and technical indicators to generate short term trading signals for {symbol}.",
            "symbol": symbol,
            "interval": interval,
            "market_data": price_summary,
            "technical_analysis": {},
            "trading_style": "short_term",
            "expected_response_format": {
                "pattern_identified": "<pattern_name>",
                "pattern_confidence": "<low/medium/high>",
                "suggested_action": "<buy/sell/hold>",
                "entry_price": "<calculated_entry_price>",
                "stop_loss": "<calculated_stop_loss>",
                "take_profit": "<calculated_take_profit>",
                "risk_reward_ratio": "<calculated_ratio>",
                "reasoning": "<evidence-based_reasoning_for_decision>",
                "alternative_scenario": "<conditions_which_invalidate_the_analysis>",
                "timeframe": "<expected_holding_period_in_hours_or_days>"
            },
            "response_instructions": {
                "format": "Please provide your analysis as a valid JSON object that matches the expected_response_format exactly.",
                "requirements": "Ensure all fields are included in your response, including the symbol, pattern_identified, pattern_confidence, and suggested_action.",
                "example": {
                    "pattern_identified": "Breakout",
                    "pattern_confidence": "high",
                    "suggested_action": "buy",
                    "entry_price": "388.50",
                    "stop_loss": "386.75",
                    "take_profit": "392.00",
                    "risk_reward_ratio": "1:2",
                    "reasoning": "Price breaking above resistance with increasing volume and positive momentum.",
                    "alternative_scenario": "If price falls back below breakout level, exit the trade.",
                    "timeframe": "1-2 days"
                },
                "important_note": "Respond ONLY with the JSON object. Do not include any additional text, explanations, or markdown formatting outside the JSON structure."
            }
        }
        
        # Add trend analysis
        trend_analysis = analyze_trend(data, focus="short_term")
        prompt["technical_analysis"]["trend_analysis"] = trend_analysis
        
        # Add support and resistance levels
        support_resistance = analyze_support_resistance(data, lookback=10)
        prompt["technical_analysis"]["support_resistance"] = support_resistance
        
        # Add volume analysis
        volume_analysis = analyze_volume(data, periods=5)
        if volume_analysis:
            prompt["technical_analysis"]["volume_analysis"] = volume_analysis
        
        # Add breakout detection
        breakouts = detect_breakouts(data, support_resistance)
        if breakouts:
            prompt["technical_analysis"]["breakouts"] = breakouts
        
        # Generate market context
        market_context = generate_market_context(data, focus="short_term")
        prompt["market_context"] = market_context
        
        # Generate an overall summary
        summary = generate_overall_summary(data, trend_analysis, breakouts, focus="short_term")
        prompt["technical_analysis"]["overall_summary"] = summary

        # Add additional guidelines for the LLM to improve the analysis
        prompt["analysis_guidelines"] = {
            "entry_timing": "Focus on precise entry timing based on intraday price action and volume confirmation.",
            "stop_placement": "Keep stops tight but outside normal market noise levels, typically using recent swing points or volatility measures.",
            "aggressive_targets": "For short-term trades, consider multiple profit targets to capture quick moves while allowing for potential continuation.",
            "momentum_emphasis": "Pay special attention to momentum indicators like RSI, Stochastics, and MACD for short-term trade direction.",
            "market_conditions": "Clearly identify if the current market environment favors day trading or if volatility is too low for effective short-term trades."
        }
        
        # Convert to JSON string
        return json.dumps(prompt, indent=2)
    
    except Exception as e:
        signals_logger.error(f"Error preparing short_term prompt for {symbol}: {e}")
        return None


def prepare_long_term_prompt(data, symbol, interval):
    """
    Prepare a prompt for long-term trading analysis.
    
    Args:
        data (dict): Data dictionary with 'bars' key containing price data
        symbol (str): Stock symbol
        interval (str): Time interval
    
    Returns:
        str: JSON prompt for OpenAI
    """
    try:
        # First, make sure we have data to work with
        if not data or 'bars' not in data or not data['bars']:
            signals_logger.error(f"No bars in data for prompt generation for {symbol}")
            return None
            
        signals_logger.info(f"Preparing long_term prompt for {symbol}")
        
        # Define the LLM's role and approach
        role_definition = {
            "role": "Strategic Investment Analyst",
            "expertise": "Long-term market analysis focusing on position trading opportunities",
            "approach": "Emphasis on macro trends, fundamental confluence, and significant technical levels",
            "time_horizon": "Weeks to months holding period",
            "risk_management": "Wider but calculated stop losses with strategic position sizing",
            "analysis_style": "Patient, trend-following with focus on high-probability setups"
        }
        
        # Extract key market data
        price_summary = extract_price_summary(data)
        
        # Prepare the prompt structure
        prompt = {
            "role_definition": role_definition,
            "task": f"Analyze market data and technical indicators to generate long term trading signals for {symbol}.",
            "symbol": symbol,
            "interval": interval,
            "market_data": price_summary,
            "technical_analysis": {},
            "trading_style": "long_term",
            "expected_response_format": {
                "pattern_identified": "<pattern_name>",
                "pattern_confidence": "<low/medium/high>",
                "suggested_action": "<buy/sell/hold>",
                "entry_price": "<calculated_entry_price_or_range>",
                "stop_loss": "<calculated_stop_loss>",
                "take_profit": "<calculated_take_profit_or_targets>",
                "risk_reward_ratio": "<calculated_ratio>",
                "reasoning": "<evidence-based_reasoning_for_decision>",
                "alternative_scenario": "<conditions_which_invalidate_the_analysis>",
                "timeframe": "<expected_holding_period_in_weeks_or_months>"
            },
            "response_instructions": {
                "format": "Please provide your analysis as a valid JSON object that matches the expected_response_format exactly.",
                "requirements": "Ensure all fields are included in your response, including the symbol, pattern_identified, pattern_confidence, and suggested_action.",
                "example": {
                    "pattern_identified": "Major Uptrend Continuation",
                    "pattern_confidence": "high",
                    "suggested_action": "buy",
                    "entry_price": "385.00-390.00",
                    "stop_loss": "365.00",
                    "take_profit": "425.00",
                    "risk_reward_ratio": "1:1.75",
                    "reasoning": "Price in confirmed uptrend above all major moving averages with healthy pullback to support.",
                    "alternative_scenario": "If price breaks below the 200-day moving average, the long-term bullish thesis is invalidated.",
                    "timeframe": "3-6 months"
                },
                "important_note": "Respond ONLY with the JSON object. Do not include any additional text, explanations, or markdown formatting outside the JSON structure."
            }
        }
        
        # Add trend analysis
        trend_analysis = analyze_trend(data, focus="long_term")
        prompt["technical_analysis"]["trend_analysis"] = trend_analysis
        
        # Add support and resistance levels
        support_resistance = analyze_support_resistance(data, lookback=50)
        prompt["technical_analysis"]["support_resistance"] = support_resistance
        
        # Add volume analysis
        volume_analysis = analyze_volume(data, periods=20)
        if volume_analysis:
            prompt["technical_analysis"]["volume_analysis"] = volume_analysis
        
        # Add breakout detection
        breakouts = detect_breakouts(data, support_resistance)
        if breakouts:
            prompt["technical_analysis"]["breakouts"] = breakouts
        
        # Generate market context
        market_context = generate_market_context(data, focus="long_term")
        prompt["market_context"] = market_context
        
        # Generate an overall summary
        summary = generate_overall_summary(data, trend_analysis, breakouts, focus="long_term")
        prompt["technical_analysis"]["overall_summary"] = summary

        # Add additional guidelines for the LLM to improve the analysis
        prompt["analysis_guidelines"] = {
            "trend_confirmation": "Emphasize the importance of multiple timeframe confirmation for long-term trends.",
            "strategic_entry": "Consider scaling into positions at key technical levels rather than single entry points.",
            "broad_market_context": "Factor in broader market conditions and sector performance in the analysis.",
            "moving_average_emphasis": "Pay special attention to the relationship between price and longer-term moving averages (50, 100, 200-day).",
            "prepare_for_volatility": "Address how to handle normal market volatility during the expected longer holding period."
        }
        
        # Convert to JSON string
        return json.dumps(prompt, indent=2)
    
    except Exception as e:
        signals_logger.error(f"Error preparing long_term prompt for {symbol}: {e}")
        return None