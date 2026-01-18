# -*- coding: utf-8 -*-
"""
SSI Streaming Bus Publisher
Publishes streaming updates to Odoo bus.bus for real-time UI updates.
"""
import logging
import threading

_logger = logging.getLogger(__name__)


class StreamingBusPublisher:
    """
    Singleton publisher for streaming updates via Odoo bus.bus.
    Enables real-time price updates in web UI without page refresh.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, db_name):
        self.db_name = db_name
        self._enabled = True
        self._batch_buffer = {}
        self._buffer_lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, db_name=None):
        """Get singleton instance"""
        if not cls._instance and db_name:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls(db_name)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)"""
        with cls._lock:
            cls._instance = None
    
    def set_enabled(self, enabled):
        """Enable or disable bus publishing"""
        self._enabled = enabled
        _logger.info("Bus publishing %s", "enabled" if enabled else "disabled")
    
    def publish_price_update(self, symbol, price_data):
        """
        Publish single price update to bus channel.
        
        Args:
            symbol: Stock symbol (e.g., 'VNM')
            price_data: Dict with price information
        """
        if not self._enabled or not self.db_name:
            return
        
        try:
            from odoo import api, registry
            
            db_registry = registry(self.db_name)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, 1, {})  # SUPERUSER_ID = 1
                
                # Build notification
                channel = 'stock_data_live'
                message = {
                    'type': 'price_update',
                    'symbol': symbol,
                    'data': price_data,
                }
                
                env['bus.bus']._sendone(channel, 'stock_data/price_update', message)
                cr.commit()
                
                _logger.debug("Published price update for %s", symbol)
                
        except ImportError:
            _logger.warning("Odoo not available for bus publishing")
        except Exception as e:
            _logger.error("Bus publish error for %s: %s", symbol, e)
    
    def publish_batch_update(self, updates):
        """
        Publish batch of price updates.
        
        Args:
            updates: Dict of {symbol: price_data}
        """
        if not self._enabled or not self.db_name or not updates:
            return
        
        try:
            from odoo import api, registry
            
            db_registry = registry(self.db_name)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, 1, {})
                bus_bus = env['bus.bus']
                
                # Transform updates to list
                batch_payload = []
                for symbol, price_data in updates.items():
                    batch_payload.append({
                        'symbol': symbol, 
                        'data': price_data
                    })
                
                if batch_payload:
                    channel = 'stock_data_live'
                    message = {
                        'type': 'batch_update',
                        'updates': batch_payload,
                    }
                    bus_bus._sendone(channel, 'stock_data/price_update', message)
                
                cr.commit()
                
                # _logger.debug("Published batch update for %d symbols", len(updates))
                
        except ImportError:
            _logger.warning("Odoo not available for bus publishing")
        except Exception as e:
            _logger.error("Bus batch publish error: %s", e)
    
    def publish_streaming_status(self, status):
        """
        Publish streaming connection status update.
        
        Args:
            status: Dict with streaming status information
        """
        if not self._enabled or not self.db_name:
            return
        
        try:
            from odoo import api, registry
            
            db_registry = registry(self.db_name)
            with db_registry.cursor() as cr:
                env = api.Environment(cr, 1, {})
                
                channel = 'stock_data_live'
                message = {
                    'type': 'streaming_status',
                    'data': status,
                }
                
                env['bus.bus']._sendone(channel, 'stock_data/streaming_status', message)
                cr.commit()
                
        except Exception as e:
            _logger.error("Bus status publish error: %s", e)
    
    def buffer_update(self, symbol, price_data):
        """
        Buffer update for batch publishing.
        Call flush_buffer() to send all buffered updates.
        
        Args:
            symbol: Stock symbol
            price_data: Price data dict
        """
        with self._buffer_lock:
            self._batch_buffer[symbol] = price_data
    
    def flush_buffer(self):
        """Flush buffered updates to bus"""
        with self._buffer_lock:
            if self._batch_buffer:
                self.publish_batch_update(self._batch_buffer.copy())
                self._batch_buffer.clear()
