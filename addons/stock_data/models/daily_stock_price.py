from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)


class DailyStockPrice(models.Model):
    """Snapshot of SSI daily stock price payload."""

    _name = 'ssi.daily.stock.price'
    _description = 'Daily Stock Price'
    _order = 'trading_date desc, symbol asc'

    def _default_currency_id(self):
        company_currency = getattr(self.env.company, 'currency_id', False)
        if company_currency:
            return company_currency.id
        try:
            return self.env.ref('base.VND').id
        except Exception:
            return False

    security_id = fields.Many2one(
        'ssi.securities',
        string='Security',
        ondelete='set null',
        index=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=_default_currency_id,
        readonly=True,
    )
    symbol = fields.Char(string='Symbol', required=True, index=True)
    market = fields.Selection(
        [
            ('HOSE', 'HOSE'),
            ('HNX', 'HNX'),
            ('UPCOM', 'UPCOM'),
            ('DER', 'DER'),
            ('BOND', 'BOND'),
        ],
        string='Market',
        required=True,
        index=True,
    )
    trading_date = fields.Date(string='Trading Date', required=True, index=True)
    trading_time = fields.Char(string='Time')
    trading_session = fields.Char(string='Trading Session')

    reference_price = fields.Float('Reference Price', digits=(12, 3))
    ceiling_price = fields.Float('Ceiling Price', digits=(12, 3))
    floor_price = fields.Float('Floor Price', digits=(12, 3))
    open_price = fields.Float('Open Price', digits=(12, 3))
    highest_price = fields.Float('Highest Price', digits=(12, 3))
    lowest_price = fields.Float('Lowest Price', digits=(12, 3))
    close_price = fields.Float('Close Price', digits=(12, 3))
    close_price_adjusted = fields.Float('Close Price Adjusted', digits=(12, 3))
    average_price = fields.Float('Average Price', digits=(12, 3))
    last_price = fields.Float('Last Price', digits=(12, 3))
    last_volume = fields.Float('Last Volume')

    price_change = fields.Float('Price Change', digits=(12, 3))
    price_change_percent = fields.Float('Price Change (%)', digits=(12, 3))

    total_match_volume = fields.Float('Total Match Volume')
    total_match_value = fields.Float('Total Match Value', digits=(20, 3))
    total_deal_volume = fields.Float('Total Deal Volume')
    total_deal_value = fields.Float('Total Deal Value', digits=(20, 3))
    total_traded_volume = fields.Float('Total Traded Volume')
    total_traded_value = fields.Float('Total Traded Value', digits=(20, 3))

    total_buy_trade = fields.Float('Total Buy Trade')
    total_buy_trade_volume = fields.Float('Total Buy Trade Volume')
    total_sell_trade = fields.Float('Total Sell Trade')
    total_sell_trade_volume = fields.Float('Total Sell Trade Volume')

    foreign_buy_volume_total = fields.Float('Foreign Buy Volume')
    foreign_sell_volume_total = fields.Float('Foreign Sell Volume')
    foreign_buy_value_total = fields.Float('Foreign Buy Value', digits=(20, 3))
    foreign_sell_value_total = fields.Float('Foreign Sell Value', digits=(20, 3))
    foreign_current_room = fields.Float('Foreign Current Room', digits=(20, 3))
    net_foreign_volume = fields.Float('Net Foreign Volume')
    net_foreign_value = fields.Float('Net Foreign Value', digits=(20, 3))

    raw_payload = fields.Text('Raw Payload')
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now, index=True)

    _sql_constraints = [
        (
            'symbol_market_date_unique',
            'unique(symbol, market, trading_date)',
            'Symbol, market and trading date combination must be unique.',
        )
    ]

    def _link_security(self):
        """Ensure security_id/currency are set if matching record exists."""
        for rec in self:
            security = rec.security_id
            if not security and rec.symbol and rec.market:
                security = self.env['ssi.securities'].search(
                    [('symbol', '=', rec.symbol), ('market', '=', rec.market)], limit=1
                )
                if security:
                    rec.security_id = security.id
            if security and security.currency_id:
                rec.currency_id = security.currency_id.id

    def _propagate_to_security(self):
        """Push latest board metrics to the parent security."""
        self._link_security()
        for rec in self.filtered(lambda r: r.security_id):
            security = rec.security_id
            vals = {
                'reference_price': rec.reference_price or security.reference_price,
                'ceiling_price': rec.ceiling_price or security.ceiling_price,
                'floor_price': rec.floor_price or security.floor_price,
                'open_price': rec.open_price or security.open_price,
                'current_price': rec.close_price or rec.last_price or security.current_price,
                'high_price': rec.highest_price or security.high_price,
                'low_price': rec.lowest_price or security.low_price,
                'last_price': rec.last_price or rec.close_price or security.last_price,
                'volume': rec.total_traded_volume or rec.total_match_volume or security.volume,
                'average_price': rec.average_price or security.average_price,
                'close_price_adjusted': rec.close_price_adjusted or security.close_price_adjusted,
                'total_match_volume': rec.total_match_volume or security.total_match_volume,
                'total_match_value': rec.total_match_value or security.total_match_value,
                'total_deal_volume': rec.total_deal_volume or security.total_deal_volume,
                'total_deal_value': rec.total_deal_value or security.total_deal_value,
                'total_traded_volume_api': rec.total_traded_volume
                or security.total_traded_volume_api,
                'total_traded_value_api': rec.total_traded_value
                or security.total_traded_value_api,
                'total_buy_trade': rec.total_buy_trade or security.total_buy_trade,
                'total_buy_trade_volume': rec.total_buy_trade_volume
                or security.total_buy_trade_volume,
                'total_sell_trade': rec.total_sell_trade or security.total_sell_trade,
                'total_sell_trade_volume': rec.total_sell_trade_volume
                or security.total_sell_trade_volume,
                'foreign_buy_volume_total': rec.foreign_buy_volume_total
                or security.foreign_buy_volume_total,
                'foreign_sell_volume_total': rec.foreign_sell_volume_total
                or security.foreign_sell_volume_total,
                'foreign_buy_value_total': rec.foreign_buy_value_total
                or security.foreign_buy_value_total,
                'foreign_sell_value_total': rec.foreign_sell_value_total
                or security.foreign_sell_value_total,
                'foreign_current_room': rec.foreign_current_room or security.foreign_current_room,
                'net_foreign_volume': rec.net_foreign_volume or security.net_foreign_volume,
                'net_foreign_value': rec.net_foreign_value or security.net_foreign_value,
                'last_volume': rec.last_volume or security.last_volume,
                'trading_session': rec.trading_session or security.trading_session,
                'last_trading_date': rec.trading_date or security.last_trading_date,
                'last_update': fields.Datetime.now(),
            }
            try:
                security.sudo().write(vals)
            except Exception as exc:
                _logger.warning('Failed to propagate stock price to %s: %s', security.symbol, exc)

    @api.model
    def create(self, vals):
        if vals.get('raw_payload') and isinstance(vals['raw_payload'], dict):
            vals['raw_payload'] = json.dumps(vals['raw_payload'], ensure_ascii=False)
        rec = super().create(vals)
        rec._propagate_to_security()
        return rec

    def write(self, vals):
        if vals.get('raw_payload') and isinstance(vals['raw_payload'], dict):
            vals['raw_payload'] = json.dumps(vals['raw_payload'], ensure_ascii=False)
        res = super().write(vals)
        self._propagate_to_security()
        return res

