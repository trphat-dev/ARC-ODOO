# -*- coding: utf-8 -*-
"""
Order Service - Quản lý Order Lifecycle
Service layer để quản lý vòng đời của order theo chuẩn quốc tế
"""

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
import logging
from typing import Dict, Optional, List
from ..utils import const, validators

_logger = logging.getLogger(__name__)


class OrderService:
    """
    Order Service - Quản lý Order Lifecycle
    
    Responsibilities:
    1. Add new orders (addOrder)
    2. Update order status (updateStatus)
    3. Validate order state transitions
    4. Handle order state changes
    """
    
    def __init__(self, env):
        """
        Initialize the service with Odoo environment
        
        Args:
            env: Odoo environment (odoo.api.Environment)
        """
        self.env = env
        self.Transaction = env['portfolio.transaction']
    
    def add_order(self, order_vals: Dict):
        """
        Thêm order mới vào hệ thống
        
        Args:
            order_vals: Dictionary chứa các giá trị để tạo order
            
        Returns:
            portfolio.transaction: Order record đã được tạo
        """
        try:
            # Validate order values
            self._validate_order_vals(order_vals)
            
            # Tạo order
            order = self.Transaction.sudo().create(order_vals)
            
            _logger.info("[ORDER SERVICE] Created order %s (%s)", order.id, order.name)
            
            return order
            
        except Exception as e:
            _logger.error("[ORDER SERVICE] Error adding order: %s", str(e))
            raise ValidationError(_("Lỗi khi tạo order: %s") % str(e))
    
    def update_status(self, order, new_status: str, matched_units: Optional[float] = None, 
                     remaining_units: Optional[float] = None, context: Optional[Dict] = None) -> bool:
        """
        Cập nhật status của order
        
        LƯU Ý: matched_units là computed field từ executions, không nên truyền vào.
        Parameter matched_units được giữ lại để tương thích nhưng sẽ bị bỏ qua.
        """
        """
        Cập nhật status của order
        
        Args:
            order: portfolio.transaction record
            new_status: Trạng thái mới ('pending', 'completed', 'cancelled')
            matched_units: Số lượng đã khớp (nếu có)
            remaining_units: Số lượng còn lại (nếu có)
            context: Context bổ sung
            
        Returns:
            bool: True nếu cập nhật thành công
        """
        try:
            order.ensure_one()
            
            # Validate status transition
            if not self._can_transition_status(order.status, new_status):
                raise ValidationError(
                    _("Không thể chuyển từ status '%s' sang '%s'") % (order.status, new_status)
                )
            
            # Prepare update values
            update_vals = {
                'status': new_status,
            }
            
            # QUAN TRỌNG: matched_units là computed field từ executions
            # KHÔNG được cập nhật trực tiếp - sẽ tự động tính từ execution records
            # if matched_units is not None:
            #     update_vals['matched_units'] = matched_units  # REMOVED - computed field
            
            # remaining_units cũng là computed field từ units - matched_units
            # Chỉ cập nhật ccq_remaining_to_match nếu cần (để tương thích)
            if remaining_units is not None:
                update_vals['ccq_remaining_to_match'] = remaining_units
            
            # Update is_matched - sẽ được tính sau khi recompute matched_units và remaining_units
            # Force recompute để đảm bảo tính toán chính xác từ executions
            # matched_units = tổng matched_quantity từ executions (computed)
            # remaining_units = units - matched_units (computed)
            order.invalidate_recordset(['matched_units', 'remaining_units'])
            
            # Tính lại remaining sau khi invalidate để set is_matched
            if remaining_units is not None:
                # Sử dụng remaining_units được truyền vào (tạm thời) để tính is_matched
                update_vals['is_matched'] = (remaining_units <= 0)
            else:
                # Nếu không truyền remaining_units, tính từ units - matched_units (sau khi recompute)
                remaining_calculated = max(0.0, float(order.units or 0) - float(order.matched_units or 0))
                update_vals['is_matched'] = (remaining_calculated <= 0)
            
            # Apply context if provided (merge into write context)
            write_context = {}
            if context:
                # Extract bypass_investment_update and other context flags
                if 'bypass_investment_update' in context:
                    write_context['bypass_investment_update'] = context.pop('bypass_investment_update')
                # Merge remaining context into update_vals
                update_vals.update({k: v for k, v in context.items() if k not in ['bypass_investment_update']})
            
            # Update order with context
            if write_context:
                order.with_context(**write_context).sudo().write(update_vals)
            else:
                order.with_context(bypass_investment_update=True).sudo().write(update_vals)
            
            _logger.info(
                "[ORDER SERVICE] Updated order %s status: %s -> %s, matched=%s, remaining=%s",
                order.id, order.status, new_status, matched_units, remaining_units
            )
            
            return True
            
        except Exception as e:
            _logger.error("[ORDER SERVICE] Error updating order %s status: %s",
                         order.id if order else 'None', str(e))
            raise
    
    def _validate_order_vals(self, order_vals: Dict):
        """
        Validate order values trước khi tạo - Sử dụng validators chuẩn sàn chứng chỉ quỹ quốc tế
        
        Args:
            order_vals: Dictionary chứa các giá trị order
        """
        required_fields = ['transaction_type', 'units', 'price', 'fund_id']
        for field in required_fields:
            if field not in order_vals or not order_vals[field]:
                raise ValidationError(_("Thiếu trường bắt buộc: %s") % field)
        
        # Validate transaction type
        if order_vals['transaction_type'] not in [const.TRANSACTION_TYPE_BUY, const.TRANSACTION_TYPE_SELL]:
            raise ValidationError(_("Transaction type không hợp lệ: %s") % order_vals['transaction_type'])
        
        # RÀNG BUỘC: Validate xung đột lệnh - User không thể có cả lệnh mua và bán pending cùng lúc cho cùng một quỹ
        transaction_type = order_vals.get('transaction_type')
        user_id = order_vals.get('user_id')
        fund_id = order_vals.get('fund_id')
        
        if transaction_type in ['buy', 'sell'] and user_id and fund_id:
            # Tìm các lệnh pending khác của cùng user, cùng fund
            existing_orders = self.Transaction.search([
                ('user_id', '=', user_id),
                ('status', '=', 'pending'),
                ('transaction_type', 'in', ['buy', 'sell']),
                ('remaining_units', '>', 0),  # Chỉ tính lệnh còn số lượng cần khớp
                ('fund_id', '=', fund_id),
            ])
            
            fund_name = self.env['portfolio.fund'].browse(fund_id).name or _('quỹ này')
            
            # Nếu đang tạo lệnh mua, kiểm tra xem có lệnh bán pending cùng quỹ không
            if transaction_type == 'buy':
                existing_sell = existing_orders.filtered(lambda o: o.transaction_type == 'sell')
                if existing_sell:
                    sell_count = len(existing_sell)
                    raise ValidationError(_(
                        'Không thể thực hiện đặt lệnh mua. '
                        'Nhà đầu tư này đang có %d lệnh bán đang chờ xử lý tại quỹ %s. '
                        'Vui lòng đợi lệnh bán được xử lý xong hoặc hủy lệnh bán trước khi đặt lệnh mua mới.'
                    ) % (sell_count, fund_name))
            
            # Nếu đang tạo lệnh bán, kiểm tra xem có lệnh mua pending cùng quỹ không
            elif transaction_type == 'sell':
                existing_buy = existing_orders.filtered(lambda o: o.transaction_type == 'buy')
                if existing_buy:
                    buy_count = len(existing_buy)
                    raise ValidationError(_(
                        'Không thể thực hiện đặt lệnh bán. '
                        'Nhà đầu tư này đang có %d lệnh mua đang chờ xử lý tại quỹ %s. '
                        'Vui lòng đợi lệnh mua được xử lý xong hoặc hủy lệnh mua trước khi đặt lệnh bán mới.'
                    ) % (buy_count, fund_name))
    
    def _can_transition_status(self, current_status: str, new_status: str) -> bool:
        """
        Kiểm tra xem có thể chuyển từ current_status sang new_status không
        Sử dụng validators chuẩn sàn chứng chỉ quỹ quốc tế
        
        Args:
            current_status: Trạng thái hiện tại
            new_status: Trạng thái mới
            
        Returns:
            bool: True nếu có thể chuyển
        """
        try:
            validators.OrderValidator.validate_status_transition(current_status, new_status)
            return True
        except ValidationError:
            return False

