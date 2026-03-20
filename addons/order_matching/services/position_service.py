# -*- coding: utf-8 -*-
"""
Position Service - Update Portfolio Positions
Service layer to update positions after order matching
"""

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import logging
from typing import Dict, Optional, List

_logger = logging.getLogger(__name__)


class PositionService:
    """
    Position Service - Update Portfolio Positions
    
    Responsibilities:
    1. Update positions after order execution
    2. Calculate position changes
    3. Handle position updates for buy/sell orders
    """
    
    def __init__(self, env):
        """
        Initialize the service with Odoo environment
        
        Args:
            env: Odoo environment (odoo.api.Environment)
        """
        self.env = env
    
    def update_positions(self, buy_order, sell_order, matched_quantity: float, 
                        matched_price: float) -> bool:
        """
        Update positions after order matching
        
        Args:
            buy_order: portfolio.transaction record (buy order)
            sell_order: portfolio.transaction record (sell order)
            matched_quantity: Matched quantity
            matched_price: Matched price
            
        Returns:
            bool: True if update successful
        """
        try:
            # Validate inputs
            if not buy_order or not buy_order.exists():
                raise ValidationError(_("Buy order does not exist"))
            
            if not sell_order or not sell_order.exists():
                raise ValidationError(_("Sell order does not exist"))
            
            if matched_quantity <= 0:
                raise ValidationError(_("Matched quantity must be greater than 0"))
            
            Investment = self.env['portfolio.investment'].sudo()
            matched_amount = matched_quantity * matched_price
            
            # Update buyer position: add units
            if buy_order.user_id:
                buyer_inv = Investment.search([
                    ('user_id', '=', buy_order.user_id.id),
                    ('fund_id', '=', buy_order.fund_id.id),
                ], limit=1)
                
                if buyer_inv:
                    buyer_inv.write({
                        'units': buyer_inv.units + matched_quantity,
                        'amount': buyer_inv.amount + matched_amount,
                    })
                else:
                    Investment.create({
                        'user_id': buy_order.user_id.id,
                        'fund_id': buy_order.fund_id.id,
                        'units': matched_quantity,
                        'amount': matched_amount,
                        'investment_type': 'fund_certificate',
                        'status': 'active',
                    })
            
            # Update seller position: subtract units
            if sell_order.user_id:
                seller_inv = Investment.search([
                    ('user_id', '=', sell_order.user_id.id),
                    ('fund_id', '=', sell_order.fund_id.id),
                ], limit=1)
                
                if seller_inv:
                    new_units = max(0.0, seller_inv.units - matched_quantity)
                    new_amount = max(0.0, seller_inv.amount - matched_amount)
                    if new_units <= 0:
                        seller_inv.write({
                            'units': 0,
                            'amount': 0,
                            'status': 'closed',
                        })
                    else:
                        seller_inv.write({
                            'units': new_units,
                            'amount': new_amount,
                        })
            
            _logger.info(
                "[POSITION SERVICE] Updated positions: Buy %s (+%s units), Sell %s (-%s units), Price=%s",
                buy_order.id, matched_quantity, sell_order.id, matched_quantity, matched_price
            )
            
            return True
            
        except Exception as e:
            _logger.error("[POSITION SERVICE] Error updating positions: %s", str(e), exc_info=True)
            # Don't raise - position update failure shouldn't block execution
            return False


