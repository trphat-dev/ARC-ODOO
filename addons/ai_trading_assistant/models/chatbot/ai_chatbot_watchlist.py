# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AIChatbotWatchlist(models.Model):
    """User's security watchlist for AI signal notifications"""
    _name = 'ai.chatbot.watchlist'
    _description = 'AI Chatbot Watchlist'
    _order = 'create_date desc'
    _rec_name = 'security_id'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        index=True,
    )
    
    security_id = fields.Many2one(
        'ssi.securities',
        string='Security',
        required=True,
        ondelete='cascade',
        index=True,
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
    )
    
    # Denormalized for faster queries
    symbol = fields.Char(
        related='security_id.symbol',
        store=True,
        index=True,
    )
    
    market = fields.Selection(
        related='security_id.market',
        store=True,
    )

    _sql_constraints = [
        ('user_security_unique', 'UNIQUE(user_id, security_id)',
         'Each security can only be added once per user.')
    ]

    @api.model
    def get_user_watchlist(self, user_id=None):
        """Get active watchlist for current or specified user"""
        user_id = user_id or self.env.user.id
        watchlist = self.search([
            ('user_id', '=', user_id),
            ('is_active', '=', True),
        ])
        return [{
            'id': w.id,
            'security_id': w.security_id.id,
            'symbol': w.symbol,
            'market': w.market,
        } for w in watchlist]

    @api.model
    def add_security(self, security_id):
        """Add a security to current user's watchlist"""
        existing = self.search([
            ('user_id', '=', self.env.user.id),
            ('security_id', '=', security_id),
        ], limit=1)
        
        if existing:
            existing.is_active = True
            return existing.id
        
        return self.create({
            'user_id': self.env.user.id,
            'security_id': security_id,
            'is_active': True,
        }).id

    @api.model
    def remove_security(self, security_id):
        """Remove a security from current user's watchlist"""
        watchlist_item = self.search([
            ('user_id', '=', self.env.user.id),
            ('security_id', '=', security_id),
        ], limit=1)
        
        if watchlist_item:
            watchlist_item.is_active = False
            return True
        return False
