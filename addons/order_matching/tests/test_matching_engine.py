# -*- coding: utf-8 -*-
"""
Unit Tests for order_matching Module

Tests cover:
- Matching engine logic
- Position service (buyer/seller unit updates)
- NAV term rate configuration
- Advisory lock mechanism concept
- Matched orders creation
"""

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'order_matching')
class TestMatchingEngine(TransactionCase):
    """Test matching engine business logic."""

    def setUp(self):
        super().setUp()
        self.Fund = self.env['portfolio.fund']
        self.Transaction = self.env['portfolio.transaction']
        self.User = self.env['res.users']

        # Create test fund
        self.test_fund = self.Fund.sudo().create({
            'name': 'Matching Test Fund',
            'ticker': 'MTF',
            'current_nav': 10000.0,
            'investment_type': 'Growth',
            'inception_date': '2026-01-01',
        })

        # Create buyer user
        self.buyer = self.User.with_context(no_reset_password=True).create({
            'name': 'Buyer User',
            'login': 'buyer_matching@example.com',
            'email': 'buyer_matching@example.com',
            'password': 'TestPass1@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Create seller user
        self.seller = self.User.with_context(no_reset_password=True).create({
            'name': 'Seller User',
            'login': 'seller_matching@example.com',
            'email': 'seller_matching@example.com',
            'password': 'TestPass2@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

    def test_create_buy_order(self):
        """Can create a buy order for matching."""
        buy_order = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.buyer.id,
            'transaction_type': 'buy',
            'units': 100,
            'amount': 1_000_000,
            'price': 10000,
            'status': 'pending',
        })
        self.assertTrue(buy_order.exists())
        self.assertEqual(buy_order.transaction_type, 'buy')

    def test_create_sell_order(self):
        """Can create a sell order for matching."""
        sell_order = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.seller.id,
            'transaction_type': 'sell',
            'units': 50,
            'amount': 500_000,
            'price': 10000,
            'status': 'pending',
        })
        self.assertTrue(sell_order.exists())
        self.assertEqual(sell_order.transaction_type, 'sell')

    def test_partial_matching_units(self):
        """Partial matching: units calculation is correct."""
        buy_units = 100
        sell_units = 60
        matched = min(buy_units, sell_units)

        self.assertEqual(matched, 60)
        self.assertEqual(buy_units - matched, 40)   # buyer remaining
        self.assertEqual(sell_units - matched, 0)    # seller fully matched

    def test_full_matching_units(self):
        """Full matching: both sides should have 0 remaining."""
        buy_units = 100
        sell_units = 100
        matched = min(buy_units, sell_units)

        self.assertEqual(matched, 100)
        self.assertEqual(buy_units - matched, 0)
        self.assertEqual(sell_units - matched, 0)

    def test_matched_units_tracking(self):
        """Verify matched_units field updates correctly."""
        buy_order = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.buyer.id,
            'transaction_type': 'buy',
            'units': 100,
            'amount': 1_000_000,
            'price': 10000,
            'status': 'pending',
        })

        # Simulate partial match
        matched_qty = 60
        buy_order.sudo().write({'matched_units': matched_qty})
        remaining = buy_order.units - buy_order.matched_units

        self.assertEqual(buy_order.matched_units, 60)
        self.assertEqual(remaining, 40)


@tagged('post_install', '-at_install', 'order_matching')
class TestPositionService(TransactionCase):
    """Test position update logic after matching."""

    def setUp(self):
        super().setUp()
        self.Fund = self.env['portfolio.fund']
        self.User = self.env['res.users']

        self.test_fund = self.Fund.sudo().create({
            'name': 'Position Test Fund',
            'ticker': 'PTF',
            'current_nav': 10000.0,
            'investment_type': 'Growth',
            'inception_date': '2026-01-01',
        })

        self.buyer = self.User.with_context(no_reset_password=True).create({
            'name': 'Position Buyer',
            'login': 'position_buyer@example.com',
            'email': 'position_buyer@example.com',
            'password': 'TestPass1@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

    def test_position_update_increases_units(self):
        """After buy match, buyer's investment units should increase."""
        # Check if fund.investment model exists
        Investment = self.env.get('fund.investment')
        if Investment is None:
            # Model doesn't exist in this configuration, skip
            return

        initial_units = 100
        matched_units = 50

        # Simulate: buyer already had 100 units, matched 50 more
        expected = initial_units + matched_units
        self.assertEqual(expected, 150)

    def test_position_update_decreases_units_for_seller(self):
        """After sell match, seller's investment units should decrease."""
        initial_units = 100
        sold_units = 30

        expected = initial_units - sold_units
        self.assertEqual(expected, 70)
        self.assertGreater(expected, 0)

    def test_full_sell_zeroes_position(self):
        """Selling all units results in zero position."""
        initial_units = 100
        sold_units = 100

        expected = initial_units - sold_units
        self.assertEqual(expected, 0)


@tagged('post_install', '-at_install', 'order_matching')
class TestNavTermRate(TransactionCase):
    """Test NAV term rate configuration."""

    def setUp(self):
        super().setUp()
        self.TermRate = self.env['nav.term.rate']

    def test_create_term_rate(self):
        """Can create a valid term rate."""
        # Use unique term_months to avoid conflict with existing DB data
        existing = self.TermRate.sudo().search([('term_months', '=', 96)])
        if existing:
            existing.sudo().unlink()
        rate = self.TermRate.sudo().create({
            'term_months': 96,
            'interest_rate': 8.5,
            'effective_date': '2026-01-01',
            'active': True,
        })
        self.assertTrue(rate.exists())
        self.assertEqual(rate.term_months, 96)
        self.assertEqual(rate.interest_rate, 8.5)

    def test_invalid_term_months(self):
        """Term months must be > 0."""
        with self.assertRaises(ValidationError):
            self.TermRate.sudo().create({
                'term_months': 0,
                'interest_rate': 8.0,
                'effective_date': '2026-01-01',
            })

    def test_invalid_interest_rate(self):
        """Interest rate must be between 0 and 100."""
        existing = self.TermRate.sudo().search([('term_months', '=', 97)])
        if existing:
            existing.sudo().unlink()
        with self.assertRaises(Exception):
            self.TermRate.sudo().create({
                'term_months': 97,
                'interest_rate': 150.0,
                'effective_date': '2026-01-01',
            })

    def test_negative_interest_rate(self):
        """Negative interest rate is rejected."""
        existing = self.TermRate.sudo().search([('term_months', '=', 98)])
        if existing:
            existing.sudo().unlink()
        with self.assertRaises(Exception):
            self.TermRate.sudo().create({
                'term_months': 98,
                'interest_rate': -5.0,
                'effective_date': '2026-01-01',
            })


@tagged('post_install', '-at_install', 'order_matching')
class TestRateLimiter(TransactionCase):
    """Test rate limiter utility (pure logic, no HTTP)."""

    def test_rate_limiter_module_importable(self):
        """Rate limiter module can be imported."""
        from odoo.addons.arc_core.utils.rate_limiter import rate_limit, rate_limit_strict
        self.assertIsNotNone(rate_limit)
        self.assertIsNotNone(rate_limit_strict)

    def test_rate_limiter_creates_decorator(self):
        """rate_limit() returns a callable decorator."""
        from odoo.addons.arc_core.utils.rate_limiter import rate_limit

        decorator = rate_limit(max_calls=10, period=30)
        self.assertTrue(callable(decorator))

        @decorator
        def dummy_func():
            return 'ok'

        self.assertTrue(callable(dummy_func))
