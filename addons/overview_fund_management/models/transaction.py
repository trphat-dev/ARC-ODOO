from odoo import models


class Transaction(models.Model):
    _inherit = "portfolio.transaction"
    # Chỉ kế thừa, không định nghĩa lại để tránh mất các field (matched_units, remaining_units, ...) cần bởi transaction_list
    pass
