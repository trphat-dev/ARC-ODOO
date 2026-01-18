/** @odoo-module **/

import { registry } from '@web/core/registry';

/**
 * Stock Price Update Service
 * Subscribes to bus.bus channels for real-time price updates
 */
const stockPriceService = {
    dependencies: ['bus_service', 'notification'],
    
    start(env, { bus_service, notification }) {
        // Subscribe to stock price channels
        const subscribedSymbols = new Set();
        
        // Global channel for all price updates
        try {
            bus_service.addChannel('stock_data.price_update');
        } catch (e) {
            // ignore if already subscribed
        }
        
        // Listen for price update notifications
        bus_service.addEventListener('notification', ({ detail: notifications }) => {
            for (const notif of notifications) {
                try {
                    const { payload, type } = notif;
                    
                    // Handle price updates
                    if (type === 'stock_data/price_update' && payload) {
                        const symbol = payload.symbol;
                        const data = payload.data || {};
                        
                        // Dispatch custom event for components
                        window.dispatchEvent(new CustomEvent('stock_price_update', {
                            detail: { symbol, data }
                        }));
                        
                        // Log for debugging
                        console.debug(`[StockPrice] ${symbol}: ${data.current_price}`);
                    }
                    
                    // Handle streaming status updates
                    if (type === 'stock_data/streaming_status' && payload) {
                        window.dispatchEvent(new CustomEvent('streaming_status_update', {
                            detail: payload.data
                        }));
                    }
                    
                } catch (e) {
                    console.warn('[StockPriceService] Error processing notification:', e);
                }
            }
        });
        
        // API for subscribing to specific symbols
        return {
            subscribeSymbol(symbol) {
                if (symbol && !subscribedSymbols.has(symbol)) {
                    try {
                        bus_service.addChannel(`stock_price_${symbol}`);
                        subscribedSymbols.add(symbol);
                        console.log(`[StockPriceService] Subscribed to ${symbol}`);
                    } catch (e) {
                        // ignore
                    }
                }
            },
            
            unsubscribeSymbol(symbol) {
                subscribedSymbols.delete(symbol);
            },
            
            getSubscribedSymbols() {
                return Array.from(subscribedSymbols);
            }
        };
    },
};

registry.category('services').add('stock_price_service', stockPriceService);
