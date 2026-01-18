from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WizardSyncFundCertificate(models.TransientModel):
    _name = 'wizard.sync.fund.certificate'
    _description = 'Wizard to Sync Fund Certificates from Stock Data'

    market_selection = fields.Selection([
        ('all', 'Tất cả'),
        ('HOSE', 'HOSE'),
        ('HNX', 'HNX'),
        ('UPCOM', 'UPCOM')
    ], string='Chọn Sàn', default='all', required=True)

    sync_option = fields.Selection([
        ('create', 'Chỉ tạo mới'),
        ('update', 'Chỉ cập nhật'),
        ('both', 'Tạo mới & Cập nhật')
    ], string='Tùy chọn đồng bộ', default='both', required=True)

    def action_sync(self):
        """Thực hiện đồng bộ dữ liệu"""
        self.ensure_one()
        
        Securities = self.env['ssi.securities'].sudo()
        FundCert = self.env['fund.certificate'].sudo()

        # Call the batch sync method on fund.certificate model
        stats = FundCert.sync_batch(self.market_selection, self.sync_option)

        # Return Notification
        message = f"Đồng bộ hoàn tất!\n- Tạo mới: {stats['created']}\n- Cập nhật: {stats['updated']}\n- Bỏ qua: {stats['skipped']}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kết quả Đồng bộ',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
