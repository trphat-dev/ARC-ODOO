from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

from ..services import PayOSService


class ResConfigSettings(models.TransientModel):
    """
    PayOS Settings - Chỉ hiển thị link đến payos.config
    Không lưu trực tiếp các fields PayOS vào TransientModel để tránh lỗi timestamp
    """
    _inherit = 'res.config.settings'

    def action_open_payos_config(self):
        """Open PayOS configuration list view"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'PayOS Configuration',
            'res_model': 'payos.config',
            'view_mode': 'list,form',
            'target': 'current',
        }
