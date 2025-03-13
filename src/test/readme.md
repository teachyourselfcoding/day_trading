# Interactive Signal Verification Dashboard User Guide

This guide explains how to use the Interactive Signal Verification Dashboard to validate that your technical indicators and trading signals are triggering correctly.

## Getting Started

1. **Install required dependencies**:
   ```bash
   pip install flask pandas numpy matplotlib plotly talib
   ```

2. **Save the dashboard files** in your project directory:
   - `src/test/web_signal_dashboard.py` (main Flask application)
   - Templates and static files will be created automatically when you run the application

3. **Run the dashboard**:
   ```bash
   python -m src.test.web_signal_dashboard
   ```

4. **Open your browser** and navigate to `http://127.0.0.1:5000/`

## Dashboard Features

### Symbol Selection
- Choose any symbol from the dropdown menu that has data in your `data/raw` directory
- Click "Load Data" to analyze the selected symbol

### Interactive Chart Controls
- **Zoom**: Click and drag on the chart to zoom in on a specific time period
- **Reset Zoom**: Click the "Reset Zoom" button to return to the full view
- **Export Data**: Download the raw data as a CSV file for further analysis

### Customizable Display
The dashboard allows you to toggle different elements on/off:

1. **Price Settings**
   - Show/hide the main price chart
   - Show/hide volume bars

2. **Moving Averages**
   - SMA 20, 50, 200
   - EMA 12, 26

3. **Bollinger Bands**
   - Upper, middle, and lower bands

4. **Technical Indicators**
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Stochastic Oscillator
   - ADX (Average Directional Index)

5. **Candlestick Patterns**
   - Bullish patterns (shown as green triangles)
   - Bearish patterns (shown as red triangles)

6. **Technical Signals**
   - RSI overbought/oversold signals
   - MACD crossover signals
   - Bollinger Band touches
   - Golden/Death Crosses

### Signal and Pattern Summary
The dashboard provides summary tables showing:
- Count of each type of technical signal detected
- Count of each candlestick pattern detected

## How to Verify Signals

To verify that your signals are triggering correctly:

1. **Load a symbol** that you know has certain patterns or indicators

2. **Enable specific indicators** you want to verify by checking the appropriate boxes in the sidebar

3. **Zoom in** on areas of interest by clicking and dragging on the chart

4. **Examine signal markers** which appear directly on the price chart:
   - Green triangles for bullish patterns
   - Red triangles for bearish patterns
   - Colored dots for technical signals (RSI, MACD, etc.)

5. **Check the summary tables** to see how many of each signal type were detected

6. **Compare indicator charts** with the price chart to verify the timing and accuracy of signals
   - E.g., confirm that RSI oversold signals appear when RSI dips below 30
   - Verify that MACD crossovers align with signal markers

7. **Export the data** if you need to perform additional validation or custom analysis

## Troubleshooting

If you encounter issues:

1. **Missing data**: Make sure you have JSON data files in your `data/raw` directory

2. **TA-Lib errors**: Ensure TA-Lib is properly installed and that your data types are correctly converted to float64

3. **Blank charts**: Check the browser console for JavaScript errors and ensure Plotly.js is loaded

4. **No signals detected**: Verify that your data has enough bars for the indicators to calculate properly (e.g., at least 14 bars for RSI)

## Extending the Dashboard

You can customize the dashboard further by:

1. **Adding new indicators**: Extend the `calculate_indicators()` function to include additional TA-Lib indicators

2. **Creating new signal types**: Add more signal detection logic in the `detect_indicator_signals()` function

3. **Modifying the UI**: Adjust the HTML template to add more controls or visualization options

## Example Workflow

Here's a recommended workflow for verifying signal accuracy:

1. Start with known historical data where you can visually identify patterns
2. Enable just one or two indicators at a time for focused verification
3. Compare the dashboard's automatic detection with your manual analysis
4. Adjust your signal detection parameters if necessary
5. Test with different symbols and timeframes to ensure consistency