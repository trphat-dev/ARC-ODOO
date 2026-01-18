import json
import logging
import time

from odoo import http
from odoo.http import request

from ..services import get_service_from_env

_logger = logging.getLogger(__name__)


class PayOSWebhookController(http.Controller):
    @http.route(['/payos/create-link'], type='json', auth='user', methods=['POST'], csrf=False)
    def create_payment_link(self, **kwargs):
        # Guard clause: required fields
        required = ['orderCode', 'amount', 'description', 'returnUrl', 'cancelUrl']
        missing = [k for k in required if k not in kwargs]
        if missing:
            return {'status': 'error', 'message': f'missing {",".join(missing)}'}

        service = get_service_from_env(request.env)
        try:
            resp = service.create_payment_link({
                'orderCode': kwargs['orderCode'],
                'amount': kwargs['amount'],
                'description': kwargs['description'],
                'returnUrl': kwargs['returnUrl'],
                'cancelUrl': kwargs['cancelUrl'],
            })
            return {'status': 'ok', 'data': resp}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route(['/payos/webhook'], type='json', auth='public', methods=['POST'], csrf=False)
    def payos_webhook(self, **kwargs):
        """
        Xử lý webhook từ PayOS khi có thanh toán
        PayOS sẽ gửi thông tin về trạng thái thanh toán
        """
        try:
            payload = request.get_json_data()
        except Exception:
            # Fallback for non-JSON content-type
            try:
                payload = json.loads(request.httprequest.data.decode('utf-8'))
            except Exception:
                _logger.error('PayOS webhook: Invalid JSON body')
                return {'status': 'error', 'message': 'invalid body'}

        if not payload:
            _logger.error('PayOS webhook: Empty payload')
            return {'status': 'error', 'message': 'empty payload'}

        # Verify webhook signature
        service = get_service_from_env(request.env)
        if not service.verify_webhook(payload or {}):
            _logger.error('PayOS webhook: Invalid signature')
            return {'status': 'error', 'message': 'invalid signature'}

        try:
            # Parse webhook data
            # PayOS webhook format: {"code": "00", "desc": "success", "data": {...}}
            webhook_code = payload.get('code', '')
            webhook_desc = payload.get('desc', '')
            webhook_data = payload.get('data', {})
            
            # Lấy orderCode từ webhook data
            order_code = webhook_data.get('orderCode') or webhook_data.get('order_code')
            
            if not order_code:
                _logger.warning('PayOS webhook: Missing orderCode in payload: %s', json.dumps(payload))
                return {'status': 'ok', 'message': 'Missing orderCode'}

            # Tìm transaction theo orderCode
            # orderCode có thể là transaction.id hoặc timestamp
            transaction = None
            
            # Thử tìm theo reference (PAYOS-{orderCode})
            transaction = request.env['portfolio.transaction'].sudo().search([
                ('reference', '=', f'PAYOS-{order_code}')
            ], limit=1)
            
            # Nếu không tìm thấy, thử tìm theo orderCode = transaction.id
            if not transaction and order_code.isdigit():
                try:
                    transaction = request.env['portfolio.transaction'].sudo().browse(int(order_code))
                    if not transaction.exists():
                        transaction = None
                except Exception:
                    transaction = None

            # Xử lý theo trạng thái thanh toán
            if webhook_code == '00' and webhook_desc == 'success':
                # Thanh toán thành công
                if transaction:
                    # Cập nhật transaction status
                    transaction.write({
                        'status': 'completed',
                        'reference': f'PAYOS-{order_code}',
                    })
                    
                    # Log thông tin thanh toán
                    payment_info = {
                        'orderCode': order_code,
                        'amount': webhook_data.get('amount'),
                        'accountNumber': webhook_data.get('accountNumber'),
                        'accountName': webhook_data.get('accountName'),
                        'transactionDateTime': webhook_data.get('transactionDateTime'),
                        'paymentLinkId': webhook_data.get('paymentLinkId'),
                    }
                    _logger.info('PayOS webhook: Payment successful for transaction %s: %s', 
                                transaction.id, json.dumps(payment_info))
                else:
                    _logger.warning('PayOS webhook: Transaction not found for orderCode: %s', order_code)
            else:
                # Thanh toán thất bại hoặc hủy
                if transaction:
                    _logger.info('PayOS webhook: Payment failed/cancelled for transaction %s. Code: %s, Desc: %s',
                                transaction.id, webhook_code, webhook_desc)
                else:
                    _logger.warning('PayOS webhook: Payment failed/cancelled for orderCode: %s', order_code)

            # Fast-ack: PayOS yêu cầu trả về ngay để tránh timeout
            return {'status': 'ok', 'code': webhook_code, 'desc': webhook_desc}
            
        except Exception as e:
            _logger.error('PayOS webhook: Error processing webhook: %s', str(e), exc_info=True)
            # Vẫn trả về ok để PayOS không retry
            return {'status': 'ok', 'message': 'Error processed'}

    @http.route(['/payos/payment-requests/info'], type='json', auth='user', methods=['POST'], csrf=False)
    def payment_request_info(self, **kwargs):
        identifier = kwargs.get('id')
        if identifier is None:
            return {'status': 'error', 'message': 'missing id'}
        service = get_service_from_env(request.env)
        try:
            resp = service.get_payment_link_info(identifier)
            return {'status': 'ok', 'data': resp}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route(['/payos/payment-requests/cancel'], type='json', auth='user', methods=['POST'], csrf=False)
    def payment_request_cancel(self, **kwargs):
        identifier = kwargs.get('id')
        if identifier is None:
            return {'status': 'error', 'message': 'missing id'}
        reason = kwargs.get('cancellationReason')
        service = get_service_from_env(request.env)
        try:
            resp = service.cancel_payment_link(identifier, reason)
            return {'status': 'ok', 'data': resp}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route(['/payos/confirm-webhook'], type='json', auth='user', methods=['POST'], csrf=False)
    def confirm_webhook(self, **kwargs):
        webhook_url = kwargs.get('webhookUrl')
        if not webhook_url:
            return {'status': 'error', 'message': 'missing webhookUrl'}
        service = get_service_from_env(request.env)
        try:
            resp = service.confirm_webhook(webhook_url)
            return {'status': 'ok', 'data': resp}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route(['/api/payment/create'], type='http', auth='user', methods=['POST'], csrf=False)
    def create_payment(self, **kwargs):
        """
        Endpoint tương thích với frontend fund_confirm.js
        Tạo PayOS payment link với VietQR
        """
        try:
            # Parse JSON từ request body
            payload = {}
            try:
                content_type = request.httprequest.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    raw_data = request.httprequest.data or b'{}'
                    payload = json.loads(raw_data.decode('utf-8'))
                else:
                    payload = kwargs
            except (json.JSONDecodeError, AttributeError, ValueError, UnicodeDecodeError):
                payload = kwargs

            # Fail-fast: kiểm tra các trường bắt buộc
            transaction_id = payload.get('transaction_id', 0)
            amount = payload.get('amount', 0)
            description = payload.get('description', '')
            cancel_url = payload.get('cancel_url', '/payment/cancel')
            return_url = payload.get('return_url', '/payment/success')

            if not amount or amount <= 0:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Số tiền không hợp lệ'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            # Tìm transaction nếu có transaction_id
            transaction = None
            if transaction_id:
                try:
                    transaction = request.env['portfolio.transaction'].sudo().browse(int(transaction_id))
                    if not transaction.exists():
                        transaction = None
                except Exception:
                    transaction = None

            # Tạo orderCode từ transaction_id hoặc timestamp
            if transaction and transaction.id:
                order_code = transaction.id
            else:
                order_code = int(time.time() * 1000)  # Millisecond timestamp

            # Chuẩn bị dữ liệu cho PayOS
            # PayOS yêu cầu description tối đa 25 ký tự
            # Nếu description không có, tạo mặc định "Nap tien TK**** tai HDC"
            if not description:
                # Lấy 4 số cuối của order_code để tạo số tài khoản
                order_code_str = str(order_code)
                account_number = order_code_str[-4:] if len(order_code_str) >= 4 else '****'
                payos_description = f'Nap tien TK{account_number} tai HDC'
            else:
                payos_description = description
                
            if len(payos_description) > 25:
                # Rút ngắn description xuống 25 ký tự
                payos_description = payos_description[:22] + '...'
            
            payos_data = {
                'orderCode': order_code,
                'amount': int(amount),  # PayOS yêu cầu số nguyên (VND)
                'description': payos_description,
                'returnUrl': return_url,
                'cancelUrl': cancel_url,
            }

            # Lấy PayOS service và tạo payment link
            service = get_service_from_env(request.env)
            
            # Fail-fast: kiểm tra credentials trước khi gọi API
            if not service.client_id or not service.api_key or not service.checksum_key:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'PayOS credentials chưa được cấu hình. Vui lòng cấu hình trong Settings > PayOS Settings'}, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')],
                    status=500
                )
            
            resp = service.create_payment_link(payos_data)
            
            # Log full response để debug
            _logger.info('PayOS API response: %s', json.dumps(resp, indent=2))
            
            # PayOS API có thể trả về nhiều format:
            # Format 1: {"code": "00", "desc": "success", "data": {"checkoutUrl": "...", "qrCode": "..."}}
            # Format 2: {"checkoutUrl": "...", "qrCode": "..."}
            # Format 3: {"data": {"checkoutUrl": "...", "qrCode": "..."}}
            # Format 4: {"code": "00", "desc": "success", "data": {"link": "https://pay.payos.vn/web/..."}}
            
            checkout_url = None
            qr_code = None
            
            # Kiểm tra response structure - PayOS API có thể trả về nhiều format
            if isinstance(resp, dict):
                # Log toàn bộ response để debug
                _logger.info('PayOS API full response structure: %s', json.dumps(resp, indent=2))
                
                # Thử format 1: có data wrapper với checkoutUrl
                if 'data' in resp and isinstance(resp['data'], dict):
                    data = resp['data']
                    # Thử checkoutUrl
                    checkout_url = data.get('checkoutUrl') or data.get('checkout_url') or data.get('link')
                    # Thử qrCode - PayOS có thể trả về:
                    # - qrCodeUrl: URL hình ảnh QR code (có logo VietQR)
                    # - qrCode: VietQR string (cần tạo QR code từ string)
                    # - qrCodeBase64: Base64 image
                    qr_code = (
                        data.get('qrCodeUrl') or 
                        data.get('qr_code_url') or
                        data.get('qrCode') or 
                        data.get('qr_code') or 
                        data.get('qrCodeBase64') or
                        data.get('qr_code_base64')
                    )
                
                # Nếu chưa có, thử format 2: trực tiếp ở root level
                if not checkout_url:
                    checkout_url = resp.get('checkoutUrl') or resp.get('checkout_url') or resp.get('link')
                if not qr_code:
                    # Ưu tiên qrCodeUrl (image URL có logo VietQR)
                    qr_code = (
                        resp.get('qrCodeUrl') or 
                        resp.get('qr_code_url') or
                        resp.get('qrCode') or 
                        resp.get('qr_code') or 
                        resp.get('qrCodeBase64') or
                        resp.get('qr_code_base64')
                    )
                
                # Log kết quả
                _logger.info('Extracted - checkout_url: %s, qr_code: %s', checkout_url, 'Có' if qr_code else 'Không')
            
            if not checkout_url:
                # Log response để debug
                _logger.error('PayOS API response không có checkoutUrl. Full response: %s', json.dumps(resp, indent=2))
                
                # Thử extract thông tin lỗi từ response
                error_msg = 'Không nhận được checkout URL từ PayOS'
                if isinstance(resp, dict):
                    if 'desc' in resp:
                        error_msg += f': {resp.get("desc")}'
                    if 'message' in resp:
                        error_msg += f': {resp.get("message")}'
                
                return request.make_response(
                    json.dumps({
                        'success': False, 
                        'error': error_msg,
                        'debug_info': 'Vui lòng kiểm tra credentials và thử lại. Xem logs để biết thêm chi tiết.'
                    }, ensure_ascii=False),
                    headers=[('Content-Type', 'application/json')],
                    status=500
                )

            # Trả về response tương thích với frontend
            result = {
                'success': True,
                'checkout_url': checkout_url,
                'order_code': order_code,
            }
            
            # Thêm QR code nếu có (VietQR)
            if qr_code:
                result['qr_code'] = qr_code
                result['data'] = {'qr_code': qr_code, 'checkout_url': checkout_url}
            
            # Parse thông tin ngân hàng từ PayOS response
            # Chỉ lấy dữ liệu từ PayOS API, không tạo mock data
            bank_info = None
            if isinstance(resp, dict) and 'data' in resp and isinstance(resp['data'], dict):
                data = resp['data']
                # Chỉ lấy nếu có đầy đủ thông tin từ PayOS
                bank_name = data.get('bankName') or data.get('bank_name')
                account_number = data.get('accountNumber') or data.get('account_number')
                account_holder = data.get('accountHolder') or data.get('account_holder')
                
                # Chỉ tạo bank_info nếu có ít nhất account_number từ PayOS
                if account_number:
                    bank_info = {
                        'bank_name': bank_name,
                        'account_number': account_number,
                        'account_holder': account_holder
                    }
            
            # Thêm thông tin ngân hàng vào response (chỉ nếu có từ PayOS)
            if bank_info:
                result['bank_info'] = bank_info
                result['data'] = result.get('data', {})
                result['data'].update(bank_info)
            
            # Nếu không có QR code từ API, có thể tạo QR code từ checkoutUrl
            # PayOS có thể trả về QR code trong response.data.qrCode hoặc cần tạo từ checkoutUrl
            if not qr_code and checkout_url:
                # Log để debug
                _logger.warning('PayOS API không trả về QR code. Checkout URL: %s', checkout_url)
                # Có thể tạo QR code từ checkoutUrl bằng thư viện QR code generator
                # Hoặc frontend có thể tự tạo QR code từ checkoutUrl
            
            # Lưu thông tin payment vào transaction nếu có
            if transaction:
                transaction.write({
                    'reference': f'PAYOS-{order_code}',
                })
            
            return request.make_response(
                json.dumps(result, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            error_msg = str(e)
            return request.make_response(
                json.dumps({'success': False, 'error': f'Lỗi tạo payment link: {error_msg}'}, ensure_ascii=False),
                headers=[('Content-Type', 'application/json')],
                status=500
            )


