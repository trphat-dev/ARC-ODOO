import logging
import json
from odoo import _, fields
from odoo.exceptions import UserError
from ssi_fc_data import model
from datetime import datetime, timedelta


_logger = logging.getLogger(__name__)


def fetch_backtest(wizard, client, sdk_config):
    """Fetch backtest data and save to database"""
    if not wizard.symbol:
        raise UserError(_("Please enter symbol for backtest"))
    
    if not wizard.from_date or not wizard.to_date:
        raise UserError(_("Please select both From Date and To Date"))
    
    if wizard.from_date > wizard.to_date:
        raise UserError(_("From Date must be less than or equal to To Date"))

    backtest_model = wizard.env['ssi.backtest']
    securities_model = wizard.env['ssi.securities']
    
    # Find or create security record
    security = securities_model.search([('symbol', '=', wizard.symbol)], limit=1)
    
    total_created = 0
    total_updated = 0
    
    # Fetch data for each date in range
    from_date = wizard.from_date
    to_date = wizard.to_date
    current_date = from_date
    
    while current_date <= to_date:
        try:
            req = model.backtest(
                symbol=wizard.symbol,
                selectedDate=current_date.strftime('%d/%m/%Y')
            )
            
            response = client.backtest(sdk_config, req)
            _logger.debug("Backtest response for %s on %s: %s", wizard.symbol, current_date, response.get('status'))
            
            if response.get('status') == 'Success' and response.get('data'):
                # Check if record already exists
                existing = backtest_model.search([
                    ('symbol', '=', wizard.symbol),
                    ('selected_date', '=', current_date)
                ], limit=1)
                
                values = {
                    'symbol': wizard.symbol,
                    'selected_date': current_date,
                    'raw_response': json.dumps(response, indent=2, ensure_ascii=False),
                    'fetch_date': fields.Datetime.now(),
                }
                
                if security:
                    values['security_id'] = security.id
                
                if existing:
                    existing.write(values)
                    total_updated += 1
                else:
                    backtest_model.create(values)
                    total_created += 1
            else:
                _logger.warning("Failed to fetch backtest for %s on %s: %s", 
                              wizard.symbol, current_date, response.get('message', 'Unknown error'))
        
        except Exception as e:
            _logger.error("Error fetching backtest for %s on %s: %s", 
                        wizard.symbol, current_date, str(e))
        
        # Move to next date
        current_date += timedelta(days=1)
        
        # Limit to avoid too many API calls
        if (current_date - from_date).days > 30:
            _logger.warning("Limiting backtest fetch to 30 days")
            break
    
    wizard.result_message = f"<p>Fetched backtest data for {wizard.symbol}</p><p>Created: {total_created}, Updated: {total_updated}</p>"
    wizard.last_count = total_created + total_updated
    
    if total_created == 0 and total_updated == 0:
        raise UserError(_("No backtest data found for symbol %s in the specified date range") % wizard.symbol)


