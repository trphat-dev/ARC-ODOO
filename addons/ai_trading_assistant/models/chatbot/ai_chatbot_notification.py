# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AIChatbotNotification(models.Model):
    """Signal notifications for watchlist securities"""
    _name = 'ai.chatbot.notification'
    _description = 'AI Chatbot Signal Notification'
    _order = 'create_date desc'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )
    
    prediction_id = fields.Many2one(
        'ai.prediction',
        string='Prediction',
        required=True,
        ondelete='cascade',
    )
    
    security_id = fields.Many2one(
        'ssi.securities',
        string='Security',
        related='prediction_id.security_id',
        store=True,
    )
    
    symbol = fields.Char(
        related='security_id.symbol',
        store=True,
    )
    
    signal_type = fields.Selection([
        ('buy', 'Buy Signal'),
        ('sell', 'Sell Signal'),
        ('hold', 'Hold Signal'),
    ], string='Signal Type', required=True)
    
    current_price = fields.Float(
        related='prediction_id.current_price',
        string='Current Price',
    )
    
    confidence = fields.Float(
        related='prediction_id.prediction_confidence',
        string='Confidence',
    )
    
    is_read = fields.Boolean(
        string='Read',
        default=False,
        index=True,
    )
    
    is_confirmed = fields.Boolean(
        string='Trade Confirmed',
        default=False,
    )
    
    is_dismissed = fields.Boolean(
        string='Dismissed',
        default=False,
    )
    
    order_id = fields.Many2one(
        'trading.order',
        string='Created Order',
    )

    @api.model
    def get_pending_notifications(self, limit=10):
        """Get unread, unconfirmed notifications for current user"""
        notifications = self.search([
            ('user_id', '=', self.env.user.id),
            ('is_read', '=', False),
            ('is_dismissed', '=', False),
            ('signal_type', 'in', ['buy', 'sell']),  # Only actionable signals
        ], limit=limit)
        
        return [{
            'id': n.id,
            'symbol': n.symbol,
            'signal_type': n.signal_type,
            'current_price': n.current_price,
            'confidence': n.confidence,
            'prediction_id': n.prediction_id.id,
            'create_date': n.create_date.isoformat() if n.create_date else None,
        } for n in notifications]

    @api.model
    def get_unread_count(self):
        """Get count of unread actionable notifications"""
        return self.search_count([
            ('user_id', '=', self.env.user.id),
            ('is_read', '=', False),
            ('is_dismissed', '=', False),
            ('signal_type', 'in', ['buy', 'sell']),
        ])

    def mark_as_read(self):
        """Mark notification as read"""
        self.write({'is_read': True})
        return True

    def dismiss(self):
        """Dismiss notification without trading"""
        self.write({
            'is_read': True,
            'is_dismissed': True,
        })
        return True

    def confirm_trade(self, quantity=100):
        """Confirm trade and create order"""
        self.ensure_one()
        
        if self.is_confirmed:
            return {'success': False, 'error': 'Already confirmed'}
        
        if self.signal_type not in ['buy', 'sell']:
            return {'success': False, 'error': 'Invalid signal type for trading'}
        
        try:
            # Get trading account
            trading_account = self.env['trading.account'].search([
                ('user_id', '=', self.env.user.id),
                ('state', '=', 'active'),
            ], limit=1)
            
            if not trading_account:
                return {'success': False, 'error': 'No active trading account found'}
            
            # Create order
            order_vals = {
                'account_id': trading_account.id,
                'symbol': self.symbol,
                'side': 'B' if self.signal_type == 'buy' else 'S',
                'quantity': quantity,
                'price': self.current_price,
                'order_type': 'LO',  # Limit Order
            }
            
            order = self.env['trading.order'].create(order_vals)
            
            # Submit the order
            order.action_submit_order()
            
            # Update notification
            self.write({
                'is_read': True,
                'is_confirmed': True,
                'order_id': order.id,
            })
            
            return {
                'success': True,
                'order_id': order.id,
                'order_ref': order.name or order.id,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
