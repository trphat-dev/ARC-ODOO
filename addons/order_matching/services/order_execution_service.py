# -*- coding: utf-8 -*-
"""
Order Execution Service - Tạo Execution Records
Service layer để tạo và quản lý execution records (matched orders)
"""

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import logging
from typing import Dict, Optional, List
from datetime import datetime

_logger = logging.getLogger(__name__)


class OrderExecutionService:
    """
    Order Execution Service - Tạo Execution Records
    
    Responsibilities:
    1. Create execution records (addExecution)
    2. Link executions to orders
    3. Validate execution data
    4. Handle execution state
    """
    
    def __init__(self, env):
        """
        Initialize the service with Odoo environment
        
        Args:
            env: Odoo environment (odoo.api.Environment)
        """
        self.env = env
        self.MatchedOrders = env['transaction.matched.orders']
    
    def add_execution(self, buy_order, sell_order, matched_quantity: float, 
                     matched_price: float, context: Optional[Dict] = None):
        """
        Tạo execution record (matched order pair)
        
        Args:
            buy_order: portfolio.transaction record (buy order)
            sell_order: portfolio.transaction record (sell order)
            matched_quantity: Số lượng đã khớp
            matched_price: Giá khớp
            context: Context bổ sung
            
        Returns:
            transaction.matched.orders: Execution record đã được tạo
        """
        try:
            # Validate inputs
            self._validate_execution_data(buy_order, sell_order, matched_quantity, matched_price)
            
            # Determine execution status
            execution_status = self._determine_execution_status(buy_order, sell_order)
            
            # QUAN TRỌNG: Không generate execution code thủ công
            # Name sẽ được tự động tạo bởi sequence trong create() method với format HDC-DDMMYY/STT
            
            # Prepare execution values
            execution_vals = {
                'buy_order_id': buy_order.id,
                'sell_order_id': sell_order.id,
                'matched_quantity': matched_quantity,
                'matched_price': matched_price,
                'fund_id': buy_order.fund_id.id if buy_order.fund_id else (sell_order.fund_id.id if sell_order.fund_id else False),
                'status': execution_status,
            }
            
            # Add context data if provided
            if context:
                # Merge context into execution_vals if needed
                pass
            
            # Create execution record
            execution = self.MatchedOrders.sudo().create(execution_vals)
            
            _logger.info(
                "[EXECUTION SERVICE] Created execution %s (%s): Buy %s x Sell %s, Qty=%s, Price=%s",
                execution.id, execution.name, buy_order.id, sell_order.id,
                matched_quantity, matched_price
            )
            
            return execution
            
        except Exception as e:
            _logger.error("[EXECUTION SERVICE] Error creating execution: %s", str(e))
            raise ValidationError(_("Lỗi khi tạo execution record: %s") % str(e))
    
    def _validate_execution_data(self, buy_order, sell_order, matched_quantity: float, matched_price: float):
        """
        Validate execution data
        
        Args:
            buy_order: Buy order record
            sell_order: Sell order record
            matched_quantity: Matched quantity
            matched_price: Matched price
        """
        if not buy_order or not buy_order.exists():
            raise ValidationError(_("Buy order không tồn tại"))
        
        if not sell_order or not sell_order.exists():
            raise ValidationError(_("Sell order không tồn tại"))
        
        if matched_quantity <= 0:
            raise ValidationError(_("Số lượng khớp phải lớn hơn 0"))
        
        if matched_price <= 0:
            raise ValidationError(_("Giá khớp phải lớn hơn 0"))
        
        # Validate same fund
        if buy_order.fund_id and sell_order.fund_id:
            if buy_order.fund_id.id != sell_order.fund_id.id:
                raise ValidationError(_("Buy và Sell order phải cùng quỹ"))
        
        # Validate different users
        if buy_order.user_id and sell_order.user_id:
            if buy_order.user_id.id == sell_order.user_id.id:
                raise ValidationError(_("Buy và Sell order không thể cùng user"))
    
    def _determine_execution_status(self, buy_order, sell_order) -> str:
        """
        Xác định status của execution.
        
        Lưu ý nghiệp vụ:
        - Mỗi execution là một lần khớp cụ thể giữa 1 lệnh mua và 1 lệnh bán.
        - Hai lệnh gốc có thể được khớp qua nhiều execution khác nhau và
          hiếm khi cả 2 về 0 cùng một lúc.
        
        Vì vậy:
        - Status 'done' được hiểu là bản thân execution đó đã được ghi nhận xong,
          KHÔNG phụ thuộc việc cả 2 lệnh gốc đã về 0 hay chưa.
        - Trạng thái của từng lệnh (pending/completed) sẽ được quản lý riêng
          trên model 'portfolio.transaction' thông qua remaining_units.
        
        Args:
            buy_order: Buy order record
            sell_order: Sell order record
            
        Returns:
            str: Execution status
        """
        # Mỗi execution được coi là hoàn tất ngay khi tạo → luôn 'done'
        return 'done'
    
    def _generate_execution_code(self, buy_order, sell_order) -> str:
        """
        Generate unique execution code
        QUAN TRỌNG: Không sử dụng method này nữa - để sequence tự động tạo format HDC-DDMMYY/STT
        
        Args:
            buy_order: Buy order record
            sell_order: Sell order record
            
        Returns:
            str: Execution code (sẽ được sequence tự động tạo)
        """
        # Không tạo code thủ công - để sequence tự động tạo format HDC-DDMMYY/STT
        # Method này được giữ lại để tương thích nhưng không được sử dụng
        return ''

