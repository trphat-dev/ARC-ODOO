# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta, timezone
import logging

_logger = logging.getLogger(__name__)

# Vietnam timezone (UTC+7)
VN_TIMEZONE = timezone(timedelta(hours=7))

def vn_now():
    """Get current datetime in Vietnam timezone"""
    return datetime.now(VN_TIMEZONE)

class IntradayOHLC(models.Model):
    _name = 'ssi.intraday.ohlc'
    _description = 'Intraday OHLC Data'
    _order = 'date desc, time desc'

    security_id = fields.Many2one('ssi.securities', string='Security', required=True, ondelete='cascade', index=True)
    symbol = fields.Char(related='security_id.symbol', string='Symbol', store=True)
    
    date = fields.Date('Date', required=True, index=True)
    time = fields.Char('Time', required=True) # HH:mm:ss
    
    open_price = fields.Float('Open', digits=(12, 3))
    high_price = fields.Float('High', digits=(12, 3))
    low_price = fields.Float('Low', digits=(12, 3))
    close_price = fields.Float('Close', digits=(12, 3))
    
    volume = fields.Float('Volume')
    total_value = fields.Float('Total Value', digits=(20, 3))
    resolution = fields.Integer('Resolution (min)')
    
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)
    
    _sql_constraints = [
        ('security_date_time_unique', 'unique(security_id, date, time)', 'Intraday OHLC must be unique per time!')
    ]

    @api.model
    def create_or_update_from_gateway(self, security, item):
        """
        Process gateway item and create/update record.
        item: dict from SSI API (Intraday)
        """
        # Parsing date/time
        # SSI Intraday often returns "09:15:00" in Time and "15/05/2023" in Date or similar.
        # Or sometimes "TradingDate"
        
        date_str = item.get('TradingDate') or item.get('Date')
        time_str = item.get('Time')
        
        if not date_str or not time_str:
            _logger.warning("IntradayOHLC: Missing Date/Time for %s. Item: %s", security.symbol, item)
            return

        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
             try:
                 date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
             except:
                 _logger.warning("IntradayOHLC: Could not parse date '%s' for %s", date_str, security.symbol)
                 return

        # Helper to get value from multiple possible keys
        def _get(dct, keys, default=0.0):
            for k in keys:
                if k in dct and dct[k] is not None:
                    try:
                        return float(dct[k])
                    except (ValueError, TypeError):
                        pass
            return default

        close_price = _get(item, ['Close', 'close', 'ClosePrice', 'closePrice'])
        vals = {
            'security_id': security.id,
            'date': date_obj,
            'time': time_str,
            'open_price': _get(item, ['Open', 'open', 'OpenPrice', 'openPrice']),
            'high_price': _get(item, ['High', 'high', 'HighPrice', 'highPrice']),
            'low_price': _get(item, ['Low', 'low', 'LowPrice', 'lowPrice']),
            'close_price': close_price,
            'volume': _get(item, ['Volume', 'volume']),
            'total_value': _get(item, ['Value', 'value', 'TotalValue', 'totalValue']),
            'resolution': int(item.get('Resolution') or item.get('resolution') or 1),
            'last_update': fields.Datetime.now()
        }

        # Improve search performance
        existing = self.search([
            ('security_id', '=', security.id),
            ('date', '=', date_obj),
            ('time', '=', time_str)
        ], limit=1)

        if existing:
            existing.write(vals)
        else:
            self.create(vals)
        
        # Update security's current_price with the latest close from intraday
        if close_price > 0 and date_obj == fields.Date.today():
            security.write({
                'current_price': close_price,
                'last_update': fields.Datetime.now()
            })
