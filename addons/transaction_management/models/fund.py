from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 16

class Fund(models.Model):
    _name = "portfolio.fund"
    _description = "Fund"
    _inherit = ['portfolio.fund', 'mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Chỉ thêm các field mới hoặc override field từ parent
    flex_sip_percentage = fields.Float(string="Flex/SIP %", default=0.0)
    # Không override field color từ parent - sử dụng field Char từ fund_management
    flex_units = fields.Float(string="Flex Units", compute='_compute_flex_units', store=True)
    sip_units = fields.Float(string="SIP Units", compute='_compute_sip_units', store=True)
    

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_all_dependent_fields()
        return records

    def write(self, vals):
        res = super(Fund, self).write(vals)
        if any(field in vals for field in ['current_nav']):
            self._recompute_all_dependent_fields()
        return res


    @api.depends('investment_ids.units', 'investment_ids.investment_type')
    def _compute_flex_units(self):
        for record in self:
            flex_investments = record.investment_ids.filtered(lambda i: i.investment_type == 'stock')
            record.flex_units = sum(flex_investments.mapped('units'))

    @api.depends('investment_ids.units', 'investment_ids.investment_type')
    def _compute_sip_units(self):
        for record in self:
            sip_investments = record.investment_ids.filtered(lambda i: i.investment_type == 'bond')
            record.sip_units = sum(sip_investments.mapped('units'))


    @api.constrains('current_nav')
    def _check_nav_values(self):
        for record in self:
            if record.current_nav < 0:
                raise ValidationError(_('Current NAV cannot be negative'))

    def action_update_nav(self):
        self.ensure_one()
        # Update last update time
        self.last_update = fields.Date.today()
        # Update NAV history
        self._update_nav_history()

    # Removed YTD history update (field deprecated)

    def _update_nav_history(self):
        self.ensure_one()
        history = []
        if self.nav_history_json:
            try:
                history = json.loads(self.nav_history_json)
            except json.JSONDecodeError:
                history = []
        
        history.append({
            'date': fields.Date.today().isoformat(),
            'value': self.current_nav
        })
        
        self.nav_history_json = json.dumps(history)

    def _recompute_all_dependent_fields(self):
        """Force recompute all computed fields"""
        self._compute_flex_units()
        self._compute_sip_units()