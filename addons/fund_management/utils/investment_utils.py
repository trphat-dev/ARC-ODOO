# Copyright 2024
# License AGPL-3.0 or later

"""
Investment operation utilities
"""
import logging
from psycopg2 import IntegrityError

from . import mround
from .constants import (
    MROUND_STEP, DEFAULT_DAYS_PER_MONTH,
    INVESTMENT_STATUS_ACTIVE, INVESTMENT_STATUS_CLOSED
)

_logger = logging.getLogger(__name__)


class InvestmentHelper:
    """Helper class for investment operations"""
    
    @staticmethod
    def compute_days(term_months=None, days=None):
        """Calculate days from term_months or days"""
        if days and days > 0:
            return max(1, int(days))
        if term_months and term_months > 0:
            return max(1, int(term_months * DEFAULT_DAYS_PER_MONTH))
        return 1
    
    @staticmethod
    def compute_sell_value(order_value, interest_rate_percent, term_months=None, days=None):
        """Calculate sell value based on interest rate and term"""
        order_value = float(order_value or 0.0)
        rate = float(interest_rate_percent or 0.0)
        d = InvestmentHelper.compute_days(term_months=term_months, days=days)
        return order_value * (rate / 100.0) / 365.0 * d + order_value
    
    @staticmethod
    def upsert_investment(env, user_id, fund_id, units_change, amount_change=None, transaction_type='buy'):
        """
        Create or update investment
        
        Args:
            env: Odoo environment
            user_id: User ID
            fund_id: Fund ID
            units_change: Units to add/subtract
            amount_change: Amount to add (optional, for buy)
            transaction_type: 'buy' or 'sell'
            
        Returns:
            investment: Created or updated investment record
        """
        Investment = env['portfolio.investment'].sudo()
        Fund = env['portfolio.fund'].sudo().browse(fund_id)
        
        # Get price from inventory or fund NAV
        price_from_inventory = InvestmentHelper._get_ccq_price_from_inventory(env, fund_id)
        if price_from_inventory <= 0:
            price_from_inventory = Fund.current_nav or 0.0
        
        # MROUND price
        current_nav_rounded = mround.mround(price_from_inventory, MROUND_STEP)
        
        # Search for existing investment
        investment = Investment.search([
            ('user_id', '=', user_id),
            ('fund_id', '=', fund_id)
        ], limit=1)
        
        if not investment:
            if transaction_type == 'buy':
                # Create new investment
                create_vals = {
                    'user_id': user_id,
                    'fund_id': fund_id,
                    'units': units_change,
                    'amount': amount_change if amount_change else (units_change * current_nav_rounded),
                    'status': INVESTMENT_STATUS_ACTIVE,
                }
                
                # MROUND amount if provided
                if amount_change:
                    create_vals['amount'] = mround.mround(amount_change, MROUND_STEP)
                else:
                    create_vals['amount'] = mround.mround(create_vals['amount'], MROUND_STEP)
                
                try:
                    with env.cr.savepoint():
                        return Investment.create(create_vals)
                except IntegrityError:
                    # Fallback: search again if concurrent creation
                    investment = Investment.search([
                        ('user_id', '=', user_id),
                        ('fund_id', '=', fund_id)
                    ], limit=1)
                    if not investment:
                        raise
        
        # Update existing investment
        old_units = investment.units or 0.0
        old_amount = investment.amount or 0.0
        
        if transaction_type == 'buy':
            new_units = old_units + units_change
            if amount_change:
                # Use provided amount
                new_amount = mround.mround(old_amount + amount_change, MROUND_STEP)
            else:
                # Calculate from units
                new_amount = mround.mround(new_units * current_nav_rounded, MROUND_STEP)
        else:  # sell
            new_units = max(0.0, old_units - units_change)
            if old_units > 0:
                unit_price = old_amount / old_units
                new_amount = mround.mround(new_units * unit_price, MROUND_STEP)
            else:
                new_amount = 0.0
        
        investment.write({
            'units': new_units,
            'amount': new_amount,
            'status': INVESTMENT_STATUS_CLOSED if new_units <= 0 else INVESTMENT_STATUS_ACTIVE,
        })
        
        return investment
    
    @staticmethod
    def _get_ccq_price_from_inventory(env, fund_id):
        """Get CCQ price from inventory"""
        try:
            from datetime import datetime
            today = datetime.now().date()
            
            Inventory = env['nav.daily.inventory'].sudo()
            inv = Inventory.search([
                ('fund_id', '=', fund_id),
                ('inventory_date', '=', today)
            ], limit=1)
            
            if inv and inv.opening_avg_price:
                return inv.opening_avg_price
            return 0.0
        except Exception as e:
            _logger.warning(f"Failed to get CCQ price from inventory: {e}")
            return 0.0

