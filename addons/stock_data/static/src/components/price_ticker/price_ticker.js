/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * PriceTicker - Realtime Price Widget
 * Pure WebSocket implementation via Odoo bus.bus
 * No polling, no refresh - 100% realtime
 */
export class PriceTickerWidget extends Component {
    static template = "stock_data.PriceTickerWidget";
    static props = {
        record: Object,
        name: String,
    };

    setup() {
        this.busService = useService("bus_service");
        
        const record = this.props.record.data;
        this.symbol = record.symbol;
        
        this.state = useState({
            price: record.current_price || 0,
            previousPrice: record.current_price || 0,
            referencePrice: record.reference_price || 0,
            ceilingPrice: record.ceiling_price || 0,
            floorPrice: record.floor_price || 0,
            change: record.change || 0,
            changePercent: record.change_percent || 0,
            volume: record.volume || 0,
            direction: this._getDirection(record.current_price, record.reference_price),
            priceClass: this._getPriceClass(record.current_price, record.reference_price, record.ceiling_price, record.floor_price),
            flashClass: '',
            updateTime: null,
            connected: false,
        });
        
        this._handler = null;
        
        onMounted(() => this._subscribeToBus());
        onWillUnmount(() => this._unsubscribeFromBus());
    }

    // =========================================================================
    // Bus Subscription - Pure WebSocket
    // =========================================================================
    
    _subscribeToBus() {
        if (!this.busService || !this.symbol) return;
        
        try {
            this._handler = this._onBusNotification.bind(this);
            
            // Odoo 18 bus API:
            // - addChannel(channel) -> adds channel to poll from server
            // - subscribe(notification_type, callback) -> subscribes to notification type
            
            // Step 1: Add channel
            if (typeof this.busService.addChannel === 'function') {
                this.busService.addChannel('stock_data_live');
            }
            
            // Step 2: Subscribe to notification TYPE (not channel)
            if (typeof this.busService.subscribe === 'function') {
                this.busService.subscribe('stock_data/price_update', this._handler);
            }
            
            // Step 3: Also listen via addEventListener for broader compatibility
            if (typeof this.busService.addEventListener === 'function') {
                this.busService.addEventListener('notification', this._handler);
            }
            
            this.state.connected = true;
        } catch (e) {
            console.error('[PriceTicker] Subscribe error:', e);
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
            // Ignore cleanup errors
        }
    }
    
    _onBusNotification(notifications) {
        // Handle both direct array and event.detail format
        const notifList = Array.isArray(notifications) 
            ? notifications 
            : (notifications?.detail || [notifications]);
        
        for (const notif of notifList) {
            if (!notif || notif.type !== 'stock_data/price_update') continue;
            
            const payload = notif.payload || {};
            
            // Batch update format
            if (payload.type === 'batch_update' && Array.isArray(payload.updates)) {
                const myUpdate = payload.updates.find(u => u.symbol === this.symbol);
                if (myUpdate?.data) {
                    this._applyPriceUpdate(myUpdate.data);
                }
                continue;
            }
            
            // Single update format
            if (payload.symbol === this.symbol && payload.data) {
                this._applyPriceUpdate(payload.data);
            }
        }
    }
    
    // =========================================================================
    // Price Update Logic
    // =========================================================================
    
    _applyPriceUpdate(data) {
        const newPrice = parseFloat(data.current_price) || 0;
        if (newPrice <= 0) return;
        
        const oldPrice = this.state.price;
        
        // Update all values
        this.state.previousPrice = oldPrice;
        this.state.price = newPrice;
        
        if (data.reference_price) this.state.referencePrice = parseFloat(data.reference_price);
        if (data.ceiling_price) this.state.ceilingPrice = parseFloat(data.ceiling_price);
        if (data.floor_price) this.state.floorPrice = parseFloat(data.floor_price);
        if (data.change !== undefined) this.state.change = parseFloat(data.change);
        if (data.change_percent !== undefined) this.state.changePercent = parseFloat(data.change_percent);
        if (data.volume) this.state.volume = parseFloat(data.volume);
        
        // Recalculate visual classes
        this.state.direction = this._getDirection(newPrice, this.state.referencePrice);
        this.state.priceClass = this._getPriceClass(newPrice, this.state.referencePrice, this.state.ceilingPrice, this.state.floorPrice);
        this.state.updateTime = new Date().toLocaleTimeString('vi-VN');
        
        // Flash animation
        this._triggerFlash(newPrice, oldPrice);
    }
    
    _triggerFlash(newPrice, oldPrice) {
        if (this.state.ceilingPrice && newPrice >= this.state.ceilingPrice) {
            this.state.flashClass = 'flash-ceiling';
        } else if (this.state.floorPrice && newPrice <= this.state.floorPrice) {
            this.state.flashClass = 'flash-floor';
        } else if (newPrice > oldPrice) {
            this.state.flashClass = 'flash-up';
        } else if (newPrice < oldPrice) {
            this.state.flashClass = 'flash-down';
        }
        
        // Clear flash after animation
        setTimeout(() => {
            this.state.flashClass = '';
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
        if (!price) return '';
        if (ceiling && price >= ceiling) return 'price-ceiling';
        if (floor && price <= floor) return 'price-floor';
        if (ref && price > ref) return 'price-up';
        if (ref && price < ref) return 'price-down';
        return 'price-ref';
    }
    
    // =========================================================================
    // Getters for Template
    // =========================================================================
    
    get formattedPrice() {
        return new Intl.NumberFormat('vi-VN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(this.state.price);
    }
    
    get formattedChange() {
        const sign = this.state.change > 0 ? '+' : '';
        return sign + this.state.change.toFixed(2);
    }
    
    get formattedChangePercent() {
        const sign = this.state.changePercent > 0 ? '+' : '';
        return sign + this.state.changePercent.toFixed(2) + '%';
    }
    
    get directionIcon() {
        if (this.state.direction === 'up') return '▲';
        if (this.state.direction === 'down') return '▼';
        return '';
    }
}

// Register as field widget
registry.category("fields").add("price_ticker", {
    component: PriceTickerWidget,
    displayName: "Price Ticker",
    supportedTypes: ["float"],
});
