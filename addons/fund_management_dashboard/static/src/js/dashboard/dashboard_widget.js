/** @odoo-module */

import { Component, xml, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { SidebarPanel } from "./sidebar_panel";

export class DashboardWidget extends Component {
    static components = { SidebarPanel };
    static template = xml`
        <div class="fund-dashboard-container">
            <div class="dashboard-shell">
                <t t-if="state.showSidebar">
                <SidebarPanel/>
                </t>

                <main class="dashboard-main">
                    <div class="dashboard-top-bar"></div>

                    <section class="dashboard-section">
                        <div class="section-header">
                            <div>
                                <p class="section-kicker">Tổng quan</p>
                                <h3>Thông kê sản phẩm</h3>
                            </div>
                            <div class="realtime-clock">
                                <span class="realtime-label">Thời gian</span>
                                <div class="realtime-time" t-esc="state.currentTime"/>
                            </div>
                                </div>
                        <t t-set="productCards" t-value="this.getProductCards()"/>
                        <div class="card-grid cols-3">
                            <t t-foreach="productCards" t-as="card" t-key="card.label">
                                <div t-attf-class="info-card #{card.variant}">
                                    <div class="card-icon">
                                        <i t-att-class="card.icon"/>
                            </div>
                                    <div class="card-content">
                                        <p class="card-label" t-esc="card.label"/>
                                        <h4 class="card-value" t-esc="card.value"/>
                                        <p class="card-description" t-if="card.description" t-esc="card.description"/>
                        </div>
                    </div>
                            </t>
                </div>
                    </section>

                    <section class="dashboard-section">
                        <div class="section-header">
                            <div>
                                <p class="section-kicker">Nguồn vốn</p>
                                <h3>Thống kê số dư (VND)</h3>
                            </div>
                            </div>
                        <t t-set="balanceCards" t-value="this.getBalanceCards()"/>
                        <div class="card-grid cols-3">
                            <t t-foreach="balanceCards" t-as="card" t-key="card.label">
                                <div t-attf-class="info-card #{card.variant}">
                                    <div class="card-icon">
                                        <i t-att-class="card.icon"/>
                        </div>
                                    <div class="card-content">
                                        <p class="card-label" t-esc="card.label"/>
                                        <h4 class="card-value" t-esc="card.value"/>
                                        <p class="card-description" t-if="card.description" t-esc="card.description"/>
                    </div>
                            </div>
                            </t>
                            </div>
                    </section>

                    <section class="dashboard-section two-column">
                        <div class="panel">
                            <div class="section-header">
                                <div>
                                    <p class="section-kicker">Người dùng</p>
                                    <h3>Thống kê người dùng</h3>
                            </div>
                                <span class="section-note">
                                    Tổng cộng <t t-esc="this.formatNumber(state.accounts.total || 0)"/> nhà đầu tư
                                    </span>
                            </div>
                            <ul class="user-status-list">
                                <t t-foreach="this.getUserStatusRows()" t-as="row" t-key="row.label">
                                    <li>
                                        <div class="user-status-info">
                                            <span t-attf-class="status-dot #{row.variant}"></span>
                                            <span class="user-status-label" t-esc="row.label"/>
                        </div>
                                        <div class="user-status-value">
                                            <span class="value" t-esc="row.value"/>
                                            <span class="badge" t-if="row.badge" t-attf-class="badge #{row.badgeVariant}">
                                                <t t-esc="row.badge"/>
                                            </span>
                    </div>
                                    </li>
                                </t>
                            </ul>
                </div>

                        <div class="panel transactions">
                            <div class="section-header">
                                <div>
                                    <p class="section-kicker">Giao dịch</p>
                                    <h3>Thống kê giao dịch</h3>
                            </div>
                                <span class="section-note">
                                    Tổng giá trị <t t-esc="this.formatCurrency(state.summary.today_total_amount)"/>
                                </span>
                                            </div>
                            <div class="transaction-card-grid">
                                <t t-foreach="this.getTransactionCards()" t-as="card" t-key="card.label">
                                    <div t-attf-class="transaction-card #{card.variant}">
                                        <div class="transaction-card-meta">
                                            <p class="label" t-esc="card.label"/>
                                            <span class="chip" t-if="card.status" t-esc="card.status"/>
                                            </div>
                                        <h4 t-esc="card.value"/>
                                        <p t-if="card.description" t-esc="card.description"/>
                                        </div>
                                </t>
                                </div>
                            </div>
                    </section>

                    <section class="dashboard-section">
                        <div class="section-header">
                            <div>
                                <p class="section-kicker">Lượt truy cập</p>
                                <h3>Thống kê lượt truy cập</h3>
                            </div>
                            </div>
                        <div class="traffic-grid">
                            <t t-foreach="this.getTrafficStats()" t-as="stat" t-key="stat.label">
                                <div class="traffic-card">
                                    <p class="label" t-esc="stat.label"/>
                                    <h4 t-esc="stat.value"/>
                                    <p class="description" t-if="stat.description" t-esc="stat.description"/>
                        </div>
                            </t>
                    </div>
                    </section>

                </main>
            </div>
        </div>
    `;

    setup() {
        this.state = useState({
            showSidebar: true, // Mặc định hiển thị sidebar
            summary: {
                total_accounts: 0,
                total_investment: 0,
                total_current_value: 0,
                total_profit_loss: 0,
                total_profit_loss_percentage: 0,
                today_transactions_count: 0,
                today_pending_count: 0,
                today_completed_count: 0,
                today_total_amount: 0,
                today_buy_count: 0,
                today_sell_count: 0,
                today_buy_amount: 0,
                today_sell_amount: 0,
            },
            transactions: [],
            accounts: {
                total: 0,
                by_status: {
                    pending: 0,
                    kyc: 0,
                    vsd: 0,
                    incomplete: 0,
                }
            },
            fund_movements: [],
            top_transactions: [],
            currentTime: '',
            nav_opening_data: {
                total_opening_ccq: 0,
                funds: [],
            },
            traffic_stats: {
                current_sessions: 0,
                today: 0,
                week: 0,
                month: 0,
                total: 0,
                alerts: 0,
            },
            transaction_status_stats: {
                buy: {
                    pending_confirm: { count: 0, amount: 0 },
                    pending_match: { count: 0, amount: 0 },
                    matched: { count: 0, amount: 0 },
                },
                sell: {
                    pending_confirm: { count: 0, amount: 0 },
                    pending_match: { count: 0, amount: 0 },
                    matched: { count: 0, amount: 0 },
                },
            },
            balance_metrics: {
                total_buy_pending_amount: 0,
                total_sell_pending_amount: 0,
                investor_assets: 0,
            },
            product_status_stats: {
                pending: 0,
                active: 0,
                total: 0,
            },
        });

        // Chart instances
        this.transactionTrendChart = null;
        this.fundDistributionChart = null;
        this.buySellComparisonChart = null;
        this.navOpeningPriceChart = null;

        // Realtime clock interval
        this.clockInterval = null;

        onMounted(() => {
            this.checkUserPermission();
            this.loadDashboardData();
            this.startRealtimeClock();
        });

        onWillUnmount(() => {
            // Clear interval when component unmounts
            if (this.clockInterval) {
                clearInterval(this.clockInterval);
            }
        });
    }

    async checkUserPermission() {
        try {
            const response = await fetch('/api/user-permission/check-user-type', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {},
                    id: Math.floor(Math.random() * 1000000)
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const jsonRpcResponse = await response.json();
            // Với type='json', Odoo trả về JSON-RPC format: {jsonrpc: '2.0', id: null, result: {...}}
            const data = jsonRpcResponse.result || jsonRpcResponse;
            
            if (data && data.success) {
                // Nếu user là fund_operator, ẩn sidebar
                if (data.user_type === 'fund_operator') {
                    this.state.showSidebar = false;
                    // Ẩn sidebar bằng CSS
                    const shell = document.querySelector('.dashboard-shell');
                    if (shell) {
                        shell.classList.add('no-sidebar');
                    }
                }
            }
        } catch (error) {
            console.error('Error checking user permission:', error);
            // Mặc định vẫn hiển thị sidebar nếu có lỗi
        }
    }

    startRealtimeClock() {
        // Update time immediately
        this.updateCurrentTime();
        
        // Update every second
        this.clockInterval = setInterval(() => {
            this.updateCurrentTime();
        }, 1000);
    }

    updateCurrentTime() {
        const now = new Date();
        
        // Format thời gian theo định dạng: HH:mm:ss DD/MM/YYYY
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();
        
        this.state.currentTime = `${hours}:${minutes}:${seconds} ${day}/${month}/${year}`;
    }

    async loadDashboardData() {
        try {
            const data = this.props?.initialData;
            if (data) {
                this.updateState(data);
            } else {
                this.showError("Không thể tải dữ liệu dashboard");
            }
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.showError("Lỗi khi tải dữ liệu dashboard");
        }
    }

    updateState(data) {
        Object.assign(this.state.summary, data.summary || {});
        this.state.transactions = data.transactions || [];
        Object.assign(this.state.accounts, data.accounts || {});
        this.state.fund_movements = data.fund_movements || [];
        this.state.top_transactions = data.top_transactions || [];
        Object.assign(this.state.nav_opening_data, data.nav_opening_data || {});
        this.state.transaction_trend = data.transaction_trend || null;
        Object.assign(
            this.state.traffic_stats,
            data.traffic_stats || this.getDefaultTrafficStats()
        );
        Object.assign(
            this.state.product_status_stats,
            data.product_stats || {}
        );
        const transactionStats = this.computeTransactionStatusStats(this.state.transactions);
        Object.assign(this.state.transaction_status_stats.buy, transactionStats.buy);
        Object.assign(this.state.transaction_status_stats.sell, transactionStats.sell);
        Object.assign(
            this.state.balance_metrics,
            this.computeBalanceMetrics(transactionStats, this.state.summary)
        );
        
        // Render charts after state update
        this.renderCharts();
    }

    renderCharts() {
        const hasChartContainer =
            document.getElementById('transactionTrendChart') ||
            document.getElementById('fundDistributionChart') ||
            document.getElementById('buySellComparisonChart') ||
            document.getElementById('navOpeningPriceChart');

        if (!hasChartContainer) {
            return;
        }

        // Wait for DOM to be ready and Chart.js to be loaded
        const checkChartJs = () => {
            if (typeof Chart !== 'undefined') {
                setTimeout(() => {
                    this.renderTransactionTrendChart();
                    this.renderFundDistributionChart();
                    this.renderBuySellComparisonChart();
                    this.renderNavOpeningPriceChart();
                }, 100);
            } else {
                // Retry after 100ms if Chart.js not loaded yet
                setTimeout(checkChartJs, 100);
            }
        };
        checkChartJs();
    }

    renderTransactionTrendChart() {
        const ctx = document.getElementById('transactionTrendChart');
        if (!ctx) {
            console.warn('transactionTrendChart canvas not found');
            return;
        }

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }

        // Destroy existing chart if exists
        if (this.transactionTrendChart) {
            this.transactionTrendChart.destroy();
        }

        const trendData = this.state.transaction_trend;
        if (!trendData || !trendData.labels || !trendData.buy_data || !trendData.sell_data) {
            console.warn('Transaction trend data not available; chart skipped.');
            return;
        }

        const labels = trendData.labels;
        const buyData = trendData.buy_data;
        const sellData = trendData.sell_data;

        // Nếu không có dữ liệu, không vẽ chart
        if (labels.length === 0 || (buyData.length === 0 && sellData.length === 0)) {
            console.warn('No data to render transaction trend chart');
            return;
        }

        try {
            this.transactionTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Lệnh mua',
                        data: buyData,
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.15)',
                        borderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#198754',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }, {
                        label: 'Lệnh bán',
                        data: sellData,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.15)',
                        borderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#dc3545',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            top: 10,
                            bottom: 10,
                            left: 10,
                            right: 10
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                font: {
                                    size: 14,
                                    weight: '600'
                                },
                                padding: 15,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 14,
                                weight: '600'
                            },
                            bodyFont: {
                                size: 13
                            },
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            cornerRadius: 8
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                font: {
                                    size: 12,
                                    weight: '500'
                                },
                                padding: 8
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                                font: {
                                    size: 12,
                                    weight: '500'
                                },
                                padding: 8
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        }
                    }
                }
            });
            console.log('Transaction trend chart rendered successfully');
        } catch (error) {
            console.error('Error rendering transaction trend chart:', error);
        }
    }

    renderFundDistributionChart() {
        const ctx = document.getElementById('fundDistributionChart');
        if (!ctx) return;

        if (this.fundDistributionChart) {
            this.fundDistributionChart.destroy();
        }

        const fundMovements = this.state.fund_movements || [];
        
        // Filter chỉ lấy các quỹ có dữ liệu (tổng giá trị > 0)
        const validMovements = fundMovements.filter(m => {
            const total = (m.buy_amount || 0) + (m.sell_amount || 0);
            return total > 0;
        });

        if (validMovements.length === 0) {
            console.warn('No data to render fund distribution chart');
            return;
        }

        const labels = validMovements.map(m => m.fund_ticker || 'N/A');
        const data = validMovements.map(m => (m.buy_amount || 0) + (m.sell_amount || 0));

        const colors = [
            '#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0',
            '#6610f2', '#e83e8c', '#fd7e14', '#20c997', '#6f42c1'
        ];

        this.fundDistributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: '#fff',
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 16,
                            padding: 15,
                            font: {
                                size: 13,
                                weight: '500'
                            },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 13
                        },
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => {
                                const index = context.dataIndex;
                                const movement = validMovements[index];
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                const fundName = movement ? movement.fund_name : '';
                                return [
                                    `${label}${fundName ? ' - ' + fundName : ''}`,
                                    `Giá trị: ${this.formatCurrency(value)}`,
                                    `Tỷ lệ: ${percentage}%`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    renderBuySellComparisonChart() {
        const ctx = document.getElementById('buySellComparisonChart');
        if (!ctx) return;

        if (this.buySellComparisonChart) {
            this.buySellComparisonChart.destroy();
        }

        const fundMovements = this.state.fund_movements || [];
        
        // Filter chỉ lấy các quỹ có giao dịch (buy_amount > 0 hoặc sell_amount > 0)
        const validMovements = fundMovements.filter(m => {
            const buyAmount = m.buy_amount || 0;
            const sellAmount = m.sell_amount || 0;
            return buyAmount > 0 || sellAmount > 0;
        });

        if (validMovements.length === 0) {
            console.warn('No data to render buy sell comparison chart');
            return;
        }

        const labels = validMovements.map(m => m.fund_ticker || 'N/A');
        const buyData = validMovements.map(m => m.buy_amount || 0);
        const sellData = validMovements.map(m => m.sell_amount || 0);

        this.buySellComparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mua',
                    data: buyData,
                    backgroundColor: '#198754',
                    borderColor: '#146c43',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }, {
                    label: 'Bán',
                    data: sellData,
                    backgroundColor: '#dc3545',
                    borderColor: '#b02a37',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: {
                                size: 14,
                                weight: '600'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 13
                        },
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: (context) => {
                                const index = context[0].dataIndex;
                                const movement = validMovements[index];
                                return movement ? `${movement.fund_ticker} - ${movement.fund_name || ''}` : '';
                            },
                            label: (context) => {
                                const index = context.dataIndex;
                                const movement = validMovements[index];
                                const value = context.parsed.y;
                                const label = context.dataset.label;
                                return `${label}: ${this.formatCurrency(value)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 8
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 8,
                            callback: (value) => {
                                const rounded = Math.round(value);
                                if (rounded >= 1000000000) {
                                    return (rounded / 1000000000).toFixed(1) + 'B';
                                } else if (rounded >= 1000000) {
                                    return (rounded / 1000000).toFixed(1) + 'M';
                                } else if (rounded >= 1000) {
                                    return (rounded / 1000).toFixed(1) + 'K';
                                }
                                return rounded;
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
    }

    renderNavOpeningPriceChart() {
        const ctx = document.getElementById('navOpeningPriceChart');
        if (!ctx) return;

        if (this.navOpeningPriceChart) {
            this.navOpeningPriceChart.destroy();
        }

        const navData = this.state.nav_opening_data?.funds || [];
        
        // Filter chỉ lấy các quỹ có giá CCQ > 0
        const validNavData = navData.filter(f => {
            const price = f.opening_price || 0;
            const numPrice = typeof price === 'string' ? parseFloat(price) : (isNaN(price) ? 0 : price);
            return numPrice > 0;
        });

        if (validNavData.length === 0) {
            console.warn('No data to render NAV opening price chart');
            return;
        }

        const labels = validNavData.map(f => f.fund_ticker || 'N/A');
        // Đảm bảo prices là số thực
        const prices = validNavData.map(f => {
            const price = f.opening_price || 0;
            return typeof price === 'string' ? parseFloat(price) : (isNaN(price) ? 0 : price);
        });
        
        // Debug log
        console.log('NAV Opening Chart Data:', {
            navData: validNavData,
            prices: prices,
            sample: validNavData.length > 0 ? {
                ticker: validNavData[0].fund_ticker,
                rawPrice: validNavData[0].opening_price,
                priceType: typeof validNavData[0].opening_price,
                parsedPrice: prices[0]
            } : null
        });

        // Calculate max price for percentage calculation
        const maxPrice = Math.max(...prices, 1);
        const pricePercentages = prices.map(p => (p / maxPrice) * 100);

        this.navOpeningPriceChart = new Chart(ctx, {
            type: 'line',
            indexAxis: 'y', // Horizontal line chart
            data: {
                labels: labels,
                datasets: [{
                    label: 'Giá CCQ đầu ngày (%)',
                    data: pricePercentages,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.15)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#0d6efd',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#0d6efd',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 16,
                            padding: 15,
                            font: {
                                size: 13,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: '600'
                        },
                        bodyFont: {
                            size: 13
                        },
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: (context) => {
                                const index = context[0].dataIndex;
                                const fund = validNavData[index];
                                return fund ? `${fund.fund_ticker} - ${fund.fund_name || ''}` : '';
                            },
                            label: (context) => {
                                const index = context.dataIndex;
                                const fund = validNavData[index];
                                const price = prices[index];
                                const percentage = context.parsed.x;
                                const ccq = fund ? (fund.opening_ccq || 0) : 0;
                                return [
                                    `Giá: ${this.formatCurrency(price)}`,
                                    `Tỷ lệ: ${percentage.toFixed(1)}%`,
                                    `CCQ: ${this.formatNumber(ccq)}`,
                                    `Giá trị: ${this.formatCurrency(fund ? (fund.opening_value || 0) : 0)}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 8,
                            callback: (value) => {
                                return value.toFixed(0) + '%';
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 8
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }

    getProductCards() {
        const stats = this.state.product_status_stats || {};
        const pending = stats.pending || 0;
        const active = stats.active || 0;
        const total = stats.total || pending + active;
        return [
            {
                label: 'Sản phẩm hoạt động chờ duyệt',
                value: this.formatNumber(pending),
                icon: 'fas fa-hourglass-half',
                variant: 'variant-neutral',
            },
            {
                label: 'Chương trình hoạt động đã duyệt',
                value: this.formatNumber(active),
                icon: 'fas fa-clipboard-check',
                variant: 'variant-accent',
            },
            {
                label: 'Tổng sản phẩm theo dõi',
                value: this.formatNumber(total),
                icon: 'fas fa-layer-group',
                variant: 'variant-primary',
            },
        ];
    }

    getBalanceCards() {
        const metrics = this.state.balance_metrics || {};
        return [
            {
                label: 'Tổng chờ mua',
                value: this.formatCurrency(metrics.total_buy_pending_amount),
                description: 'Giá trị lệnh mua đang xử lý',
                icon: 'fas fa-hand-holding-usd',
                variant: 'variant-neutral',
            },
            {
                label: 'Tổng chờ bán',
                value: this.formatCurrency(metrics.total_sell_pending_amount),
                description: 'Giá trị lệnh bán đang xử lý',
                icon: 'fas fa-wallet',
                variant: 'variant-sky',
            },
            {
                label: 'Tài sản nhà đầu tư',
                value: this.formatCurrency(metrics.investor_assets || this.state.summary.total_current_value),
                description: `${this.formatNumber(this.state.summary.total_accounts || 0)} tài khoản`,
                icon: 'fas fa-building',
                variant: 'variant-green',
            },
        ];
    }

    getUserStatusRows() {
        const total = this.state.accounts.total || 0;
        const statuses = this.state.accounts.by_status || {};
        const mapping = [
            { key: 'pending', label: 'Nhà đầu tư chờ KYC', variant: 'dot-warning' },
            { key: 'kyc', label: 'Nhà đầu tư đã KYC', variant: 'dot-success' },
            { key: 'vsd', label: 'Nhà đầu tư đã có VSD', variant: 'dot-info' },
            { key: 'incomplete', label: 'Nhà đầu tư thiếu hồ sơ', variant: 'dot-muted' },
        ];

        const rows = mapping.map((item) => {
            const value = statuses[item.key] || 0;
            return {
                label: item.label,
                value: this.formatNumber(value),
                variant: item.variant,
                badge: total ? this.formatPercentage(value, total) : null,
                badgeVariant: 'badge-light',
            };
        });

        rows.push({
            label: 'Tổng người dùng',
            value: this.formatNumber(total),
            variant: 'dot-primary',
            badge: '100%',
            badgeVariant: 'badge-strong',
        });

        return rows;
    }

    getTransactionCards() {
        const stats = this.state.transaction_status_stats || {};
        const buyStats = stats.buy || {};
        const sellStats = stats.sell || {};
        const pendingPlaceholder = {
            value: '--',
            description: 'Đang cập nhật từ kết quả lệnh',
        };
        return [
            {
                label: 'Lệnh mua chờ xác nhận',
                value: pendingPlaceholder.value,
                description: pendingPlaceholder.description,
                status: 'BUY',
                variant: 'variant-buy-pending',
            },
            {
                label: 'Lệnh mua chờ khớp lệnh',
                value: this.formatNumber(buyStats.pending_match?.count || 0),
                description: this.formatCurrency(buyStats.pending_match?.amount || 0),
                status: 'BUY',
                variant: 'variant-buy-waiting',
            },
            {
                label: 'Lệnh mua đã khớp lệnh',
                value: this.formatNumber(buyStats.matched?.count || 0),
                description: this.formatCurrency(buyStats.matched?.amount || 0),
                status: 'BUY',
                variant: 'variant-buy-matched',
            },
            {
                label: 'Lệnh bán chờ xác nhận',
                value: pendingPlaceholder.value,
                description: pendingPlaceholder.description,
                status: 'SELL',
                variant: 'variant-sell-pending',
            },
            {
                label: 'Lệnh bán chờ khớp lệnh',
                value: this.formatNumber(sellStats.pending_match?.count || 0),
                description: this.formatCurrency(sellStats.pending_match?.amount || 0),
                status: 'SELL',
                variant: 'variant-sell-waiting',
            },
            {
                label: 'Lệnh bán đã khớp lệnh',
                value: this.formatNumber(sellStats.matched?.count || 0),
                description: this.formatCurrency(sellStats.matched?.amount || 0),
                status: 'SELL',
                variant: 'variant-sell-matched',
            },
        ];
    }

    getTrafficStats() {
        const stats = this.state.traffic_stats || {};
        return [
            {
                label: 'Đang truy cập',
                value: this.formatNumber(stats.current_sessions || 0),
                description: 'Phiên hoạt động',
            },
            {
                label: 'Hôm nay',
                value: this.formatNumber(stats.today || 0),
                description: 'Tổng lượt ghi nhận',
            },
            {
                label: 'Trong tuần',
                value: this.formatNumber(stats.week || 0),
                description: 'Ước tính 5 ngày',
            },
            {
                label: 'Trong tháng',
                value: this.formatNumber(stats.month || 0),
                description: 'Ước tính 4 tuần',
            },
            {
                label: 'Cảnh báo bảo mật',
                value: this.formatNumber(stats.alerts || 0),
                description: 'Sự kiện cần chú ý',
            },
            {
                label: 'Tổng truy cập',
                value: this.formatNumber(stats.total || 0),
                description: 'Bao gồm giao dịch & NĐT',
            },
        ];
    }

    getDefaultTrafficStats() {
        return {
            current_sessions: 0,
            today: 0,
            week: 0,
            month: 0,
            total: 0,
            alerts: 0,
        };
    }

    computeTransactionStatusStats(transactions = []) {
        const baseBucket = () => ({ count: 0, amount: 0 });
        const stats = {
            buy: {
                pending_confirm: baseBucket(),
                pending_match: baseBucket(),
                matched: baseBucket(),
            },
            sell: {
                pending_confirm: baseBucket(),
                pending_match: baseBucket(),
                matched: baseBucket(),
            },
        };
        const buyTypes = ['buy'];
        const sellTypes = ['sell'];
        transactions.forEach((tx) => {
            const type = buyTypes.includes(tx.transaction_type) ? 'buy'
                : sellTypes.includes(tx.transaction_type) ? 'sell'
                : null;
            if (!type) {
                return;
            }
            const status = tx.status || '';
            let bucket = null;
            if (status === 'pending') {
                bucket = 'pending_match';
            } else if (status === 'completed') {
                bucket = 'matched';
            }
            if (bucket && stats[type][bucket]) {
                stats[type][bucket].count += 1;
                stats[type][bucket].amount += tx.amount || 0;
            }
        });
        return stats;
    }

    computeBalanceMetrics(transactionStats, summary = {}) {
        const buyPending = ((transactionStats.buy?.pending_confirm?.amount) || 0) +
            ((transactionStats.buy?.pending_match?.amount) || 0);
        const sellPending = ((transactionStats.sell?.pending_confirm?.amount) || 0) +
            ((transactionStats.sell?.pending_match?.amount) || 0);
        return {
            total_buy_pending_amount: buyPending,
            total_sell_pending_amount: sellPending,
            investor_assets: summary.total_current_value || 0,
        };
    }

    showError(message) {
        console.error(message);
        const widgetContainer = document.getElementById('dashboard-widget');
        const errorContainer = document.getElementById('error-container');
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = message;
        }
        if (errorContainer) {
            errorContainer.style.display = 'block';
        }
        if (widgetContainer) {
            widgetContainer.style.display = 'none';
        }
    }

    formatCurrency(value) {
        if (!value && value !== 0) return "0 ₫";
        // Đảm bảo value là number
        const numValue = typeof value === 'string' ? parseFloat(value) : value;
        if (isNaN(numValue)) return "0 ₫";
        // Làm tròn số
        const rounded = Math.round(numValue);
        // Format thủ công để đảm bảo hiển thị đúng
        // Chia thành phần nguyên và format với dấu chấm phân cách hàng nghìn
        const parts = rounded.toString().split('.');
        let integerPart = parts[0];
        // Thêm dấu chấm phân cách hàng nghìn
        integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return integerPart + ' ₫';
    }

    formatNumber(value) {
        if (!value && value !== 0) return "0";
        // Đảm bảo value là number
        const numValue = typeof value === 'string' ? parseFloat(value) : value;
        if (isNaN(numValue)) return "0";
        const formatted = new Intl.NumberFormat("vi-VN", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2,
        }).format(numValue);
        // Bỏ ,00 nếu có
        return formatted.replace(/,00$/, '');
    }

    formatPercentage(value, total) {
        if (!total) {
            return "0%";
        }
        const ratio = (value / total) * 100;
        return `${ratio.toFixed(1)}%`;
    }
}

