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
        partners = super().create(vals_list)
        for partner in partners:
            # Auto-create status info for new partner
            investor_profile = self.env['investor.profile'].search([('partner_id', '=', partner.id)], limit=1)
            status_vals = {
                'partner_id': partner.id,
                'account_status': 'pending',
                'profile_status': 'incomplete'
            }
            if investor_profile:
                status_vals['investor_id'] = investor_profile.id
            self.env['status.info'].create(status_vals)
        return partners