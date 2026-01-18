/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";

/**
 * NormalOrdersComponent
 * 
 * Displays a list of "Normal Orders" (Lệnh đặt thông thường) with:
 * - Filter tabs: Pending / Filled
 * - Checkbox selection for batch operations
 * - Send to Exchange button
 * - Convert to Negotiated (Market Maker feature)
 */
export class NormalOrdersComponent extends Component {
    static template = xml`
        <div class="order-book-page">
            <div class="order-book-hero">
                <div class="hero-content">
                    <div class="hero-copy">
                        <div class="hero-pill">Trung tâm sổ lệnh</div>
                        <h1>Lệnh đặt thường</h1>
                        <p class="hero-lead">
                            Quản lý lệnh mua/bán gửi trực tiếp lên sàn giao dịch. Theo dõi trạng thái lệnh từ chờ khớp đến hoàn tất.
                        </p>
                        <div class="hero-meta">
                            <span class="status-chip">
                                <i class="fa fa-clock-o"></i>
                                Cập nhật:
                                <t t-esc="formatDateTime(state.lastUpdate)"/>
                            </span>
                        </div>
                        <div class="order-book-nav">
                            <a href="/order-book" class="nav-link">Khoản đầu tư chờ xử lý</a>
                            <a href="/completed-orders" class="nav-link">Khoản đầu tư đã khớp</a>
                            <a href="/negotiated-orders" class="nav-link">Khoản đầu tư khớp theo thỏa thuận</a>
                            <a href="/normal-orders" class="nav-link active">Lệnh đặt thường</a>
                        </div>
                        <t t-if="state.isMarketMaker">
                            <div class="mt-3">
                                <a href="/investment_dashboard" class="btn-back-market-maker" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: white; color: #2563EB; border: 2px solid #2563EB; border-radius: 8px; font-weight: 600; font-size: 14px; text-decoration: none; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2); transition: all 0.2s ease;">
                                    <i class="fa fa-arrow-left"></i>Quay lại Dashboard
                                </a>
                            </div>
                        </t>
                    </div>
                </div>
                <div class="hero-actions">
                    <button class="btn btn-refresh" title="Làm mới dữ liệu" t-on-click="refreshData">
                        <i class="fa fa-refresh"></i>
                        Làm mới
                    </button>
                    <button class="btn btn-secondary btn-sm" t-att-disabled="state.selectedIds.size === 0 || state.sending" t-on-click="sendSelectedToExchange">
                        <i class="fa fa-paper-plane"></i>
                        Gửi lên sàn (<t t-esc="state.selectedIds.size"/>)
                    </button>
                </div>
            </div>
            
            <div class="partial-orders-card">
                <div class="negotiated-header">
                    <h2>
                        <i class="fa fa-exchange"></i>
                        Danh sách lệnh đặt thường
                    </h2>
                    <div class="header-actions">
                        <div class="filter-tabs">
                            <button 
                                t-att-class="'filter-tab' + (state.statusFilter === 'pending' ? ' active' : '')"
                                t-on-click="() => this.setStatusFilter('pending')"
                            >
                                Chờ khớp (<t t-esc="state.pendingCount"/>)
                            </button>
                            <button 
                                t-att-class="'filter-tab' + (state.statusFilter === 'filled' ? ' active' : '')"
                                t-on-click="() => this.setStatusFilter('filled')"
                            >
                                Đã khớp (<t t-esc="state.filledCount"/>)
                            </button>
                        </div>
                    </div>
                </div>
                
                <div t-if="state.loading" class="loading-container">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Đang tải...</span>
                    </div>
                    <div class="loading-text">Đang tải dữ liệu...</div>
                </div>
                
                <div t-elif="state.orders.length === 0" class="no-orders">
                    <i class="fa fa-inbox"></i>
                    Không có lệnh nào
                </div>
                
                <div t-else="" class="orders-table table-responsive">
                    <table class="table table-sm table-hover table-striped align-middle matched-table">
                        <thead class="table-light sticky-head">
                            <tr>
                                <th style="width:36px;" class="text-center">
                                    <input type="checkbox" class="form-check-input" t-att-checked="state.selectAll" t-on-change="toggleSelectAll"/>
                                </th>
                                <th class="text-center">Loại</th>
                                <th class="text-center">Mã CCQ</th>
                                <th class="text-center">SL CCQ</th>
                                <th class="text-center">Giá</th>
                                <th class="text-center">Loại lệnh</th>
                                <th class="text-center">Nhà đầu tư</th>
                                <th class="text-center">Thời gian</th>
                                <th class="text-center">Trạng thái</th>
                                <th class="text-center">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="state.orders" t-as="order" t-key="order.id">
                                <tr t-att-class="order.transaction_type === 'sell' ? 'sell-order' : 'buy-order'">
                                    <td class="text-center">
                                        <input type="checkbox" class="form-check-input" t-att-checked="state.selectedIds.has(order.id)" t-att-disabled="order.exchange_status !== 'pending'" t-on-change="(e) => this.toggleSelect(order.id, e)"/>
                                    </td>
                                    <td class="text-center">
                                        <span t-att-class="'badge ' + (order.transaction_type === 'buy' ? 'bg-success' : 'bg-danger')">
                                            <t t-esc="order.transaction_type === 'buy' ? 'Mua' : 'Bán'"/>
                                        </span>
                                    </td>
                                    <td class="text-center fw-semibold fund-symbol">
                                        <t t-esc="order.fund_ticker"/>
                                    </td>
                                    <td class="text-end">
                                        <t t-esc="formatNumber(order.units)"/>
                                    </td>
                                    <td class="text-end">
                                        <t t-esc="formatPrice(order.price)"/>
                                    </td>
                                    <td class="text-center">
                                        <span class="badge bg-info text-dark">
                                            <t t-esc="order.order_type_detail"/>
                                        </span>
                                    </td>
                                    <td class="text-center">
                                        <t t-esc="order.user_name"/>
                                    </td>
                                    <td class="text-nowrap">
                                        <t t-esc="formatDateTime(order.created_at)"/>
                                    </td>
                                    <td class="text-center">
                                        <span t-att-class="'badge ' + getStatusBadgeClass(order.exchange_status)">
                                            <t t-esc="formatExchangeStatus(order.exchange_status)"/>
                                        </span>
                                    </td>
                                    <td class="text-center">
                                        <t t-if="order.exchange_status === 'pending'">
                                            <button class="btn btn-sm btn-outline-primary" title="Chuyển thành lệnh thỏa thuận" t-on-click="() => this.openConvertModal(order)">
                                                <i class="fa fa-random"></i>
                                            </button>
                                        </t>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    static props = {
        funds: { type: Array, optional: true },
        selectedFund: { type: Object, optional: true },
    };
    
    setup() {
        this.state = useState({
            orders: [],
            loading: false,
            statusFilter: 'pending',
            pendingCount: 0,
            filledCount: 0,
            selectedIds: new Set(),
            selectAll: false,
            sending: false,
            lastUpdate: null,
            isMarketMaker: false,
        });
        
        onMounted(() => {
            this.loadOrders();
            this.checkUserPermission();
            // Auto refresh every 10 seconds
            this.refreshInterval = setInterval(() => this.loadOrders(), 10000);
        });
        
        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }
    
    async refreshData() {
        await this.loadOrders();
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
                })
            });
            const jsonRpcResponse = await response.json();
            const data = jsonRpcResponse.result || jsonRpcResponse;
            if (data && data.success) {
                this.state.isMarketMaker = data.is_market_maker === true && data.user_type === 'portal';
            }
        } catch (error) {
            console.error('Error checking user permission:', error);
        }
    }
    
    getStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-warning text-dark',
            'sent': 'bg-info',
            'filled': 'bg-success',
            'partial': 'bg-primary',
            'rejected': 'bg-danger',
            'cancelled': 'bg-secondary'
        };
        return classes[status] || 'bg-secondary';
    }
    
    // ==========================================================================
    // DATA LOADING
    // ==========================================================================
    async loadOrders() {
        this.state.loading = true;
        
        try {
            const fundId = this.props.selectedFund?.id;
            
            const response = await fetch('/api/fund/normal-order/list', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        fund_id: fundId,
                        status: this.state.statusFilter === 'filled' ? 'filled' : 'pending',
                        limit: 100
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.result && result.result.success) {
                this.state.orders = result.result.orders || [];
                this.updateCounts();
            } else {
                console.error('[NormalOrders] Load error:', result);
            }
            
            this.state.lastUpdate = new Date();
        } catch (error) {
            console.error('[NormalOrders] Fetch error:', error);
        } finally {
            this.state.loading = false;
        }
    }
    
    async updateCounts() {
        try {
            // Get pending count
            const pendingRes = await fetch('/api/fund/normal-order/list', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { status: 'pending', limit: 1000 }
                })
            });
            const pendingData = await pendingRes.json();
            this.state.pendingCount = pendingData.result?.orders?.length || 0;
            
            // Get filled count
            const filledRes = await fetch('/api/fund/normal-order/list', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { status: 'filled', limit: 1000 }
                })
            });
            const filledData = await filledRes.json();
            this.state.filledCount = filledData.result?.orders?.length || 0;
        } catch (e) {
            console.warn('[NormalOrders] Count update failed:', e);
        }
    }
    
    // ==========================================================================
    // FILTER & SELECTION
    // ==========================================================================
    setStatusFilter(status) {
        if (this.state.statusFilter === status) return;
        
        this.state.statusFilter = status;
        this.state.selectedIds = new Set();
        this.state.selectAll = false;
        this.loadOrders();
    }
    
    toggleSelectAll(e) {
        const checked = e.target.checked;
        this.state.selectAll = checked;
        
        if (checked) {
            this.state.selectedIds = new Set(
                this.state.orders
                    .filter(o => o.exchange_status === 'pending')
                    .map(o => o.id)
            );
        } else {
            this.state.selectedIds = new Set();
        }
    }
    
    toggleSelect(orderId, e) {
        const checked = e.target.checked;
        const newSet = new Set(this.state.selectedIds);
        
        if (checked) {
            newSet.add(orderId);
        } else {
            newSet.delete(orderId);
        }
        
        this.state.selectedIds = newSet;
        this.state.selectAll = newSet.size === this.state.orders.filter(o => o.exchange_status === 'pending').length;
    }
    
    // ==========================================================================
    // SEND TO EXCHANGE
    // ==========================================================================
    async sendSelectedToExchange() {
        if (this.state.selectedIds.size === 0) return;
        
        this.state.sending = true;
        
        try {
            const response = await fetch('/api/fund/normal-order/send-to-exchange', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        order_ids: Array.from(this.state.selectedIds)
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.result) {
                const { sent_count, failed, message } = result.result;
                
                // Show success notification if any orders were sent
                if (sent_count > 0) {
                    this.showNotification(message, 'success');
                }
                
                // Show detailed error messages from SSI for failed orders
                if (failed && failed.length > 0) {
                    console.warn('[NormalOrders] Failed orders:', JSON.stringify(failed, null, 2));
                    
                    // Display each error to the user
                    for (const failedOrder of failed) {
                        const errorMsg = failedOrder.error || 'Lỗi không xác định';
                        this.showNotification(`Lệnh #${failedOrder.id}: ${errorMsg}`, 'error');
                    }
                }
                
                // If no success and no specific errors shown, show generic message
                if (sent_count === 0 && (!failed || failed.length === 0)) {
                    this.showNotification(message, 'error');
                }
                
                // Refresh list
                this.state.selectedIds = new Set();
                this.state.selectAll = false;
                await this.loadOrders();
            }
        } catch (error) {
            console.error('[NormalOrders] Send error:', error);
            this.showNotification('Lỗi gửi lệnh lên sàn', 'error');
        } finally {
            this.state.sending = false;
        }
    }
    
    // ==========================================================================
    // CONVERT TO NEGOTIATED
    // ==========================================================================
    async openConvertModal(order) {
        // Use SweetAlert for modal
        if (typeof Swal === 'undefined') {
            alert('Chức năng đang phát triển');
            return;
        }
        
        const { value: formValues } = await Swal.fire({
            title: 'Chuyển thành lệnh thỏa thuận',
            html: `
                <div style="text-align: left;">
                    <p><strong>Lệnh:</strong> ${order.transaction_type === 'buy' ? 'Mua' : 'Bán'} ${order.units} CCQ @ ${this.formatPrice(order.price)}</p>
                    <div style="margin-top: 16px;">
                        <label>Kỳ hạn (tháng)</label>
                        <input id="swal-term" type="number" class="swal2-input" min="1" max="12" value="3">
                    </div>
                    <div style="margin-top: 12px;">
                        <label>Lãi suất (%)</label>
                        <input id="swal-rate" type="number" class="swal2-input" step="0.01" min="0" max="20" value="6.0">
                    </div>
                </div>
            `,
            focusConfirm: false,
            showCancelButton: true,
            confirmButtonText: 'Chuyển đổi',
            cancelButtonText: 'Hủy',
            preConfirm: () => {
                return {
                    term_months: parseInt(document.getElementById('swal-term').value),
                    interest_rate: parseFloat(document.getElementById('swal-rate').value)
                };
            }
        });
        
        if (formValues) {
            await this.convertToNegotiated(order.id, formValues.term_months, formValues.interest_rate);
        }
    }
    
    async convertToNegotiated(orderId, termMonths, interestRate) {
        try {
            const response = await fetch('/api/fund/normal-order/convert-to-negotiated', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        order_id: orderId,
                        term_months: termMonths,
                        interest_rate: interestRate
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.result && result.result.success) {
                this.showNotification('Đã chuyển thành lệnh thỏa thuận', 'success');
                await this.loadOrders();
            } else {
                this.showNotification(result.result?.message || 'Lỗi chuyển đổi', 'error');
            }
        } catch (error) {
            console.error('[NormalOrders] Convert error:', error);
            this.showNotification('Lỗi hệ thống', 'error');
        }
    }
    
    // ==========================================================================
    // FORMATTERS
    // ==========================================================================
    formatNumber(value) {
        return new Intl.NumberFormat('vi-VN').format(value || 0);
    }
    
    formatPrice(price) {
        return new Intl.NumberFormat('vi-VN', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(price || 0);
    }
    
    formatDateTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }
    
    formatExchangeStatus(status) {
        const statusMap = {
            'pending': 'Chờ gửi',
            'sent': 'Đã gửi',
            'filled': 'Đã khớp',
            'partial': 'Khớp 1 phần',
            'rejected': 'Từ chối',
            'cancelled': 'Đã hủy'
        };
        return statusMap[status] || status;
    }
    
    showNotification(message, type = 'info') {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: type === 'error' ? 'error' : type === 'success' ? 'success' : 'info',
                title: message,
                timer: 3000,
                showConfirmButton: false,
                position: 'top-end',
                toast: true
            });
        }
    }
}
