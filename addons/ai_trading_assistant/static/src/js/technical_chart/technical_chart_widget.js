/** @odoo-module */

import { Component, xml, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class TechnicalChartWidget extends Component {
    static template = xml`
        <div class="o_technical_chart_widget">
            <div class="chart-header" t-if="state.symbol">
                <h2>
                    <t t-esc="state.symbol"/>
                    <span t-if="state.market"> (<t t-esc="state.market"/>)</span>
                    - Golden Cross / Death Cross Strategy
                </h2>
            </div>
            <div class="chart-controls">
                <div class="control-group">
                    <label class="control-label">Khung thời gian:</label>
                    <div class="resolution-buttons btn-group">
                        <button class="btn btn-sm btn-outline-primary" t-att-class="{active: state.resolution === '1D'}" t-att-disabled="state.loading" t-on-click="() => this.onChangeResolution('1D')">1D</button>
                        <button class="btn btn-sm btn-outline-primary" t-att-class="{active: state.resolution === '1'}" t-att-disabled="state.loading" t-on-click="() => this.onChangeResolution('1')">1m</button>
                        <button class="btn btn-sm btn-outline-primary" t-att-class="{active: state.resolution === '5'}" t-att-disabled="state.loading" t-on-click="() => this.onChangeResolution('5')">5m</button>
                        <button class="btn btn-sm btn-outline-primary" t-att-class="{active: state.resolution === '15'}" t-att-disabled="state.loading" t-on-click="() => this.onChangeResolution('15')">15m</button>
                        <button class="btn btn-sm btn-outline-primary" t-att-class="{active: state.resolution === '30'}" t-att-disabled="state.loading" t-on-click="() => this.onChangeResolution('30')">30m</button>
                        <button class="btn btn-sm btn-outline-primary" t-att-class="{active: state.resolution === '60'}" t-att-disabled="state.loading" t-on-click="() => this.onChangeResolution('60')">1h</button>
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label">Chỉ báo:</label>
                    <div class="control-toggles">
                        <label class="toggle-switch">
                            <input type="checkbox" t-model="state.showSMA50" t-on-change="onToggleIndicator"/>
                            <span class="toggle-label">SMA 50</span>
                        </label>
                        <label class="toggle-switch">
                            <input type="checkbox" t-model="state.showSMA200" t-on-change="onToggleIndicator"/>
                            <span class="toggle-label">SMA 200</span>
                        </label>
                        <label class="toggle-switch">
                            <input type="checkbox" t-model="state.showRSI" t-on-change="onToggleIndicator"/>
                            <span class="toggle-label">RSI</span>
                        </label>
                        <label class="toggle-switch">
                            <input type="checkbox" t-model="state.showVolume" t-on-change="onToggleIndicator"/>
                            <span class="toggle-label">Volume</span>
                        </label>
                        <label class="toggle-switch">
                            <input type="checkbox" t-model="state.showMarkers" t-on-change="onToggleIndicator"/>
                            <span class="toggle-label">Golden/Death Cross</span>
                        </label>
                    </div>
                </div>
            </div>
            <div class="chart-container" t-ref="chartContainer"></div>
            <div class="chart-error" t-if="state.error">
                <p t-esc="state.error"/>
            </div>
            <div class="chart-loading" t-if="state.loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2" t-esc="_t('Loading chart...')"/>
            </div>
        </div>
    `;

    static props = {
        action: { type: Object, optional: true },
    };

    setup() {
        this.busService = useService("bus_service");
        this.state = useState({
            loading: true,
            error: null,
            chart: null,
            symbol: null,
            market: null,
            resolution: '15',
            // Indicator visibility toggles
            showSMA50: true,
            showSMA200: true,
            showRSI: true,
            showVolume: true,
            showMarkers: true,
        });
        this.chartContainerRef = useRef("chartContainer");
        this.chartInstance = null;
        this.chartLibrary = null;
        this.createChartFn = null;
        this.priceMarkersPrimitive = null;
        
        // Series references for toggling
        this.seriesRefs = {
            price: null,
            sma50: null,
            sma200: null,
            rsi: null,
            volume: null,
        };
        
        // Extract params from multiple sources
        const initialParams = this._extractInitialParams();
        this.predictionId = initialParams.prediction_id;
        this.symbol = initialParams.symbol;
        this.market = initialParams.market;
        this.days = parseInt(initialParams.days, 10) || 30;

        this.state.symbol = this.symbol;
        this.state.market = this.market;
        
        // Subscribe to WebSocket channel
        // Subscribe to WebSocket channel
        this.busService.addChannel("ai_prediction_channel");
        this.onNotificationBound = this.onNotification.bind(this);
        this.busService.subscribe("notification", this.onNotificationBound);

        onMounted(() => {
            this.loadChart();
        });

        onWillUnmount(() => {
            if (this.busService) {
                this.busService.unsubscribe("notification", this.onNotificationBound);
            }
            this.destroyChart();
        });
    }
    
    onNotification(notifications) {
        // Defensive: Check if component state is still valid
        if (!this.state) return;

        // Defensive: Ensure notifications is an iterable array
        if (!notifications) return;
        const notifList = Array.isArray(notifications) ? notifications : [notifications];
        
        for (const notification of notifList) {
            if (notification.type === 'prediction_update' && notification.payload) {
               const payload = notification.payload;
               // Check if update is for this symbol or prediction
               const matchSymbol = this.state.symbol && payload.symbol === this.state.symbol;
               const matchPrediction = this.predictionId && String(payload.prediction_id) === String(this.predictionId);
               
               if (matchSymbol || matchPrediction) {
                   console.log('Technical Chart: Received realtime update!', payload);
                   // Reload chart to get new candle/indicators
                   this.loadChart();
               }
            }
        }
    }
    
    onChangeResolution(resolution) {
        if (this.state.resolution === resolution) return;
        this.state.resolution = resolution;
        // Adjust default days for intraday
        if (resolution !== '1D') {
             // For intraday, we usually want shorter range or similar range but handled differently
             // For now keep days same or maybe restrict if needed backend side
        }
        this.loadChart();
    }
    
    onToggleIndicator() {
        // Update series visibility based on state
        this._updateSeriesVisibility();
    }
    
    _updateSeriesVisibility() {
        if (!this.chartInstance) {
            return;
        }
        
        // Toggle SMA 50
        if (this.seriesRefs.sma50) {
            if (typeof this.seriesRefs.sma50.setVisible === "function") {
                this.seriesRefs.sma50.setVisible(this.state.showSMA50);
            } else if (this.seriesRefs.sma50.applyOptions) {
                this.seriesRefs.sma50.applyOptions({ visible: this.state.showSMA50 });
            }
        }
        
        // Toggle SMA 200
        if (this.seriesRefs.sma200) {
            if (typeof this.seriesRefs.sma200.setVisible === "function") {
                this.seriesRefs.sma200.setVisible(this.state.showSMA200);
            } else if (this.seriesRefs.sma200.applyOptions) {
                this.seriesRefs.sma200.applyOptions({ visible: this.state.showSMA200 });
            }
        }
        
        // Toggle RSI
        if (this.seriesRefs.rsi) {
            if (typeof this.seriesRefs.rsi.setVisible === "function") {
                this.seriesRefs.rsi.setVisible(this.state.showRSI);
            } else if (this.seriesRefs.rsi.applyOptions) {
                this.seriesRefs.rsi.applyOptions({ visible: this.state.showRSI });
            }
        }
        
        // Toggle Volume
        if (this.seriesRefs.volume) {
            if (typeof this.seriesRefs.volume.setVisible === "function") {
                this.seriesRefs.volume.setVisible(this.state.showVolume);
            } else if (this.seriesRefs.volume.applyOptions) {
                this.seriesRefs.volume.applyOptions({ visible: this.state.showVolume });
            }
        }
        
        // Toggle Markers
        if (this.priceMarkersPrimitive) {
            const markers = this.state.showMarkers ? (this.currentMarkers || []) : [];
            if (typeof this.priceMarkersPrimitive.setMarkers === "function") {
                this.priceMarkersPrimitive.setMarkers(markers);
            }
        } else if (this.seriesRefs.price) {
            const markers = this.state.showMarkers ? (this.currentMarkers || []) : [];
            if (typeof this.seriesRefs.price.setMarkers === "function") {
                this.seriesRefs.price.setMarkers(markers);
            }
        }
    }

    async loadChart() {
        try {
            this.state.loading = true;
            this.state.error = null;
            
            // Re-extract params in case they weren't available during setup
            const params = this._extractInitialParams();
            
            // Update instance variables from extracted params
            if (params.prediction_id) {
                this.predictionId = params.prediction_id;
            }
            if (params.symbol) {
                this.symbol = params.symbol;
            }
            if (params.market) {
                this.market = params.market;
            }
            if (params.days) {
                this.days = parseInt(params.days, 10) || 30;
            }
            
            // Debug logging
            console.log('Technical Chart Widget - loadChart params:', {
                predictionId: this.predictionId,
                symbol: this.symbol,
                market: this.market,
                days: this.days,
                extractedParams: params,
            });
            
            if (!this.predictionId && !this.symbol) {
                const errorMsg = `Prediction ID or Symbol required. Extracted params: ${JSON.stringify(params)}`;
                console.error('Technical Chart Widget - Error:', errorMsg);
                this.state.error = _t("Prediction ID or Symbol required. Please ensure the prediction is saved and try again.");
                this.state.loading = false;
                return;
            }

            // Load Lightweight Charts library
            await this.loadLightweightCharts();

            // Fetch chart data
            const chartData = await this.fetchChartData();

            if (!chartData.success) {
                this.state.error = chartData.error || _t("Failed to load chart data");
                this.state.loading = false;
                return;
            }

            // Render chart
            this.renderChart(chartData);
            this.state.symbol = chartData.symbol || this.symbol;
            this.state.market = chartData.market || this.market;

            this.state.loading = false;
        } catch (error) {
            this.state.error = error.message || _t("Failed to load chart");
            this.state.loading = false;
        }
    }

    async loadLightweightCharts() {
        if (this.createChartFn) {
            return;
        }

        // Check if already loaded globally
        if (window.LightweightCharts && typeof window.LightweightCharts.createChart === "function") {
            this.chartLibrary = window.LightweightCharts;
            this.createChartFn = window.LightweightCharts.createChart;
            console.log('Technical Chart: Using global LightweightCharts');
            return;
        }

        // Check if script tag already exists
        const existingScript = document.getElementById("ai-lightweight-charts");
        if (existingScript) {
            // Wait for it to load if still loading
            if (!window.LightweightCharts) {
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(new Error(_t("Lightweight Charts library load timeout")));
                    }, 10000);
                    existingScript.addEventListener("load", () => {
                        clearTimeout(timeout);
                        resolve();
                    });
                    existingScript.addEventListener("error", () => {
                        clearTimeout(timeout);
                        reject(new Error(_t("Failed to load Lightweight Charts library")));
                    });
                });
            }
            
            if (window.LightweightCharts && typeof window.LightweightCharts.createChart === "function") {
                this.chartLibrary = window.LightweightCharts;
                this.createChartFn = window.LightweightCharts.createChart;
                console.log('Technical Chart: Using existing script tag');
                return;
            }
        }

        // Load via script tag (most reliable method)
        await new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.id = "ai-lightweight-charts";
            // Use unpkg with latest version (more reliable than jsdelivr)
            script.src = "https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js";
            script.async = true;
            script.defer = true;
            
            const timeout = setTimeout(() => {
                reject(new Error(_t("Lightweight Charts library load timeout")));
            }, 15000);
            
            script.onload = () => {
                clearTimeout(timeout);
                if (window.LightweightCharts && typeof window.LightweightCharts.createChart === "function") {
                    console.log('Technical Chart: LightweightCharts loaded successfully');
                    resolve();
                } else {
                    reject(new Error(_t("Lightweight Charts library loaded but API not available")));
                }
            };
            
            script.onerror = () => {
                clearTimeout(timeout);
                // Try alternative CDN
                console.warn('Technical Chart: unpkg failed, trying jsdelivr');
                script.src = "https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js";
                script.onerror = () => {
                    reject(new Error(_t("Failed to load Lightweight Charts library from CDN")));
                };
            };
            
            document.head.appendChild(script);
        });

        if (window.LightweightCharts && typeof window.LightweightCharts.createChart === "function") {
            this.chartLibrary = window.LightweightCharts;
            this.createChartFn = window.LightweightCharts.createChart;
            console.log('Technical Chart: LightweightCharts initialized');
        } else {
            throw new Error(_t("Lightweight Charts library unavailable"));
        }
    }

    async fetchChartData() {
        const params = {};
        if (this.predictionId) {
            params.prediction_id = this.predictionId;
        }
        if (this.symbol) {
            params.symbol = this.symbol;
        }
        if (this.market) {
            params.market = this.market;
        }
        if (this.state.resolution) {
            params.resolution = this.state.resolution;
        }
        if (this.days) {
            params.days = this.days;
        }

        const url = "/ai_chart/technical_chart_data_json";
        return await this._jsonRpc(url, params);
    }

    async _jsonRpc(url, params = {}) {
        const payload = {
            jsonrpc: "2.0",
            method: "call",
            params,
            id: Date.now(),
        };

        const headers = {
            "Content-Type": "application/json",
        };

        if (window.odoo && window.odoo.csrf_token) {
            headers["X-ODoo-CSRFToken"] = window.odoo.csrf_token;
        }

        const response = await fetch(url, {
            method: "POST",
            credentials: "include",
            headers,
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error(_t("Failed to fetch chart data"));
        }

        const result = await response.json();
        if (result.error) {
            const message = result.error.data?.message || result.error.message || _t("Unknown error");
            throw new Error(message);
        }
        return result.result || result;
    }

    _extractInitialParams() {
        // Try multiple ways to get action
        // Priority: props.action > env.services.action.current.action > env.action
        let action = this.props?.action;
        if (!action && this.env?.services?.action) {
            action = this.env.services.action.current?.action;
        }
        if (!action && this.env?.actionService) {
            action = this.env.actionService.current?.action;
        }
        if (!action) {
            action = this.env?.action || {};
        }
        
        // Extract from context, params, or directly from action
        const context = action?.context || {};
        const params = action?.params || {};
        
        // Also check if values are directly in action
        const directParams = {
            prediction_id: action?.prediction_id || context?.prediction_id || params?.prediction_id,
            symbol: action?.symbol || context?.symbol || params?.symbol,
            market: action?.market || context?.market || params?.market,
            days: action?.days || context?.days || params?.days,
        };
        
        const hashParams = this._parseParamsFromString(window?.location?.hash);
        const queryParams = this._parseParamsFromString(window?.location?.search);
        
        // Combine all sources, with priority: directParams > params > context > hash > query
        const extracted = {
            ...context,
            ...params,
            ...directParams,
            ...hashParams,
            ...queryParams,
        };
        
        // Debug logging
        console.log('Technical Chart Widget - Extracted params:', {
            action: action,
            context: context,
            params: params,
            directParams: directParams,
            extracted: extracted,
            props: this.props,
            env: this.env,
        });
        
        return extracted;
    }

    _parseParamsFromString(input) {
        if (!input) {
            return {};
        }
        const trimmed = input.startsWith("#") || input.startsWith("?") ? input.slice(1) : input;
        if (!trimmed) {
            return {};
        }
        const searchParams = new URLSearchParams(trimmed);
        const result = {};
        for (const [key, value] of searchParams.entries()) {
            if (!value) {
                continue;
            }
            if (key === "context") {
                try {
                    Object.assign(result, JSON.parse(decodeURIComponent(value)));
                } catch (error) {
                    // Ignore malformed context payloads
                }
            } else {
                result[key] = value;
            }
        }
        return result;
    }

    renderChart(chartData) {
        if (!this.chartContainerRef.el) {
            return;
        }

        const chartOptions = {
            layout: {
                textColor: "#d1d4dc",
                background: { type: "solid", color: "#131722" },
            },
            grid: {
                vertLines: { color: "#2a2e39" },
                horzLines: { color: "#2a2e39" },
            },
            crosshair: {
                mode: 1, // CrosshairMode.Normal
                vertLine: {
                    width: 1,
                    color: "#758696",
                    style: 3, // LineStyle.Dashed
                    labelBackgroundColor: "#758696",
                },
                horzLine: {
                    width: 1,
                    color: "#758696",
                    style: 3, // LineStyle.Dashed
                    labelBackgroundColor: "#758696",
                },
            },
            rightPriceScale: {
                borderColor: "#2a2e39",
            },
            timeScale: {
                borderColor: "#2a2e39",
                timeVisible: true,
                secondsVisible: false,
            },
        };

        const createChartFn = this.createChartFn;
        if (typeof createChartFn !== "function") {
            throw new Error("Lightweight Charts createChart() not available");
        }

        const chart = createChartFn(this.chartContainerRef.el, chartOptions);
        if (!chart) {
            throw new Error(_t("Unable to initialize chart instance"));
        }
        
        // Resize chart to fit container after a short delay to ensure container has dimensions
        const container = this.chartContainerRef.el;
        if (container && typeof chart.resize === "function") {
            const resizeChart = () => {
                const width = container.clientWidth || container.offsetWidth || 800;
                const height = container.clientHeight || container.offsetHeight || 600;
                if (width > 0 && height > 0) {
                    chart.resize(width, height);
                    console.log(`Technical Chart: Resized to ${width}x${height}`);
                }
            };
            
            // Initial resize with multiple attempts to ensure container is ready
            setTimeout(resizeChart, 50);
            setTimeout(resizeChart, 200);
            setTimeout(resizeChart, 500);
            
            // Resize on window resize
            window.addEventListener('resize', resizeChart);
            this.resizeHandler = resizeChart;
        }

        const priceSeries = this._createPriceSeries(chart);
        if (!priceSeries) {
            this.state.error = _t("Chart library missing required series APIs. Please reload or update assets.");
            this.state.loading = false;
            return;
        }

        const candlestickData = chartData.candlestick_data || [];
        if (typeof priceSeries.setData === "function") {
            priceSeries.setData(candlestickData);
        }
        
        // Store price series reference
        this.seriesRefs.price = priceSeries;

        // Moving Average Short
        const maShortPeriod = chartData.ma_short_period || 50;
        const maShortSeries = this._createLineSeries(chart, {
            color: "#ff6b6b",
            lineWidth: 2,
            title: `MA${maShortPeriod}`,
            priceFormat: {
                type: "price",
                precision: 2,
                minMove: 0.01,
            },
            visible: this.state.showSMA50,
        });

        const maShortData = chartData.ma_short_data || [];
        console.log(`Technical Chart: SMA 50 data points: ${maShortData.length}`, maShortData.slice(0, 3));
        if (maShortSeries) {
            if (typeof maShortSeries.setData === "function") {
                maShortSeries.setData(maShortData);
                console.log('Technical Chart: SMA 50 series data set');
            } else {
                console.warn('Technical Chart: SMA 50 series does not have setData method');
            }
            // Ensure series is visible
            if (typeof maShortSeries.setVisible === "function") {
                maShortSeries.setVisible(this.state.showSMA50);
            } else if (maShortSeries.applyOptions) {
                maShortSeries.applyOptions({ visible: this.state.showSMA50 });
            }
            console.log(`Technical Chart: SMA 50 series visible: ${this.state.showSMA50}`);
        } else {
            console.error('Technical Chart: SMA 50 series is null!');
        }
        this.seriesRefs.sma50 = maShortSeries;

        // Moving Average Long
        const maLongPeriod = chartData.ma_long_period || 200;
        const maLongSeries = this._createLineSeries(chart, {
            color: "#4ecdc4", // Teal color for SMA 200
            lineWidth: 2,
            title: `SMA${maLongPeriod}`,
            priceFormat: {
                type: "price",
                precision: 2,
                minMove: 0.01,
            },
            visible: this.state.showSMA200,
            priceLineVisible: false,
            lastValueVisible: true,
        });
        
        if (!maLongSeries) {
            console.error('Technical Chart: Failed to create SMA 200 series!');
        } else {
            console.log('Technical Chart: SMA 200 series created successfully', maLongSeries);
        }

        const maLongData = chartData.ma_long_data || [];
        console.log(`Technical Chart: SMA 200 data points: ${maLongData.length}`, maLongData.slice(0, 3));
        if (maLongSeries) {
            if (typeof maLongSeries.setData === "function") {
                maLongSeries.setData(maLongData);
                console.log('Technical Chart: SMA 200 series data set');
            } else {
                console.warn('Technical Chart: SMA 200 series does not have setData method');
            }
            // Ensure series is visible
            if (typeof maLongSeries.setVisible === "function") {
                maLongSeries.setVisible(this.state.showSMA200);
            } else if (maLongSeries.applyOptions) {
                maLongSeries.applyOptions({ visible: this.state.showSMA200 });
            }
            console.log(`Technical Chart: SMA 200 series visible: ${this.state.showSMA200}`);
        } else {
            console.error('Technical Chart: SMA 200 series is null!');
        }
        this.seriesRefs.sma200 = maLongSeries;

        // RSI series (secondary scale)
        const rsiSeries = this._createLineSeries(chart, {
            color: "#7b2cbf",
            lineWidth: 2,
            title: "RSI",
            priceScaleId: "rsi",
            priceFormat: {
                type: "price",
                precision: 1,
                minMove: 0.1,
            },
            visible: this.state.showRSI,
        });

        const rsiScale = chart.priceScale("rsi");
        if (rsiScale) {
            rsiScale.applyOptions({
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
        }

        const rsiData = chartData.rsi_data || [];
        if (rsiSeries && typeof rsiSeries.setData === "function") {
            rsiSeries.setData(rsiData);
        }
        this.seriesRefs.rsi = rsiSeries;

        // RSI levels (Pine Script logic: Buy > 45, Sell < 55)
        const rsiBuyLevel = chartData.rsi_buy_level || 45;
        const rsiSellLevel = chartData.rsi_sell_level || 55;
        
        rsiSeries.createPriceLine({
            price: rsiSellLevel,
            color: "#e91e63",
            lineWidth: 1,
            lineStyle: 2,
            axisLabelVisible: true,
            title: `RSI Sell (${rsiSellLevel})`,
        });

        rsiSeries.createPriceLine({
            price: rsiBuyLevel,
            color: "#2196F3",
            lineWidth: 1,
            lineStyle: 2,
            axisLabelVisible: true,
            title: `RSI Buy (${rsiBuyLevel})`,
        });

        rsiSeries.createPriceLine({
            price: 50,
            color: "#999999",
            lineWidth: 1,
            lineStyle: 0,
            axisLabelVisible: false,
        });

        // Volume histogram (overlay scale)
        const volumeSeries = this._createHistogramSeries(chart, {
            color: "#26a69a",
            priceFormat: {
                type: "volume",
            },
            priceScaleId: "volume",
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
            visible: this.state.showVolume,
        });

        const volumeScale = chart.priceScale("volume");
        if (volumeScale) {
            volumeScale.applyOptions({
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
        }

        const volumeData = chartData.volume_data || [];
        if (volumeSeries && typeof volumeSeries.setData === "function") {
            const volumeHistogramData = volumeData.map((item) => ({
                time: item.time,
                value: item.value,
                color: item.value > 0 ? "#26a69a" : "#ef5350",
            }));
            volumeSeries.setData(volumeHistogramData);
        }
        this.seriesRefs.volume = volumeSeries;
        
        // Store RSI series reference
        this.seriesRefs.rsi = rsiSeries;

        // Markers for Golden Cross / Death Cross
        const markers = chartData.markers || [];
        console.log(`Technical Chart: Markers count: ${markers.length}`, markers);
        this.currentMarkers = markers; // Store for toggling
        if (this.state.showMarkers) {
            this._applyMarkers(priceSeries, markers);
        } else {
            console.log('Technical Chart: Markers disabled by toggle');
        }

        // Fit content
        if (chart.timeScale && typeof chart.timeScale === "function") {
            chart.timeScale().fitContent();
        }

        this.chartInstance = chart;
    }

    destroyChart() {
        // Remove resize handler
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
            this.resizeHandler = null;
        }
        
        if (this.priceMarkersPrimitive && typeof this.priceMarkersPrimitive.setMarkers === "function") {
            this.priceMarkersPrimitive.setMarkers([]);
        }
        this.priceMarkersPrimitive = null;
        if (this.chartInstance) {
            this.chartInstance.remove();
            this.chartInstance = null;
        }
    }

    _createPriceSeries(chart) {
        if (!chart) {
            return null;
        }
        const candlestickOptions = {
            upColor: "#26a69a",
            downColor: "#ef5350",
            borderVisible: false,
            wickUpColor: "#26a69a",
            wickDownColor: "#ef5350",
        };
        return (
            this._addSeries(chart, "CandlestickSeries", candlestickOptions, "addCandlestickSeries") ||
            this._addSeries(
                chart,
                "BarSeries",
                {
                    ...candlestickOptions,
                    upColor: "#26a69a",
                    downColor: "#ef5350",
                },
                "addBarSeries"
            ) ||
            this._addSeries(
                chart,
                "LineSeries",
                {
                    color: "#26a69a",
                    lineWidth: 2,
                },
                "addLineSeries"
            )
        );
    }

    _createLineSeries(chart, options) {
        return this._addSeries(chart, "LineSeries", options, "addLineSeries");
    }

    _createHistogramSeries(chart, options) {
        return (
            this._addSeries(chart, "HistogramSeries", options, "addHistogramSeries") ||
            this._addSeries(chart, "LineSeries", options, "addLineSeries")
        );
    }

    _addSeries(chart, seriesType, options, legacyMethod) {
        if (!chart) {
            console.error(`Technical Chart: Cannot add ${seriesType} - chart is null`);
            return null;
        }
        const namespace = this._getLightweightChartsNamespace();
        
        // Try modern API first
        if (namespace && typeof chart.addSeries === "function" && namespace[seriesType]) {
            try {
                const series = chart.addSeries(namespace[seriesType], options);
                console.log(`Technical Chart: Added ${seriesType} using addSeries()`, series);
                return series;
            } catch (error) {
                console.warn(`Technical Chart: Failed to add ${seriesType} using addSeries():`, error);
            }
        }
        
        // Try legacy method
        if (legacyMethod && typeof chart[legacyMethod] === "function") {
            try {
                const series = chart[legacyMethod](options);
                console.log(`Technical Chart: Added ${seriesType} using ${legacyMethod}()`, series);
                return series;
            } catch (error) {
                console.warn(`Technical Chart: Failed to add ${seriesType} using ${legacyMethod}():`, error);
            }
        }
        
        console.error(`Technical Chart: Cannot add ${seriesType} - no suitable method found`);
        return null;
    }

    _applyMarkers(series, markers) {
        if (!series) {
            console.warn('Technical Chart: Cannot apply markers - series is null');
            return;
        }
        if (!markers || markers.length === 0) {
            console.log('Technical Chart: No markers to apply');
            return;
        }
        
        console.log(`Technical Chart: Applying ${markers.length} markers to chart`, markers);
        
        // Try Lightweight Charts native setMarkers first (v4+)
        if (typeof series.setMarkers === "function") {
            try {
                series.setMarkers(markers);
                console.log('Technical Chart: Markers applied using series.setMarkers()');
                return;
            } catch (error) {
                console.warn('Technical Chart: series.setMarkers() failed, trying alternative method', error);
            }
        }
        
        // Fallback: Try using namespace createSeriesMarkers (older versions)
        const namespace = this._getLightweightChartsNamespace();
        if (namespace && typeof namespace.createSeriesMarkers === "function") {
            try {
                if (!this.priceMarkersPrimitive) {
                    this.priceMarkersPrimitive = namespace.createSeriesMarkers(series, markers);
                    console.log('Technical Chart: Markers applied using createSeriesMarkers()');
                } else if (typeof this.priceMarkersPrimitive.setMarkers === "function") {
                    this.priceMarkersPrimitive.setMarkers(markers);
                    console.log('Technical Chart: Markers updated using setMarkers()');
                }
                return;
            } catch (error) {
                console.error('Technical Chart: Failed to apply markers using namespace method', error);
            }
        }
        
        console.warn('Technical Chart: No suitable method found to apply markers');
    }

    _getLightweightChartsNamespace() {
        if (this.chartLibrary) {
            return this.chartLibrary;
        }
        if (window.LightweightCharts) {
            return window.LightweightCharts;
        }
        return null;
    }

    get _t() {
        return _t;
    }
}

