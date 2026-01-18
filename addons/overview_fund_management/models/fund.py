from odoo import models


class Fund(models.Model):
    _inherit = "portfolio.fund"
    # Sử dụng đầy đủ định nghĩa và liên kết (certificate_id, sync, ...) từ module fund_management
    # Không định nghĩa lại fields để tránh ghi đè và đảm bảo liên kết với fund.certificate hoạt động
    pass