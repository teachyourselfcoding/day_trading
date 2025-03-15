# Timeframe Selection Guide

## Best Practices for Different Trading Styles

| Trading Style | Recommended Timeframes | Look-back Period | Best Indicators |
|---------------|------------------------|------------------|-----------------|
| Scalping | 1m, 5m | 1d - 3d | Fast EMA (5,10), RSI (7), MACD (6-13-5), Stochastic |
| Day Trading | 15m, 30m, 1h | 5d - 10d | SMA (10,20,50), RSI (14), MACD (12-26-9), Bollinger Bands |
| Swing Trading | 1h, 4h, 1d | 1mo - 3mo | SMA (20,50), EMA (12,26), RSI (14), MACD (12-26-9) |
| Position Trading | 1d, 1wk | 6mo - 1y | SMA (50,200), RSI (14), MACD (12-26-9), ATR (14) |

## Indicator Adjustments Based on Timeframe

### Moving Averages
- **Short-term charts (1m, 5m)**: Use shorter periods like SMA (5,10,20)
- **Medium-term charts (15m, 1h)**: Use standard periods like SMA (10,20,50)
- **Long-term charts (1d, 1wk)**: Use extended periods like SMA (20,50,200)

### Oscillators
- **RSI**: 
  - Short timeframes: 7-10 periods
  - Standard: 14 periods
  - Use with the same thresholds (30/70) regardless of timeframe

- **MACD**:
  - Short timeframes: (6,13,5)
  - Standard: (12,26,9)
  - Long timeframes: (12,26,9) still works well

### Bollinger Bands
- Standard 20 periods work well across timeframes
- For short-term charts (1m-5m), consider reducing to 10 periods
- For weekly charts, consider using 2.5 standard deviations instead of 2

## Common Pitfalls to Avoid

1. **Using too short a look-back period**: 
   - For daily charts, you need at least 200 days to calculate SMA 200
   - For 5-minute charts, 5 days provides enough data for most indicators

2. **Mismatch between trading style and timeframe**:
   - Scalpers should focus on 1m, 5m charts
   - Day traders should focus on 15m, 30m, 1h charts
   - Position traders should focus on 1d, 1wk charts

3. **Using the same indicator settings across all timeframes**:
   - Shorter timeframes need faster indicators (shorter periods)
   - Longer timeframes need slower indicators (longer periods)

4. **Overfitting indicators**:
   - Changing indicator settings too frequently can lead to curve-fitting
   - Test a setting thoroughly before making adjustments

## Getting Started with Timeframe Selection

1. Determine your trading style (scalping, day trading, swing trading, position trading)
2. Select the appropriate timeframe range from the table above
3. Use the recommended indicator settings for that timeframe
4. Review the results of multiple signals to determine effectiveness
5. Make small adjustments as needed based on your specific strategy and the asset being traded