import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional

import requests


class PayOSService:
    def __init__(self, client_id: str, api_key: str, checksum_key: str, base_url: Optional[str] = None):
        self.client_id = client_id
        self.api_key = api_key
        self.checksum_key = checksum_key
        self.base_url = base_url or os.getenv('PAYOS_BASE_URL', 'https://api-merchant.payos.vn')

    @staticmethod
    def _hmac_sha256_hex(secret: str, message: str) -> str:
        return hmac.HMAC(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

    def _signature_for_create_payment(self, payload: Dict[str, Any]) -> str:
        # Follow createSignatureOfPaymentRequest: use a stable key order relevant for create payment
        # Common fields include: amount, cancelUrl, description, orderCode, returnUrl, items (if any)
        # Flatten only top-level fields in canonical order
        canonical_keys = [
            'amount',
            'cancelUrl',
            'description',
            'orderCode',
            'returnUrl',
        ]
        parts: list[str] = []
        for key in canonical_keys:
            if key in payload and payload[key] is not None:
                parts.append(f"{key}={payload[key]}")
        message = '&'.join(parts)
        return self._hmac_sha256_hex(self.checksum_key, message)

    def create_payment_link(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/v2/payment-requests"
        payload = dict(data)
        payload['signature'] = self._signature_for_create_payment(payload)
        headers = {
            'Content-Type': 'application/json',
            'x-client-id': self.client_id,
            'x-api-key': self.api_key,
        }
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('PayOS API request - URL: %s', url)
        _logger.info('PayOS API request - Payload: %s', json.dumps(payload, indent=2))
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        
        # Log response status và content
        _logger.info('PayOS API response - Status: %s', response.status_code)
        _logger.info('PayOS API response - Headers: %s', dict(response.headers))
        
        response.raise_for_status()
        result = response.json()
        _logger.info('PayOS API response - Body: %s', json.dumps(result, indent=2))
        return result

    def get_payment_link_info(self, identifier: Any) -> Dict[str, Any]:
        url = f"{self.base_url}/v2/payment-requests/{identifier}"
        headers = {
            'x-client-id': self.client_id,
            'x-api-key': self.api_key,
        }
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    def cancel_payment_link(self, identifier: Any, reason: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/v2/payment-requests/{identifier}/cancel"
        headers = {
            'Content-Type': 'application/json',
            'x-client-id': self.client_id,
            'x-api-key': self.api_key,
        }
        payload: Dict[str, Any] = {}
        if reason:
            payload['cancellationReason'] = reason
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        return response.json()

    def confirm_webhook(self, webhook_url: str) -> Dict[str, Any]:
        url = f"{self.base_url}/confirm-webhook"
        headers = {
            'Content-Type': 'application/json',
            'x-client-id': self.client_id,
            'x-api-key': self.api_key,
        }
        payload = {'webhookUrl': webhook_url}
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        return response.json()

    def verify_webhook(self, body: Dict[str, Any]) -> bool:
        # For webhook/payment-requests signature: sign all top-level fields except 'signature' in key-sorted order
        signature = body.get('signature')
        if not signature:
            return False
        items = []
        for k in sorted(k for k in body.keys() if k != 'signature'):
            v = body.get(k)
            if isinstance(v, (dict, list)):
                v = json.dumps(v, separators=(',', ':'), ensure_ascii=False)
            items.append(f"{k}={v}")
        message = '&'.join(items)
        expected = self._hmac_sha256_hex(self.checksum_key, message)
        return hmac.compare_digest(signature, expected)


def get_service_from_env(env) -> PayOSService:
    """
    Lấy PayOSService từ cấu hình trong payos.config model.
    Fallback về environment variables nếu không có cấu hình.
    """
    PayOSConfig = env['payos.config'].sudo()
    config = PayOSConfig.search([('is_active', '=', True)], limit=1)
    
    if config:
        return PayOSService(
            client_id=config.client_id or '',
            api_key=config.api_key or '',
            checksum_key=config.checksum_key or '',
            base_url=config.base_url or None
        )
    
    # Fallback to environment variables
    import os
    return PayOSService(
        client_id=os.getenv('PAYOS_CLIENT_ID', ''),
        api_key=os.getenv('PAYOS_API_KEY', ''),
        checksum_key=os.getenv('PAYOS_CHECKSUM_KEY', ''),
        base_url=os.getenv('PAYOS_BASE_URL')
    )

