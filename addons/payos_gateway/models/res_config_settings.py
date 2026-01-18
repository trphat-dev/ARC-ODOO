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
        """Mở trang cấu hình PayOS (singleton pattern)"""
        PayOSConfig = self.env['payos.config']
        config = PayOSConfig.get_or_create_config()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cấu hình PayOS',
            'res_model': 'payos.config',
            'res_id': config.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }
