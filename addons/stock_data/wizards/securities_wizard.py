# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from ..utils.ssi_gateway import SSIGateway, SSIConnectionError, SSIDataError

_logger = logging.getLogger(__name__)

def fetch_securities_all(wizard, client, sdk_config):
    """
    Fetch all securities data using Gateway.
    Note: client/sdk_config args are legacy from old wizard call, ignored in favor of Gateway.
    """
    fetch_securities(wizard)
    # fetch_securities_details_all(wizard) # Optional, can be slow for all.

def fetch_securities(wizard):
    """Fetch securities list from SSI via Gateway"""
    config = wizard.env['ssi.api.config'].get_config()
    if not config:
        raise UserError(_("No active SSI Configuration found."))
    
    gateway = SSIGateway(config.consumer_id, config.consumer_secret, config.api_url)
    securities_model = wizard.env['ssi.securities']
    
    total_created = 0
    total_updated = 0
    
    markets = ['HOSE', 'HNX', 'UPCOM'] if wizard.market == 'ALL' else [wizard.market]
    
    for market in markets:
        try:
            _logger.debug("Fetching securities for %s...", market)
            # Gateway handles pagination internally? No, returns raw response.
            # We need to loop pages here or Gateway should helper. 
            # Gateway `get_securities` is raw.
            # Let's simple loop similar to before but cleaner.
            
            page = 1
            while True:
                data = gateway.get_securities(market, page_index=page, page_size=1000)
                items = data.get('items', [])
                if not items:
                    break
                
                for item in items:
                    symbol = item.get('Symbol') or item.get('symbol')
                    if not symbol: continue
                    
                    val = {
                        'symbol': symbol,
                        'market': market,
                        'stock_name_vn': item.get('StockName') or item.get('stockName'),
                        'stock_name_en': item.get('StockEnName') or item.get('stockEnName'),
                        'floor_code': item.get('floorCode'),
                        'security_type': item.get('securityType'),
                        'is_active': True
                    }
                    
                    existing = securities_model.search([('symbol', '=', symbol), ('market', '=', market)], limit=1)
                    if existing:
                        existing.write(val)
                        total_updated += 1
                    else:
                        securities_model.create(val)
                        total_created += 1
                
                page += 1
                wizard.env.cr.commit()
                
        except Exception as e:
            _logger.error("Error fetching market %s: %s", market, e)
            
    wizard.result_message = f"<p>Finished. Created: {total_created}, Updated: {total_updated}</p>"
    wizard.last_count = total_created + total_updated
