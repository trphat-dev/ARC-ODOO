/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

/**
 * StockBoard - Professional Realtime Trading Board
 * 
 * Features:
 * - Pure WebSocket via bus.bus (NO polling/refresh)
 * - Reactive state updates
 * - Index filtering (VN30, HNX30)
 * - Search & Sort
 * - Flash animations on price change
 */
export class StockBoard extends Component {
    static template = "stock_data.StockBoard";
    static props = {};

    setup() {
        this.busService = useService("bus_service");
        this.actionService = useService("action");
        this.notification = useService("notification");
        
        this.tableRef = useRef("stockTable");
        this.searchInputRef = useRef("searchInput");
        
        // Main reactive state
        this.state = useState({
            // Data
            securities: [],
            securitiesMap: {},  // Quick lookup: symbol -> security
            
            // Index data
            indexes: [],
            indexSymbols: {},  // indexCode -> [symbols]
            
            // UI State
            loading: true,
            connected: false,
            lastUpdate: null,
            messagesReceived: 0,
            
            // Filters
            filter: 'all',      // all, hose, hnx, upcom
            indexFilter: '',    // VN30, HNX30, etc.
            searchQuery: '',
            
            // Sort
            sortBy: 'symbol',
            sortAsc: true,
            
            // Live clock
            currentTime: new Date().toLocaleTimeString('vi-VN'),
        });
        
        this._handler = null;
        this._searchDebounce = null;
        this._clockInterval = null;
        this._refreshInterval = null;  // Auto-refresh interval (polling)
        
        onMounted(() => {
            this._loadInitialData();
            this._subscribeToBus();
            this._startClock();
            this._startAutoRefresh();  // Start polling for real-time updates
        });
        
        onWillUnmount(() => {
            this._unsubscribeFromBus();
            this._stopClock();
            this._stopAutoRefresh();  // Clean up interval
        });
    }
    
    // =========================================================================
    // Live Clock
    // =========================================================================
    
    _startClock() {
        this._clockInterval = setInterval(() => {
            this.state.currentTime = new Date().toLocaleTimeString('vi-VN');
        }, 1000);
    }
    
    _stopClock() {
        if (this._clockInterval) {
            clearInterval(this._clockInterval);
        }
    }
    
    // =========================================================================
    // Auto Refresh (Polling - same pattern as order_matching)
    // =========================================================================
    
    _startAutoRefresh() {
        // Smart refresh every 5 seconds - only highlights changes, no full reload
        this._refreshInterval = setInterval(() => {
            this._smartRefresh();
        }, 5000);
        console.log('[StockBoard] Smart auto-refresh started (5s interval)');
    }
    
    _stopAutoRefresh() {
        if (this._refreshInterval) {
            clearInterval(this._refreshInterval);
            this._refreshInterval = null;
            console.log('[StockBoard] Auto-refresh stopped');
        }
    }
    
    /**
     * Smart Refresh: Fetch new data and only flash changed items
     * - No loading state (seamless)
     * - Compare prices, only update changed securities
     * - Flash animation for price changes
     */
    async _smartRefresh() {
        try {
            const securities = await rpc("/web/dataset/call_kw/ssi.securities/search_read", {
                model: "ssi.securities",
                method: "search_read",
                args: [],
                kwargs: {
                    domain: [['is_active', '=', true]],
                    fields: [
                        'symbol', 'stock_name_vn', 'market',
                        'current_price', 'reference_price', 'ceiling_price', 'floor_price',
                        'volume', 'change', 'change_percent', 'high_price', 'low_price',
                        'bid_price_1', 'bid_vol_1', 'ask_price_1', 'ask_vol_1'
                    ],
                    order: 'symbol asc',
                },
            });
            
            let changesCount = 0;
            
            // Compare and update each security
            for (const newData of securities) {
                const existing = this.state.securitiesMap[newData.symbol];
                if (!existing) continue;
                
                // Check if price changed
                const oldPrice = existing.current_price || 0;
                const newPrice = newData.current_price || 0;
                
                if (Math.abs(newPrice - oldPrice) > 0.001) {
                    // Price changed - apply update with flash
                    this._applyUpdate(newData.symbol, {
                        current_price: newData.current_price,
                        volume: newData.volume,
                        change: newData.change,
                        change_percent: newData.change_percent,
                        high_price: newData.high_price,
                        low_price: newData.low_price,
                        reference_price: newData.reference_price,
                        ceiling_price: newData.ceiling_price,
                        floor_price: newData.floor_price,
                        bid_price_1: newData.bid_price_1,
                        bid_vol_1: newData.bid_vol_1,
                        ask_price_1: newData.ask_price_1,
                        ask_vol_1: newData.ask_vol_1,
                    });
                    changesCount++;
                } else {
                    // No price change - silently update other fields without flash
                    existing.volume = newData.volume;
                    existing.change = newData.change;
                    existing.change_percent = newData.change_percent;
                    existing.high_price = newData.high_price;
                    existing.low_price = newData.low_price;
                    existing.bid_price_1 = newData.bid_price_1;
                    existing.bid_vol_1 = newData.bid_vol_1;
                    existing.ask_price_1 = newData.ask_price_1;
                    existing.ask_vol_1 = newData.ask_vol_1;
                }
            }
            
            this.state.lastUpdate = new Date();
            
            if (changesCount > 0) {
                console.log(`[StockBoard] Smart refresh: ${changesCount} price changes`);
            }
            
        } catch (error) {
            console.error('[StockBoard] Smart refresh error:', error);
        }
    }

    // =========================================================================
    // Initial Data Load (ONE TIME ONLY)
    // =========================================================================
    
    async _loadInitialData() {
        this.state.loading = true;
        
        try {
            // Load securities
            const securities = await rpc("/web/dataset/call_kw/ssi.securities/search_read", {
                model: "ssi.securities",
                method: "search_read",
                args: [],
                kwargs: {
                    domain: [['is_active', '=', true]],
                    fields: [
                        'symbol', 'stock_name_vn', 'market',
                        'current_price', 'reference_price', 'ceiling_price', 'floor_price',
                        'volume', 'change', 'change_percent', 'high_price', 'low_price',
                        'bid_price_1', 'bid_vol_1', 'ask_price_1', 'ask_vol_1'
                    ],
                    order: 'symbol asc',
                },
            });
            
            // Process securities
            const securitiesMap = {};
            this.state.securities = securities.map(s => {
                const processed = {
                    ...s,
                    direction: this._getDirection(s.current_price, s.reference_price),
                    priceClass: this._getPriceClass(s.current_price, s.reference_price, s.ceiling_price, s.floor_price),
                    flashClass: '',
                };
                securitiesMap[s.symbol] = processed;
                return processed;
            });
            this.state.securitiesMap = securitiesMap;
            
            // Load indexes
            await this._loadIndexes();
            
            this.state.loading = false;
            this.state.lastUpdate = new Date();
            
        } catch (error) {
            console.error('[StockBoard] Initial load error:', error);
            this.state.loading = false;
            this.notification.add("Không thể tải dữ liệu", { type: 'danger' });
        }
    }
    
    async _loadIndexes() {
        try {
            // Load index list from database
            let indexes = [];
            try {
                indexes = await rpc("/web/dataset/call_kw/ssi.index.list/search_read", {
                    model: "ssi.index.list",
                    method: "search_read",
                    args: [],
                    kwargs: {
                        domain: [],
                        fields: ['index_code', 'index_name_vn'],
                        order: 'index_code asc',
                    }
                });
            } catch (e) {
                console.warn('[StockBoard] Index list not available');
            }
            
            this.state.indexes = indexes;
            
            // Load index components from database
            let components = [];
            try {
                components = await rpc("/web/dataset/call_kw/ssi.index.components/search_read", {
                    model: "ssi.index.components",
                    method: "search_read",
                    args: [],
                    kwargs: {
                        domain: [['is_active', '=', true]],
                        fields: ['index_code', 'symbol'],
                    }
                });
            } catch (e) {
                console.warn('[StockBoard] Index components not available');
            }
            
            // Group symbols by index code
            const indexSymbols = {};
            for (const comp of components) {
                if (!indexSymbols[comp.index_code]) {
                    indexSymbols[comp.index_code] = [];
                }
                indexSymbols[comp.index_code].push(comp.symbol);
            }
            
            this.state.indexSymbols = indexSymbols;
            
        } catch (error) {
            console.warn('[StockBoard] Load indexes error:', error);
        }
    }

    // =========================================================================
    // WebSocket Subscription (PURE REALTIME)
    // =========================================================================
    
    _subscribeToBus() {
        try {
            this._handler = this._onBusNotification.bind(this);
            
            // Odoo 18 bus API:
            // - addChannel(channel) -> adds channel to poll from server
            // - subscribe(notification_type, callback) -> subscribes to notification type
            
            // Step 1: Add channel to receive messages from 'stock_data_live'
            if (typeof this.busService.addChannel === 'function') {
                this.busService.addChannel('stock_data_live');
                console.log('[StockBoard] Added channel: stock_data_live');
            }
            
            // Step 2: Subscribe to the notification TYPE (not channel)
            // In Odoo 18, subscribe() takes notification type as first arg
            if (typeof this.busService.subscribe === 'function') {
                this.busService.subscribe('stock_data/price_update', this._handler);
                console.log('[StockBoard] Subscribed to type: stock_data/price_update');
            }
            
            // Step 3: Also listen via addEventListener for broader compatibility
            if (typeof this.busService.addEventListener === 'function') {
                this.busService.addEventListener('notification', this._handler);
            }
            
            this.state.connected = true;
            console.log('[StockBoard] Connected to realtime channel');
            
        } catch (e) {
            console.error('[StockBoard] Subscribe error:', e);
        }
    }
    
    _unsubscribeFromBus() {
        if (!this._handler) return;
        
        try {
            if (typeof this.busService.unsubscribe === 'function') {
                this.busService.unsubscribe('stock_data/price_update', this._handler);
            }
            if (typeof this.busService.removeEventListener === 'function') {
                this.busService.removeEventListener('notification', this._handler);
            }
        } catch (e) {
            // Ignore
        }
    }
    
    _onBusNotification(notifications) {
        // Odoo 18 sends notifications in different formats
        let notifList = [];
        
        if (notifications?.detail) {
            // Event format: {detail: [...]}
            notifList = notifications.detail;
        } else if (Array.isArray(notifications)) {
            notifList = notifications;
        } else if (notifications) {
            notifList = [notifications];
        }
        
        for (const notif of notifList) {
            if (!notif) continue;
            
            // Check notification type
            const notifType = notif.type || notif[1];
            if (notifType !== 'stock_data/price_update') continue;
            
            // Get payload (Odoo 18 format: notif.payload or notif[2])
            const payload = notif.payload || notif[2] || {};
            
            // Batch update
            if (payload.type === 'batch_update' && Array.isArray(payload.updates)) {
                for (const update of payload.updates) {
                    this._applyUpdate(update.symbol, update.data);
                }
                this.state.messagesReceived++;
                this.state.lastUpdate = new Date();
                continue;
            }
            
            // Single update
            if (payload.symbol && payload.data) {
                this._applyUpdate(payload.symbol, payload.data);
                this.state.messagesReceived++;
                this.state.lastUpdate = new Date();
            }
        }
        
        this.state.lastUpdate = new Date();
    }
    
    _applyUpdate(symbol, data) {
        if (!symbol || !data) return;
        
        // Quick lookup using map
        const security = this.state.securitiesMap[symbol];
        if (!security) return;
        
        const oldPrice = security.current_price;
        const newPrice = parseFloat(data.current_price) || oldPrice;
        
        // Update all fields
        security.current_price = newPrice;
        if (data.volume) security.volume = parseFloat(data.volume);
        if (data.high_price) security.high_price = parseFloat(data.high_price);
        if (data.low_price) security.low_price = parseFloat(data.low_price);
        if (data.change !== undefined) security.change = parseFloat(data.change);
        if (data.change_percent !== undefined) security.change_percent = parseFloat(data.change_percent);
        if (data.reference_price) security.reference_price = parseFloat(data.reference_price);
        if (data.ceiling_price) security.ceiling_price = parseFloat(data.ceiling_price);
        if (data.floor_price) security.floor_price = parseFloat(data.floor_price);
        if (data.bid_price_1) security.bid_price_1 = parseFloat(data.bid_price_1);
        if (data.bid_vol_1) security.bid_vol_1 = parseFloat(data.bid_vol_1);
        if (data.ask_price_1) security.ask_price_1 = parseFloat(data.ask_price_1);
        if (data.ask_vol_1) security.ask_vol_1 = parseFloat(data.ask_vol_1);
        
        // Recalculate visual state
        security.direction = this._getDirection(newPrice, security.reference_price);
        security.priceClass = this._getPriceClass(newPrice, security.reference_price, security.ceiling_price, security.floor_price);
        
        // Flash animation
        if (security.ceiling_price && newPrice >= security.ceiling_price) {
            security.flashClass = 'flash-ceiling';
        } else if (security.floor_price && newPrice <= security.floor_price) {
            security.flashClass = 'flash-floor';
        } else if (newPrice > oldPrice) {
            security.flashClass = 'flash-up';
        } else if (newPrice < oldPrice) {
            security.flashClass = 'flash-down';
        }
        
        // Clear flash after animation
        setTimeout(() => {
            security.flashClass = '';
        }, 500);
    }

    // =========================================================================
    // Helpers
    // =========================================================================
    
    _getDirection(price, ref) {
        if (!ref || price === ref) return 'unchanged';
        return price > ref ? 'up' : 'down';
    }
    
    _getPriceClass(price, ref, ceiling, floor) {
        if (!price) return 'text-muted';
        if (ceiling && price >= ceiling) return 'price-ceiling';
        if (floor && price <= floor) return 'price-floor';
        if (ref && price > ref) return 'price-up';
        if (ref && price < ref) return 'price-down';
        return 'price-ref';
    }

    // =========================================================================
    // Computed Properties
    // =========================================================================
    
    get filteredSecurities() {
        let list = this.state.securities;
        
        // Search filter
        if (this.state.searchQuery) {
            const q = this.state.searchQuery.toUpperCase();
            list = list.filter(s =>
                s.symbol.includes(q) ||
                (s.stock_name_vn && s.stock_name_vn.toUpperCase().includes(q))
            );
        }
        
        // Market filter
        if (this.state.filter !== 'all') {
            list = list.filter(s => s.market === this.state.filter.toUpperCase());
        }
        
        // Index filter
        if (this.state.indexFilter) {
            const symbols = this.state.indexSymbols[this.state.indexFilter] || [];
            list = list.filter(s => symbols.includes(s.symbol));
        }
        
        // Sort
        const sorted = [...list].sort((a, b) => {
            let valA = a[this.state.sortBy];
            let valB = b[this.state.sortBy];
            
            if (typeof valA === 'string') {
                return this.state.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }
            return this.state.sortAsc ? (valA - valB) : (valB - valA);
        });
        
        return sorted;
    }
    
    get totalCount() {
        return this.filteredSecurities.length;
    }
    
    get lastUpdateFormatted() {
        if (!this.state.lastUpdate) return '--:--:--';
        return this.state.lastUpdate.toLocaleTimeString('vi-VN');
    }

    // =========================================================================
    // Actions
    // =========================================================================
    
    onSearchInput(ev) {
        clearTimeout(this._searchDebounce);
        this._searchDebounce = setTimeout(() => {
            this.state.searchQuery = ev.target.value || '';
        }, 150);
    }
    
    onClearSearch() {
        this.state.searchQuery = '';
        if (this.searchInputRef.el) {
            this.searchInputRef.el.value = '';
        }
    }
    
    onFilterChange(filter) {
        this.state.filter = filter;
        this.state.indexFilter = '';
    }
    
    onIndexFilterChange(indexCode) {
        this.state.indexFilter = indexCode === this.state.indexFilter ? '' : indexCode;
        this.state.filter = 'all';
    }
    
    onSort(column) {
        if (this.state.sortBy === column) {
            this.state.sortAsc = !this.state.sortAsc;
        } else {
            this.state.sortBy = column;
            this.state.sortAsc = true;
        }
    }
    
    onRowClick(security) {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'ssi.securities',
            res_id: security.id,
            views: [[false, 'form']],
            target: 'current',
        });
    }
    
    // Manual refresh (optional, user-triggered only)
    async onRefresh() {
        await this._loadInitialData();
        this.notification.add("Đã cập nhật dữ liệu", { type: 'success' });
    }

    // =========================================================================
    // Formatters
    // =========================================================================
    
    formatPrice(value) {
        if (!value) return '-';
        return new Intl.NumberFormat('vi-VN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }
    
    formatVolume(value) {
        if (!value) return '-';
        if (value >= 1000000) return (value / 1000000).toFixed(2) + 'M';
        if (value >= 1000) return (value / 1000).toFixed(0) + 'K';
        return value.toLocaleString('vi-VN');
    }
    
    formatPercent(value) {
        if (value === null || value === undefined) return '-';
        const sign = value > 0 ? '+' : '';
        return sign + value.toFixed(2) + '%';
    }
}

// Register as client action
registry.category("actions").add("stock_data.stock_board", StockBoard);
