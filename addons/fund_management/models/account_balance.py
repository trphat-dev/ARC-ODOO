from odoo import api, fields, models


class AccountBalance(models.Model):
    _name = "portfolio.account_balance"
    _description = "Account Balance"

    user_id = fields.Many2one("res.users", string="User", required=True)
    balance = fields.Float(string="Balance", required=True)

    # _sql_constraints = [
    #     ('account_balance_user_uniq', 'unique(user_id)', 'Each user can only have one balance record.')
    # ]
