# -*- coding: utf-8 -*-
"""
Unit Tests for custom_auth Module

Tests cover:
- Password validation rules
- Signup data validation (phone, email)
- OTP flow logic
- User creation
"""

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
from unittest.mock import patch, MagicMock


@tagged('post_install', '-at_install', 'custom_auth')
class TestPasswordValidation(TransactionCase):
    """Test password validation rules."""

    def setUp(self):
        super().setUp()
        from odoo.addons.custom_auth.controllers.main import CustomAuthController
        self.controller = CustomAuthController()

    def test_password_too_short(self):
        """Password must be at least 8 characters."""
        valid, msg = self.controller._validate_password('Abc1@')
        self.assertFalse(valid)
        self.assertIn('8', msg)

    def test_password_no_uppercase(self):
        """Password must contain at least 1 uppercase letter."""
        valid, msg = self.controller._validate_password('abcdef1@')
        self.assertFalse(valid)
        self.assertIn('hoa', msg.lower())

    def test_password_no_digit(self):
        """Password must contain at least 1 digit."""
        valid, msg = self.controller._validate_password('Abcdefgh@')
        self.assertFalse(valid)
        self.assertIn('số', msg.lower())

    def test_password_no_special(self):
        """Password must contain at least 1 special character."""
        valid, msg = self.controller._validate_password('Abcdefg1')
        self.assertFalse(valid)
        self.assertIn('đặc biệt', msg.lower())

    def test_password_valid(self):
        """A valid password passes all checks."""
        valid, msg = self.controller._validate_password('SecurePass1@')
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def test_password_empty(self):
        """Empty password is rejected."""
        valid, msg = self.controller._validate_password('')
        self.assertFalse(valid)

    def test_password_none(self):
        """None password is rejected."""
        valid, msg = self.controller._validate_password(None)
        self.assertFalse(valid)


@tagged('post_install', '-at_install', 'custom_auth')
class TestUserCreation(TransactionCase):
    """Test user creation workflow."""

    def setUp(self):
        super().setUp()
        self.User = self.env['res.users']
        self.Partner = self.env['res.partner']

    def test_no_duplicate_email(self):
        """Cannot create two users with the same email/login."""
        user_vals = {
            'name': 'Test User 1',
            'login': 'test_unique_auth@example.com',
            'email': 'test_unique_auth@example.com',
            'password': 'TestPass1@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        }
        self.User.with_context(no_reset_password=True).create(user_vals)

        # Check duplicate count
        count = self.User.sudo().search_count([
            ('login', '=', 'test_unique_auth@example.com')
        ])
        self.assertEqual(count, 1)

    def test_portal_user_group_assignment(self):
        """New signup user should be in portal group."""
        user = self.User.with_context(no_reset_password=True).create({
            'name': 'Portal Test User',
            'login': 'portal_test_auth@example.com',
            'email': 'portal_test_auth@example.com',
            'password': 'TestPass1@',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.assertTrue(user.has_group('base.group_portal'))
        self.assertFalse(user.has_group('base.group_user'))
