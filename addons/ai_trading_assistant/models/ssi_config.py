from odoo import models, fields, api, exceptions
import requests

# Must match ai_chatbot_service.DEFAULT_LLM_MODEL
DEFAULT_LLM_MODEL = 'google/gemini-2.0-flash-001'


class SSIConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    ssi_consumer_id = fields.Char(string='SSI Consumer ID', config_parameter='ai_trading.ssi_consumer_id')
    ssi_consumer_secret = fields.Char(string='SSI Consumer Secret', config_parameter='ai_trading.ssi_consumer_secret')
    ssi_api_url = fields.Char(string='SSI API URL', default='https://fc-data.ssi.com.vn/', config_parameter='ai_trading.ssi_api_url')

    # LLM Settings
    llm_provider = fields.Selection([
        ('openrouter', 'OpenRouter')
    ], string="Nhà cung cấp AI (Cổng kết nối)", default='openrouter', config_parameter='ai_trading.llm_provider')
    llm_api_key = fields.Char(string='LLM API Key', config_parameter='ai_trading.llm_api_key')
    llm_model_name = fields.Char(
        string='Mã AI Model (OpenRouter ID)',
        default=DEFAULT_LLM_MODEL,
        config_parameter='ai_trading.llm_model_name'
    )

    def get_values(self):
        res = super(SSIConfig, self).get_values()
        return res

    def set_values(self):
        super(SSIConfig, self).set_values()

    def action_test_ssi_connection(self):
        consumer_id = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_consumer_id')
        consumer_secret = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_consumer_secret')
        api_url = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_api_url', 'https://fc-data.ssi.com.vn/')

        if not consumer_id or not consumer_secret:
            raise exceptions.UserError('Vui lòng điền đầy đủ Consumer ID và Consumer Secret!')

        try:
            payload = {
                "consumerID": consumer_id,
                "consumerSecret": consumer_secret
            }
            response = requests.post(f"{api_url}api/v2/Market/AccessToken", json=payload, timeout=5)
            if response.status_code == 200 and response.json().get('status') == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Kết nối SSI',
                        'message': 'Kết nối thành công tới SSI API!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise exceptions.UserError(f'Kết nối thất bại: {response.text}')
        except exceptions.UserError:
            raise
        except Exception as e:
            raise exceptions.UserError(f'Lỗi kết nối: {str(e)}')

    def action_test_llm_connection(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('ai_trading.llm_api_key')

        if not api_key:
            raise exceptions.UserError('Vui lòng nhập OpenRouter API Key để kiểm tra!')

        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.env['ir.config_parameter'].sudo().get_param(
                    'ai_trading.llm_model_name', DEFAULT_LLM_MODEL
                ),
                "messages": [{"role": "user", "content": "Kiểm tra kết nối"}]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Kết nối LLM',
                        'message': 'Chúc mừng! Kết nối tới OpenRouter đã sẵn sàng.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                res_data = response.json()
                msg = res_data.get('error', {}).get('message', response.text)
                raise exceptions.UserError(f'Lỗi OpenRouter: {msg}')
        except exceptions.UserError:
            raise
        except Exception as e:
            raise exceptions.UserError(f'Lỗi kết nối tới hệ thống OpenRouter: {str(e)}')
