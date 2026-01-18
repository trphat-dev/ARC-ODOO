from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from ..utils.ssi_gateway import SSIGateway

_logger = logging.getLogger(__name__)

class WizardFetchMarketData(models.TransientModel):
    _name = 'wizard.fetch.market.data'
    _description = 'Fetch Market Data Wizard'

    action_type = fields.Selection([
        ('securities_all', 'Fetch All Securities Data'),
        ('fetch_all_ohlc', 'Fetch OHLC for All Securities'),
    ], string='Action Type', required=True, default='securities_all')

    market = fields.Selection([
        ('ALL', 'All Markets'),
        ('HOSE', 'HOSE'),
        ('HNX', 'HNX'),
        ('UPCOM', 'UPCOM')
    ], string='Market', default='ALL')
    
    # Simple wizard fields for manual runs
    last_count = fields.Integer(readonly=True)
    result_message = fields.Html(readonly=True)
    
    def action_fetch_data(self):
        self.ensure_one()
        config = self.env['ssi.api.config'].get_config()
        if not config:
            raise UserError(_("Please configure SSI API settings first."))
        
        gateway = SSIGateway(config.consumer_id, config.consumer_secret, config.api_url)
        
        if self.action_type == 'securities_all':
            self._fetch_securities(gateway)
        elif self.action_type == 'fetch_all_ohlc':
            self._fetch_ohlc(gateway)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Operation completed'),
                'type': 'success',
            }
        }

    def _fetch_securities(self, gateway):
        markets = ['HOSE', 'HNX', 'UPCOM'] if self.market == 'ALL' else [self.market]
        total = 0
        securities_model = self.env['ssi.securities']
        
        for m in markets:
            page = 1
            while True:
                data = gateway.get_securities(m, page_index=page, page_size=1000)
                items = data.get('items', [])
                if not items: break
                
                for item in items:
                    symbol = item.get('Symbol') or item.get('symbol')
                    if not symbol: continue
                    val = {
                        'symbol': symbol,
                        'market': m,
                        'stock_name_vn': item.get('StockName'),
                        'is_active': True 
                    }
                    existing = securities_model.search([('symbol','=',symbol), ('market','=',m)], limit=1)
                    if existing:
                        existing.write(val)
                    else:
                        securities_model.create(val)
                    total += 1
                page += 1
                self.env.cr.commit()
        self.last_count = total

    def _fetch_ohlc(self, gateway):
        # Fetch OHLC for active securities
        securities = self.env['ssi.securities'].search([('is_active','=',True)])
        today = fields.Date.today()
        count = 0
        for s in securities:
            try:
                data = gateway.get_daily_ohlc(s.symbol, today, today)
                if data:
                    item = data.get('data') if isinstance(data.get('data'), dict) else (data.get('data')[0] if data.get('data') else None)
                    if item:
                        self.env['ssi.daily.ohlc'].create_or_update_from_gateway(s, item)
                        count += 1
            except Exception as e:
                _logger.warning("Failed OHLC for %s: %s", s.symbol, e)
        self.last_count = count
