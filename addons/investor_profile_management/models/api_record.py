from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class ApiRecord(models.Model):
    _name = 'api.record'
    _description = 'API Request/Response Records'
    _order = 'create_date desc'
    _rec_name = 'endpoint'

    # Basic Information
    endpoint = fields.Char(string='Endpoint/URL', required=True, index=True)
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ], string='HTTP Method', required=True, default='POST')
    
    # Request Information
    request_headers = fields.Text(string='Request Headers', help='JSON format')
    request_data = fields.Text(string='Request Data', help='Request body/payload in JSON format')
    request_params = fields.Text(string='Request Parameters', help='Query parameters in JSON format')
    
    # Response Information
    response_status = fields.Integer(string='Response Status Code')
    response_data = fields.Text(string='Response Data', help='Response body in JSON format')
    response_headers = fields.Text(string='Response Headers', help='JSON format')
    
    # Status and Error
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
        ('pending', 'Pending'),
    ], string='Status', default='pending', required=True)
    
    error_message = fields.Text(string='Error Message')
    duration_ms = fields.Float(string='Duration (ms)', help='Request duration in milliseconds')
    
    # Metadata
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Related Partner', index=True)
    investor_profile_id = fields.Many2one('investor.profile', string='Related Investor Profile', index=True)
    
    # API Type
    api_type = fields.Selection([
        ('ekyc', 'VNPT eKYC'),
        ('odoo', 'Odoo Internal'),
        ('external', 'External API'),
        ('other', 'Other'),
    ], string='API Type', default='ekyc', required=True)
    
    # Timestamps
    request_timestamp = fields.Datetime(string='Request Time', default=fields.Datetime.now, readonly=True)
    response_timestamp = fields.Datetime(string='Response Time', readonly=True)
    
    # Additional Info
    notes = fields.Text(string='Notes')
    retry_count = fields.Integer(string='Retry Count', default=0)
    is_retry = fields.Boolean(string='Is Retry', default=False)
    
    # Computed Fields
    formatted_request = fields.Html(string='Formatted Request', compute='_compute_formatted_data')
    formatted_response = fields.Html(string='Formatted Response', compute='_compute_formatted_data')
    
    @api.depends('request_data', 'response_data', 'request_headers', 'response_headers')
    def _compute_formatted_data(self):
        """Format JSON data for better display"""
        for record in self:
            # Format Request
            request_html = '<div class="o_field_text">'
            if record.request_headers:
                try:
                    headers = json.loads(record.request_headers) if isinstance(record.request_headers, str) else record.request_headers
                    request_html += f'<strong>Headers:</strong><pre>{json.dumps(headers, indent=2, ensure_ascii=False)}</pre>'
                except:
                    request_html += f'<strong>Headers:</strong><pre>{record.request_headers}</pre>'
            
            if record.request_data:
                try:
                    data = json.loads(record.request_data) if isinstance(record.request_data, str) else record.request_data
                    request_html += f'<strong>Data:</strong><pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>'
                except:
                    request_html += f'<strong>Data:</strong><pre>{record.request_data}</pre>'
            
            if record.request_params:
                try:
                    params = json.loads(record.request_params) if isinstance(record.request_params, str) else record.request_params
                    request_html += f'<strong>Params:</strong><pre>{json.dumps(params, indent=2, ensure_ascii=False)}</pre>'
                except:
                    request_html += f'<strong>Params:</strong><pre>{record.request_params}</pre>'
            
            request_html += '</div>'
            record.formatted_request = request_html
            
            # Format Response
            response_html = '<div class="o_field_text">'
            if record.response_status:
                status_color = 'green' if 200 <= record.response_status < 300 else 'red'
                response_html += f'<strong>Status:</strong> <span style="color: {status_color};">{record.response_status}</span><br/>'
            
            if record.response_headers:
                try:
                    headers = json.loads(record.response_headers) if isinstance(record.response_headers, str) else record.response_headers
                    response_html += f'<strong>Headers:</strong><pre>{json.dumps(headers, indent=2, ensure_ascii=False)}</pre>'
                except:
                    response_html += f'<strong>Headers:</strong><pre>{record.response_headers}</pre>'
            
            if record.response_data:
                try:
                    data = json.loads(record.response_data) if isinstance(record.response_data, str) else record.response_data
                    response_html += f'<strong>Data:</strong><pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>'
                except:
                    response_html += f'<strong>Data:</strong><pre>{record.response_data}</pre>'
            
            if record.error_message:
                response_html += f'<strong style="color: red;">Error:</strong><pre>{record.error_message}</pre>'
            
            response_html += '</div>'
            record.formatted_response = response_html
    
    @api.model
    def create_record(self, endpoint, method='POST', request_data=None, request_headers=None, 
                     request_params=None, response_status=None, response_data=None, 
                     response_headers=None, status='pending', error_message=None, 
                     duration_ms=None, api_type='ekyc', partner_id=None, investor_profile_id=None):
        """
        Helper method to create API record
        
        Args:
            endpoint: API endpoint URL
            method: HTTP method
            request_data: Request body (dict or JSON string)
            request_headers: Request headers (dict or JSON string)
            request_params: Request parameters (dict or JSON string)
            response_status: HTTP status code
            response_data: Response body (dict or JSON string)
            response_headers: Response headers (dict or JSON string)
            status: Record status
            error_message: Error message if any
            duration_ms: Request duration in milliseconds
            api_type: Type of API
            partner_id: Related partner ID
            investor_profile_id: Related investor profile ID
        
        Returns:
            api.record recordset
        """
        # Convert dict to JSON string if needed
        def to_json_string(data):
            if data is None:
                return None
            if isinstance(data, str):
                return data
            try:
                return json.dumps(data, indent=2, ensure_ascii=False)
            except:
                return str(data)
        
        vals = {
            'endpoint': endpoint,
            'method': method,
            'request_data': to_json_string(request_data),
            'request_headers': to_json_string(request_headers),
            'request_params': to_json_string(request_params),
            'response_status': response_status,
            'response_data': to_json_string(response_data),
            'response_headers': to_json_string(response_headers),
            'status': status,
            'error_message': error_message,
            'duration_ms': duration_ms,
            'api_type': api_type,
            'partner_id': partner_id,
            'investor_profile_id': investor_profile_id,
        }
        
        if status != 'pending':
            vals['response_timestamp'] = fields.Datetime.now()
        
        return self.create(vals)
    
    def action_retry(self):
        """Retry the API call (placeholder for future implementation)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Retry API'),
                'message': _('Retry functionality will be implemented soon.'),
                'type': 'warning',
            }
        }
    
    def action_view_related_profile(self):
        """View related investor profile"""
        self.ensure_one()
        if not self.investor_profile_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Investor Profile'),
            'res_model': 'investor.profile',
            'res_id': self.investor_profile_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

