# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AIChatbotGlobalConfig(models.Model):
    """Global Chatbot configuration shared by all users"""
    _name = 'ai.chatbot.global.config'
    _description = 'AI Chatbot Global Configuration'
    _order = 'is_default desc, create_date desc'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        default=lambda self: _('Chatbot Configuration')
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    is_default = fields.Boolean(
        string='Default Configuration',
        default=False,
        help='Only one configuration can be marked as default'
    )

    provider = fields.Selection([
        ('openrouter', 'OpenRouter'),
    ], string='Provider', default='openrouter', required=True)

    api_key = fields.Char(
        string='API Key',
        required=True,
        help='API key provided by the chatbot provider'
    )

    model_name = fields.Char(
        string='Default Model',
        required=True,
        default='xiaomi/mimo-v2-flash:free',
        help='Model identifier on OpenRouter (e.g., xiaomi/mimo-v2-flash:free)'
    )

    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_single_default()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._ensure_single_default()
        return res

    def _ensure_single_default(self):
        """Ensure only one config remains default"""
        default_records = self.search([('is_default', '=', True)], order='create_date asc')
        if len(default_records) > 1:
            # Keep the most recent as default, unset others
            for rec in default_records[:-1]:
                rec.is_default = False

    @api.constrains('is_default')
    def _check_single_default(self):
        for record in self:
            if record.is_default:
                duplicates = self.search([
                    ('is_default', '=', True),
                    ('id', '!=', record.id),
                ])
                if duplicates:
                    raise ValidationError(_('Only one Chatbot configuration can be default.'))

    @api.model
    def get_active_config(self):
        """Return the active/default configuration"""
        config = self.search([
            ('active', '=', True),
            ('is_default', '=', True),
        ], limit=1)
        if not config:
            config = self.search([('active', '=', True)], order='create_date desc', limit=1)
        return config

