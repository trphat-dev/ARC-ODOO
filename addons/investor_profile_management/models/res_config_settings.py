import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Display fields — sourced from ekyc.api.config
    ekyc_base_url = fields.Char(
        string='VNPT eKYC Base URL',
        help='Base URL cho VNPT eKYC API. Mặc định: https://api.idg.vnpt.vn',
    )
    ekyc_token_id = fields.Char(string='Token ID')
    ekyc_token_key = fields.Char(string='Token Key', password=True)
    ekyc_access_token = fields.Char(string='Access Token')
    ekyc_token_expiration = fields.Datetime(string='Access Token hết hạn')
    ekyc_public_key_ca = fields.Text(
        string='Public Key CA',
        help='Public Key CA để xác thực chứng chỉ SSL của VNPT eKYC',
    )

    def _get_ekyc_config(self):
        """Get the active ekyc.api.config record"""
        return self.env['ekyc.api.config'].sudo().get_config()

    def get_values(self):
        res = super().get_values()
        config = self._get_ekyc_config()
        res.update({
            'ekyc_base_url': config.base_url or '',
            'ekyc_token_id': config.token_id or '',
            'ekyc_token_key': config.token_key or '',
            'ekyc_access_token': config.access_token or '',
            'ekyc_token_expiration': config.token_expiration,
            'ekyc_public_key_ca': config.public_key_ca or '',
        })
        return res

    def set_values(self):
        super().set_values()
        config = self._get_ekyc_config()
        vals = {}
        if self.ekyc_base_url:
            vals['base_url'] = self.ekyc_base_url
        if self.ekyc_token_id:
            vals['token_id'] = self.ekyc_token_id
        if self.ekyc_token_key:
            vals['token_key'] = self.ekyc_token_key
        if self.ekyc_public_key_ca:
            vals['public_key_ca'] = self.ekyc_public_key_ca
        if self.ekyc_access_token:
            vals['access_token'] = self.ekyc_access_token
        if self.ekyc_token_expiration:
            vals['token_expiration'] = self.ekyc_token_expiration
        if vals:
            config.write(vals)

    def action_generate_ekyc_token(self):
        """Generate new access token — delegates to ekyc.api.config"""
        config = self._get_ekyc_config()

        # Sync any unsaved form values to config first
        vals = {}
        if self.ekyc_token_id:
            vals['token_id'] = self.ekyc_token_id
        if self.ekyc_token_key:
            vals['token_key'] = self.ekyc_token_key
        if vals:
            config.write(vals)

        result = config.action_generate_token()

        # Update display fields
        self.ekyc_access_token = config.access_token
        self.ekyc_token_expiration = config.token_expiration

        return result

    def action_create_sample_api_records(self):
        """Create sample API records for testing"""
        self.ensure_one()

        api_record_model = self.env['api.record']

        samples = [
            {
                'endpoint': 'https://api.idg.vnpt.vn/file-service/v1/addFile',
                'method': 'POST',
                'api_type': 'ekyc',
                'request_headers': {'Token-id': '...', 'Authorization': 'Bearer ...'},
                'request_data': {'title': 'CCCD mặt trước', 'description': 'OCR front ID'},
                'response_status': 200,
                'response_data': {'message': 'IDG-00000000', 'object': {'hash': 'idg-xxx-xxx-xxx'}},
                'status': 'success',
                'duration_ms': 1250.5,
            },
            {
                'endpoint': 'https://api.idg.vnpt.vn/ai/v1/ocr/id/front',
                'method': 'POST',
                'api_type': 'ekyc',
                'request_headers': {'Token-id': '...', 'Content-Type': 'application/json'},
                'request_data': {'img_front': 'idg-xxx-xxx-xxx', 'type': -1},
                'response_status': 200,
                'response_data': {'message': 'IDG-00000000', 'object': {'name': 'NGUYỄN VĂN A', 'id': '012345678'}},
                'status': 'success',
                'duration_ms': 2340.2,
            },
            {
                'endpoint': 'https://api.idg.vnpt.vn/ai/v1/face/compare',
                'method': 'POST',
                'api_type': 'ekyc',
                'request_headers': {'Token-id': '...', 'Content-Type': 'application/json'},
                'request_data': {'img_front': 'idg-xxx-xxx-xxx', 'img_face': 'idg-yyy-yyy-yyy'},
                'response_status': 200,
                'response_data': {'message': 'IDG-00000000', 'object': {'result': 'Khuôn mặt khớp 99.7%', 'msg': 'MATCH', 'prob': 99.7}},
                'status': 'success',
                'duration_ms': 1567.3,
            },
        ]

        created_count = 0
        for sample in samples:
            try:
                api_record_model.create_record(
                    endpoint=sample['endpoint'],
                    method=sample['method'],
                    request_headers=sample.get('request_headers'),
                    request_data=sample.get('request_data'),
                    response_status=sample.get('response_status'),
                    response_data=sample.get('response_data'),
                    status=sample.get('status', 'success'),
                    error_message=sample.get('error_message'),
                    duration_ms=sample.get('duration_ms'),
                    api_type=sample.get('api_type', 'ekyc'),
                )
                created_count += 1
            except Exception as e:
                _logger.exception('Failed to create sample API record: %s', e)

        message = _('Đã tạo %d bản ghi API mẫu thành công.') % created_count
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('API Records'), 'message': message, 'type': 'success'},
        }
