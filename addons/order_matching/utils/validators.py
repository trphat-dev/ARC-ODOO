# -*- coding: utf-8 -*-
"""
Validators for Order Matching Module - Chuẩn Sàn Chứng Chỉ Quỹ Quốc Tế
"""

# -*- coding: utf-8 -*-

from odoo import _
from odoo.exceptions import ValidationError
from datetime import datetime, time
from . import const
import logging

_logger = logging.getLogger(__name__)


class OrderValidator:
    """Validator cho Order Matching - Chuẩn Sàn Chứng Chỉ Quỹ Quốc Tế"""
    
    @staticmethod
    def validate_status_transition(current_status, new_status):
        """
        Validate chuyển đổi trạng thái lệnh
        
        Args:
            current_status: Trạng thái hiện tại
            new_status: Trạng thái mới
            
        Returns:
            bool: True nếu có thể chuyển đổi
            
        Raises:
            ValidationError: Nếu không thể chuyển đổi
        """
        if current_status == new_status:
            return True
        
        valid_transitions = const.VALID_STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in valid_transitions:
            raise ValidationError(_(const.ERROR_INVALID_STATUS_TRANSITION) % (current_status, new_status))
        
        return True
    
    @staticmethod
    def validate_matching_conditions(buy_order, sell_order):
        """
        Validate điều kiện khớp lệnh theo chuẩn sàn chứng chỉ quỹ quốc tế
        
        Args:
            buy_order: Lệnh mua (portfolio.transaction record)
            sell_order: Lệnh bán (portfolio.transaction record)
            
        Returns:
            tuple: (can_match: bool, reason: str)
        """
        # Kiểm tra khác user
        if const.MATCH_CONDITION_DIFFERENT_USER:
            if buy_order.user_id.id == sell_order.user_id.id:
                return False, _("Không thể khớp lệnh của cùng một user")
        
        # Kiểm tra trạng thái pending
        if const.MATCH_CONDITION_PENDING_STATUS:
            if buy_order.status != const.ORDER_STATUS_PENDING:
                return False, _("Lệnh mua phải ở trạng thái 'pending'")
            if sell_order.status != const.ORDER_STATUS_PENDING:
                return False, _("Lệnh bán phải ở trạng thái 'pending'")
        
        # Kiểm tra điều kiện giá: buy_price >= sell_price
        buy_price = float(buy_order.price or 0)
        sell_price = float(sell_order.price or 0)
        if buy_price < sell_price:
            return False, _("Điều kiện giá không thỏa mãn: buy_price (%s) < sell_price (%s)") % (buy_price, sell_price)
        
        # Kiểm tra remaining_units > 0
        buy_remaining = float(buy_order.remaining_units or 0)
        sell_remaining = float(sell_order.remaining_units or 0)
        if buy_remaining <= 0:
            return False, _("Lệnh mua đã hết số lượng còn lại")
        if sell_remaining <= 0:
            return False, _("Lệnh bán đã hết số lượng còn lại")
        
        return True, _("Có thể khớp")
    
    @staticmethod
    def validate_order_before_match(order):
        """
        Validate lệnh trước khi khớp
        
        Args:
            order: portfolio.transaction record
            
        Returns:
            bool: True nếu hợp lệ
            
        Raises:
            ValidationError: Nếu không hợp lệ
        """
        # Kiểm tra trạng thái
        if order.status != const.ORDER_STATUS_PENDING:
            raise ValidationError(_(const.ERROR_INVALID_ORDER_STATUS))
        
        # Kiểm tra remaining_units > 0
        remaining = float(order.remaining_units or 0)
        if remaining <= 0:
            raise ValidationError(_("Lệnh đã hết số lượng còn lại"))
        
        # Kiểm tra giá
        price = float(order.price or 0)
        if price <= 0:
            raise ValidationError(_("Giá lệnh không hợp lệ"))
        
        # Kiểm tra số lượng
        units = float(order.units or 0)
        if units <= 0:
            raise ValidationError(_("Số lượng lệnh không hợp lệ"))
        
        return True
    
    @staticmethod
    def validate_match_quantity(match_quantity, buy_remaining, sell_remaining):
        """
        Validate số lượng khớp
        
        Args:
            match_quantity: Số lượng khớp
            buy_remaining: Số lượng còn lại của lệnh mua
            sell_remaining: Số lượng còn lại của lệnh bán
            
        Returns:
            float: Số lượng khớp đã được validate
            
        Raises:
            ValidationError: Nếu số lượng khớp không hợp lệ
        """
        match_qty = float(match_quantity or 0)
        buy_rem = float(buy_remaining or 0)
        sell_rem = float(sell_remaining or 0)
        
        # Kiểm tra số lượng khớp > 0
        if match_qty <= 0:
            raise ValidationError(_("Số lượng khớp phải lớn hơn 0"))
        
        # Kiểm tra số lượng khớp <= min(buy_remaining, sell_remaining)
        max_match = min(buy_rem, sell_rem)
        if match_qty > max_match:
            raise ValidationError(_(const.ERROR_INSUFFICIENT_REMAINING) % (max_match, match_qty))
        
        # Kiểm tra số lượng khớp >= min_match_quantity
        if match_qty < const.MIN_MATCH_QUANTITY:
            raise ValidationError(_("Số lượng khớp phải >= %s") % const.MIN_MATCH_QUANTITY)
        
        return match_qty


class UserValidator:
    """Validator cho User - Chuẩn Sàn Chứng Chỉ Quỹ Quốc Tế"""
    
    @staticmethod
    def validate_user_permission(user, action):
        """
        Validate quyền của user
        
        Args:
            user: res.users record
            action: Hành động cần kiểm tra ('create_order', 'cancel_order', 'match_orders', etc.)
            
        Returns:
            bool: True nếu có quyền
            
        Raises:
            ValidationError: Nếu không có quyền
        """
        if not user:
            raise ValidationError(_("User không tồn tại"))
        
        # Có thể mở rộng thêm kiểm tra quyền theo action
        # Ví dụ: kiểm tra user có quyền tạo lệnh, hủy lệnh, khớp lệnh, etc.
        
        return True
    
    @staticmethod
    def validate_user_type(user, expected_type):
        """
        Validate loại user
        
        Args:
            user: res.users record
            expected_type: Loại user mong đợi ('investor', 'market_maker')
            
        Returns:
            bool: True nếu đúng loại
            
        Raises:
            ValidationError: Nếu không đúng loại
        """
        if not user:
            raise ValidationError(_("User không tồn tại"))
        
        # Có thể mở rộng thêm kiểm tra loại user
        # Ví dụ: kiểm tra user có phải là market_maker không
        
        return True

