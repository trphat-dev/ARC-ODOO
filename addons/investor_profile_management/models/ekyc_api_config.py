from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import timedelta
import requests

_logger = logging.getLogger(__name__)


class EKYCApiConfig(models.Model):
    """Configuration for VNPT eKYC API — Single source of truth for token management"""
    _name = 'ekyc.api.config'
    _description = 'VNPT eKYC API Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Configuration Name', required=True, default='Default Configuration')

    # API Credentials
    token_id = fields.Char('Token ID', required=True)
    token_key = fields.Char('Token Key', required=True, password=True)
    access_token = fields.Char('Access Token', password=True)
    public_key_ca = fields.Text('Public Key CA', help='Public Key CA để xác thực chứng chỉ SSL')

    # API URLs
    base_url = fields.Char('Base URL', required=True, default='https://api.idg.vnpt.vn')
    token_endpoint = fields.Char(
        'Token Endpoint',
        help='Endpoint để lấy access token. Nếu để trống sẽ dùng base_url/oauth/token',
    )

    # Status
    is_active = fields.Boolean('Is Active', default=True)
    token_expiration = fields.Datetime('Token Expiration')
    last_sync_date = fields.Datetime('Last Sync Date', readonly=True)
    last_sync_status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('not_synced', 'Not Synced')
    ], string='Last Sync Status', default='not_synced', readonly=True)

    # Statistics
    total_api_calls = fields.Integer('Total API Calls', compute='_compute_statistics', readonly=True)
    success_calls = fields.Integer('Success Calls', compute='_compute_statistics', readonly=True)
    failed_calls = fields.Integer('Failed Calls', compute='_compute_statistics', readonly=True)
    last_api_call_date = fields.Datetime('Last API Call Date', compute='_compute_statistics', readonly=True)

    # Token refresh settings
    TOKEN_REFRESH_BUFFER_MINUTES = 10  # Refresh token 10 minutes before expiration
    TOKEN_DEFAULT_TTL_HOURS = 8        # Default token TTL if not provided by API
    REQUEST_TIMEOUT = 30               # HTTP request timeout in seconds

    @api.depends('name')
    def _compute_statistics(self):
        """Compute statistics from API records"""
        for record in self:
            api_records = self.env['api.record'].search([
                ('api_type', '=', 'ekyc')
            ])
            record.total_api_calls = len(api_records)
            record.success_calls = len(api_records.filtered(lambda r: r.status == 'success'))
            record.failed_calls = len(api_records.filtered(lambda r: r.status == 'error'))
            last_record = api_records.sorted('request_timestamp', reverse=True)[:1]
            record.last_api_call_date = last_record.request_timestamp if last_record else False

    @api.model
    def get_config(self):
        """Get active configuration, create default if not exists"""
        config = self.search([('is_active', '=', True)], limit=1)
        if not config:
            config = self.create({
                'name': 'Default Configuration',
                'is_active': True,
            })
        return config

    # ─── Core token management (SINGLE SOURCE OF TRUTH) ───

    def _get_token_endpoint(self):
        """Resolve the OAuth token endpoint URL"""
        self.ensure_one()
        if self.token_endpoint:
            return self.token_endpoint
        if not self.base_url:
            raise UserError(_('Vui lòng cấu hình Base URL hoặc Token Endpoint.'))
        return self.base_url.rstrip('/') + '/oauth/token'

    def _parse_token_response(self, data):
        """Extract token and expiration from VNPT OAuth response.

        VNPT API may return token/expiration in different field names depending
        on API version, so we try multiple keys.
        """
        token = (
            data.get('access_token')
            or data.get('accessToken')
            or data.get('token')
            or data.get('data', {}).get('access_token')
            or data.get('data', {}).get('accessToken')
        )

        expires_in = (
            data.get('expires_in')
            or data.get('expire_in')
            or data.get('expiresIn')
            or data.get('data', {}).get('expires_in')
            or self.TOKEN_DEFAULT_TTL_HOURS * 3600
        )

        return token, int(expires_in)

    def refresh_access_token(self):
        """Fetch a new access token from VNPT OAuth API.

        This is the SINGLE method for token refresh — used by:
        - Cron job (_cron_refresh_token)
        - Manual button (action_generate_token)
        - Controller auto-refresh (ensure_valid_token)

        Returns:
            str: The new access token

        Raises:
            UserError: If credentials are missing or API call fails
        """
        self.ensure_one()

        if not self.token_id or not self.token_key:
            raise UserError(_('Vui lòng nhập Token ID và Token Key.'))

        token_endpoint = self._get_token_endpoint()
        payload = {
            'tokenId': self.token_id,
            'tokenKey': self.token_key,
        }

        _logger.info(
            'Requesting new VNPT access token from %s (token_id=%s...)',
            token_endpoint, (self.token_id or '')[:20],
        )
        try:
            resp = requests.post(token_endpoint, json=payload, timeout=self.REQUEST_TIMEOUT)

            if not resp.ok:
                # Extract detailed error from response body
                try:
                    error_detail = resp.json()
                except Exception:
                    error_detail = resp.text[:500] if resp.text else '(empty response)'
                _logger.error(
                    'VNPT OAuth error: status=%s, url=%s, token_id=%s, response=%s',
                    resp.status_code, token_endpoint, self.token_id, error_detail,
                )
                self.write({
                    'last_sync_date': fields.Datetime.now(),
                    'last_sync_status': 'failed',
                })
                raise UserError(_(
                    'VNPT eKYC trả về lỗi %s.\n\n'
                    'URL: %s\n'
                    'Token ID: %s\n'
                    'Chi tiết: %s\n\n'
                    'Vui lòng kiểm tra Token ID và Token Key trong cấu hình.'
                ) % (resp.status_code, token_endpoint, self.token_id, error_detail))

            data = resp.json() or {}
        except UserError:
            raise
        except requests.exceptions.RequestException as exc:
            self.write({
                'last_sync_date': fields.Datetime.now(),
                'last_sync_status': 'failed',
            })
            _logger.exception('VNPT OAuth request failed: %s', exc)
            raise UserError(_(
                'Không thể kết nối VNPT eKYC: %s\n\n'
                'URL: %s\n'
                'Kiểm tra kết nối mạng và thử lại.'
            ) % (exc, token_endpoint))

        token, expires_in = self._parse_token_response(data)
        if not token:
            self.write({
                'last_sync_date': fields.Datetime.now(),
                'last_sync_status': 'failed',
            })
            raise UserError(_('Phản hồi không có access token: %s') % data)

        expiration_dt = fields.Datetime.now() + timedelta(seconds=expires_in)

        self.write({
            'access_token': token,
            'token_expiration': expiration_dt,
            'last_sync_date': fields.Datetime.now(),
            'last_sync_status': 'success',
        })

        _logger.info(
            'VNPT access token refreshed successfully. Expires at %s',
            expiration_dt,
        )
        return token

    def is_token_valid(self):
        """Check if the current access token is still valid.

        Returns True if:
        - Token exists AND no expiration set (manually entered token)
        - Token exists AND not yet expired (with buffer)
        """
        self.ensure_one()
        if not self.access_token:
            return False
        if not self.token_expiration:
            # Token without expiration = manually entered, treat as valid
            return True
        buffer = timedelta(minutes=self.TOKEN_REFRESH_BUFFER_MINUTES)
        return self.token_expiration > (fields.Datetime.now() + buffer)

    def ensure_valid_token(self):
        """Return a valid access token, refreshing if necessary.

        This is the primary entry point for controllers needing a token.
        It will:
        1. Return existing token if still valid
        2. Try auto-refresh if expired/expiring
        3. Fallback to existing token if refresh fails

        Returns:
            str: A valid (or best-effort) access token
        """
        self.ensure_one()
        if self.is_token_valid():
            return self.access_token

        _logger.info(
            'Access token expired or missing (expiration=%s). Refreshing...',
            self.token_expiration,
        )
        try:
            return self.refresh_access_token()
        except Exception as exc:
            if self.access_token:
                _logger.warning(
                    'Token refresh failed: %s. Using existing token as fallback.', exc,
                )
                return self.access_token
            raise

    def get_auth_headers(self, content_type='application/json', include_mac=True):
        """Build authentication headers for VNPT eKYC API requests.

        This centralizes header construction so controllers don't
        need to know about token management internals.

        Args:
            content_type: Content-Type header value (None for multipart)
            include_mac: Whether to include mac-address header

        Returns:
            dict: Ready-to-use request headers
        """
        self.ensure_one()
        headers = {}

        if content_type:
            headers['Content-Type'] = content_type
        if self.token_id:
            headers['Token-id'] = self.token_id
        if self.token_key:
            headers['Token-key'] = self.token_key

        try:
            token = self.ensure_valid_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
        except Exception as exc:
            _logger.warning('Could not obtain VNPT access token: %s', exc)

        if include_mac:
            headers['mac-address'] = 'TEST1'

        return headers

    # ─── UI Actions (buttons in form view) ───

    def action_generate_token(self):
        """Button action: Generate new access token"""
        self.ensure_one()
        self.refresh_access_token()
        message = _('Đã lấy access token mới. Hết hạn vào: %s') % self.token_expiration
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('VNPT eKYC'), 'message': message, 'type': 'success'},
        }

    def action_check_connection(self):
        """Button action: Check connection to VNPT eKYC"""
        self.ensure_one()

        results = []
        has_error = False

        # 1. Check Configuration
        if not self.base_url:
            results.append("❌ Base URL chưa được cấu hình")
            has_error = True
        else:
            results.append(f"✅ Base URL: {self.base_url}")

        if not self.token_id or not self.token_key:
            results.append("❌ Token ID hoặc Token Key chưa được cấu hình")
            has_error = True
        else:
            results.append("✅ Token ID và Token Key đã được nhập")

        # 2. Check Token
        if not self.access_token:
            results.append("⚠️ Access Token chưa có — sẽ tự động lấy khi cần")
        elif not self.is_token_valid():
            results.append(f"⚠️ Access Token đã/sắp hết hạn ({self.token_expiration}) — sẽ tự động làm mới")
        else:
            results.append(f"✅ Access Token còn hạn đến {self.token_expiration}")

        # 3. Check Network Connection
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code < 500:
                results.append("✅ Kết nối mạng đến VNPT OK")
            else:
                results.append(f"⚠️ Server VNPT trả về lỗi: {response.status_code}")
        except Exception as e:
            results.append(f"❌ Không thể kết nối đến VNPT: {str(e)}")
            has_error = True

        # 4. Try token refresh if possible
        if not has_error and not self.is_token_valid() and self.token_id and self.token_key:
            try:
                self.refresh_access_token()
                results.append(f"✅ Tự động lấy token mới thành công! Hết hạn: {self.token_expiration}")
            except Exception as e:
                results.append(f"⚠️ Không thể tự động lấy token: {str(e)}")

        message = "\n".join(results)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Kết quả kiểm tra kết nối'),
                'message': message,
                'type': 'danger' if has_error else 'success',
                'sticky': True,
            },
        }

    def action_view_api_records(self):
        """View API records for this configuration"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('API Records'),
            'res_model': 'api.record',
            'view_mode': 'list,form',
            'domain': [('api_type', '=', 'ekyc')],
            'context': {'default_api_type': 'ekyc'},
        }

    # ─── Cron job ───

    @api.model
    def _cron_refresh_token(self):
        """Scheduled action: refresh token for all active configs.

        Runs periodically (recommended: every 7 hours for 8h TTL tokens).
        Only refreshes if token is expired or about to expire.
        """
        configs = self.search([('is_active', '=', True)])
        for config in configs:
            if config.is_token_valid():
                _logger.info(
                    'Cron: Token for "%s" still valid until %s, skipping refresh.',
                    config.name, config.token_expiration,
                )
                continue

            try:
                config.refresh_access_token()
                _logger.info('Cron: Token refreshed for "%s".', config.name)
            except Exception as exc:
                _logger.error(
                    'Cron: Failed to refresh token for "%s": %s',
                    config.name, exc,
                )
