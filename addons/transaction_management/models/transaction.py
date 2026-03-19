from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json
from datetime import datetime


class Transaction(models.Model):
    _name = "portfolio.transaction"
    _description = "Transaction"
    _inherit = ['portfolio.transaction', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Chỉ thêm các field mới hoặc override field từ parent
    # Added fields for NAV Management integration (ensure related fields exist)
    term_months = fields.Integer(string="Kỳ hạn (tháng)", default=12)
    interest_rate = fields.Float(string="Lãi suất (%)", digits=(16, 2))

    # Source field for transaction origin
    source = fields.Selection([
        ('portal', 'Portal'),
        ('sale', 'Sale Portal'),
        ('portfolio', 'Portfolio')
    ], string="Source", default='portfolio', tracking=True)

    # Chỉ thêm các method mới hoặc override method từ parent
    def _update_fund_units(self):
        """Override method to update fund units via explicit write() for ORM safety"""
        self.ensure_one()
        if self.transaction_type == 'buy':
            self.fund_id.write({'total_units': self.fund_id.total_units + self.units})
        elif self.transaction_type == 'sell':
            self.fund_id.write({'total_units': self.fund_id.total_units - self.units})
