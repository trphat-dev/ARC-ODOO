from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)

class Securities(models.Model):
    _inherit = 'ssi.securities'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger update on related fund certificates"""
        records = super(Securities, self).create(vals_list)
        for rec in records:
             # Propagate create event
            rec._propagate_to_fund_certificate()
        return records

    def write(self, vals):
        """Override write to trigger update on related fund certificates"""
        res = super(Securities, self).write(vals)
        
        # Check if fields related to fund certificate are updated
        # We perform this check AFTER write to ensure data is committed (though in same transaction)
        # Using separate method to keep write clean
        if self._should_propagate_to_fund(vals):
            self._propagate_to_fund_certificate()
            
        return res

    def _should_propagate_to_fund(self, vals):
        """Check if updated fields are relevant for Fund Certificate"""
        relevant_fields = {
            'current_price', 'reference_price', 'ceiling_price', 'floor_price',
            'high_price', 'low_price', 'volume', 'total_value', 
            'change', 'change_percent', 'last_update', 'is_active',
            'stock_name_vn', 'stock_name_en'
        }
        return bool(set(vals.keys()) & relevant_fields)

    def _propagate_to_fund_certificate(self):
        """Find and update related fund certificates, or create if not exists"""
        FundCert = self.env['fund.certificate'].sudo()
        for rec in self:
            if not rec.symbol or not rec.market:
                continue
                
            # Find related fund certificate
            # We use sudo() because streaming user might not have access to fund models
            existing = FundCert.search([
                ('symbol', '=', rec.symbol),
                ('market', '=', rec.market)
            ], limit=1)
            
            if existing:
                try:
                    existing.update_from_security_data(rec)
                except Exception as e:
                    _logger.error(f"Failed to propagate security update for {rec.symbol} to fund: {str(e)}")
            else:
                # CREATION LOGIC: Auto-create fund certificate from Security
                try:
                    vals = {
                        'symbol': rec.symbol,
                        'market': rec.market,
                        'floor_code': rec.floor_code or '',
                        'security_type': rec.security_type or '',
                        'short_name_vn': rec.stock_name_vn or '',
                        'short_name_en': rec.stock_name_en or '',
                        'reference_price': rec.reference_price or 0.0,
                        'ceiling_price': rec.ceiling_price or 0.0,
                        'floor_price': rec.floor_price or 0.0,
                        'current_price': rec.current_price or 0.0,
                        'high_price': rec.high_price or 0.0,
                        'low_price': rec.low_price or 0.0,
                        'initial_certificate_quantity': int(rec.volume) if rec.volume else 0,
                        'initial_certificate_price': rec.current_price or rec.reference_price or 0.0,
                        'total_value': rec.total_value or 0.0,
                        'change': rec.change or 0.0,
                        'change_percent': rec.change_percent or 0.0,
                        'is_active': True,
                        'last_update': fields.Datetime.now(),
                        'product_status': 'active',
                        'fund_description': f"{rec.symbol} - {rec.security_type or 'Stock'} - {rec.market}",
                    }
                    FundCert.create(vals)
                    _logger.info(f"Auto-created Fund Certificate for {rec.symbol}")
                except Exception as e:
                     _logger.error(f"Failed to auto-create fund certificate for {rec.symbol}: {str(e)}")

    @api.model
    def _streaming_update_hook(self, bus_updates):
        """
        Intercept streaming updates (Raw SQL) and propagate to Fund Certificates.
        """
        if not bus_updates:
            return

        _logger.info(f"🪝 [HOOK] _streaming_update_hook triggered for {len(bus_updates)} symbols: {list(bus_updates.keys())}")

        try:
            # 1. Identify symbols involved
            symbols = list(bus_updates.keys())
            
            # 2. Find Securities records
            # Note: We must search to get records bound to the current environment/cursor.
            # The environment sees the Raw SQL updates caused by the main process because we are in the same transaction context (or subsequent one).
            securities = self.search([('symbol', 'in', symbols)])
            _logger.info(f"🪝 [HOOK] Found {len(securities)} securities in DB.")
            
            if not securities:
                _logger.warning("🪝 [HOOK] No securities found for symbols! Raw SQL update might use different symbols?")
                return

            # 3. Trigger Propagation
            # This reuses the logic that normally runs on write/create
            updated_count = 0
            for sec in securities:
                _logger.info(f"🪝 [HOOK] Propagating for {sec.symbol}...")
                # We can filter further if needed, but _propagate_to_fund_certificate checks internal logic
                sec._propagate_to_fund_certificate()
                updated_count += 1
            
            # 4. Commit updates to Fund Certificates
            # Since the hook is called AFTER the main stock_data commit, we need to commit our side-effects.
            if updated_count > 0:
                _logger.info(f"🪝 [HOOK] Committing {updated_count} propagations.")
                self.env.cr.commit()
                
        except Exception as e:
            _logger.error("Error in Fund Management streaming hook: %s", e)
            # Don't raise, to avoid crashing the streaming thread
        
        # Call super to ensure other modules can also hook in
        super(Securities, self)._streaming_update_hook(bus_updates)

