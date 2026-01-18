# -*- coding: utf-8 -*-
"""
Backtest Wizard - International Standard
Supports Simple, Walk-Forward Analysis, and Monte Carlo Simulation
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BacktestWizard(models.TransientModel):
    """Enhanced wizard for international-standard backtesting."""
    _name = 'backtest.wizard'
    _description = 'Backtest Wizard'

    strategy_id = fields.Many2one(
        'ai.strategy',
        string='Strategy',
        required=True,
        readonly=True
    )

    from_date = fields.Date(
        string='From Date',
        required=True,
        help='Start date for backtest'
    )

    to_date = fields.Date(
        string='To Date',
        required=True,
        help='End date for backtest'
    )

    initial_capital = fields.Float(
        string='Initial Capital (VND)',
        default=100000000.0,  # 100M VND
        required=True,
        help='Initial capital for backtest'
    )
    
    # =========================================================================
    # International Standard Options
    # =========================================================================
    
    backtest_mode = fields.Selection([
        ('simple', 'Simple (Single Pass)'),
        ('walk_forward', 'Walk-Forward Analysis'),
        ('monte_carlo', 'Monte Carlo Simulation'),
    ], string='Backtest Mode', default='simple', required=True,
       help='Simple: Traditional single-pass backtest.\n'
            'Walk-Forward: Rolling windows to detect overfitting.\n'
            'Monte Carlo: Statistical simulation for robustness testing.')
    
    benchmark_symbol = fields.Char(
        string='Benchmark Symbol',
        default='VN30',
        help='Symbol for benchmark comparison (e.g., VN30, VNINDEX, HPG). '
             'Leave empty for no benchmark.'
    )
    
    n_monte_carlo = fields.Integer(
        string='Monte Carlo Simulations',
        default=1000,
        help='Number of Monte Carlo simulations (only for Monte Carlo mode)'
    )
    
    n_walk_forward_windows = fields.Integer(
        string='Walk-Forward Windows',
        default=5,
        help='Number of rolling windows for Walk-Forward Analysis'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        res = super().default_get(fields_list)
        
        # Check context for strategy_id
        strategy_id = self.env.context.get('default_strategy_id')
        if not strategy_id and self.env.context.get('active_model') == 'ai.strategy':
             strategy_id = self.env.context.get('active_id')
             
        if strategy_id:
            strategy = self.env['ai.strategy'].browse(strategy_id)
            if strategy.exists():
                res['strategy_id'] = strategy.id
                res['from_date'] = strategy.from_date
                res['to_date'] = strategy.to_date
        return res

    def action_run_backtest(self):
        """Run international-standard backtest."""
        self.ensure_one()

        # Validate dates
        if self.from_date >= self.to_date:
            raise UserError(_('From Date must be before To Date'))

        try:
            # Use FinRL service for DRL backtest
            service = self.env['ai.finrl.service']
            stats = service.run_backtest(
                strategy=self.strategy_id,
                date_from=self.from_date,
                date_to=self.to_date,
                mode=self.backtest_mode,
                benchmark_symbol=self.benchmark_symbol or None,
                n_monte_carlo=self.n_monte_carlo,
                n_walk_forward_windows=self.n_walk_forward_windows,
            )
            
            # Build result message based on mode
            message = self._build_result_message(stats)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Backtest Completed (%s)') % self.backtest_mode.replace('_', ' ').title(),
                    'message': message,
                    'type': 'success',
                    'sticky': True,
                }
            }

        except Exception as e:
            _logger.error(f'Backtest failed: {e}', exc_info=True)
            raise UserError(_('Backtest failed: %s') % str(e))
    
    def _build_result_message(self, stats):
        """Build comprehensive result message based on backtest mode."""
        metrics = stats.get('metrics', stats)
        
        # Core metrics
        lines = [
            _('Return: %(return).2f%% | Sharpe: %(sharpe).2f | Max DD: %(drawdown).2f%%') % {
                'return': metrics.get('total_return', 0.0) * 100,
                'sharpe': metrics.get('sharpe_ratio', 0.0),
                'drawdown': metrics.get('max_drawdown', 0.0) * 100,
            },
            _('Trades: %(trades)d | Win Rate: %(winrate).1f%% | Profit Factor: %(pf).2f') % {
                'trades': metrics.get('total_trades', 0),
                'winrate': metrics.get('win_rate', 0.0) * 100,
                'pf': metrics.get('profit_factor', 0.0),
            },
        ]
        
        # Mode-specific additions
        if self.backtest_mode == 'walk_forward':
            wfa_results = stats.get('walk_forward_results', [])
            if wfa_results:
                lines.append(_('WFA: %(windows)d windows | Consistency: %(consistency).0f%%') % {
                    'windows': len(wfa_results),
                    'consistency': metrics.get('wfa_consistency', 0.0) * 100,
                })
        
        elif self.backtest_mode == 'monte_carlo':
            mc = stats.get('monte_carlo', {})
            if mc:
                lines.append(
                    _('MC: Prob(Profit): %(prob).0f%% | Realistic MDD: %(mdd).1f%%') % {
                        'prob': mc.get('prob_profit', 0.0) * 100,
                        'mdd': mc.get('max_drawdown_95', 0.0) * 100,
                    }
                )
        
        # Benchmark comparison
        benchmark = stats.get('benchmark', {})
        if benchmark and self.benchmark_symbol:
            outperformance = benchmark.get('outperformance', 0.0)
            lines.append(
                _('vs %(symbol)s: %(sign)s%(diff).2f%%') % {
                    'symbol': self.benchmark_symbol,
                    'sign': '+' if outperformance >= 0 else '',
                    'diff': outperformance * 100,
                }
            )
        
        return '\n'.join(lines)
