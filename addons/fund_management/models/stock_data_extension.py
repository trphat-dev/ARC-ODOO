from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)

class Securities(models.Model):
    _inherit = 'ssi.securities'

    @api.model
    def _streaming_update_hook(self, bus_updates):
        """
        Intercept streaming updates to update Portfolio Funds directly.
        This runs alongside the fund_management_control hook (which handles fund.certificate).
        """
        if not bus_updates:
            return

        try:
            # 1. Identify symbols involved
            symbols = list(bus_updates.keys())
            
            # 2. Iterate and Update/Create
            updated_count = 0
            
            for symbol, data in bus_updates.items():
                if not data:
                    continue
                    
                # Find existing fund
                fund = self.env['portfolio.fund'].sudo().search([
                    ('ticker', '=', symbol),
                    '|', ('status', '=', 'active'), ('status', '=', False)
                ], limit=1)
                
                vals = {}
                # Update NAV
                current_price = data.get('current_price') or data.get('price')
                
                # --- UPDATE EXISTING ---
                if fund:
                    if current_price:
                        vals['current_nav'] = current_price
                    if 'change' in data:
                        vals['change'] = data['change']
                    if 'change_percent' in data:
                        vals['change_percent'] = data['change_percent']
                    
                    # Volume
                    if 'volume' in data:
                         vals['volume'] = data['volume']
                    
                    # OHLC
                    if 'high_price' in data: vals['high_price'] = data['high_price']
                    if 'low_price' in data: vals['low_price'] = data['low_price']
                    if 'today_open_price' in data: vals['open_price'] = data['today_open_price']
                    
                    if 'reference_price' in data: vals['reference_price'] = data['reference_price']
                    if 'ceiling_price' in data: vals['ceiling_price'] = data['ceiling_price']
                    if 'floor_price' in data: vals['floor_price'] = data['floor_price']
                    
                    if vals:
                        vals['last_update'] = fields.Datetime.now()
                        fund.write(vals)
                        updated_count += 1
                        
                # --- CREATE NEW ---
                else:
                    try:
                        create_vals = {
                            'ticker': symbol,
                            'name': symbol, # Default name
                            'current_nav': current_price or 0.0,
                            'inception_date': fields.Date.today(),
                            'investment_type': 'Growth', # Default
                            'status': 'active',
                            'last_update': fields.Datetime.now(),
                        }
                        # Add optional fields if available
                        if 'change' in data: create_vals['change'] = data['change']
                        if 'change_percent' in data: create_vals['change_percent'] = data['change_percent']
                        if 'volume' in data: create_vals['volume'] = data['volume']
                        if 'high_price' in data: create_vals['high_price'] = data['high_price']
                        if 'low_price' in data: create_vals['low_price'] = data['low_price']
                        if 'today_open_price' in data: create_vals['open_price'] = data['today_open_price']
                        
                        if 'reference_price' in data: create_vals['reference_price'] = data['reference_price']
                        if 'ceiling_price' in data: create_vals['ceiling_price'] = data['ceiling_price']
                        if 'floor_price' in data: create_vals['floor_price'] = data['floor_price']
                         
                        # Try to link Cert if exists
                        cert = self.env['fund.certificate'].sudo().search([('symbol', '=', symbol)], limit=1)
                        if cert:
                            create_vals['certificate_id'] = cert.id
                            if cert.short_name_vn:
                                create_vals['name'] = cert.short_name_vn
                            
                        self.env['portfolio.fund'].sudo().create(create_vals)
                        _logger.info(f"Auto-created Portfolio Fund for {symbol}")
                        updated_count += 1
                    except Exception as e:
                        _logger.error(f"Failed to auto-create Portfolio Fund for {symbol}: {e}")

            # 3. Commit
            if updated_count > 0:
                self.env.cr.commit()
                
        except Exception as e:
            _logger.error("Error in Portfolio Fund streaming hook: %s", e)
        
        # Always call super
        super(Securities, self)._streaming_update_hook(bus_updates)
