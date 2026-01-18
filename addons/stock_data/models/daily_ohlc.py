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

class DailyOHLC(models.Model):
    _name = 'ssi.daily.ohlc'
    _description = 'Daily OHLC Data'
    _order = 'date desc, symbol asc'
    _rec_name = 'date'

    security_id = fields.Many2one('ssi.securities', string='Security', required=True, ondelete='cascade', index=True)
    symbol = fields.Char(related='security_id.symbol', string='Symbol', store=True, readonly=True)
    date = fields.Date('Date', required=True, index=True)
    
    open_price = fields.Float('Open', digits=(12, 3))
    high_price = fields.Float('High', digits=(12, 3))
    low_price = fields.Float('Low', digits=(12, 3))
    close_price = fields.Float('Close', digits=(12, 3))
    
    volume = fields.Float('Volume')
    value = fields.Float('Value', digits=(20, 3))
    
    change = fields.Float('Change', digits=(12, 3))
    change_percent = fields.Float('Change %', digits=(12, 3))
    
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)

    _sql_constraints = [
        ('security_date_unique', 'unique(security_id, date)', 'Daily OHLC must be unique per security and date!')
    ]

    @api.model
    def create_or_update_from_gateway(self, security, item):
        """
        Process gateway item and create/update record.
        item: dict from SSI API
        """
        # SSI API returns 'TradingDate' key for daily OHLC
        date_str = item.get('TradingDate') or item.get('Date') or item.get('tradingDate') or item.get('date') or ''
        if not date_str:
            _logger.warning("DailyOHLC: No date found for %s. Item keys: %s", security.symbol, list(item.keys()))
            return

        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
             try:
                 date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
             except:
                 _logger.warning("DailyOHLC: Could not parse date '%s' for %s", date_str, security.symbol)
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

        vals = {
            'security_id': security.id,
            'date': date_obj,
            'open_price': _get(item, ['Open', 'open', 'OpenPrice', 'openPrice']),
            'high_price': _get(item, ['High', 'high', 'HighPrice', 'highPrice', 'Highest', 'highest']),
            'low_price': _get(item, ['Low', 'low', 'LowPrice', 'lowPrice', 'Lowest', 'lowest']),
            'close_price': _get(item, ['Close', 'close', 'ClosePrice', 'closePrice']),
            'volume': _get(item, ['Volume', 'volume', 'TotalVolume', 'totalVolume']),
            'value': _get(item, ['Value', 'value', 'TotalValue', 'totalValue']),
            'change': _get(item, ['Change', 'change']),
            'change_percent': _get(item, ['ChangePercent', 'changePercent', 'Change%', 'change%']),
            'last_update': fields.Datetime.now()
        }

        existing = self.search([
            ('security_id', '=', security.id),
            ('date', '=', date_obj)
        ], limit=1)

        if existing:
            existing.write(vals)
        else:
            self.create(vals)
        
        # Trigger Intraday Fetch if "Today"?
        # Logic: If date is today, we might want intraday.
        # But let's keep it simple for now or delegate to a separate call.
