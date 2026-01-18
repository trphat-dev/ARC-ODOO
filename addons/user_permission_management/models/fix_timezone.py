# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

# Timezone mặc định và mapping
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'
OLD_TIMEZONE = 'Asia/Saigon'  # Timezone cũ cần được convert


class ResUsersTimezoneFix(models.Model):
    """Fix timezone để luôn set về Asia/Ho_Chi_Minh, không bao giờ set về Asia/Saigon"""
    _inherit = 'res.users'

    # Không override field tz, chỉ override default và methods
    # Field tz sẽ giữ nguyên type Selection từ base model

    @api.model
    def create(self, vals):
        """Override create để tự động set timezone về Asia/Ho_Chi_Minh"""
        # Fix timezone nếu có trong vals
        if 'tz' in vals:
            vals['tz'] = self._fix_timezone(vals['tz'])
        else:
            # Set default timezone nếu không có
            vals['tz'] = DEFAULT_TIMEZONE
        
        return super().create(vals)

    def write(self, vals):
        """Override write để tự động fix timezone về Asia/Ho_Chi_Minh"""
        # Skip timezone fix nếu đang trong quá trình fix (tránh recursion)
        if self.env.context.get('skip_timezone_fix'):
            return super().write(vals)
        
        # Fix timezone nếu có trong vals
        if 'tz' in vals:
            fixed_tz = self._fix_timezone(vals['tz'])
            if fixed_tz != vals['tz']:
                _logger.info(f"Timezone fixed from '{vals['tz']}' to '{fixed_tz}' for user(s) {self.ids}")
            vals['tz'] = fixed_tz
        
        result = super().write(vals)
        
        # Sau khi write, kiểm tra và fix timezone cho các user có timezone sai
        # Chỉ check các user đang được update
        # Sử dụng context để tránh recursion khi gọi write() lại
        users_to_fix = self.filtered(lambda u: u.tz == OLD_TIMEZONE or not u.tz)
        if users_to_fix:
            # Sử dụng context flag để bypass timezone fix khi đang fix
            users_to_fix.with_context(skip_timezone_fix=True).sudo().write({'tz': DEFAULT_TIMEZONE})
            _logger.info(f"Timezone auto-fixed to '{DEFAULT_TIMEZONE}' for {len(users_to_fix)} user(s)")
        
        return result

    @api.model
    def _fix_timezone(self, timezone):
        """
        Fix timezone: convert Asia/Saigon thành Asia/Ho_Chi_Minh
        Nếu timezone là None hoặc empty, trả về DEFAULT_TIMEZONE
        """
        if not timezone:
            return DEFAULT_TIMEZONE
        
        # Convert Asia/Saigon thành Asia/Ho_Chi_Minh
        if timezone == OLD_TIMEZONE:
            return DEFAULT_TIMEZONE
        
        # Trả về timezone hiện tại nếu đã đúng
        return timezone


    @api.model
    def _update_all_users_timezone(self):
        """
        Method để update tất cả users có timezone sai về Asia/Ho_Chi_Minh
        Có thể gọi từ cron job hoặc manually
        """
        users_with_wrong_tz = self.search([
            '|',
            ('tz', '=', OLD_TIMEZONE),
            ('tz', '=', False),
        ])
        
        if users_with_wrong_tz:
            # Sử dụng context flag để bypass timezone fix khi đang fix
            users_with_wrong_tz.with_context(skip_timezone_fix=True).write({'tz': DEFAULT_TIMEZONE})
            _logger.info(f"Fixed timezone for {len(users_with_wrong_tz)} users")
            return len(users_with_wrong_tz)
        return 0

