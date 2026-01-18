# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class AITradingController(http.Controller):
    """Controller for AI Trading API endpoints"""

    @http.route('/ai_trading/predictions', type='json', auth='user', methods=['POST'])
    def get_predictions(self, strategy_id=None, limit=10):
        """Get recent predictions"""
        try:
            domain = [('user_id', '=', request.env.user.id)]
            if strategy_id:
                domain.append(('strategy_id', '=', strategy_id))

            predictions = request.env['ai.prediction'].search(
                domain,
                order='prediction_date desc',
                limit=limit
            )

            return {
                'success': True,
                'data': [{
                    'id': p.id,
                    'symbol': p.symbol,
                    'date': p.prediction_date.isoformat(),
                    'signal': p.final_signal,
                    'confidence': p.prediction_confidence,
                    'buy_signal': p.buy_signal,
                    'sell_signal': p.sell_signal,
                } for p in predictions]
            }

        except Exception as e:
            _logger.error(f'Get predictions error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/ai_trading/strategies', type='json', auth='user', methods=['GET'])
    def get_strategies(self):
        """Get user strategies"""
        try:
            strategies = request.env['ai.strategy'].search([
                ('user_id', '=', request.env.user.id)
            ])

            return {
                'success': True,
                'data': [{
                    'id': s.id,
                    'name': s.name,
                    'symbol': s.symbol,
                    'market': s.market,
                    'state': s.state,
                    'model_accuracy': s.model_accuracy,
                } for s in strategies]
            }

        except Exception as e:
            _logger.error(f'Get strategies error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}


