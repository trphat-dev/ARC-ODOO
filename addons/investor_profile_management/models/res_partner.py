from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    investor_profile_ids = fields.One2many('investor.profile', 'partner_id', string='Investor Profiles')
    bank_account_ids = fields.One2many('investor.bank.account', 'partner_id', string='Bank Accounts')
    address_ids = fields.One2many('investor.address', 'partner_id', string='Addresses')
    status_info_ids = fields.One2many('status.info', 'partner_id', string='Status Information')

    @api.model_create_multi
    def create(self, vals_list):
        """Consolidated create override to ensure status information is created for new partners."""
        partners = super().create(vals_list)
        for partner in partners:
            # Only create status info for natural persons (not companies, not child contacts)
            if not partner.parent_id and not partner.is_company:
                status_model = self.env['status.info']
                # Check if already exists to prevent duplicates (e.g. from multiple inheritance paths)
                if not status_model.search([('partner_id', '=', partner.id)], limit=1):
                    status_model.create({
                        'partner_id': partner.id,
                        'account_status': 'pending',
                        'profile_status': 'incomplete'
                    })
        return partners