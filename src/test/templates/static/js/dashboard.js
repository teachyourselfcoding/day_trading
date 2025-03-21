// dashboard.js - Interactive Signal Verification Dashboard

// Global variables
let chartData = null;
let priceChart = null;
let rsiChart = null;
let macdChart = null;
let stochChart = null;
let adxChart = null;
let currentSymbol = '';
let syncedZoom = true; // Toggle for synchronizing zooms across charts

// Chart layout settings
const chartConfig = {
    responsive: true,
    displayModeBar: true,
    scrollZoom: true,
    displaylogo: false,
    toImageButtonOptions: {
        format: 'png',
        filename: 'chart_image',
        height: 800,
        width: 1200
    }
};

// Initialize the dashboard when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard.js loaded successfully');
    
    // Get references to DOM elements
    const loadSymbolBtn = document.getElementById('loadSymbolBtn');
    const zoomResetBtn = document.getElementById('zoomResetBtn');
    const exportDataBtn = document.getElementById('exportDataBtn');
    const syncZoomToggle = document.createElement('input');
    syncZoomToggle.type = 'checkbox';
    syncZoomToggle.id = 'syncZoomToggle';
    syncZoomToggle.className = 'form-check-input me-2';
    syncZoomToggle.checked = syncedZoom;
    
    // Add sync zoom toggle to the toolbar
    const toolbarGroup = document.querySelector('.btn-group');
    if (toolbarGroup) {
        const syncZoomLabel = document.createElement('label');
        syncZoomLabel.className = 'btn btn-sm btn-outline-secondary d-flex align-items-center';
        syncZoomLabel.appendChild(syncZoomToggle);
        syncZoomLabel.appendChild(document.createTextNode('Sync Zoom'));
        toolbarGroup.appendChild(syncZoomLabel);
        
        // Add event listener for sync zoom toggle
        syncZoomToggle.addEventListener('change', function() {
            syncedZoom = this.checked;
        });
        
        // Add statistics button 
        const statsBtn = document.createElement('button');
        statsBtn.id = 'statsBtn';
        statsBtn.className = 'btn btn-sm btn-outline-secondary ms-2';
        statsBtn.textContent = 'Statistics';
        toolbarGroup.appendChild(statsBtn);
        
        // Add event listener for statistics button
        statsBtn.addEventListener('click', showStatistics);
    }
    
    // Set up button event listeners
    if (loadSymbolBtn) {
        loadSymbolBtn.addEventListener('click', loadSymbolData);
    }
    
    if (zoomResetBtn) {
        zoomResetBtn.addEventListener('click', resetZoom);
    }
    
    if (exportDataBtn) {
        exportDataBtn.addEventListener('click', exportData);
    } 
    // Set up checkbox event listeners
    setupCheckboxListeners();
});

// Setup checkbox event listeners
function setupCheckboxListeners() {
    // Price settings
    document.getElementById('showPriceChart').addEventListener('change', updateCharts);
    document.getElementById('showVolume').addEventListener('change', updateCharts);
    
    // Moving averages
    document.getElementById('showSMA20').addEventListener('change', updateCharts);
    document.getElementById('showSMA50').addEventListener('change', updateCharts);
    document.getElementById('showSMA200').addEventListener('change', updateCharts);
    document.getElementById('showEMA12').addEventListener('change', updateCharts);
    document.getElementById('showEMA26').addEventListener('change', updateCharts);
    
    // Bollinger Bands
    document.getElementById('showBBUpper').addEventListener('change', updateCharts);
    document.getElementById('showBBMiddle').addEventListener('change', updateCharts);
    document.getElementById('showBBLower').addEventListener('change', updateCharts);
    
    // Indicators
    document.getElementById('showRSI').addEventListener('change', function() {
        document.getElementById('rsiChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    document.getElementById('showMACD').addEventListener('change', function() {
        document.getElementById('macdChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    document.getElementById('showStochastic').addEventListener('change', function() {
        document.getElementById('stochChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    document.getElementById('showADX').addEventListener('change', function() {
        document.getElementById('adxChart').style.display = this.checked ? 'block' : 'none';
        updateCharts();
    });
    
    // Patterns and signals
    document.getElementById('showBullishPatterns').addEventListener('change', updateCharts);
    document.getElementById('showBearishPatterns').addEventListener('change', updateCharts);
    document.getElementById('showRSISignals').addEventListener('change', updateCharts);
    document.getElementById('showMACDSignals').addEventListener('change', updateCharts);
    document.getElementById('showBBSignals').addEventListener('change', updateCharts);
    document.getElementById('showCrossovers').addEventListener('change', updateCharts);
}

// Load data for the selected symbol
function loadSymbolData() {
    // Get the selected symbol
    const symbolSelect = document.getElementById('symbolSelect');
    currentSymbol = symbolSelect.value;
    
    // Only proceed if a symbol is selected
    if (!currentSymbol) {
        alert("Please select a symbol first");
        return;
    }
    
    // Show loading message
    const loadingMessage = document.getElementById('loadingMessage');
    const chartContainer = document.getElementById('chartContainer');
    
    if (loadingMessage) loadingMessage.style.display = 'block';
    if (chartContainer) chartContainer.style.opacity = '0.5';
    
    // Update page title with symbol
    document.title = `${currentSymbol} - Signal Verification Dashboard`;
    
    // Fetch data from the server
    fetch(`/api/data/${currentSymbol}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide loading message
            if (loadingMessage) loadingMessage.style.display = 'none';
            if (chartContainer) chartContainer.style.opacity = '1';
            
            // Store the data globally
            chartData = data;
            
            // Create charts
            createCharts();
            
            // Update summary tables
            updateSummaries();
            
            // Show success toast
            showToast(`Loaded data for ${currentSymbol} successfully`);
        })
        .catch(error => {
            console.error('Error loading data:', error);
            if (loadingMessage) loadingMessage.style.display = 'none';
            if (chartContainer) chartContainer.style.opacity = '1';
            showToast(`Error loading data: ${error.message}`, 'danger');
        });
}

// Create all charts
function createCharts() {
    if (!chartData) return;
    
    // Store current chart time range if zoomed
    let timeRange = null;
    if (document.getElementById('priceChart').data && 
        document.getElementById('priceChart').layout.xaxis.range) {
        timeRange = document.getElementById('priceChart').layout.xaxis.range;
    }
    
    // Create the main price chart
    createPriceChart();
    
    // Create indicator charts if their display is enabled
    if (document.getElementById('showRSI').checked) {
        createRSIChart();
    }
    
    if (document.getElementById('showMACD').checked) {
        createMACDChart();
    }
    
    if (document.getElementById('showStochastic').checked) {
        createStochasticChart();
    }
    
    if (document.getElementById('showADX').checked) {
        createADXChart();
    }
    
    // Restore zoom level if it was set
    if (timeRange) {
        Plotly.relayout('priceChart', {
            'xaxis.range': timeRange
        });
        
        // Apply same time range to other charts if sync is enabled
        if (syncedZoom) {
            const charts = ['rsiChart', 'macdChart', 'stochChart', 'adxChart'];
            charts.forEach(chart => {
                if (document.getElementById(chart).style.display !== 'none') {
                    Plotly.relayout(chart, {
                        'xaxis.range': timeRange
                    });
                }
            });
        }
    }
}

// Create the main price chart
function createPriceChart() {
    // Skip if chart container is not visible
    if (!document.getElementById('showPriceChart').checked) {
        document.getElementById('priceChart').style.display = 'none';
        return;
    } else {
        document.getElementById('priceChart').style.display = 'block';
    }
    
    // Prepare the main candlestick trace
    const ohlc = {
        x: chartData.datetime,
        open: chartData.price.open,
        high: chartData.price.high,
        low: chartData.price.low,
        close: chartData.price.close,
        type: 'candlestick',
        name: currentSymbol,
        yaxis: 'y1'
    };
    
    // Prepare volume bars
    const volume = {
        x: chartData.datetime,
        y: chartData.price.volume,
        type: 'bar',
        name: 'Volume',
        marker: {
            color: 'rgba(100, 100, 100, 0.3)'
        },
        yaxis: 'y2',
        visible: document.getElementById('showVolume').checked
    };
    
    // Initialize traces array with OHLC
    const traces = [ohlc];
    
    // Add volume if visible
    if (document.getElementById('showVolume').checked) {
        traces.push(volume);
    }
    
    // Add moving averages
    if (document.getElementById('showSMA20').checked && chartData.indicators.sma_20) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.sma_20,
            type: 'scatter',
            mode: 'lines',
            name: 'SMA 20',
            line: { color: 'blue', width: 1 }
        });
    }
    
    if (document.getElementById('showSMA50').checked && chartData.indicators.sma_50) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.sma_50,
            type: 'scatter',
            mode: 'lines',
            name: 'SMA 50',
            line: { color: 'green', width: 1 }
        });
    }
    
    if (document.getElementById('showSMA200').checked && chartData.indicators.sma_200) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.sma_200,
            type: 'scatter',
            mode: 'lines',
            name: 'SMA 200',
            line: { color: 'red', width: 1 }
        });
    }
    
    if (document.getElementById('showEMA12').checked && chartData.indicators.ema_12) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.ema_12,
            type: 'scatter',
            mode: 'lines',
            name: 'EMA 12',
            line: { color: 'purple', width: 1, dash: 'dash' }
        });
    }
    
    if (document.getElementById('showEMA26').checked && chartData.indicators.ema_26) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.ema_26,
            type: 'scatter',
            mode: 'lines',
            name: 'EMA 26',
            line: { color: 'orange', width: 1, dash: 'dash' }
        });
    }
    
    // Add Bollinger Bands
    if (document.getElementById('showBBUpper').checked && chartData.indicators.bb_upper) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.bb_upper,
            type: 'scatter',
            mode: 'lines',
            name: 'BB Upper',
            line: { color: 'gray', width: 1 }
        });
    }
    
    if (document.getElementById('showBBMiddle').checked && chartData.indicators.bb_middle) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.bb_middle,
            type: 'scatter',
            mode: 'lines',
            name: 'BB Middle',
            line: { color: 'gray', width: 1, dash: 'dash' }
        });
    }
    
    if (document.getElementById('showBBLower').checked && chartData.indicators.bb_lower) {
        traces.push({
            x: chartData.datetime,
            y: chartData.indicators.bb_lower,
            type: 'scatter',
            mode: 'lines',
            name: 'BB Lower',
            line: { color: 'gray', width: 1 }
        });
    }
    
    // Add pattern markers
    if (chartData.patterns) {
        // Bullish patterns
        if (document.getElementById('showBullishPatterns').checked && chartData.patterns.bullish) {
            const bullishX = [];
            const bullishY = [];
            const bullishText = [];
            
            for (const patternType in chartData.patterns.bullish) {
                const patternValues = chartData.patterns.bullish[patternType];
                
                for (let i = 0; i < patternValues.length; i++) {
                    if (patternValues[i] > 0) {
                        bullishX.push(chartData.datetime[i]);
                        bullishY.push(chartData.price.low[i] * 0.99);
                        bullishText.push(patternType.replace(/_/g, ' '));
                    }
                }
            }
            
            if (bullishX.length > 0) {
                traces.push({
                    x: bullishX,
                    y: bullishY,
                    text: bullishText,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Bullish Patterns',
                    marker: {
                        symbol: 'triangle-up',
                        size: 12,
                        color: 'green'
                    }
                });
            }
        }
        
        // Bearish patterns
        if (document.getElementById('showBearishPatterns').checked && chartData.patterns.bearish) {
            const bearishX = [];
            const bearishY = [];
            const bearishText = [];
            
            for (const patternType in chartData.patterns.bearish) {
                const patternValues = chartData.patterns.bearish[patternType];
                
                for (let i = 0; i < patternValues.length; i++) {
                    if (patternValues[i] > 0) {
                        bearishX.push(chartData.datetime[i]);
                        bearishY.push(chartData.price.high[i] * 1.01);
                        bearishText.push(patternType.replace(/_/g, ' '));
                    }
                }
            }
            
            if (bearishX.length > 0) {
                traces.push({
                    x: bearishX,
                    y: bearishY,
                    text: bearishText,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Bearish Patterns',
                    marker: {
                        symbol: 'triangle-down',
                        size: 12,
                        color: 'red'
                    }
                });
            }
        }
    }
    
    // Add technical signals
    if (chartData.signals) {
        // RSI Oversold signals
        if (document.getElementById('showRSISignals').checked && chartData.signals.rsi_oversold) {
            const signalIndices = [];
            for (let i = 0; i < chartData.signals.rsi_oversold.length; i++) {
                if (chartData.signals.rsi_oversold[i] > 0) signalIndices.push(i);
            }
            
            if (signalIndices.length > 0) {
                const signalX = signalIndices.map(i => chartData.datetime[i]);
                const signalY = signalIndices.map(i => chartData.price.low[i] * 0.98);
                
                traces.push({
                    x: signalX,
                    y: signalY,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'RSI Oversold',
                    marker: {
                        symbol: 'circle',
                        size: 10,
                        color: 'green'
                    }
                });
            }
        }
        
        // RSI Overbought signals
        if (document.getElementById('showRSISignals').checked && chartData.signals.rsi_overbought) {
            const signalIndices = [];
            for (let i = 0; i < chartData.signals.rsi_overbought.length; i++) {
                if (chartData.signals.rsi_overbought[i] > 0) signalIndices.push(i);
            }
            
            if (signalIndices.length > 0) {
                const signalX = signalIndices.map(i => chartData.datetime[i]);
                const signalY = signalIndices.map(i => chartData.price.high[i] * 1.02);
                
                traces.push({
                    x: signalX,
                    y: signalY,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'RSI Overbought',
                    marker: {
                        symbol: 'circle',
                        size: 10,
                        color: 'red'
                    }
                });
            }
        }
        
        // MACD Bullish Cross signals
        if (document.getElementById('showMACDSignals').checked && chartData.signals.macd_bullish_cross) {
            const signalIndices = [];
            for (let i = 0; i < chartData.signals.macd_bullish_cross.length; i++) {
                if (chartData.signals.macd_bullish_cross[i] > 0) signalIndices.push(i);
            }
            
            if (signalIndices.length > 0) {
                const signalX = signalIndices.map(i => chartData.datetime[i]);
                const signalY = signalIndices.map(i => chartData.price.low[i] * 0.97);
                
                traces.push({
                    x: signalX,
                    y: signalY,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'MACD Bullish Cross',
                    marker: {
                        symbol: 'star',
                        size: 12,
                        color: 'lime'
                    }
                });
            }
        }
        
        // MACD Bearish Cross signals
        if (document.getElementById('showMACDSignals').checked && chartData.signals.macd_bearish_cross) {
            const signalIndices = [];
            for (let i = 0; i < chartData.signals.macd_bearish_cross.length; i++) {
                if (chartData.signals.macd_bearish_cross[i] > 0) signalIndices.push(i);
            }
            
            if (signalIndices.length > 0) {
                const signalX = signalIndices.map(i => chartData.datetime[i]);
                const signalY = signalIndices.map(i => chartData.price.high[i] * 1.03);
                
                traces.push({
                    x: signalX,
                    y: signalY,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'MACD Bearish Cross',
                    marker: {
                        symbol: 'star',
                        size: 12,
                        color: 'orange'
                    }
                });
            }
        }
        
        // Bollinger Band signals
        if (document.getElementById('showBBSignals').checked) {
            // Lower Band Touch
            if (chartData.signals.bb_lower_touch) {
                const signalIndices = [];
                for (let i = 0; i < chartData.signals.bb_lower_touch.length; i++) {
                    if (chartData.signals.bb_lower_touch[i] > 0) signalIndices.push(i);
                }
                
                if (signalIndices.length > 0) {
                    const signalX = signalIndices.map(i => chartData.datetime[i]);
                    const signalY = signalIndices.map(i => chartData.price.low[i]);
                    
                    traces.push({
                        x: signalX,
                        y: signalY,
                        mode: 'markers',
                        type: 'scatter',
                        name: 'BB Lower Touch',
                        marker: {
                            symbol: 'circle',
                            size: 8,
                            color: 'cyan'
                        }
                    });
                }
            }
            
            // Upper Band Touch
            if (chartData.signals.bb_upper_touch) {
                const signalIndices = [];
                for (let i = 0; i < chartData.signals.bb_upper_touch.length; i++) {
                    if (chartData.signals.bb_upper_touch[i] > 0) signalIndices.push(i);
                }
                
                if (signalIndices.length > 0) {
                    const signalX = signalIndices.map(i => chartData.datetime[i]);
                    const signalY = signalIndices.map(i => chartData.price.high[i]);
                    
                    traces.push({
                        x: signalX,
                        y: signalY,
                        mode: 'markers',
                        type: 'scatter',
                        name: 'BB Upper Touch',
                        marker: {
                            symbol: 'circle',
                            size: 8,
                            color: 'magenta'
                        }
                    });
                }
            }
        }
        
        // Golden/Death Cross signals
        if (document.getElementById('showCrossovers').checked) {
            // Golden Cross
            if (chartData.signals.golden_cross) {
                const signalIndices = [];
                for (let i = 0; i < chartData.signals.golden_cross.length; i++) {
                    if (chartData.signals.golden_cross[i] > 0) signalIndices.push(i);
                }
                
                if (signalIndices.length > 0) {
                    const signalX = signalIndices.map(i => chartData.datetime[i]);
                    const signalY = signalIndices.map(i => chartData.price.high[i] * 1.05);
                    
                    traces.push({
                        x: signalX,
                        y: signalY,
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Golden Cross',
                        text: ['Golden Cross'],
                        textposition: 'top',
                        marker: {
                            symbol: 'cross',
                            size: 16,
                            color: 'gold'
                        }
                    });
                }
            }
            
            // Death Cross
            if (chartData.signals.death_cross) {
                const signalIndices = [];
                for (let i = 0; i < chartData.signals.death_cross.length; i++) {
                    if (chartData.signals.death_cross[i] > 0) signalIndices.push(i);
                }
                
                if (signalIndices.length > 0) {
                    const signalX = signalIndices.map(i => chartData.datetime[i]);
                    const signalY = signalIndices.map(i => chartData.price.high[i] * 1.05);
                    
                    traces.push({
                        x: signalX,
                        y: signalY,
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Death Cross',
                        text: ['Death Cross'],
                        textposition: 'top',
                        marker: {
                            symbol: 'cross',
                            size: 16,
                            color: 'black'
                        }
                    });
                }
            }
        }
    }
    
    // Define the layout
    const layout = {
        title: `${currentSymbol} Price Chart with Technical Indicators`,
        dragmode: 'zoom',
        showlegend: true,
        xaxis: {
            rangeslider: {
                visible: false
            },
            title: 'Date'
        },
        yaxis: {
            title: 'Price',
            domain: [0.2, 1],
            tickformat: '.2f'
        },
        yaxis2: {
            title: 'Volume',
            domain: [0, 0.15],
            tickformat: '.0f'
        },
        grid: {
            rows: 2,
            columns: 1,
            pattern: 'independent'
        },
        legend: {
            orientation: 'h',
            y: 1.1
        },
        annotations: [],
        hovermode: 'closest'
    };
    
    // Create the main price chart
    Plotly.newPlot('priceChart', traces, layout, chartConfig);
    
    // Set up event listeners for zoom sync
    document.getElementById('priceChart').on('plotly_relayout', function(eventData) {
        if (!syncedZoom) return;
        
        // Check if this is a zoom event
        if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
            const xRange = [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']];
            
            // Sync zoom to other visible charts
            if (document.getElementById('rsiChart').style.display !== 'none') {
                Plotly.relayout('rsiChart', {
                    'xaxis.range[0]': xRange[0],
                    'xaxis.range[1]': xRange[1]
                });
            }
            
            if (document.getElementById('macdChart').style.display !== 'none') {
                Plotly.relayout('macdChart', {
                    'xaxis.range[0]': xRange[0],
                    'xaxis.range[1]': xRange[1]
                });
            }
            
            if (document.getElementById('stochChart').style.display !== 'none') {
                Plotly.relayout('stochChart', {
                    'xaxis.range[0]': xRange[0],
                    'xaxis.range[1]': xRange[1]
                });
            }
            
            if (document.getElementById('adxChart').style.display !== 'none') {
                Plotly.relayout('adxChart', {
                    'xaxis.range[0]': xRange[0],
                    'xaxis.range[1]': xRange[1]
                });
            }
        }
    });
}

// Create the RSI chart
function createRSIChart() {
    if (!chartData || !chartData.indicators.rsi) return;
    
    const trace = {
        x: chartData.datetime,
        y: chartData.indicators.rsi,
        type: 'scatter',
        mode: 'lines',
        name: 'RSI',
        line: {
            color: 'purple',
            width: 1
        }
    };
    
    const layout = {
        title: 'RSI (14)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'RSI',
            range: [0, 100]
        },
        shapes: [
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 80,
                y1: 80,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 20,
                y1: 20,
                line: {
                    color: 'green',
                    width: 1,
                    dash: 'dash'
                }
            }
        ],
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('stochChart', [kLine, dLine], layout, chartConfig);
}

// Create the ADX chart
function createADXChart() {
    if (!chartData || !chartData.indicators.adx) return;
    
    const adxLine = {
        x: chartData.datetime,
        y: chartData.indicators.adx,
        type: 'scatter',
        mode: 'lines',
        name: 'ADX',
        line: {
            color: 'black',
            width: 1
        }
    };
    
    const layout = {
        title: 'ADX (14)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'ADX',
            range: [0, 100]
        },
        shapes: [
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 25,
                y1: 25,
                line: {
                    color: 'orange',
                    width: 1,
                    dash: 'dash'
                }
            }
        ],
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('adxChart', [adxLine], layout, chartConfig);
}

// Update all charts based on current settings
function updateCharts() {
    createCharts();
}

// Reset zoom on all charts
function resetZoom() {
    Plotly.relayout('priceChart', {
        'xaxis.autorange': true,
        'yaxis.autorange': true
    });
    
    if (document.getElementById('rsiChart').style.display !== 'none') {
        Plotly.relayout('rsiChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (document.getElementById('macdChart').style.display !== 'none') {
        Plotly.relayout('macdChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (document.getElementById('stochChart').style.display !== 'none') {
        Plotly.relayout('stochChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (document.getElementById('adxChart').style.display !== 'none') {
        Plotly.relayout('adxChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    // Show success message
    showToast('Zoom reset successfully');
}

// Export data to CSV
function exportData() {
    if (!chartData) return;
    
    // Create CSV content
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add header row
    let headers = ["DateTime", "Open", "High", "Low", "Close", "Volume"];
    
    // Add indicator headers
    if (chartData.indicators) {
        for (const indicator in chartData.indicators) {
            headers.push(indicator);
        }
    }
    
    csvContent += headers.join(",") + "\n";
    
    // Add data rows
    for (let i = 0; i < chartData.datetime.length; i++) {
        let row = [
            chartData.datetime[i],
            chartData.price.open[i],
            chartData.price.high[i],
            chartData.price.low[i],
            chartData.price.close[i],
            chartData.price.volume[i]
        ];
        
        // Add indicator values
        if (chartData.indicators) {
            for (const indicator in chartData.indicators) {
                row.push(chartData.indicators[indicator][i] || "");
            }
        }
        
        csvContent += row.join(",") + "\n";
    }
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${currentSymbol}_data.csv`);
    document.body.appendChild(link);
    
    // Trigger download and remove link
    link.click();
    document.body.removeChild(link);
    
    // Show success message
    showToast('Data exported successfully');
}

// Update the summary tables
function updateSummaries() {
    if (!chartData) return;
    
    // Update signal summary
    updateSignalSummary();
    
    // Update pattern summary
    updatePatternSummary();
}

// Update signal summary table
function updateSignalSummary() {
    const signalSummaryElement = document.getElementById('signalSummary');
    
    // Count signals
    const signalCounts = {};
    if (chartData.signals) {
        for (const signalType in chartData.signals) {
            signalCounts[signalType] = chartData.signals[signalType].filter(val => val > 0).length;
        }
    }
    
    // Create HTML content
    let html = '<table class="table table-sm">';
    html += '<thead><tr><th>Signal Type</th><th>Count</th></tr></thead>';
    html += '<tbody>';
    
    // Bullish signals
    html += '<tr class="table-success"><td colspan="2"><strong>Bullish Signals</strong></td></tr>';
    html += `<tr><td>RSI Oversold</td><td>${signalCounts.rsi_oversold || 0}</td></tr>`;
    html += `<tr><td>MACD Bullish Cross</td><td>${signalCounts.macd_bullish_cross || 0}</td></tr>`;
    html += `<tr><td>Bollinger Lower Touch</td><td>${signalCounts.bb_lower_touch || 0}</td></tr>`;
    html += `<tr><td>Golden Cross</td><td>${signalCounts.golden_cross || 0}</td></tr>`;
    html += `<tr><td>Stochastic Oversold</td><td>${signalCounts.stoch_oversold || 0}</td></tr>`;
    
    // Bearish signals
    html += '<tr class="table-danger"><td colspan="2"><strong>Bearish Signals</strong></td></tr>';
    html += `<tr><td>RSI Overbought</td><td>${signalCounts.rsi_overbought || 0}</td></tr>`;
    html += `<tr><td>MACD Bearish Cross</td><td>${signalCounts.macd_bearish_cross || 0}</td></tr>`;
    html += `<tr><td>Bollinger Upper Touch</td><td>${signalCounts.bb_upper_touch || 0}</td></tr>`;
    html += `<tr><td>Death Cross</td><td>${signalCounts.death_cross || 0}</td></tr>`;
    html += `<tr><td>Stochastic Overbought</td><td>${signalCounts.stoch_overbought || 0}</td></tr>`;
    
    html += '</tbody></table>';
    
    signalSummaryElement.innerHTML = html;
}

// Add toast notification function
function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = 1050;
        document.body.appendChild(toastContainer);
    }
    
    // Create unique ID for this toast
    const toastId = 'toast-' + Date.now();
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast bg-${type} text-white`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Set toast content
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">Signal Dashboard</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize Bootstrap toast
    const bsToast = new bootstrap.Toast(toast, { 
        autohide: true,
        delay: 3000
    });
    
    // Show toast
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Add a statistics function to show summary metrics
function showStatistics() {
    if (!chartData) return;
    
    // Calculate key statistics
    const prices = chartData.price.close;
    const lastPrice = prices[prices.length - 1];
    const firstPrice = prices[0];
    const priceChange = lastPrice - firstPrice;
    const percentChange = (priceChange / firstPrice) * 100;
    
    // Find high and low
    const high = Math.max(...chartData.price.high);
    const low = Math.min(...chartData.price.low);
    
    // Calculate volatility (standard deviation of daily returns)
    let returns = [];
    for (let i = 1; i < prices.length; i++) {
        returns.push((prices[i] - prices[i-1]) / prices[i-1]);
    }
    const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // Annualized volatility
    
    // Create modal for statistics
    let modalHtml = `
        <div class="modal fade" id="statisticsModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${currentSymbol} Statistics</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <table class="table table-striped">
                            <tbody>
                                <tr>
                                    <th>Current Price</th>
                                    <td>${lastPrice.toFixed(2)}</td>
                                </tr>
                                <tr>
                                    <th>Price Change</th>
                                    <td class="${priceChange >= 0 ? 'text-success' : 'text-danger'}">
                                        ${priceChange.toFixed(2)} (${percentChange.toFixed(2)}%)
                                    </td>
                                </tr>
                                <tr>
                                    <th>Period High</th>
                                    <td>${high.toFixed(2)}</td>
                                </tr>
                                <tr>
                                    <th>Period Low</th>
                                    <td>${low.toFixed(2)}</td>
                                </tr>
                                <tr>
                                    <th>Volatility (Annualized)</th>
                                    <td>${volatility.toFixed(2)}%</td>
                                </tr>
                                <tr>
                                    <th>Data Points</th>
                                    <td>${prices.length}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('statisticsModal'));
    modal.show();
    
    // Remove modal after it's hidden
    document.getElementById('statisticsModal').addEventListener('hidden.bs.modal', function() {
        modalContainer.remove();
    });
    
    Plotly.newPlot('rsiChart', [trace], layout, chartConfig);
}

// Create the MACD chart
function createMACDChart() {
    if (!chartData || !chartData.indicators.macd || !chartData.indicators.macd_signal) return;
    
    const macdLine = {
        x: chartData.datetime,
        y: chartData.indicators.macd,
        type: 'scatter',
        mode: 'lines',
        name: 'MACD',
        line: {
            color: 'blue',
            width: 1
        }
    };
    
    const signalLine = {
        x: chartData.datetime,
        y: chartData.indicators.macd_signal,
        type: 'scatter',
        mode: 'lines',
        name: 'Signal',
        line: {
            color: 'red',
            width: 1
        }
    };
    
    // Create histogram bars
    const histColors = [];
    for (let i = 0; i < chartData.indicators.macd_hist.length; i++) {
        histColors.push(chartData.indicators.macd_hist[i] >= 0 ? 'green' : 'red');
    }
    
    const histogram = {
        x: chartData.datetime,
        y: chartData.indicators.macd_hist,
        type: 'bar',
        name: 'Histogram',
        marker: {
            color: histColors
        }
    };
    
    const layout = {
        title: 'MACD (12,26,9)',
        xaxis: {
            rangeslider: {
                visible: false
            }
        },
        yaxis: {
            title: 'MACD'
        },
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    Plotly.newPlot('macdChart', [macdLine, signalLine, histogram], layout, chartConfig);
}

// Create the Stochastic chart
function createStochasticChart() {
    if (!chartData || !chartData.indicators.stoch_k || !chartData.indicators.stoch_d) return;
    
    const kLine = {
        x: chartData.datetime,
        y: chartData.indicators.stoch_k,
        type: 'scatter',
        mode: 'lines',
        name: '%K',
        line: {
            color: 'blue',
            width: 1
        }
    };
    
    const dLine = {
        x: chartData.datetime,
        y: chartData.indicators.stoch_d,
        type: 'scatter',
        mode: 'lines',
        name: '%D',
        line: {
            color: 'red',
            width: 1
        }
    };
    
    const layout = { 
        title: 'Stochastic Oscillator (14,3,3)', 
        xaxis: { 
            rangeslider: { visible: false } 
        }, 
        yaxis: { 
            title: 'Stochastic', 
            range: [0, 100] 
        }, 
        shapes: [
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 80,
                y1: 80,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: chartData.datetime[0],
                x1: chartData.datetime[chartData.datetime.length - 1],
                y0: 20,
                y1: 20,
                line: {
                    color: 'green',
                    width: 1,
                    dash: 'dash'
                }
            }
        ],
        margin: {
            t: 30,
            b: 30,
            l: 50,
            r: 50
        }
    };
    
    // Add annotations for key signals
    if (chartData.signals && chartData.signals.stoch_overbought) {
        const overboughtIndices = [];
        for (let i = 0; i < chartData.signals.stoch_overbought.length; i++) {
            if (chartData.signals.stoch_overbought[i] > 0) {
                overboughtIndices.push(i);
            }
        }
        
        if (overboughtIndices.length > 0) {
            // Add annotations for overbought signals
            overboughtIndices.forEach(idx => {
                layout.annotations = layout.annotations || [];
                layout.annotations.push({
                    x: chartData.datetime[idx],
                    y: chartData.indicators.stoch_k[idx],
                    text: 'Overbought',
                    showarrow: true,
                    arrowhead: 2,
                    arrowcolor: 'red',
                    arrowsize: 1,
                    arrowwidth: 1,
                    ax: -30,
                    ay: -20
                });
            });
        }
    }
    
    if (chartData.signals && chartData.signals.stoch_oversold) {
        const oversoldIndices = [];
        for (let i = 0; i < chartData.signals.stoch_oversold.length; i++) {
            if (chartData.signals.stoch_oversold[i] > 0) {
                oversoldIndices.push(i);
            }
        }
        
        if (oversoldIndices.length > 0) {
            // Add annotations for oversold signals
            oversoldIndices.forEach(idx => {
                layout.annotations = layout.annotations || [];
                layout.annotations.push({
                    x: chartData.datetime[idx],
                    y: chartData.indicators.stoch_k[idx],
                    text: 'Oversold',
                    showarrow: true,
                    arrowhead: 2,
                    arrowcolor: 'green',
                    arrowsize: 1,
                    arrowwidth: 1,
                    ax: 30,
                    ay: 20
                });
            });
        }
    }
    
    // Create the stochastic chart
    Plotly.newPlot('stochChart', [kLine, dLine], layout, chartConfig);
    
    // Add click event listener to the chart
    document.getElementById('stochChart').on('plotly_click', function(data) {
        // Get the point that was clicked
        const pointClicked = data.points[0];
        const dateClicked = pointClicked.x;
        const valueClicked = pointClicked.y;
        
        // Find the index of this point in our data
        const pointIndex = chartData.datetime.indexOf(dateClicked);
        if (pointIndex === -1) return;
        
        // Get values at this point
        const stochK = chartData.indicators.stoch_k[pointIndex];
        const stochD = chartData.indicators.stoch_d[pointIndex];
        const closePrice = chartData.price.close[pointIndex];
        
        // Create info popup
        const infoContent = `
            <div class="p-2">
                <h6>Stochastic Values at ${dateClicked}</h6>
                <table class="table table-sm">
                    <tr>
                        <th>%K:</th>
                        <td>${stochK.toFixed(2)}</td>
                    </tr>
                    <tr>
                        <th>%D:</th>
                        <td>${stochD.toFixed(2)}</td>
                    </tr>
                    <tr>
                        <th>Close Price:</th>
                        <td>${closePrice.toFixed(2)}</td>
                    </tr>
                </table>
            </div>
        `;
        
        // Show tooltip with information
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-custom';
        tooltip.innerHTML = infoContent;
        tooltip.style.position = 'absolute';
        tooltip.style.backgroundColor = 'white';
        tooltip.style.border = '1px solid #ddd';
        tooltip.style.borderRadius = '3px';
        tooltip.style.padding = '5px';
        tooltip.style.boxShadow = '0 0 10px rgba(0,0,0,0.1)';
        tooltip.style.zIndex = 1000;
        
        // Position tooltip near the point
        const chartRect = document.getElementById('stochChart').getBoundingClientRect();
        tooltip.style.left = data.event.pageX + 'px';
        tooltip.style.top = data.event.pageY + 'px';
        
        // Add tooltip to the document
        document.body.appendChild(tooltip);
        
        // Remove tooltip when clicked
        tooltip.addEventListener('click', function() {
            tooltip.remove();
        });
        
        // Also remove after 5 seconds
        setTimeout(function() {
            if (document.body.contains(tooltip)) {
                tooltip.remove();
            }
        }, 5000);
    });
    
    // Create the ADX chart
    function createADXChart() {
        if (!chartData || !chartData.indicators.adx) return;
        
        const adxLine = {
            x: chartData.datetime,
            y: chartData.indicators.adx,
            type: 'scatter',
            mode: 'lines',
            name: 'ADX',
            line: {
                color: 'black',
                width: 1
            }
        };
        
        // Add +DI and -DI if available
        const traces = [adxLine];
        
        if (chartData.indicators.plus_di) {
            const plusDI = {
                x: chartData.datetime,
                y: chartData.indicators.plus_di,
                type: 'scatter',
                mode: 'lines',
                name: '+DI',
                line: {
                    color: 'green',
                    width: 1
                }
            };
            traces.push(plusDI);
        }
        
        if (chartData.indicators.minus_di) {
            const minusDI = {
                x: chartData.datetime,
                y: chartData.indicators.minus_di,
                type: 'scatter',
                mode: 'lines',
                name: '-DI',
                line: {
                    color: 'red',
                    width: 1
                }
            };
            traces.push(minusDI);
        }
        
        const layout = {
            title: 'ADX (14)',
            xaxis: {
                rangeslider: {
                    visible: false
                }
            },
            yaxis: {
                title: 'ADX',
                range: [0, 100]
            },
            shapes: [
                {
                    type: 'line',
                    x0: chartData.datetime[0],
                    x1: chartData.datetime[chartData.datetime.length - 1],
                    y0: 25,
                    y1: 25,
                    line: {
                        color: 'orange',
                        width: 1,
                        dash: 'dash'
                    }
                }
            ],
            margin: {
                t: 30,
                b: 30,
                l: 50,
                r: 50
            }
        };
        
        // Add annotations for high ADX values (strong trend)
        if (chartData.indicators.adx) {
            const highAdxIndices = [];
            for (let i = 0; i < chartData.indicators.adx.length; i++) {
                if (chartData.indicators.adx[i] > 40) {
                    highAdxIndices.push(i);
                }
            }
            
            if (highAdxIndices.length > 0) {
                layout.annotations = [];
                // Just add annotation for the first and last high ADX points
                const firstIdx = highAdxIndices[0];
                const lastIdx = highAdxIndices[highAdxIndices.length - 1];
                
                layout.annotations.push({
                    x: chartData.datetime[firstIdx],
                    y: chartData.indicators.adx[firstIdx],
                    text: 'Strong Trend',
                    showarrow: true,
                    arrowhead: 2,
                    arrowcolor: 'purple',
                    arrowsize: 1,
                    arrowwidth: 1,
                    ax: 0,
                    ay: -30
                });
                
                if (firstIdx !== lastIdx) {
                    layout.annotations.push({
                        x: chartData.datetime[lastIdx],
                        y: chartData.indicators.adx[lastIdx],
                        text: 'Strong Trend',
                        showarrow: true,
                        arrowhead: 2,
                        arrowcolor: 'purple',
                        arrowsize: 1,
                        arrowwidth: 1,
                        ax: 0,
                        ay: -30
                    });
                }
            }
        }
        
        Plotly.newPlot('adxChart', traces, layout, chartConfig);
        
        // Add click event listener to the chart
        document.getElementById('adxChart').on('plotly_click', function(data) {
            // Get the point that was clicked
            const pointClicked = data.points[0];
            const dateClicked = pointClicked.x;
            
            // Find the index of this point in our data
            const pointIndex = chartData.datetime.indexOf(dateClicked);
            if (pointIndex === -1) return;
            
            // Get values at this point
            const adxValue = chartData.indicators.adx[pointIndex];
            const closePrice = chartData.price.close[pointIndex];
            
            let trendStrength = 'No trend';
            if (adxValue < 20) {
                trendStrength = 'Weak trend';
            } else if (adxValue < 40) {
                trendStrength = 'Moderate trend';
            } else {
                trendStrength = 'Strong trend';
            }
            
            // Create info popup
            const infoContent = `
                <div class="p-2">
                    <h6>ADX Values at ${dateClicked}</h6>
                    <table class="table table-sm">
                        <tr>
                            <th>ADX:</th>
                            <td>${adxValue.toFixed(2)}</td>
                        </tr>
                        <tr>
                            <th>Interpretation:</th>
                            <td>${trendStrength}</td>
                        </tr>
                        <tr>
                            <th>Close Price:</th>
                            <td>${closePrice.toFixed(2)}</td>
                        </tr>
                    </table>
                </div>
            `;
            
            // Show tooltip with information
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip-custom';
            tooltip.innerHTML = infoContent;
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = 'white';
            tooltip.style.border = '1px solid #ddd';
            tooltip.style.borderRadius = '3px';
            tooltip.style.padding = '5px';
            tooltip.style.boxShadow = '0 0 10px rgba(0,0,0,0.1)';
            tooltip.style.zIndex = 1000;
            
            // Position tooltip near the point
            tooltip.style.left = data.event.pageX + 'px';
            tooltip.style.top = data.event.pageY + 'px';
            
            // Add tooltip to the document
            document.body.appendChild(tooltip);
            
            // Remove tooltip when clicked
            tooltip.addEventListener('click', function() {
                tooltip.remove();
            });
            
            // Also remove after 5 seconds
            setTimeout(function() {
                if (document.body.contains(tooltip)) {
                    tooltip.remove();
                }
            }, 5000);
        });
    }
    
    // Create pattern comparison function
    function comparePatterns() {
        if (!chartData || !chartData.patterns) return;
        
        // Count all pattern occurrences
        const patternCounts = {
            bullish: {},
            bearish: {}
        };
        
        // Process bullish patterns
        if (chartData.patterns.bullish) {
            for (const pattern in chartData.patterns.bullish) {
                const values = chartData.patterns.bullish[pattern];
                const occurrences = values.filter(v => v > 0).length;
                patternCounts.bullish[pattern] = occurrences;
            }
        }
        
        // Process bearish patterns
        if (chartData.patterns.bearish) {
            for (const pattern in chartData.patterns.bearish) {
                const values = chartData.patterns.bearish[pattern];
                const occurrences = values.filter(v => v > 0).length;
                patternCounts.bearish[pattern] = occurrences;
            }
        }
        
        // Calculate success rates for each pattern
        const patternSuccessRates = {
            bullish: {},
            bearish: {}
        };
        
        // Check bullish patterns
        for (const pattern in patternCounts.bullish) {
            if (patternCounts.bullish[pattern] === 0) continue;
            
            const occurrences = [];
            
            // Find all occurrences of this pattern
            for (let i = 0; i < chartData.patterns.bullish[pattern].length; i++) {
                if (chartData.patterns.bullish[pattern][i] > 0) {
                    // Check if we have enough data to verify success
                    if (i + 5 < chartData.price.close.length) {
                        const entryPrice = chartData.price.close[i];
                        const exitPrice = chartData.price.close[i + 5]; // Check 5 bars later
                        const success = exitPrice > entryPrice;
                        
                        occurrences.push({
                            date: chartData.datetime[i],
                            entryPrice: entryPrice,
                            exitPrice: exitPrice,
                            change: ((exitPrice - entryPrice) / entryPrice) * 100,
                            success: success
                        });
                    }
                }
            }
            
            // Calculate success rate
            const successCount = occurrences.filter(o => o.success).length;
            const successRate = occurrences.length > 0 ? (successCount / occurrences.length) * 100 : 0;
            
            patternSuccessRates.bullish[pattern] = {
                rate: successRate.toFixed(1),
                total: occurrences.length,
                details: occurrences
            };
        }
        
        // Check bearish patterns
        for (const pattern in patternCounts.bearish) {
            if (patternCounts.bearish[pattern] === 0) continue;
            
            const occurrences = [];
            
            // Find all occurrences of this pattern
            for (let i = 0; i < chartData.patterns.bearish[pattern].length; i++) {
                if (chartData.patterns.bearish[pattern][i] > 0) {
                    // Check if we have enough data to verify success
                    if (i + 5 < chartData.price.close.length) {
                        const entryPrice = chartData.price.close[i];
                        const exitPrice = chartData.price.close[i + 5]; // Check 5 bars later
                        const success = exitPrice < entryPrice;
                        
                        occurrences.push({
                            date: chartData.datetime[i],
                            entryPrice: entryPrice,
                            exitPrice: exitPrice,
                            change: ((exitPrice - entryPrice) / entryPrice) * 100,
                            success: success
                        });
                    }
                }
            }
            
            // Calculate success rate
            const successCount = occurrences.filter(o => o.success).length;
            const successRate = occurrences.length > 0 ? (successCount / occurrences.length) * 100 : 0;
            
            patternSuccessRates.bearish[pattern] = {
                rate: successRate.toFixed(1),
                total: occurrences.length,
                details: occurrences
            };
        }
        
        // Create modal to display comparison
        let modalHtml = `
            <div class="modal fade" id="patternComparisonModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Pattern Backtesting Results for ${currentSymbol}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted">Success rate measured on 5-bar forward performance. 
                            For bullish patterns, success means a higher price 5 bars later.
                            For bearish patterns, success means a lower price 5 bars later.</p>
                            
                            <ul class="nav nav-tabs" id="patternTabs" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" id="bullish-tab" data-bs-toggle="tab" 
                                            data-bs-target="#bullish-patterns" type="button" role="tab" 
                                            aria-controls="bullish-patterns" aria-selected="true">
                                        Bullish Patterns
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="bearish-tab" data-bs-toggle="tab" 
                                            data-bs-target="#bearish-patterns" type="button" role="tab" 
                                            aria-controls="bearish-patterns" aria-selected="false">
                                        Bearish Patterns
                                    </button>
                                </li>
                            </ul>
                            
                            <div class="tab-content pt-3" id="patternTabContent">
                                <div class="tab-pane fade show active" id="bullish-patterns" role="tabpanel" 
                                     aria-labelledby="bullish-tab">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Pattern</th>
                                                <th>Occurrences</th>
                                                <th>Success Rate</th>
                                                <th>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>`;
        
        // Add bullish pattern rows
        for (const pattern in patternSuccessRates.bullish) {
            const data = patternSuccessRates.bullish[pattern];
            const displayName = pattern.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            
            let successClass = '';
            if (data.rate >= 70) {
                successClass = 'text-success fw-bold';
            } else if (data.rate >= 50) {
                successClass = 'text-primary';
            } else {
                successClass = 'text-danger';
            }
            
            modalHtml += `
                <tr>
                    <td>${displayName}</td>
                    <td>${data.total}</td>
                    <td class="${successClass}">${data.rate}%</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary pattern-details-btn" 
                                data-pattern="${pattern}" 
                                data-type="bullish">
                            Details
                        </button>
                    </td>
                </tr>`;
        }
        
        if (Object.keys(patternSuccessRates.bullish).length === 0) {
            modalHtml += `<tr><td colspan="4" class="text-center">No bullish patterns with sufficient data</td></tr>`;
        }
        
        modalHtml += `
                                        </tbody>
                                    </table>
                                </div>
                                <div class="tab-pane fade" id="bearish-patterns" role="tabpanel" 
                                     aria-labelledby="bearish-tab">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Pattern</th>
                                                <th>Occurrences</th>
                                                <th>Success Rate</th>
                                                <th>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>`;
        
        // Add bearish pattern rows
        for (const pattern in patternSuccessRates.bearish) {
            const data = patternSuccessRates.bearish[pattern];
            const displayName = pattern.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            
            let successClass = '';
            if (data.rate >= 70) {
                successClass = 'text-success fw-bold';
            } else if (data.rate >= 50) {
                successClass = 'text-primary';
            } else {
                successClass = 'text-danger';
            }
            
            modalHtml += `
                <tr>
                    <td>${displayName}</td>
                    <td>${data.total}</td>
                    <td class="${successClass}">${data.rate}%</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary pattern-details-btn" 
                                data-pattern="${pattern}" 
                                data-type="bearish">
                            Details
                        </button>
                    </td>
                </tr>`;
        }
        
        if (Object.keys(patternSuccessRates.bearish).length === 0) {
            modalHtml += `<tr><td colspan="4" class="text-center">No bearish patterns with sufficient data</td></tr>`;
        }
        
        modalHtml += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('patternComparisonModal'));
        modal.show();
        
        // Add event listeners for pattern details buttons
        document.querySelectorAll('.pattern-details-btn').forEach(button => {
            button.addEventListener('click', function() {
                const pattern = this.getAttribute('data-pattern');
                const type = this.getAttribute('data-type');
                
                // Get pattern details
                const details = patternSuccessRates[type][pattern].details;
                
                // Create details modal
                let detailsHtml = `
                    <div class="modal fade" id="patternDetailsModal" tabindex="-1" aria-hidden="true">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">${pattern.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} Details</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    <table class="table table-striped table-sm">
                                        <thead>
                                            <tr>
                                                <th>Date</th>
                                                <th>Entry</th>
                                                <th>Exit (5 bars)</th>
                                                <th>Change %</th>
                                                <th>Result</th>
                                            </tr>
                                        </thead>
                                        <tbody>`;
                
                // Add each occurrence
                details.forEach(occurrence => {
                    detailsHtml += `
                        <tr>
                            <td>${occurrence.date}</td>
                            <td>${occurrence.entryPrice.toFixed(2)}</td>
                            <td>${occurrence.exitPrice.toFixed(2)}</td>
                            <td class="${occurrence.success ? 'text-success' : 'text-danger'}">${occurrence.change.toFixed(2)}%</td>
                            <td>${occurrence.success ? '✓' : '✗'}</td>
                        </tr>`;
                });
                
                detailsHtml += `
                                        </tbody>
                                    </table>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add modal to page
                const detailsContainer = document.createElement('div');
                detailsContainer.innerHTML = detailsHtml;
                document.body.appendChild(detailsContainer);
                
                // Show modal
                const detailsModal = new bootstrap.Modal(document.getElementById('patternDetailsModal'));
                detailsModal.show();
                
                // Remove modal after it's hidden
                document.getElementById('patternDetailsModal').addEventListener('hidden.bs.modal', function() {
                    detailsContainer.remove();
                });
            });
        });
        
        // Remove modal after it's hidden
        document.getElementById('patternComparisonModal').addEventListener('hidden.bs.modal', function() {
            modalContainer.remove();
        });
    }
    
    // Add a function to show all indicators at once in a dashboard view
    function showAllIndicators() {
        if (!chartData) return;
        
        // First, make sure all indicator charts are visible
        document.getElementById('rsiChart').style.display = 'block';
        document.getElementById('macdChart').style.display = 'block';
        document.getElementById('stochChart').style.display = 'block';
        document.getElementById('adxChart').style.display = 'block';
        
        // Update the checkboxes to match
        document.getElementById('showRSI').checked = true;
        document.getElementById('showMACD').checked = true;
        document.getElementById('showStochastic').checked = true;
        document.getElementById('showADX').checked = true;
        
        // Create the charts if they don't exist yet
        createRSIChart();
        createMACDChart();
        createStochasticChart();
        createADXChart();
        
        // Calculate performance metrics
        const performance = calculatePerformance();
        
        // Show toast confirmation
        showToast('All indicators displayed', 'info');
    }
    
    // Function to print a summary report
    function printSummaryReport() {
        if (!chartData) return;
        
        // Create a report window
        const reportWindow = window.open('', '_blank', 'width=800,height=600');
        reportWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>${currentSymbol} Technical Analysis Report</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { padding: 20px; }
                    .header { text-align: center; margin-bottom: 20px; }
                    .section { margin-bottom: 30px; }
                    .table { margin-bottom: 15px; }
                    .footer { text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>${currentSymbol} Technical Analysis Report</h2>
                    <p class="text-muted">Generated on ${new Date().toLocaleString()}</p>
                </div>
                
                <div class="section">
                    <h4>Price Summary</h4>
                    <table class="table table-bordered table-sm">
                        <tbody>
                            <tr>
                                <th>Current Price</th>
                                <td>${chartData.price.close[chartData.price.close.length-1].toFixed(2)}</td>
                                <th>Open Price</th>
                                <td>${chartData.price.open[0].toFixed(2)}</td>
                            </tr>
                            <tr>
                                <th>High</th>
                                <td>${Math.max(...chartData.price.high).toFixed(2)}</td>
                                <th>Low</th>
                                <td>${Math.min(...chartData.price.low).toFixed(2)}</td>
                            </tr>
                            <tr>
                                <th>Price Change</th>
                                <td colspan="3">${(chartData.price.close[chartData.price.close.length-1] - chartData.price.open[0]).toFixed(2)} 
                                (${(((chartData.price.close[chartData.price.close.length-1] - chartData.price.open[0]) / chartData.price.open[0]) * 100).toFixed(2)}%)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h4>Technical Indicators</h4>
                    <table class="table table-bordered table-sm">
                        <tbody>
        `);
        
        // Add technical indicator values
        const lastIdx = chartData.price.close.length - 1;
        
        reportWindow.document.write(`
                            <tr>
                                <th>RSI (14)</th>
                                <td>${chartData.indicators.rsi ? chartData.indicators.rsi[lastIdx].toFixed(2) : 'N/A'}</td>
                                <th>MACD</th>
                                <td>${chartData.indicators.macd ? chartData.indicators.macd[lastIdx].toFixed(2) : 'N/A'}</td>
                            </tr>
                            <tr>
                            <th>Stochastic %K</th>
                            <td>${chartData.indicators.stoch_k ? chartData.indicators.stoch_k[lastIdx].toFixed(2) : 'N/A'}</td>
                            <th>Stochastic %D</th>
                            <td>${chartData.indicators.stoch_d ? chartData.indicators.stoch_d[lastIdx].toFixed(2) : 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>ADX</th>
                            <td>${chartData.indicators.adx ? chartData.indicators.adx[lastIdx].toFixed(2) : 'N/A'}</td>
                            <th>ATR</th>
                            <td>${chartData.indicators.atr ? chartData.indicators.atr[lastIdx].toFixed(2) : 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>SMA 20</th>
                            <td>${chartData.indicators.sma_20 ? chartData.indicators.sma_20[lastIdx].toFixed(2) : 'N/A'}</td>
                            <th>SMA 50</th>
                            <td>${chartData.indicators.sma_50 ? chartData.indicators.sma_50[lastIdx].toFixed(2) : 'N/A'}</td>
                        </tr>
                        <tr>
                            <th>SMA 200</th>
                            <td>${chartData.indicators.sma_200 ? chartData.indicators.sma_200[lastIdx].toFixed(2) : 'N/A'}</td>
                            <th>Bollinger Bands</th>
                            <td>
                                Upper: ${chartData.indicators.bb_upper ? chartData.indicators.bb_upper[lastIdx].toFixed(2) : 'N/A'}<br>
                                Middle: ${chartData.indicators.bb_middle ? chartData.indicators.bb_middle[lastIdx].toFixed(2) : 'N/A'}<br>
                                Lower: ${chartData.indicators.bb_lower ? chartData.indicators.bb_lower[lastIdx].toFixed(2) : 'N/A'}
                            </td>
                        </tr>
    `);
    
    // Add signal summary
    reportWindow.document.write(`
            </tbody>
            </table>
            </div>
            
            <div class="section">
                <h4>Technical Signals</h4>
                <div class="row">
                    <div class="col-md-6">
                        <h5 class="text-success">Bullish Signals</h5>
                        <table class="table table-sm">
                            <tbody>
    `);
    
    // Process bullish signals
    const bullishSignals = [
        { name: 'RSI Oversold', key: 'rsi_oversold' },
        { name: 'MACD Bullish Cross', key: 'macd_bullish_cross' },
        { name: 'Bollinger Lower Touch', key: 'bb_lower_touch' },
        { name: 'Golden Cross', key: 'golden_cross' },
        { name: 'Stochastic Oversold', key: 'stoch_oversold' }
    ];
    
    let hasBullishSignals = false;
    bullishSignals.forEach(signal => {
        if (chartData.signals && chartData.signals[signal.key]) {
            const count = chartData.signals[signal.key].filter(val => val > 0).length;
            if (count > 0) {
                hasBullishSignals = true;
                reportWindow.document.write(`
                    <tr>
                        <td>${signal.name}</td>
                        <td>${count}</td>
                    </tr>
                `);
            }
        }
    });
    
    if (!hasBullishSignals) {
        reportWindow.document.write(`
            <tr>
                <td colspan="2">No bullish signals detected</td>
            </tr>
        `);
    }
    
    reportWindow.document.write(`
                        </tbody>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5 class="text-danger">Bearish Signals</h5>
                    <table class="table table-sm">
                        <tbody>
    `);
    
    // Process bearish signals
    const bearishSignals = [
        { name: 'RSI Overbought', key: 'rsi_overbought' },
        { name: 'MACD Bearish Cross', key: 'macd_bearish_cross' },
        { name: 'Bollinger Upper Touch', key: 'bb_upper_touch' },
        { name: 'Death Cross', key: 'death_cross' },
        { name: 'Stochastic Overbought', key: 'stoch_overbought' }
    ];
    
    let hasBearishSignals = false;
    bearishSignals.forEach(signal => {
        if (chartData.signals && chartData.signals[signal.key]) {
            const count = chartData.signals[signal.key].filter(val => val > 0).length;
            if (count > 0) {
                hasBearishSignals = true;
                reportWindow.document.write(`
                    <tr>
                        <td>${signal.name}</td>
                        <td>${count}</td>
                    </tr>
                `);
            }
        }
    });
    
    if (!hasBearishSignals) {
        reportWindow.document.write(`
            <tr>
                <td colspan="2">No bearish signals detected</td>
            </tr>
        `);
    }
    
    reportWindow.document.write(`
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h4>Candlestick Patterns</h4>
            <div class="row">
                <div class="col-md-6">
                    <h5 class="text-success">Bullish Patterns</h5>
                    <table class="table table-sm">
                        <tbody>
    `);
    
    // Process bullish patterns
    let hasBullishPatterns = false;
    if (chartData.patterns && chartData.patterns.bullish) {
        for (const pattern in chartData.patterns.bullish) {
            const count = chartData.patterns.bullish[pattern].filter(val => val > 0).length;
            if (count > 0) {
                hasBullishPatterns = true;
                const displayName = pattern.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                reportWindow.document.write(`
                    <tr>
                        <td>${displayName}</td>
                        <td>${count}</td>
                    </tr>
                `);
            }
        }
    }
    
    if (!hasBullishPatterns) {
        reportWindow.document.write(`
            <tr>
                <td colspan="2">No bullish patterns detected</td>
            </tr>
        `);
    }
    
    reportWindow.document.write(`
                        </tbody>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5 class="text-danger">Bearish Patterns</h5>
                    <table class="table table-sm">
                        <tbody>
    `);
    
    // Process bearish patterns
    let hasBearishPatterns = false;
    if (chartData.patterns && chartData.patterns.bearish) {
        for (const pattern in chartData.patterns.bearish) {
            const count = chartData.patterns.bearish[pattern].filter(val => val > 0).length;
            if (count > 0) {
                hasBearishPatterns = true;
                const displayName = pattern.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                reportWindow.document.write(`
                    <tr>
                        <td>${displayName}</td>
                        <td>${count}</td>
                    </tr>
                `);
            }
        }
    }
    
    if (!hasBearishPatterns) {
        reportWindow.document.write(`
            <tr>
                <td colspan="2">No bearish patterns detected</td>
            </tr>
        `);
    }
    
    // Add performance metrics
    const performance = calculatePerformance();
    
    reportWindow.document.write(`
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h4>Performance Metrics</h4>
            <table class="table table-bordered table-sm">
                <tbody>
                    <tr>
                        <th>Total Return</th>
                        <td>${performance ? performance.totalReturn : 'N/A'}</td>
                        <th>Max Drawdown</th>
                        <td>${performance ? performance.maxDrawdown : 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Annualized Return</th>
                        <td>${performance ? performance.annualizedReturn : 'N/A'}</td>
                        <th>Volatility</th>
                        <td>${performance ? performance.volatility : 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Sharpe Ratio</th>
                        <td>${performance ? performance.sharpeRatio : 'N/A'}</td>
                        <th>Average Daily Return</th>
                        <td>${performance ? performance.avgDailyReturn : 'N/A'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h4>Trend Analysis</h4>
            <p>
    `);
    
    // Add trend analysis
    let trendDirection = 'Neutral';
    if (chartData.indicators.sma_20 && chartData.indicators.sma_50) {
        if (chartData.indicators.sma_20[lastIdx] > chartData.indicators.sma_50[lastIdx]) {
            trendDirection = 'Bullish';
        } else if (chartData.indicators.sma_20[lastIdx] < chartData.indicators.sma_50[lastIdx]) {
            trendDirection = 'Bearish';
        }
    }
    
    let adxStrength = 'Weak';
    if (chartData.indicators.adx) {
        const adxValue = chartData.indicators.adx[lastIdx];
        if (adxValue >= 40) {
            adxStrength = 'Strong';
        } else if (adxValue >= 20) {
            adxStrength = 'Moderate';
        }
    }
    
    reportWindow.document.write(`
                The current trend for ${currentSymbol} is <strong>${trendDirection}</strong> with 
                <strong>${adxStrength}</strong> strength. 
    `);
    
    // Add RSI conditions
    if (chartData.indicators.rsi) {
        const rsiValue = chartData.indicators.rsi[lastIdx];
        if (rsiValue > 70) {
            reportWindow.document.write(`
                The RSI is currently in <strong class="text-danger">overbought</strong> territory at ${rsiValue.toFixed(2)}.
            `);
        } else if (rsiValue < 30) {
            reportWindow.document.write(`
                The RSI is currently in <strong class="text-success">oversold</strong> territory at ${rsiValue.toFixed(2)}.
            `);
        } else {
            reportWindow.document.write(`
                The RSI is currently in <strong>neutral</strong> territory at ${rsiValue.toFixed(2)}.
            `);
        }
    }
    
    // Add MACD conditions
    if (chartData.indicators.macd && chartData.indicators.macd_signal) {
        const macdValue = chartData.indicators.macd[lastIdx];
        const signalValue = chartData.indicators.macd_signal[lastIdx];
        
        if (macdValue > signalValue) {
            reportWindow.document.write(`
                <br>The MACD is above the signal line, indicating <strong class="text-success">bullish</strong> momentum.
            `);
        } else {
            reportWindow.document.write(`
                <br>The MACD is below the signal line, indicating <strong class="text-danger">bearish</strong> momentum.
            `);
        }
    }
    
    // Close the final tags
    reportWindow.document.write(`
            </p>
        </div>
        
        <div class="footer">
            <p>This report was generated by the Trading Signal Verification Dashboard.</p>
            <p>Data analysis date: ${new Date().toLocaleDateString()}</p>
        </div>
        
        <script>
            window.onload = function() {
                window.print();
            }
        </script>
    </body>
    </html>
    `);
    
    reportWindow.document.close();
}

// Function to compare multiple symbols
function compareSymbols(symbols) {
    if (!symbols || symbols.length < 2) {
        // Prompt user to select symbols for comparison
        const modalHtml = `
            <div class="modal fade" id="compareSymbolsModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Compare Symbols</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>Select symbols to compare with ${currentSymbol}:</p>
                            <div class="mb-3" id="symbolCheckboxes">
                                Loading symbols...
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="runComparisonBtn">Compare</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('compareSymbolsModal'));
        modal.show();
        
        // Load available symbols
        fetch('/api/data/')
            .then(response => response.json())
            .then(data => {
                if (data.available_symbols) {
                    let checkboxesHtml = '';
                    data.available_symbols.forEach(symbol => {
                        if (symbol !== currentSymbol) {
                            checkboxesHtml += `
                                <div class="form-check">
                                    <input class="form-check-input symbol-checkbox" type="checkbox" value="${symbol}" id="check_${symbol}">
                                    <label class="form-check-label" for="check_${symbol}">
                                        ${symbol}
                                    </label>
                                </div>
                            `;
                        }
                    });
                    
                    if (checkboxesHtml) {
                        document.getElementById('symbolCheckboxes').innerHTML = checkboxesHtml;
                    } else {
                        document.getElementById('symbolCheckboxes').innerHTML = 'No other symbols available for comparison';
                    }
                } else {
                    document.getElementById('symbolCheckboxes').innerHTML = 'Error loading symbols';
                }
            })
            .catch(error => {
                document.getElementById('symbolCheckboxes').innerHTML = 'Error loading symbols: ' + error.message;
            });
        
        // Set up button event handler
        document.getElementById('runComparisonBtn').addEventListener('click', function() {
            // Get selected symbols
            const selectedSymbols = [];
            document.querySelectorAll('.symbol-checkbox:checked').forEach(checkbox => {
                selectedSymbols.push(checkbox.value);
            });
            
            if (selectedSymbols.length > 0) {
                // Add current symbol
                selectedSymbols.unshift(currentSymbol);
                
                // Close modal
                modal.hide();
                
                // Run comparison with selected symbols
                runSymbolComparison(selectedSymbols);
            } else {
                alert('Please select at least one symbol to compare');
            }
        });
        
        // Remove modal after it's hidden
        document.getElementById('compareSymbolsModal').addEventListener('hidden.bs.modal', function() {
            modalContainer.remove();
        });
    } else {
        // Run comparison directly with provided symbols
        runSymbolComparison(symbols);
    }
}

// Function to actually run the symbol comparison
function runSymbolComparison(symbols) {
    if (!symbols || symbols.length < 2) return;
    
    // Show loading toast
    showToast(`Loading data for ${symbols.length} symbols...`, 'info');
    
    // Store promises for all symbol data
    const dataPromises = symbols.map(symbol => 
        fetch(`/api/data/${symbol}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error loading ${symbol}`);
                }
                return response.json();
            })
            .then(data => {
                return { symbol, data };
            })
            .catch(error => {
                console.error(`Error loading ${symbol}:`, error);
                return { symbol, error };
            })
    );
    
    // Wait for all data to load
    Promise.all(dataPromises)
        .then(results => {
            // Filter out any failed loads
            const validResults = results.filter(result => !result.error);
            
            if (validResults.length < 2) {
                showToast('Not enough valid data for comparison', 'danger');
                return;
            }
            
            // Create comparison table
            createComparisonTable(validResults);
        })
        .catch(error => {
            showToast(`Error in comparison: ${error.message}`, 'danger');
        });
}

// Function to create the comparison table
function createComparisonTable(symbolData) {
    // Create modal for comparison
    let modalHtml = `
        <div class="modal fade" id="symbolComparisonModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Symbol Comparison</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <ul class="nav nav-tabs" id="comparisonTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="price-tab" data-bs-toggle="tab" 
                                        data-bs-target="#price-comparison" type="button" role="tab" 
                                        aria-controls="price-comparison" aria-selected="true">
                                    Price Data
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="indicators-tab" data-bs-toggle="tab" 
                                        data-bs-target="#indicators-comparison" type="button" role="tab" 
                                        aria-controls="indicators-comparison" aria-selected="false">
                                    Indicators
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="signals-tab" data-bs-toggle="tab" 
                                        data-bs-target="#signals-comparison" type="button" role="tab" 
                                        aria-controls="signals-comparison" aria-selected="false">
                                    Signals
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="performance-tab" data-bs-toggle="tab" 
                                        data-bs-target="#performance-comparison" type="button" role="tab" 
                                        aria-controls="performance-comparison" aria-selected="false">
                                    Performance
                                </button>
                            </li>
                        </ul>
                        <div class="tab-content pt-3" id="comparisonTabContent">
                            <div class="tab-pane fade show active" id="price-comparison" role="tabpanel" 
                                 aria-labelledby="price-tab">
                                <table class="table table-striped table-hover">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            ${symbolData.map(item => `<th>${item.symbol}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <th>Current Price</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.price.close.length - 1;
                                                return `<td>${item.data.price.close[lastIdx].toFixed(2)}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Open Price</th>
                                            ${symbolData.map(item => `<td>${item.data.price.open[0].toFixed(2)}</td>`).join('')}
                                        </tr>
                                        <tr>
                                            <th>High</th>
                                            ${symbolData.map(item => `<td>${Math.max(...item.data.price.high).toFixed(2)}</td>`).join('')}
                                        </tr>
                                        <tr>
                                            <th>Low</th>
                                            ${symbolData.map(item => `<td>${Math.min(...item.data.price.low).toFixed(2)}</td>`).join('')}
                                        </tr>
                                        <tr>
                                            <th>Price Change</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.price.close.length - 1;
                                                const change = item.data.price.close[lastIdx] - item.data.price.open[0];
                                                const pctChange = (change / item.data.price.open[0]) * 100;
                                                const colorClass = change >= 0 ? 'text-success' : 'text-danger';
                                                return `<td class="${colorClass}">${change.toFixed(2)} (${pctChange.toFixed(2)}%)</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Average Volume</th>
                                            ${symbolData.map(item => {
                                                const avgVol = item.data.price.volume.reduce((sum, vol) => sum + vol, 0) / item.data.price.volume.length;
                                                return `<td>${Math.round(avgVol).toLocaleString()}</td>`;
                                            }).join('')}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div class="tab-pane fade" id="indicators-comparison" role="tabpanel" 
                                 aria-labelledby="indicators-tab">
                                <table class="table table-striped table-hover">
                                    <thead>
                                        <tr>
                                            <th>Indicator</th>
                                            ${symbolData.map(item => `<th>${item.symbol}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <th>RSI (14)</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.indicators.rsi.length - 1;
                                                const rsi = item.data.indicators.rsi[lastIdx];
                                                let colorClass = '';
                                                if (rsi > 70) colorClass = 'text-danger';
                                                else if (rsi < 30) colorClass = 'text-success';
                                                return `<td class="${colorClass}">${rsi.toFixed(2)}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>MACD</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.indicators.macd.length - 1;
                                                const macd = item.data.indicators.macd[lastIdx];
                                                const signal = item.data.indicators.macd_signal[lastIdx];
                                                const colorClass = macd > signal ? 'text-success' : 'text-danger';
                                                return `<td class="${colorClass}">${macd.toFixed(2)}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>ADX</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.indicators.adx.length - 1;
                                                const adx = item.data.indicators.adx[lastIdx];
                                                let trendStrength = '';
                                                if (adx >= 40) trendStrength = 'Strong';
                                                else if (adx >= 20) trendStrength = 'Moderate';
                                                else trendStrength = 'Weak';
                                                return `<td>${adx.toFixed(2)} (${trendStrength})</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>SMA20 vs SMA50</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.indicators.sma_20.length - 1;
                                                const sma20 = item.data.indicators.sma_20[lastIdx];
                                                const sma50 = item.data.indicators.sma_50[lastIdx];
                                                const comparison = sma20 > sma50 ? 'Above (Bullish)' : 'Below (Bearish)';
                                                const colorClass = sma20 > sma50 ? 'text-success' : 'text-danger';
                                                return `<td class="${colorClass}">${comparison}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>BB Width</th>
                                            ${symbolData.map(item => {
                                                const lastIdx = item.data.indicators.bb_upper.length - 1;
                                                const upper = item.data.indicators.bb_upper[lastIdx];
                                                const lower = item.data.indicators.bb_lower[lastIdx];
                                                const middle = item.data.indicators.bb_middle[lastIdx];
                                                const width = ((upper - lower) / middle) * 100;
                                                return `<td>${width.toFixed(2)}%</td>`;
                                            }).join('')}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div class="tab-pane fade" id="signals-comparison" role="tabpanel" 
                                 aria-labelledby="signals-tab">
                                <table class="table table-striped table-hover">
                                    <thead>
                                        <tr>
                                            <th>Signal Type</th>
                                            ${symbolData.map(item => `<th>${item.symbol}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <th>Bullish Signals</th>
                                            ${symbolData.map(item => {
                                                let count = 0;
                                                const signals = item.data.signals;
                                                if (signals.rsi_oversold) count += signals.rsi_oversold.filter(val => val > 0).length;
                                                if (signals.macd_bullish_cross) count += signals.macd_bullish_cross.filter(val => val > 0).length;
                                                if (signals.bb_lower_touch) count += signals.bb_lower_touch.filter(val => val > 0).length;
                                                if (signals.golden_cross) count += signals.golden_cross.filter(val => val > 0).length;
                                                return `<td>${count}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Bearish Signals</th>
                                            ${symbolData.map(item => {
                                                let count = 0;
                                                const signals = item.data.signals;
                                                if (signals.rsi_overbought) count += signals.rsi_overbought.filter(val => val > 0).length;
                                                if (signals.macd_bearish_cross) count += signals.macd_bearish_cross.filter(val => val > 0).length;
                                                if (signals.bb_upper_touch) count += signals.bb_upper_touch.filter(val => val > 0).length;
                                                if (signals.death_cross) count += signals.death_cross.filter(val => val > 0).length;
                                                return `<td>${count}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Bullish Patterns</th>
                                            ${symbolData.map(item => {
                                                let count = 0;
                                                if (item.data.patterns && item.data.patterns.bullish) {
                                                    Object.values(item.data.patterns.bullish).forEach(pattern => {
                                                        count += pattern.filter(val => val > 0).length;
                                                    });
                                                }
                                                return `<td>${count}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Bearish Patterns</th>
                                            ${symbolData.map(item => {
                                                let count = 0;
                                                if (item.data.patterns && item.data.patterns.bearish) {
                                                    Object.values(item.data.patterns.bearish).forEach(pattern => {
                                                        count += pattern.filter(val => val > 0).length;
                                                    });
                                                }
                                                return `<td>${count}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Overall Signal Strength</th>
                                            ${symbolData.map(item => {
                                                // Calculate bullish vs bearish signal ratio
                                                let bullishCount = 0;
                                                let bearishCount = 0;
                                                
                                                const signals = item.data.signals;
                                                if (signals.rsi_oversold) bullishCount += signals.rsi_oversold.filter(val => val > 0).length;
                                                if (signals.macd_bullish_cross) bullishCount += signals.macd_bullish_cross.filter(val => val > 0).length;
                                                if (signals.bb_lower_touch) bullishCount += signals.bb_lower_touch.filter(val => val > 0).length;
                                                if (signals.golden_cross) bullishCount += signals.golden_cross.filter(val => val > 0).length;
                                                
                                                if (signals.rsi_overbought) bearishCount += signals.rsi_overbought.filter(val => val > 0).length;
                                                if (signals.macd_bearish_cross) bearishCount += signals.macd_bearish_cross.filter(val => val > 0).length;
                                                if (signals.bb_upper_touch) bearishCount += signals.bb_upper_touch.filter(val => val > 0).length;
                                                if (signals.death_cross) bearishCount += signals.death_cross.filter(val => val > 0).length;
                                                
                                                // Add pattern counts
                                                if (item.data.patterns && item.data.patterns.bullish) {
                                                    Object.values(item.data.patterns.bullish).forEach(pattern => {
                                                        bullishCount += pattern.filter(val => val > 0).length;
                                                    });
                                                }
                                                
                                                if (item.data.patterns && item.data.patterns.bearish) {
                                                    Object.values(item.data.patterns.bearish).forEach(pattern => {
                                                        bearishCount += pattern.filter(val => val > 0).length;
                                                    });
                                                }
                                                
                                                let signalStrength = 'Neutral';
                                                let colorClass = '';
                                                
                                                if (bullishCount > bearishCount * 2) {
                                                    signalStrength = 'Strong Bullish';
                                                    colorClass = 'text-success fw-bold';
                                                } else if (bullishCount > bearishCount) {
                                                    signalStrength = 'Moderate Bullish';
                                                    colorClass = 'text-success';
                                                } else if (bearishCount > bullishCount * 2) {
                                                    signalStrength = 'Strong Bearish';
                                                    colorClass = 'text-danger fw-bold';
                                                } else if (bearishCount > bullishCount) {
                                                    signalStrength = 'Moderate Bearish';
                                                    colorClass = 'text-danger';
                                                }
                                                
                                                return `<td class="${colorClass}">${signalStrength}</td>`;
                                            }).join('')}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div class="tab-pane fade" id="performance-comparison" role="tabpanel" 
                                 aria-labelledby="performance-tab">
                                <table class="table table-striped table-hover">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            ${symbolData.map(item => `<th>${item.symbol}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <th>Total Return</th>
                                            ${symbolData.map(item => {
                                                const prices = item.data.price.close;
                                                const totalReturn = ((prices[prices.length-1] - prices[0]) / prices[0]) * 100;
                                                const colorClass = totalReturn >= 0 ? 'text-success' : 'text-danger';
                                                return `<td class="${colorClass}">${totalReturn.toFixed(2)}%</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Volatility</th>
                                            ${symbolData.map(item => {
                                                const prices = item.data.price.close;
                                                const returns = [];
                                                for (let i = 1; i < prices.length; i++) {
                                                    returns.push((prices[i] - prices[i-1]) / prices[i-1]);
                                                }
                                                const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
                                                const variance = returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length;
                                                const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100;
                                                return `<td>${volatility.toFixed(2)}%</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Sharpe Ratio</th>
                                            ${symbolData.map(item => {
                                                const prices = item.data.price.close;
                                                const returns = [];
                                                for (let i = 1; i < prices.length; i++) {
                                                    returns.push((prices[i] - prices[i-1]) / prices[i-1]);
                                                }
                                                const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
                                                const variance = returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length;
                                                const volatility = Math.sqrt(variance);
                                                const sharpeRatio = (avgReturn * 252) / (volatility * Math.sqrt(252));
                                                
                                                let colorClass = '';
                                                if (sharpeRatio > 1) colorClass = 'text-success';
                                                else if (sharpeRatio < 0) colorClass = 'text-danger';
                                                
                                                return `<td class="${colorClass}">${sharpeRatio.toFixed(2)}</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Drawdown</th>
                                            ${symbolData.map(item => {
                                                const prices = item.data.price.close;
                                                let maxDrawdown = 0;
                                                let peak = prices[0];
                                                
                                                for (let i = 1; i < prices.length; i++) {
                                                    if (prices[i] > peak) {
                                                        peak = prices[i];
                                                    } else {
                                                        const drawdown = (peak - prices[i]) / peak * 100;
                                                        if (drawdown > maxDrawdown) {
                                                            maxDrawdown = drawdown;
                                                        }
                                                    }
                                                }
                                                
                                                return `<td class="text-danger">-${maxDrawdown.toFixed(2)}%</td>`;
                                            }).join('')}
                                        </tr>
                                        <tr>
                                            <th>Correlation to ${symbolData[0].symbol}</th>
                                            ${symbolData.map((item, index) => {
                                                if (index === 0) {
                                                    return '<td>1.00</td>'; // Self-correlation is always 1
                                                } else {
                                                    const prices1 = symbolData[0].data.price.close;
                                                    const prices2 = item.data.price.close;
                                                    
                                                    // Calculate returns for correlation
                                                    const returns1 = [];
                                                    const returns2 = [];
                                                    
                                                    const minLength = Math.min(prices1.length, prices2.length);
                                                    
                                                    for (let i = 1; i < minLength; i++) {
                                                        returns1.push((prices1[i] - prices1[i-1]) / prices1[i-1]);
                                                        returns2.push((prices2[i] - prices2[i-1]) / prices2[i-1]);
                                                    }
                                                    
                                                    // Calculate correlation
                                                    const avg1 = returns1.reduce((a, b) => a + b, 0) / returns1.length;
                                                    const avg2 = returns2.reduce((a, b) => a + b, 0) / returns2.length;
                                                    
                                                    let numerator = 0;
                                                    for (let i = 0; i < returns1.length; i++) {
                                                        numerator += (returns1[i] - avg1) * (returns2[i] - avg2);
                                                    }
                                                    
                                                    let denominator1 = 0;
                                                    let denominator2 = 0;
                                                    
                                                    for (let i = 0; i < returns1.length; i++) {
                                                        denominator1 += Math.pow(returns1[i] - avg1, 2);
                                                        denominator2 += Math.pow(returns2[i] - avg2, 2);
                                                    }
                                                    
                                                    const correlation = numerator / Math.sqrt(denominator1 * denominator2);
                                                    
                                                    let colorClass = '';
                                                    if (correlation > 0.7) colorClass = 'text-danger'; // High correlation
                                                    else if (correlation < 0.3) colorClass = 'text-success'; // Low correlation
                                                    
                                                    return `<td class="${colorClass}">${correlation.toFixed(2)}</td>`;
                                                }
                                            }).join('')}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-primary" id="exportComparisonBtn">Export Comparison</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the page
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('symbolComparisonModal'));
    modal.show();
    
    // Set up export button
    document.getElementById('exportComparisonBtn').addEventListener('click', function() {
        exportComparisonTable(symbolData);
    });
    
    // Remove modal when hidden
    document.getElementById('symbolComparisonModal').addEventListener('hidden.bs.modal', function() {
        modalContainer.remove();
    });
    
    // Show success toast
    showToast(`Comparison of ${symbolData.length} symbols completed`, 'success');
}

// Function to export the comparison table
function exportComparisonTable(symbolData) {
    // Create a CSV content
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add headers
    csvContent += "Metric," + symbolData.map(item => item.symbol).join(",") + "\n";
    
    // Price data
    csvContent += "Current Price," + symbolData.map(item => {
        const lastIdx = item.data.price.close.length - 1;
        return item.data.price.close[lastIdx].toFixed(2);
    }).join(",") + "\n";
    
    csvContent += "Open Price," + symbolData.map(item => item.data.price.open[0].toFixed(2)).join(",") + "\n";
    
    csvContent += "High," + symbolData.map(item => Math.max(...item.data.price.high).toFixed(2)).join(",") + "\n";
    
    csvContent += "Low," + symbolData.map(item => Math.min(...item.data.price.low).toFixed(2)).join(",") + "\n";
    
    csvContent += "Price Change," + symbolData.map(item => {
        const lastIdx = item.data.price.close.length - 1;
        const change = item.data.price.close[lastIdx] - item.data.price.open[0];
        const pctChange = (change / item.data.price.open[0]) * 100;
        return `${change.toFixed(2)} (${pctChange.toFixed(2)}%)`;
    }).join(",") + "\n";
    
    // Indicator data
    csvContent += "RSI (14)," + symbolData.map(item => {
        const lastIdx = item.data.indicators.rsi.length - 1;
        return item.data.indicators.rsi[lastIdx].toFixed(2);
    }).join(",") + "\n";
    
    csvContent += "MACD," + symbolData.map(item => {
        const lastIdx = item.data.indicators.macd.length - 1;
        return item.data.indicators.macd[lastIdx].toFixed(2);
    }).join(",") + "\n";
    
    csvContent += "ADX," + symbolData.map(item => {
        const lastIdx = item.data.indicators.adx.length - 1;
        return item.data.indicators.adx[lastIdx].toFixed(2);
    }).join(",") + "\n";
    
    // Signal counts
    csvContent += "Bullish Signals," + symbolData.map(item => {
        let count = 0;
        const signals = item.data.signals;
        if (signals.rsi_oversold) count += signals.rsi_oversold.filter(val => val > 0).length;
        if (signals.macd_bullish_cross) count += signals.macd_bullish_cross.filter(val => val > 0).length;
        if (signals.bb_lower_touch) count += signals.bb_lower_touch.filter(val => val > 0).length;
        if (signals.golden_cross) count += signals.golden_cross.filter(val => val > 0).length;
        return count;
    }).join(",") + "\n";
    
    csvContent += "Bearish Signals," + symbolData.map(item => {
        let count = 0;
        const signals = item.data.signals;
        if (signals.rsi_overbought) count += signals.rsi_overbought.filter(val => val > 0).length;
        if (signals.macd_bearish_cross) count += signals.macd_bearish_cross.filter(val => val > 0).length;
        if (signals.bb_upper_touch) count += signals.bb_upper_touch.filter(val => val > 0).length;
        if (signals.death_cross) count += signals.death_cross.filter(val => val > 0).length;
        return count;
    }).join(",") + "\n";
    
    // Performance metrics
    csvContent += "Total Return (%)," + symbolData.map(item => {
        const prices = item.data.price.close;
        const totalReturn = ((prices[prices.length-1] - prices[0]) / prices[0]) * 100;
        return totalReturn.toFixed(2);
    }).join(",") + "\n";
    
    csvContent += "Volatility (%)," + symbolData.map(item => {
        const prices = item.data.price.close;
        const returns = [];
        for (let i = 1; i < prices.length; i++) {
            returns.push((prices[i] - prices[i-1]) / prices[i-1]);
        }
        const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
        const variance = returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length;
        const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100;
        return volatility.toFixed(2);
    }).join(",") + "\n";
    
    csvContent += "Sharpe Ratio," + symbolData.map(item => {
        const prices = item.data.price.close;
        const returns = [];
        for (let i = 1; i < prices.length; i++) {
            returns.push((prices[i] - prices[i-1]) / prices[i-1]);
        }
        const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
        const variance = returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length;
        const volatility = Math.sqrt(variance);
        const sharpeRatio = (avgReturn * 252) / (volatility * Math.sqrt(252));
        return sharpeRatio.toFixed(2);
    }).join(",") + "\n";
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `symbol_comparison_${new Date().getTime()}.csv`);
    document.body.appendChild(link);
    
    // Trigger download
    link.click();
    document.body.removeChild(link);
    
    // Show toast
    showToast('Comparison data exported successfully');
}

// Add additional utility functions for keyboard navigation
document.addEventListener('keydown', function(e) {
    // Skip if inside an input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    
    // Spacebar: Toggle zoom sync
    if (e.key === ' ' && document.getElementById('syncZoomToggle')) {
        e.preventDefault();
        document.getElementById('syncZoomToggle').click();
    }
    
    // R key: Reset zoom
    if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        resetZoom();
    }
    
    // S key: Show statistics
    if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        showStatistics();
    }
    
    // C key: Compare symbols
    if (e.key === 'c' || e.key === 'C') {
        e.preventDefault();
        compareSymbols();
    }
    
    // P key: Print report
    if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();
        printSummaryReport();
    }
    
    // Forward/back keys for scrolling through indicators
    if (e.key === 'ArrowRight' && e.ctrlKey) {
        e.preventDefault();
        // Cycle through indicator visibility
        const indicators = ['showRSI', 'showMACD', 'showStochastic', 'showADX'];
        const currentIdx = indicators.findIndex(id => document.getElementById(id).checked);
        if (currentIdx >= 0) {
            // Uncheck current
            document.getElementById(indicators[currentIdx]).checked = false;
            document.getElementById(indicators[currentIdx]).dispatchEvent(new Event('change'));
            
            // Check next (or first if we're at the end)
            const nextIdx = (currentIdx + 1) % indicators.length;
            document.getElementById(indicators[nextIdx]).checked = true;
            document.getElementById(indicators[nextIdx]).dispatchEvent(new Event('change'));
        } else {
            // None checked, check the first one
            document.getElementById(indicators[0]).checked = true;
            document.getElementById(indicators[0]).dispatchEvent(new Event('change'));
        }
    }
    
    if (e.key === 'ArrowLeft' && e.ctrlKey) {
        e.preventDefault();
        // Cycle through indicator visibility (backwards)
        const indicators = ['showRSI', 'showMACD', 'showStochastic', 'showADX'];
        const currentIdx = indicators.findIndex(id => document.getElementById(id).checked);
        if (currentIdx >= 0) {
            // Uncheck current
            document.getElementById(indicators[currentIdx]).checked = false;
            document.getElementById(indicators[currentIdx]).dispatchEvent(new Event('change'));
            
            // Check previous (or last if we're at the beginning)
            const prevIdx = (currentIdx - 1 + indicators.length) % indicators.length;
            document.getElementById(indicators[prevIdx]).checked = true;
            document.getElementById(indicators[prevIdx]).dispatchEvent(new Event('change'));
        } else {
            // None checked, check the last one
            document.getElementById(indicators[indicators.length - 1]).checked = true;
            document.getElementById(indicators[indicators.length - 1]).dispatchEvent(new Event('change'));
        }
    }
});
}
