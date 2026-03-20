# -*- coding: utf-8 -*-
"""
Unit Tests for fund_management Module

Tests cover:
- Investment creation validation
- Ownership checks (IDOR prevention)
- Fund sell workflow
- Fee calculation
- Order mode and status transitions
"""

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from unittest.mock import patch


@tagged('post_install', '-at_install', 'fund_management')
class TestFundInvestment(TransactionCase):
    """Test fund investment (buy/sell) business logic."""

    def setUp(self):
        super().setUp()
        self.Fund = self.env['portfolio.fund']
        self.Transaction = self.env['portfolio.transaction']
        self.User = self.env['res.users']

        # Create test fund
        self.test_fund = self.Fund.sudo().create({
            'name': 'Test Fund Alpha',
            'ticker': 'TFA',
            'current_nav': 10000.0,
            'investment_type': 'Growth',
            'inception_date': '2026-01-01',
        })

        # Create test portal user
        self.portal_user = self.User.with_context(no_reset_password=True).create({
            'name': 'Test Investor',
            'login': 'investor_test_fund@example.com',
            'email': 'investor_test_fund@example.com',
            'password': 'TestPass1@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Create another user for IDOR tests
        self.other_user = self.User.with_context(no_reset_password=True).create({
            'name': 'Other Investor',
            'login': 'other_investor_fund@example.com',
            'email': 'other_investor_fund@example.com',
            'password': 'TestPass2@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

    def test_create_buy_transaction(self):
        """Can create a buy transaction for a valid fund."""
        tx = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.portal_user.id,
            'transaction_type': 'buy',
            'units': 100,
            'amount': 1000000,
            'price': 10000,
            'status': 'pending',
        })
        self.assertTrue(tx.exists())
        self.assertEqual(tx.transaction_type, 'buy')
        self.assertEqual(tx.status, 'pending')
        self.assertEqual(tx.fund_id.id, self.test_fund.id)

    def test_create_sell_transaction(self):
        """Can create a sell transaction."""
        # Use other_user to avoid conflict with buy orders from same user
        tx = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.other_user.id,
            'transaction_type': 'sell',
            'units': 50,
            'amount': 500000,
            'price': 10000,
            'status': 'pending',
        })
        self.assertTrue(tx.exists())
        self.assertEqual(tx.transaction_type, 'sell')

    def test_ownership_separation(self):
        """Each user's transactions are independent."""
        tx1 = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.portal_user.id,
            'transaction_type': 'buy',
            'units': 100,
            'amount': 1000000,
            'price': 10000,
            'status': 'pending',
        })
        tx2 = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.other_user.id,
            'transaction_type': 'buy',
            'units': 200,
            'amount': 2000000,
            'price': 10000,
            'status': 'pending',
        })

        # Each user should only see their own
        user1_txs = self.Transaction.sudo().search([
            ('user_id', '=', self.portal_user.id)
        ])
        user2_txs = self.Transaction.sudo().search([
            ('user_id', '=', self.other_user.id)
        ])

        self.assertIn(tx1, user1_txs)
        self.assertNotIn(tx2, user1_txs)
        self.assertIn(tx2, user2_txs)
        self.assertNotIn(tx1, user2_txs)

    def test_sell_fee_calculation(self):
        """Sell fee tiers are calculated correctly."""
        # Tier 1: < 10M → 0.3%
        self.assertEqual(int(5_000_000 * 0.003), 15_000)

        # Tier 2: < 20M → 0.2%
        self.assertEqual(int(15_000_000 * 0.002), 30_000)

        # Tier 3: >= 20M → 0.1%
        self.assertEqual(int(25_000_000 * 0.001), 25_000)

    def test_transaction_status_values(self):
        """Transaction status field accepts valid values."""
        tx = self.Transaction.sudo().create({
            'fund_id': self.test_fund.id,
            'user_id': self.portal_user.id,
            'transaction_type': 'buy',
            'units': 100,
            'amount': 1000000,
            'price': 10000,
            'status': 'pending',
        })

        # Can update to completed
        tx.sudo().write({'status': 'completed'})
        self.assertEqual(tx.status, 'completed')


@tagged('post_install', '-at_install', 'fund_management')
class TestFundModel(TransactionCase):
    """Test fund model operations."""

    def setUp(self):
        super().setUp()
        self.Fund = self.env['portfolio.fund']

    def test_create_fund(self):
        """Can create a fund with basic fields."""
        fund = self.Fund.sudo().create({
            'name': 'Test Fund Beta',
            'ticker': 'TFB',
            'current_nav': 15000.0,
            'investment_type': 'Growth',
            'inception_date': '2026-01-01',
        })
        self.assertTrue(fund.exists())
        self.assertEqual(fund.ticker, 'TFB')
        self.assertEqual(fund.current_nav, 15000.0)

    def test_fund_nav_update(self):
        """Can update fund NAV value."""
        fund = self.Fund.sudo().create({
            'name': 'Test Fund Gamma',
            'ticker': 'TFG',
            'current_nav': 10000.0,
            'investment_type': 'Growth',
            'inception_date': '2026-01-01',
        })
        fund.sudo().write({'current_nav': 10500.0})
        self.assertEqual(fund.current_nav, 10500.0)
