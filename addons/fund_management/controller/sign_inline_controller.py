import base64
import json
import logging

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request, Response

from ..utils import pdf_utils, url_utils, contract_utils
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access

_logger = logging.getLogger(__name__)


class SignInlineController(http.Controller):
    """Controller for inline contract signing"""
    
    @staticmethod
    def _get_json_body():
        """Extract JSON body from request"""
        try:
            if hasattr(request, 'httprequest') and hasattr(request.httprequest, 'get_json'):
                data = request.httprequest.get_json(silent=True)
                if isinstance(data, dict):
                    return data
            raw = request.httprequest.get_data() if hasattr(request, 'httprequest') else None
            if raw:
                return json.loads(raw.decode('utf-8'))
        except Exception as e:
            _logger.warning(f"Failed to parse JSON body: {e}")
        return {}
    
    @staticmethod
    def _create_contract_record(
        pdf_bytes: bytes,
        signed_type: str,
        signer_info: dict,
        investment_id: int = None,
        transaction_id: int = None
    ) -> 'fund.signed.contract':
        """Create contract record from signed PDF"""
        try:
            # Encode PDF to base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Generate contract code and filename
            code = contract_utils.ContractCodeGenerator.generate_code(signed_type)
            filename = contract_utils.ContractCodeGenerator.generate_filename(code)
            
            # Prepare contract values
            vals = {
                'name': code,
                'partner_id': request.env.user.partner_id.id or False,
                'investment_id': investment_id or False,
                'transaction_id': transaction_id or False,
                'signed_type': signed_type,
                'file_data': pdf_base64,
                'filename': filename,
                'signer_email': signer_info.get('email', ''),
                'signer_phone': signer_info.get('phone', ''),
                'signer_id_number': signer_info.get('id_number', ''),
                'signer_birth_date': signer_info.get('birth_date', ''),
            }
            
            return request.env['fund.signed.contract'].sudo().create(vals)
        except Exception as e:
            _logger.error(f"Failed to create contract record: {e}")
            raise
    
    @http.route('/api/sign', type='http', auth='user', methods=['POST'], csrf=False)
    @require_module_access('fund_management')
    def sign_document(self, **kwargs):
        """Sign document with digital signature"""
        try:
            data = self._get_json_body()
            document_b64 = data.get('document_base64')
            
            if not document_b64:
                return Response(
                    json.dumps({'error': 'Thiếu document_base64'}),
                    content_type='application/json',
                    status=400
                )
            
            # Get signer info
            signer = data.get('signer') or contract_utils.ContractSignerInfo.get_signer_from_request()
            positions = data.get('positions') or {}
            investment_id = data.get('investment_id')
            transaction_id = data.get('transaction_id')
            
            # Decode and sign PDF
            try:
                pdf_bytes = pdf_utils.PdfSigner.decode_base64_pdf(document_b64)
                signed_pdf_bytes = pdf_utils.PdfSigner.add_digital_signature(
                    pdf_bytes,
                    signer,
                    positions
                )
            except ValueError as e:
                return Response(
                    json.dumps({'error': str(e)}),
                    content_type='application/json',
                    status=400
                )
            
            # Create contract record
            try:
                signer_info = {'email': signer}
                self._create_contract_record(
                    signed_pdf_bytes,
                    'digital',
                    signer_info,
                    investment_id=investment_id,
                    transaction_id=transaction_id
                )
            except Exception as e:
                _logger.error(f"Failed to save contract: {e}")
                # Continue to return PDF even if save fails
            
            return Response(
                signed_pdf_bytes,
                content_type='application/pdf',
                status=200
            )
        except Exception as e:
            _logger.error(f"Error in sign_document: {e}", exc_info=True)
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500
            )

    @http.route('/api/append_signature', type='http', auth='user', methods=['POST'], csrf=False)
    @require_module_access('fund_management')
    def append_signature(self, **kwargs):
        """Append hand signature to PDF"""
        try:
            data = self._get_json_body()
            image_data_url = data.get('signature_image')
            pdf_url = data.get('pdf_url')
            
            if not image_data_url or not pdf_url:
                return Response(
                    json.dumps({'error': 'Thiếu dữ liệu đầu vào'}),
                    content_type='application/json',
                    status=400
                )
            
            # Extract signer info
            signer_info = {
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
                'id_number': data.get('id_number', ''),
                'birth_date': data.get('birth_date', ''),
            }
            positions = data.get('positions') or {}
            investment_id = data.get('investment_id')
            transaction_id = data.get('transaction_id')
            
            # Validate and fetch PDF
            is_allowed, internal_url = url_utils.UrlValidator.is_allowed_url(pdf_url)
            if not is_allowed:
                return Response(
                    json.dumps({'error': 'Chỉ cho phép PDF từ cùng domain'}),
                    content_type='application/json',
                    status=400
                )
            
            try:
                pdf_bytes = url_utils.UrlValidator.fetch_pdf(internal_url)
            except ValueError as e:
                return Response(
                    json.dumps({'error': str(e)}),
                    content_type='application/json',
                    status=400
                )
            
            # Prepare signature image
            try:
                signature_image_bytes = pdf_utils.PdfSigner.prepare_signature_image(image_data_url)
            except ValueError as e:
                return Response(
                    json.dumps({'error': str(e)}),
                    content_type='application/json',
                    status=400
                )

            # Add signature to PDF
            try:
                signed_pdf_bytes = pdf_utils.PdfSigner.add_hand_signature(
                    pdf_bytes,
                    signature_image_bytes,
                    signer_info,
                    positions
                )
            except Exception as e:
                _logger.error(f"Failed to add signature to PDF: {e}")
                return Response(
                    json.dumps({'error': f'Không thể thêm chữ ký vào PDF: {str(e)}'}),
                    content_type='application/json',
                    status=500
                )
            
            # Create contract record
            try:
                self._create_contract_record(
                    signed_pdf_bytes,
                    'hand',
                    signer_info,
                    investment_id=investment_id,
                    transaction_id=transaction_id
                )
            except Exception as e:
                _logger.error(f"Failed to save contract: {e}")
                # Continue to return PDF even if save fails
            
            return Response(
                signed_pdf_bytes,
                content_type='application/pdf',
                status=200
            )
        except Exception as e:
            _logger.error(f"Error in append_signature: {e}", exc_info=True)
            return Response(
                str(e),
                content_type='text/plain; charset=utf-8',
                status=500
            )


