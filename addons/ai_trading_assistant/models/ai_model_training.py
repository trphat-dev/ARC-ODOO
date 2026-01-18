# -*- coding: utf-8 -*-

import base64
import gzip
import logging
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIModelTraining(models.Model):
    """AI Model Training Records"""
    _name = 'ai.model.training'
    _description = 'AI Model Training'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Training Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )

    strategy_id = fields.Many2one(
        'ai.strategy',
        string='Strategy',
        required=True,
        ondelete='cascade'
    )

    config_id = fields.Many2one(
        'ai.trading.config',
        related='strategy_id.config_id',
        string='Configuration',
        readonly=True,
        store=True
    )

    # Training Parameters
    from_date = fields.Date(
        string='From Date',
        required=True
    )

    to_date = fields.Date(
        string='To Date',
        required=True
    )

    model_type = fields.Selection(
        related='strategy_id.model_type',
        string='Model Type',
        readonly=True,
        store=True
    )

    # Training Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('downloading', 'Downloading Data'),
        ('training', 'Training Model'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status', default='pending', required=True, tracking=True)

    # Training Results
    training_start_time = fields.Datetime(
        string='Training Start Time',
        readonly=True
    )

    training_end_time = fields.Datetime(
        string='Training End Time',
        readonly=True
    )

    training_duration = fields.Float(
        string='Training Duration (seconds)',
        compute='_compute_training_duration',
        store=True,
        readonly=True
    )

    progress_percent = fields.Float(
        string='Progress (%)',
        readonly=True,
        default=0.0
    )

    current_security = fields.Char(
        string='Current Security',
        readonly=True
    )

    @api.depends('training_start_time', 'training_end_time')
    def _compute_training_duration(self):
        """Compute training duration"""
        for record in self:
            if record.training_start_time and record.training_end_time:
                delta = record.training_end_time - record.training_start_time
                record.training_duration = delta.total_seconds()
            else:
                record.training_duration = 0.0

    # Model Metrics
    model_accuracy = fields.Float(
        string='Accuracy (Win Rate)',
        readonly=True,
        help='Percentage of winning trades (Winning Trades / Total Trades)'
    )

    model_precision = fields.Float(
        string='Precision (Profit Factor)',
        readonly=True,
        help='Ratio of Gross Profit to Gross Loss'
    )

    model_recall = fields.Float(
        string='Recall (1 - Drawdown)',
        readonly=True,
        help='Capital retention rate (1.0 - Max Drawdown)'
    )

    model_f1_score = fields.Float(
        string='F1 Score (Harmonic)',
        readonly=True,
        help='Harmonic mean of Win Rate and Profit Factor'
    )

    # Raw Metrics (JSON)
    raw_metrics = fields.Text(
        string='Raw Metrics (JSON)',
        readonly=True
    )

    # Per-symbol results for index mode training (JSON)
    symbol_results_json = fields.Text(
        string='Per-Symbol Results (JSON)',
        readonly=True,
        help='Stores individual model paths and metrics for each symbol when training in index mode'
    )

    # Training Logs
    training_log = fields.Text(
        string='Training Log',
        readonly=True
    )

    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )

    # Model Data (stored in database)
    model_data = fields.Binary(
        string='Model Data',
        readonly=True
    )
    
    model_filename = fields.Char(
        string='Model Filename',
        readonly=True
    )
    
    feature_columns = fields.Text(
        string='Feature Columns (JSON)',
        readonly=True
    )

    dataset_json = fields.Binary(
        string='Dataset (JSON)',
        readonly=True
    )

    dataset_summary = fields.Text(
        string='Dataset Summary',
        readonly=True
    )

    dataset_filename = fields.Char(
        string='Dataset Filename',
        readonly=True
    )

    # FreqAI Model Information (DEPRECATED)
    freqai_identifier = fields.Char(
        string='FreqAI Identifier',
        readonly=True,
        help='[DEPRECATED] FreqAI model identifier'
    )

    freqai_model_path = fields.Char(
        string='FreqAI Model Path',
        readonly=True,
        help='[DEPRECATED] Path to FreqAI model files'
    )

    freqai_model_type = fields.Char(
        string='FreqAI Model Type',
        readonly=True,
        help='[DEPRECATED] FreqAI model type'
    )

    train_period_days = fields.Integer(
        string='Train Period (Days)',
        readonly=True,
        help='Number of days used for training the model'
    )

    backtest_period_days = fields.Integer(
        string='Backtest Period (Days)',
        readonly=True,
        help='Number of days used for backtesting after training'
    )

    # ============================================
    # FinRL Model Information
    # ============================================
    
    finrl_model_path = fields.Char(
        string='FinRL Model Path',
        readonly=True,
        help='Path to saved FinRL DRL model'
    )
    
    finrl_algorithm = fields.Char(
        string='FinRL Algorithm',
        readonly=True,
        help='DRL algorithm used (PPO, A2C, SAC, TD3, DDPG)'
    )
    
    # FinRL-specific metrics
    cumulative_reward = fields.Float(
        string='Cumulative Reward',
        readonly=True,
        help='Total cumulative reward from training'
    )
    
    sharpe_ratio = fields.Float(
        string='Sharpe Ratio',
        readonly=True,
        help='Risk-adjusted return metric'
    )
    
    max_drawdown = fields.Float(
        string='Max Drawdown',
        readonly=True,
        help='Maximum portfolio drawdown during training'
    )
    
    total_trades = fields.Integer(
        string='Total Trades',
        readonly=True,
        help='Number of trades executed during training'
    )
    
    training_timesteps = fields.Integer(
        string='Training Timesteps',
        readonly=True,
        help='Total training timesteps used'
    )

    model_path = fields.Char(
        string='Model Path',
        readonly=True,
        help='Path to saved model (FinRL or FreqAI)'
    )

    def action_start_finrl_training(self):
        """Start FinRL DRL model training."""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError(_('Training can only be started from pending state'))

        start_time = fields.Datetime.now()
        self.write({
            'state': 'training',
            'training_start_time': start_time,
            'progress_percent': 0.0,
            'current_security': 'Initializing FinRL...',
        })
        
        # Commit to show progress in UI
        self.env.cr.commit()

        try:
            service = self.env['ai.finrl.service']
            
            # Throttling state for progress updates - optimized for large index training
            last_update = {'time': datetime.now(), 'percent': -1}
            
            # Get symbol count for progress display
            symbol_count = len(self.strategy_id.effective_security_ids) if hasattr(self.strategy_id, 'effective_security_ids') else 0

            def progress_callback(progress, current_step, total_steps):
                """Update training progress (throttled for performance).
                
                Optimized for large index training:
                - Commits only every 5% or 5 seconds to reduce DB load
                - Shows symbol count in progress
                """
                now = datetime.now()
                # Update if > 5% change OR > 5 seconds elapsed OR completion
                if (progress >= 99.9 or 
                    progress - last_update['percent'] >= 5 or 
                    (now - last_update['time']).total_seconds() > 5):
                    
                    status_msg = f'Training {symbol_count} symbols...' if symbol_count else 'Training...'
                    self.write({
                        'progress_percent': min(progress, 100.0),
                        'current_security': status_msg,
                    })
                    self.env.cr.commit()

                    last_update['time'] = now
                    last_update['percent'] = progress
            
            # Get Real Account Balance from stock_trading module
            initial_balance = None
            try:
                balance_rec = self.env['trading.account.balance'].search([
                    ('user_id', '=', self.env.user.id)
                ], order='create_date desc', limit=1)
                
                if balance_rec:
                    # Prioritize purchasing power -> available cash -> cash balance
                    initial_balance = (
                        balance_rec.purchasing_power or 
                        balance_rec.available_cash or 
                        balance_rec.cash_balance
                    )
                    if initial_balance and initial_balance >= 1000000:
                        _logger.info(f"Using Real Account Balance for Training: {initial_balance:,.0f} VND")
                    else:
                        _logger.warning(f"Real Account Balance too low ({initial_balance or 0:,.0f} VND), using default simulated balance.")
                        initial_balance = None
            except Exception as e:
                _logger.warning(f"Could not fetch real account balance: {e}")

            # Use per-symbol training for index mode to get individual models
            if hasattr(self.strategy_id, 'selection_mode') and self.strategy_id.selection_mode == 'index':
                _logger.info("Index mode detected: Using per-symbol training for accurate predictions")
                result = service.run_training_per_symbol(
                    self.strategy_id,
                    self.from_date,
                    self.to_date,
                    progress_callback=progress_callback,
                    initial_balance=initial_balance,
                )
            else:
                # Standard portfolio training for manual mode
                result = service.run_training(
                    self.strategy_id,
                    self.from_date,
                    self.to_date,
                    progress_callback=progress_callback,
                    initial_balance=initial_balance,
                )
            
        except Exception as exc:
            _logger.error('FinRL training failed: %s', exc, exc_info=True)
            self.write({
                'state': 'failed',
                'training_end_time': fields.Datetime.now(),
                'error_message': str(exc),
                'current_security': False,
            })
            
            # Final Bus Notification (Failure)
            try:
                channel = (self.env.cr.dbname, 'ai.model.training', self.id)
                message = {
                    'progress_percent': 0.0,
                    'current_security': f'Training Failed: {str(exc)}',
                    'state': 'failed'
                }
                self.env['bus.bus']._sendone(channel, 'training_update', message)
            except Exception as e:
                pass
                
            raise

        # Extract metrics from result
        _logger.info(f'Training result keys: {result.keys()}')
        _logger.info(f'Full training result: {result}')
        
        cumulative_reward = result.get('cumulative_reward', 0.0)
        sharpe_ratio = result.get('sharpe_ratio', 0.0)
        max_drawdown = result.get('max_drawdown', 0.0)
        total_trades = result.get('total_trades', 0)
        win_rate = result.get('win_rate', 0.0)
        profit_factor = result.get('profit_factor', 0.0)
        
        _logger.info(f'Extracted metrics - trades: {total_trades}, win_rate: {win_rate}, sharpe: {sharpe_ratio}')
        
        # Build training log
        log_lines = [
            _('FinRL training completed.'),
            _('Algorithm: %s') % result.get('algorithm', 'unknown'),
            _('Training samples: %s') % result.get('training_samples', 0),
            _('Duration: %s seconds') % result.get('training_duration_seconds', 0),
            _('Cumulative Reward: %.4f') % cumulative_reward,
            _('Sharpe Ratio: %.4f') % sharpe_ratio,
            _('Max Drawdown: %.4f') % max_drawdown,
            _('Total Trades: %d') % total_trades,
        ]
        
        if result.get('model_path'):
            log_lines.append(_('Model saved to: %s') % result['model_path'])
        
        training_log = '\n'.join(log_lines)

        end_time = fields.Datetime.now()
        self.write({
            'state': 'completed',
            'training_end_time': end_time,
            'progress_percent': 100.0,
            'current_security': False,
            # FinRL specific metrics
            'cumulative_reward': cumulative_reward,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'finrl_model_path': result.get('model_path', ''),
            'finrl_algorithm': result.get('algorithm', ''),
            'training_timesteps': result.get('params', {}).get('total_timesteps', 0),
            'model_path': result.get('model_path', ''),
            # Legacy fields for compatibility
            # Enhanced Metrics Mapping
            'model_accuracy': result.get('win_rate', 0.0),  # Accuracy = Win Rate
            'model_precision': result.get('profit_factor', 0.0), # Precision = Profit Factor
            'model_recall': 1.0 - result.get('max_drawdown', 0.0), # Recall = Retention (1 - Risk)
            'model_f1_score': 2 * (result.get('win_rate', 0.0) * result.get('profit_factor', 0.0)) / (result.get('win_rate', 0.0) + result.get('profit_factor', 0.0) + 1e-9), # Harmonic Mean
            
            # Raw Metrics storage (stored as JSON in raw_metrics field)
            'raw_metrics': json.dumps(result, ensure_ascii=False, default=str),
            # Per-symbol results for index mode (stores individual model paths)
            'symbol_results_json': json.dumps(result.get('symbol_results', {}), ensure_ascii=False, default=str) if result.get('symbol_results') else '',
            'training_log': training_log,
        })
        self.env.cr.commit()

        # Update strategy status
        self.strategy_id.write({
            'model_f1_score': self.model_f1_score,
            'state': 'trained',
        })
        self.env.cr.commit()
        
        return True

    # Legacy FreqAI training method removed - use action_start_finrl_training instead

    @api.model
    def create(self, vals):
        """Generate sequence for training reference"""
        if vals.get('name', _('New')) == _('New'):
            try:
                sequence_code = 'ai.model.training'
                sequence = self.env['ir.sequence'].search([
                    ('code', '=', sequence_code)
                ], limit=1)
                
                if sequence:
                    vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or _('New')
                else:
                    # Fallback: generate name manually if sequence doesn't exist
                    _logger.warning(f'Sequence {sequence_code} not found, using fallback naming')
                    existing_count = self.search_count([])
                    vals['name'] = f'TRAIN-{str(existing_count + 1).zfill(5)}'
            except Exception as e:
                _logger.error(f'Error generating sequence: {e}', exc_info=True)
                # Fallback: generate name manually
                existing_count = self.search_count([])
                vals['name'] = f'TRAIN-{str(existing_count + 1).zfill(5)}'
        
        return super().create(vals)

