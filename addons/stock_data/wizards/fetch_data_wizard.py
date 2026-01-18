# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import datetime, timedelta
from ..utils.ssi_gateway import SSIGateway

_logger = logging.getLogger(__name__)

class SSMDataFetchWizard(models.TransientModel):
    _name = 'ssi.data.fetch.wizard'
    _description = 'Wizard to fetch SSI Market Data'

    fetch_type = fields.Selection([
        ('securities', 'Securities List'),
        ('details', 'Securities Details (Active)'),
        ('price', 'Latest Prices (Active)'),
        ('daily_ohlc', 'Daily OHLC (Active)'),
        ('intraday_ohlc', 'Intraday OHLC (Active)'),
    ], string="Fetch Target", required=True, default='price')

    from_date = fields.Date('From Date', default=lambda self: fields.Date.today() - timedelta(days=30))
    to_date = fields.Date('To Date', default=fields.Date.today())
    
    market = fields.Selection([
        ('HOSE', 'HOSE'),
        ('HNX', 'HNX'),
        ('UPCOM', 'UPCOM'),
        ('ALL', 'All Markets')
    ], string='Market', default='ALL')

    def action_fetch(self):
        """Execute the fetch operation"""
        self.ensure_one()
        model = self.env['ssi.securities']
        
        # Dispatch based on type
        if self.fetch_type == 'securities':
            return self._fetch_securities()
        elif self.fetch_type == 'details':
            return model.action_global_fetch_securities_details()
        elif self.fetch_type == 'price':
            return model.action_global_fetch_latest_price()
        elif self.fetch_type == 'daily_ohlc':
            return self._fetch_daily_ohlc()
        elif self.fetch_type == 'intraday_ohlc':
            return self._fetch_intraday_ohlc()

    def _get_gateway(self):
        config = self.env['ssi.api.config'].get_config()
        if not config:
            raise UserError(_("No active SSI API Configuration found."))
        return SSIGateway(config.consumer_id, config.consumer_secret, config.api_url)

    def _fetch_securities(self):
        """Wrapper for global securities fetch"""
        # Could customize to respect 'market' field if needed, but global fetch handles all usually
        return self.env['ssi.securities'].action_global_fetch_securities_list()

    def _fetch_daily_ohlc(self):
        """Fetch Daily OHLC with custom date range"""
        active_secs = self.env['ssi.securities'].search([('is_active','=',True)])
        gateway = self._get_gateway()
        count = 0
        
        for rec in active_secs:
            try:
                # Use Wizard Dates
                data = gateway.get_daily_ohlc(rec.symbol, self.from_date, self.to_date)
                if data:
                    items = data if isinstance(data, list) else data.get('data', [])
                    for item in items:
                        if not item: continue
                        self.env['ssi.daily.ohlc'].create_or_update_from_gateway(rec, item)
                    count += 1
                    if count % 10 == 0: self.env.cr.commit()
            except Exception as e:
                _logger.warning("Daily OHLC sync failed for %s: %s", rec.symbol, e)
                
        return self._notify_success("Fetched Daily OHLC for %s securities (%s -> %s)" % (count, self.from_date, self.to_date))

    def _fetch_intraday_ohlc(self):
        """Fetch Intraday OHLC with custom date range"""
        active_secs = self.env['ssi.securities'].search([('is_active','=',True)])
        gateway = self._get_gateway()
        count = 0
        
        for rec in active_secs:
            try:
                # Use Wizard Dates
                data = gateway.get_intraday_ohlc(rec.symbol, self.from_date, self.to_date, page_size=2000)
                if data:
                    items = data if isinstance(data, list) else data.get('data', [])
                    for item in items:
                        if not item: continue
                        self.env['ssi.intraday.ohlc'].create_or_update_from_gateway(rec, item)
                    count += 1
                    if count % 5 == 0: self.env.cr.commit()
            except Exception as e:
                _logger.warning("Intraday OHLC sync failed for %s: %s", rec.symbol, e)

        return self._notify_success("Fetched Intraday OHLC for %s securities" % count)

    def _notify_success(self, msg):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Success', 'message': msg, 'type': 'success', 'sticky': False}
        }
