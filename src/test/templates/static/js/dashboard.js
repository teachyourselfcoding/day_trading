
// dashboard.js - Interactive Signal Verification Dashboard

// Global variables
let chartData = null;
let priceChart = null;
let rsiChart = null;
let macdChart = null;
let stochChart = null;
let adxChart = null;
let currentSymbol = '';

// Initialize the dashboard when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard.js loaded successfully');
    
    // Get references to DOM elements
    const selectedStock = document.getElementById('symbolSelect').value;
    const loadDataBtn = document.getElementById('loadSymbolBtn');
    const dataContainer = document.getElementById('data-container');
    
    // Simple test to verify the button is working
    if (loadDataBtn) {
        console.log('Load data button found');
        
        // Add a direct onclick handler for testing
        loadDataBtn.onclick = function() {
            console.log('Button clicked via onclick');
        };
        
        // Add a more robust event listener
        loadDataBtn.addEventListener('click', function() {
            console.log('Button clicked via addEventListener');
            
            // Get the selected stock
            const selectedStock = document.getElementById('symbolSelect') ? document.getElementById('symbolSelect').value : '';
            console.log('Selected stock:', selectedStock);
            if (!selectedStock) {
                console.log('No stock selected');
                alert('Please select a stock first');
                return;
            }
            
            // Show loading indicator
            if (dataContainer) {
                dataContainer.innerHTML = '<p>Loading data...</p>';
            }
            
            // Make the AJAX request
            fetch('/load_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ticker: selectedStock })
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Data received:', data);
                displayData(data);
            })
            .catch(error => {
                console.error('Error:', error);
                if (dataContainer) {
                    dataContainer.innerHTML = '<p>Error loading data: ' + error.message + '</p>';
                }
            });
        });
    } else {
        console.error('Load data button not found');
    }
    
    // Function to display the data
    function displayData(data) {
        if (!dataContainer) return;
        
        try {
            // Create a heading for the data
            let html = '<h2>Data for ' + data.ticker + '</h2>';
            
            if (data.data && data.data.length > 0) {
                // Get the column names from the first data item
                const columns = Object.keys(data.data[0]);
                
                // Create a table
                html += '<table border="1"><tr>';
                
                // Add table headers
                columns.forEach(column => {
                    html += '<th>' + column + '</th>';
                });
                html += '</tr>';
                
                // Add table rows
                data.data.forEach(row => {
                    html += '<tr>';
                    columns.forEach(column => {
                        html += '<td>' + row[column] + '</td>';
                    });
                    html += '</tr>';
                });
                
                html += '</table>';
            } else {
                html += '<p>No data available for this stock</p>';
            }
            
            // Update the data container
            dataContainer.innerHTML = html;
        } catch (error) {
            console.error('Error displaying data:', error);
            dataContainer.innerHTML = '<p>Error displaying data: ' + error.message + '</p>';
        }
    }
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
    // Show loading message
    document.getElementById('loadingMessage').style.display = 'block';
    document.getElementById('chartContainer').style.opacity = '0.5';
    
    // Get the selected symbol
    const symbolSelect = document.getElementById('symbolSelect');
    currentSymbol = symbolSelect.value;
    
    // Fetch data from the server
    fetch(`/api/data/${currentSymbol}`)
        .then(response => response.json())
        .then(data => {
            // Hide loading message
            document.getElementById('loadingMessage').style.display = 'none';
            document.getElementById('chartContainer').style.opacity = '1';
            
            // Store the data globally
            chartData = data;
            
            // Create charts
            createCharts();
            
            // Update summary tables
            updateSummaries();
        })
        .catch(error => {
            console.error('Error loading data:', error);
            document.getElementById('loadingMessage').style.display = 'none';
            document.getElementById('chartContainer').style.opacity = '1';
            alert('Error loading data. See console for details.');
        });
}

// Create all charts
function createCharts() {
    if (!chartData) return;
    
    // Create the main price chart
    createPriceChart();
    
    // Create indicator charts
    createRSIChart();
    createMACDChart();
    createStochasticChart();
    createADXChart();
}

// Create the main price chart
function createPriceChart() {
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
    
    // Prepare moving averages
    const sma20 = {
        x: chartData.datetime,
        y: chartData.indicators.sma_20,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA 20',
        line: {
            color: 'blue',
            width: 1
        },
        visible: document.getElementById('showSMA20').checked
    };
    
    const sma50 = {
        x: chartData.datetime,
        y: chartData.indicators.sma_50,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA 50',
        line: {
            color: 'green',
            width: 1
        },
        visible: document.getElementById('showSMA50').checked
    };
    
    const sma200 = {
        x: chartData.datetime,
        y: chartData.indicators.sma_200,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA 200',
        line: {
            color: 'red',
            width: 1
        },
        visible: document.getElementById('showSMA200').checked
    };
    
    const ema12 = {
        x: chartData.datetime,
        y: chartData.indicators.ema_12,
        type: 'scatter',
        mode: 'lines',
        name: 'EMA 12',
        line: {
            color: 'purple',
            width: 1,
            dash: 'dash'
        },
        visible: document.getElementById('showEMA12').checked
    };
    
    const ema26 = {
        x: chartData.datetime,
        y: chartData.indicators.ema_26,
        type: 'scatter',
        mode: 'lines',
        name: 'EMA 26',
        line: {
            color: 'orange',
            width: 1,
            dash: 'dash'
        },
        visible: document.getElementById('showEMA26').checked
    };
    
    // Prepare Bollinger Bands
    const bbUpper = {
        x: chartData.datetime,
        y: chartData.indicators.bb_upper,
        type: 'scatter',
        mode: 'lines',
        name: 'BB Upper',
        line: {
            color: 'gray',
            width: 1
        },
        visible: document.getElementById('showBBUpper').checked
    };
    
    const bbMiddle = {
        x: chartData.datetime,
        y: chartData.indicators.bb_middle,
        type: 'scatter',
        mode: 'lines',
        name: 'BB Middle',
        line: {
            color: 'gray',
            width: 1,
            dash: 'dash'
        },
        visible: document.getElementById('showBBMiddle').checked
    };
    
    const bbLower = {
        x: chartData.datetime,
        y: chartData.indicators.bb_lower,
        type: 'scatter',
        mode: 'lines',
        name: 'BB Lower',
        line: {
            color: 'gray',
            width: 1
        },
        visible: document.getElementById('showBBLower').checked
    };
    
    // Prepare bullish pattern markers
    const bullishPatterns = {
        x: [],
        y: [],
        text: [],
        mode: 'markers+text',
        type: 'scatter',
        name: 'Bullish Patterns',
        marker: {
            symbol: 'triangle-up',
            size: 12,
            color: 'green'
        },
        textposition: 'bottom',
        visible: document.getElementById('showBullishPatterns').checked
    };
    
    // Prepare bearish pattern markers
    const bearishPatterns = {
        x: [],
        y: [],
        text: [],
        mode: 'markers+text',
        type: 'scatter',
        name: 'Bearish Patterns',
        marker: {
            symbol: 'triangle-down',
            size: 12,
            color: 'red'
        },
        textposition: 'top',
        visible: document.getElementById('showBearishPatterns').checked
    };
    
    // Add bullish pattern markers
    if (document.getElementById('showBullishPatterns').checked) {
        const bullishPatternTypes = ['bullish_engulfing', 'hammer', 'morning_star', 'three_white_soldiers', 'piercing', 'doji_star'];
        
        for (let i = 0; i < chartData.datetime.length; i++) {
            for (const pattern of bullishPatternTypes) {
                if (chartData.patterns.bullish[pattern][i] > 0) {
                    bullishPatterns.x.push(chartData.datetime[i]);
                    bullishPatterns.y.push(chartData.price.low[i] * 0.99);  // Slightly below the low
                    bullishPatterns.text.push(pattern.replace(/_/g, ' '));
                    break;  // Only add one marker per bar
                }
            }
        }
    }
    
    // Add bearish pattern markers
    if (document.getElementById('showBearishPatterns').checked) {
        const bearishPatternTypes = ['bearish_engulfing', 'hanging_man', 'evening_star', 'three_black_crows', 'dark_cloud_cover', 'shooting_star'];
        
        for (let i = 0; i < chartData.datetime.length; i++) {
            for (const pattern of bearishPatternTypes) {
                if (chartData.patterns.bearish[pattern][i] > 0) {
                    bearishPatterns.x.push(chartData.datetime[i]);
                    bearishPatterns.y.push(chartData.price.high[i] * 1.01);  // Slightly above the high
                    bearishPatterns.text.push(pattern.replace(/_/g, ' '));
                    break;  // Only add one marker per bar
                }
            }
        }
    }
    
    // Prepare signal markers
    const signalMarkers = {
        x: [],
        y: [],
        text: [],
        mode: 'markers',
        type: 'scatter',
        name: 'Technical Signals',
        marker: {
            size: 10,
            color: []
        },
        showlegend: false
    };
    
    // Add signal markers
    if (document.getElementById('showRSISignals').checked || 
        document.getElementById('showMACDSignals').checked || 
        document.getElementById('showBBSignals').checked || 
        document.getElementById('showCrossovers').checked) {
        
        for (let i = 0; i < chartData.datetime.length; i++) {
            // RSI signals
            if (document.getElementById('showRSISignals').checked) {
                if (chartData.signals.rsi_oversold[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.low[i] * 0.99);
                    signalMarkers.text.push('RSI Oversold');
                    signalMarkers.marker.color.push('blue');
                }
                
                if (chartData.signals.rsi_overbought[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.01);
                    signalMarkers.text.push('RSI Overbought');
                    signalMarkers.marker.color.push('orange');
                }
            }
            
            // MACD signals
            if (document.getElementById('showMACDSignals').checked) {
                if (chartData.signals.macd_bullish_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.low[i] * 0.98);
                    signalMarkers.text.push('MACD Bullish Cross');
                    signalMarkers.marker.color.push('lime');
                }
                
                if (chartData.signals.macd_bearish_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.02);
                    signalMarkers.text.push('MACD Bearish Cross');
                    signalMarkers.marker.color.push('red');
                }
            }
            
            // Bollinger Band signals
            if (document.getElementById('showBBSignals').checked) {
                if (chartData.signals.bb_lower_touch[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.low[i]);
                    signalMarkers.text.push('BB Lower Touch');
                    signalMarkers.marker.color.push('cyan');
                }
                
                if (chartData.signals.bb_upper_touch[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i]);
                    signalMarkers.text.push('BB Upper Touch');
                    signalMarkers.marker.color.push('magenta');
                }
            }
            
            // Crossover signals
            if (document.getElementById('showCrossovers').checked) {
                if (chartData.signals.golden_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.03);
                    signalMarkers.text.push('Golden Cross');
                    signalMarkers.marker.color.push('gold');
                }
                
                if (chartData.signals.death_cross[i] > 0) {
                    signalMarkers.x.push(chartData.datetime[i]);
                    signalMarkers.y.push(chartData.price.high[i] * 1.03);
                    signalMarkers.text.push('Death Cross');
                    signalMarkers.marker.color.push('black');
                }
            }
        }
    }
    
    // Combine all traces
    const data = [
        ohlc,
        volume,
        sma20,
        sma50,
        sma200,
        ema12,
        ema26,
        bbUpper,
        bbMiddle,
        bbLower,
        bullishPatterns,
        bearishPatterns,
        signalMarkers
    ];
    
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
    
    // Add Golden Cross and Death Cross annotations if enabled
    if (document.getElementById('showCrossovers').checked) {
        for (let i = 0; i < chartData.datetime.length; i++) {
            if (chartData.signals.golden_cross[i] > 0) {
                layout.annotations.push({
                    x: chartData.datetime[i],
                    y: chartData.price.high[i] * 1.05,
                    xref: 'x',
                    yref: 'y',
                    text: 'Golden Cross',
                    showarrow: true,
                    arrowhead: 2,
                    arrowsize: 1,
                    arrowwidth: 1,
                    arrowcolor: 'gold'
                });
            }
            
            if (chartData.signals.death_cross[i] > 0) {
                layout.annotations.push({
                    x: chartData.datetime[i],
                    y: chartData.price.high[i] * 1.05,
                    xref: 'x',
                    yref: 'y',
                    text: 'Death Cross',
                    showarrow: true,
                    arrowhead: 2,
                    arrowsize: 1,
                    arrowwidth: 1,
                    arrowcolor: 'black'
                });
            }
        }
    }
    
    // Create the chart
    Plotly.newPlot('priceChart', data, layout);
}

// Create the RSI chart
function createRSIChart() {
    if (!chartData || !document.getElementById('showRSI').checked) return;
    
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
                y0: 70,
                y1: 70,
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
                y0: 30,
                y1: 30,
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
    
    Plotly.newPlot('rsiChart', [trace], layout);
}

// Create the MACD chart
function createMACDChart() {
    if (!chartData || !document.getElementById('showMACD').checked) return;
    
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
    
    Plotly.newPlot('macdChart', [macdLine, signalLine, histogram], layout);
}

// Create the Stochastic chart
function createStochasticChart() {
    if (!chartData || !document.getElementById('showStochastic').checked) return;
    
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
            rangeslider: {
                visible: false
            }
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
    
    Plotly.newPlot('stochChart', [kLine, dLine], layout);
}

// Create the ADX chart
function createADXChart() {
    if (!chartData || !document.getElementById('showADX').checked) return;
    
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
    
    Plotly.newPlot('adxChart', [adxLine], layout);
}

// Update all charts based on current settings
function updateCharts() {
    createCharts();
}

// Reset zoom on all charts
function resetZoom() {
    if (priceChart) {
        Plotly.relayout('priceChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (rsiChart) {
        Plotly.relayout('rsiChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (macdChart) {
        Plotly.relayout('macdChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (stochChart) {
        Plotly.relayout('stochChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    if (adxChart) {
        Plotly.relayout('adxChart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
}

// Export data to CSV
function exportData() {
    if (!chartData) return;
    
    // Create CSV content
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add header row
    csvContent += "DateTime,Open,High,Low,Close,Volume,SMA20,SMA50,SMA200,EMA12,EMA26,BB_Upper,BB_Middle,BB_Lower,RSI,MACD,MACD_Signal,MACD_Hist,Stoch_K,Stoch_D,ADX";
    
    // Add data rows
    for (let i = 0; i < chartData.datetime.length; i++) {
        const row = [
            chartData.datetime[i],
            chartData.price.open[i],
            chartData.price.high[i],
            chartData.price.low[i],
            chartData.price.close[i],
            chartData.price.volume[i],
            chartData.indicators.sma_20[i] || "",
            chartData.indicators.sma_50[i] || "",
            chartData.indicators.sma_200[i] || "",
            chartData.indicators.ema_12[i] || "",
            chartData.indicators.ema_26[i] || "",
            chartData.indicators.bb_upper[i] || "",
            chartData.indicators.bb_middle[i] || "",
            chartData.indicators.bb_lower[i] || "",
            chartData.indicators.rsi[i] || "",
            chartData.indicators.macd[i] || "",
            chartData.indicators.macd_signal[i] || "",
            chartData.indicators.macd_hist[i] || "",
            chartData.indicators.stoch_k[i] || "",
            chartData.indicators.stoch_d[i] || "",
            chartData.indicators.adx[i] || ""
        ];
        
        csvContent += row.join(",");
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
    const signalCounts = {
        rsi_oversold: 0,
        rsi_overbought: 0,
        macd_bullish_cross: 0,
        macd_bearish_cross: 0,
        bb_lower_touch: 0,
        bb_upper_touch: 0,
        golden_cross: 0,
        death_cross: 0,
        stoch_oversold: 0,
        stoch_overbought: 0
    };
    
    for (const signalType in chartData.signals) {
        signalCounts[signalType] = chartData.signals[signalType].filter(val => val > 0).length;
    }
    
    // Create HTML content
    let html = '<table class="table table-sm">';
    html += '<thead><tr><th>Signal Type</th><th>Count</th></tr></thead>';
    html += '<tbody>';
    
    // Bullish signals
    html += '<tr class="table-success"><td colspan="2"><strong>Bullish Signals</strong></td></tr>';
    html += `<tr><td>RSI Oversold</td><td>${signalCounts.rsi_oversold}</td></tr>`;
    html += `<tr><td>MACD Bullish Cross</td><td>${signalCounts.macd_bullish_cross}</td></tr>`;
    html += `<tr><td>Bollinger Lower Touch</td><td>${signalCounts.bb_lower_touch}</td></tr>`;
    html += `<tr><td>Golden Cross</td><td>${signalCounts.golden_cross}</td></tr>`;
    html += `<tr><td>Stochastic Oversold</td><td>${signalCounts.stoch_oversold}</td></tr>`;
    
    // Bearish signals
    html += '<tr class="table-danger"><td colspan="2"><strong>Bearish Signals</strong></td></tr>';
    html += `<tr><td>RSI Overbought</td><td>${signalCounts.rsi_overbought}</td></tr>`;
    html += `<tr><td>MACD Bearish Cross</td><td>${signalCounts.macd_bearish_cross}</td></tr>`;
    html += `<tr><td>Bollinger Upper Touch</td><td>${signalCounts.bb_upper_touch}</td></tr>`;
    html += `<tr><td>Death Cross</td><td>${signalCounts.death_cross}</td></tr>`;
    html += `<tr><td>Stochastic Overbought</td><td>${signalCounts.stoch_overbought}</td></tr>`;
    
    html += '</tbody></table>';
    
    signalSummaryElement.innerHTML = html;
}

// Update pattern summary table
function updatePatternSummary() {
    const patternSummaryElement = document.getElementById('patternSummary');
    
    // Count patterns
    const patternCounts = {
        bullish: {},
        bearish: {}
    };
    
    // Bullish patterns
    for (const patternType in chartData.patterns.bullish) {
        patternCounts.bullish[patternType] = chartData.patterns.bullish[patternType].filter(val => val > 0).length;
    }
    
    // Bearish patterns
    for (const patternType in chartData.patterns.bearish) {
        patternCounts.bearish[patternType] = chartData.patterns.bearish[patternType].filter(val => val > 0).length;
    }
    
    // Create HTML content
    let html = '<table class="table table-sm">';
    html += '<thead><tr><th>Pattern Type</th><th>Count</th></tr></thead>';
    html += '<tbody>';
    
    // Bullish patterns
    html += '<tr class="table-success"><td colspan="2"><strong>Bullish Patterns</strong></td></tr>';
    for (const pattern in patternCounts.bullish) {
        const displayName = pattern.replace(/_/g, ' ');
        html += `<tr><td>${displayName}</td><td>${patternCounts.bullish[pattern]}</td></tr>`;
    }
    
    // Bearish patterns
    html += '<tr class="table-danger"><td colspan="2"><strong>Bearish Patterns</strong></td></tr>';
    for (const pattern in patternCounts.bearish) {
        const displayName = pattern.replace(/_/g, ' ');
        html += `<tr><td>${displayName}</td><td>${patternCounts.bearish[pattern]}</td></tr>`;
    }
    
    html += '</tbody></table>';
    
    patternSummaryElement.innerHTML = html;
}