from odoo import api, fields, models


class Comparison(models.Model):
    _name = "portfolio.comparison"
    _description = "Fund Comparison"

    user_id = fields.Many2one("res.users", string="User", required=True)
    fund_ids = fields.Text(string="Fund IDs (JSON)")

    # _sql_constraints = [
    #     ('comparison_user_uniq', 'unique(user_id)', 'Each user can only have one comparison record.')
    # ]
