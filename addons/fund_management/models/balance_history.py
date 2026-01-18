from odoo import api, fields, models

from ..utils import constants


class BalanceHistory(models.Model):
    _name = "portfolio.balance_history"
    _description = "Balance History"

    user_id = fields.Many2one("res.users", string="User", required=True)
    balance = fields.Float(string="Balance", required=True)
    change = fields.Float(string="Change", required=True)
    change_type = fields.Selection([
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Investment', 'Investment'),
        ('Divestment', 'Divestment')
    ], string="Change Type", required=True)
    created_at = fields.Datetime(string="Created At", required=True, default=fields.Datetime.now)
