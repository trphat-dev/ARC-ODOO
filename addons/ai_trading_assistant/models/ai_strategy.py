# -*- coding: utf-8 -*-

import logging
import json
import base64
import gzip
import math
import pandas as pd
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from .trading_signal import (
    TradingSignal,
    create_entry_signal,
    create_exit_signal,
    SignalDirection,
    ExitType,
    create_signal_from_legacy,
)

_logger = logging.getLogger(__name__)

try:
    import pandas_ta as ta
except ImportError:
    ta = None
    _logger.warning("pandas_ta is not installed. Lean VBao2 indicators will be skipped.")


class AIStrategy(models.Model):
    """AI Trading Strategy Configuration"""
    _name = 'ai.strategy'
    _description = 'AI Trading Strategy'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Strategy Name',
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )

    config_id = fields.Many2one(
        'ai.trading.config',
        string='Trading Configuration',
        required=True
    )

    training_count = fields.Integer(compute='_compute_counts')
    prediction_count = fields.Integer(compute='_compute_counts')

    # Account Balance Info
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    current_balance = fields.Monetary(
        string='Purchasing Power',
        currency_field='currency_id',
        compute='_compute_current_balance',
        help='Current purchasing power from Trading Account'
    )
    
    @api.depends('user_id')
    def _compute_current_balance(self):
        for record in self:
            balance = 0.0
            try:
                # Get latest balance record for the user
                balance_rec = self.env['trading.account.balance'].search([
                    ('user_id', '=', record.user_id.id)
                ], order='create_date desc', limit=1)
                
                if balance_rec:
                    balance = (
                        balance_rec.purchasing_power or 
                        balance_rec.available_cash or 
                        balance_rec.cash_balance or 
                        0.0
                    )
            except Exception:
                pass
            record.current_balance = balance

    # Symbol Configuration
    # Selection Mode: Manual or Index-based
    selection_mode = fields.Selection([
        ('manual', 'Manual Securities Selection'),
        ('index', 'Index Components (VN30, VNX50, etc.)'),
    ], string='Selection Mode', default='manual', required=True,
       help='Choose how to select securities for training')

    index_id = fields.Many2one(
        'ssi.index.list',
        string='Stock Index',
        help='Select an index to train on all its component stocks'
    )

    security_ids = fields.Many2many(
        'ssi.securities',
        string='Securities',
        domain="[('market', '=', market), ('is_active', '=', True)]"
    )

    # Computed: Effective securities based on selection mode
    effective_security_ids = fields.Many2many(
        'ssi.securities',
        string='Effective Securities',
        compute='_compute_effective_securities',
        store=False,
        help='Securities that will be used for training/prediction'
    )

    @api.depends('selection_mode', 'index_id', 'index_id.component_ids', 'security_ids')
    def _compute_effective_securities(self):
        """Get effective securities based on selection mode"""
        for record in self:
            if record.selection_mode == 'index' and record.index_id:
                # Get all securities from index components
                record.effective_security_ids = record.index_id.component_ids.filtered(
                    lambda c: c.is_active and c.security_id.is_active
                ).mapped('security_id')
            else:
                # Use manually selected securities
                record.effective_security_ids = record.security_ids

    market = fields.Selection([
        ('HOSE', 'HOSE'),
        ('HNX', 'HNX'),
        ('UPCOM', 'UPCOM'),
    ], string='Market', required=True, default='HOSE')
    
    # Data Type Configuration
    data_type = fields.Selection([
        ('daily', 'Daily OHLC'),
        ('intraday', 'Intraday OHLC'),
    ], string='Data Type', required=True, default='daily')
    
    intraday_resolution = fields.Selection([
        ('1', '1 minute'),
        ('5', '5 minutes'),
        ('15', '15 minutes'),
        ('30', '30 minutes'),
        ('60', '1 hour'),
    ], string='Intraday Resolution', default='1')
    
    # Computed field for backward compatibility
    symbol = fields.Char(
        string='Symbol (First Selected)',
        compute='_compute_symbol',
        store=False
    )
    
    @api.depends('effective_security_ids')
    def _compute_symbol(self):
        """Compute symbol from first effective security"""
        for record in self:
            if record.effective_security_ids:
                record.symbol = record.effective_security_ids[0].symbol
            else:
                record.symbol = ''


    # ============================================
    # GOLDEN CROSS / DEATH CROSS (SMA 50-200)
    # ============================================
    # Fixed: SMA 50 and SMA 200 for Vietnamese market
    ma_short_period = fields.Integer(
        string='MA Short Period (SMA)',
        default=50,
        required=True,
        readonly=True
    )

    ma_long_period = fields.Integer(
        string='MA Long Period (SMA)',
        default=200,
        required=True,
        readonly=True
    )

    # ============================================
    # RSI FILTER
    # ============================================
    rsi_length = fields.Integer(
        string='RSI Length',
        default=14,
        required=True
    )

    rsi_buy_level = fields.Float(
        string='RSI Min (Buy)',
        default=45.0,
        required=True,
        help='RSI pháº£i lá»›n hÆ¡n giÃ¡ trá»‹ nÃ y Ä‘á»ƒ táº¡o tÃ­n hiá»‡u mua (máº·c Ä‘á»‹nh: 45)'
    )

    rsi_sell_level = fields.Float(
        string='RSI Max (Sell)',
        default=55.0,
        required=True,
        help='RSI pháº£i nhá» hÆ¡n giÃ¡ trá»‹ nÃ y Ä‘á»ƒ táº¡o tÃ­n hiá»‡u bÃ¡n (máº·c Ä‘á»‹nh: 55)'
    )

    # ============================================
    # BOLLINGER BANDS
    # ============================================
    bb_length = fields.Integer(
        string='Bollinger Length',
        default=20,
        required=True,
        help='Sá»‘ lÆ°á»£ng náº¿n Ä‘á»ƒ tÃ­nh Bollinger Bands (máº·c Ä‘á»‹nh: 20)'
    )

    bb_std = fields.Float(
        string='Bollinger Std Dev',
        default=2.0,
        required=True,
        help='Äá»™ lá»‡ch chuáº©n cho Bollinger Bands (máº·c Ä‘á»‹nh: 2.0)'
    )

    # ============================================
    # MACD CONFIRMATION
    # ============================================
    macd_fast_period = fields.Integer(
        string='MACD Fast Period',
        default=12,
        required=True
    )

    macd_slow_period = fields.Integer(
        string='MACD Slow Period',
        default=26,
        required=True
    )

    macd_signal_period = fields.Integer(
        string='MACD Signal Period',
        default=9,
        required=True
    )

    # ============================================
    # VOLUME FILTER
    # ============================================
    volume_ma_period = fields.Integer(
        string='Volume MA Period',
        default=20,
        required=True
    )

    volume_threshold = fields.Float(
        string='Volume Multiplier',
        default=1.2,
        required=True,
        help='Volume pháº£i lá»›n hÆ¡n trung bÃ¬nh bao nhiÃªu láº§n? (máº·c Ä‘á»‹nh: 1.2)'
    )

    # ============================================
    # RISK MANAGEMENT
    # ============================================
    stoploss_pct = fields.Float(
        string='Stop Loss (%)',
        default=-4.0,
        required=True,
        help='Stop Loss % (máº·c Ä‘á»‹nh: -4.0%)'
    )

    takeprofit_pct = fields.Float(
        string='Take Profit (%)',
        default=8.0,
        required=True,
        help='Take Profit % (máº·c Ä‘á»‹nh: 8.0%)'
    )

    # Strategy Logic (Golden Cross / Death Cross)
    buy_signal_logic = fields.Text(
        string='Buy Signal Logic',
        default='Golden Cross: MA_short crosses above MA_long (bullish signal)',
        readonly=True
    )

    sell_signal_logic = fields.Text(
        string='Sell Signal Logic',
        default='Death Cross: MA_short crosses below MA_long (bearish signal)',
        readonly=True
    )
    
    # Signal Type
    current_signal = fields.Selection([
        ('golden_cross', 'Golden Cross'),
        ('death_cross', 'Death Cross'),
        ('none', 'No Signal'),
    ], string='Current Signal', compute='_compute_current_signal', store=False)

    # AI Model Configuration
    model_type = fields.Selection([
        ('ppo', 'PPO - Proximal Policy Optimization'),
        ('a2c', 'A2C - Advantage Actor Critic'),
        ('sac', 'SAC - Soft Actor Critic'),
        ('td3', 'TD3 - Twin Delayed DDPG'),
        ('ddpg', 'DDPG - Deep Deterministic Policy Gradient'),
    ], string='Model Type', required=True, default='ppo',
       help='Select the DRL algorithm to train.')

    # Ensemble Specific Configuration
    use_algo_ppo = fields.Boolean(string='Use PPO', default=True)
    use_algo_a2c = fields.Boolean(string='Use A2C', default=True)
    use_algo_sac = fields.Boolean(string='Use SAC', default=True)
    use_algo_td3 = fields.Boolean(string='Use TD3', default=True)
    use_algo_ddpg = fields.Boolean(string='Use DDPG', default=True)

    @api.onchange('model_type')
    def _onchange_model_type(self):
        if self.model_type != 'ensemble':
            self.use_algo_ppo = False
            self.use_algo_a2c = False
            self.use_algo_sac = False
            self.use_algo_td3 = False
            self.use_algo_ddpg = False
        else:
            self.use_algo_ppo = True
            self.use_algo_a2c = True
            self.use_algo_sac = True
            self.use_algo_td3 = True
            self.use_algo_ddpg = True

    # Training Configuration
    from_date = fields.Date(
        string='Training From Date',
        required=True
    )

    to_date = fields.Date(
        string='Training To Date',
        required=True
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('training', 'Training'),
        ('trained', 'Trained'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Model Performance Metrics
    model_accuracy = fields.Float(
        string='Model Accuracy',
        readonly=True
    )

    model_precision = fields.Float(
        string='Model Precision',
        readonly=True
    )

    model_recall = fields.Float(
        string='Model Recall',
        readonly=True
    )

    model_f1_score = fields.Float(
        string='Model F1 Score',
        readonly=True
    )

    # Relations
    training_ids = fields.One2many(
        'ai.model.training',
        'strategy_id',
        string='Training History'
    )

    prediction_ids = fields.One2many(
        'ai.prediction',
        'strategy_id',
        string='Predictions'
    )
    
    # Strategy Code (stored in database)
    strategy_code = fields.Text(
        string='Strategy Code',
        readonly=True
    )

    # Notes
    notes = fields.Text(string='Notes')

    is_investor_strategy = fields.Boolean(
        string='Investor Copilot Strategy',
        default=False
    )

    # ============================================
    # FinRL Model Detection
    # ============================================
    
    @property
    def is_finrl_model(self):
        """Check if the model type is a supported DRL algorithm."""
        return self.model_type in ('ppo', 'a2c', 'sac', 'td3', 'ddpg')
    
    @property
    def is_legacy_model(self):
        """Check if the model type is deprecated legacy ML model."""
        return self.model_type not in ('ppo', 'ensemble')


    


    @api.constrains('from_date', 'to_date')
    def _check_date_range(self):
        """Validate date range"""
        for record in self:
            if record.from_date and record.to_date:
                if record.from_date >= record.to_date:
                    raise ValidationError(
                        _('From Date must be before To Date')
                    )

    @api.constrains('rsi_buy_level', 'rsi_sell_level', 'ma_short_period', 'ma_long_period',
                    'macd_fast_period', 'macd_slow_period', 'macd_signal_period',
                    'volume_ma_period', 'volume_threshold', 'stoploss_pct', 'takeprofit_pct')
    def _check_strategy_parameters(self):
        """Validate strategy parameters"""
        for record in self:
            # RSI Buy Level (Min) pháº£i < RSI Sell Level (Max) Ä‘á»ƒ Ä‘áº£m báº£o logic Ä‘Ãºng
            if record.rsi_buy_level >= record.rsi_sell_level:
                raise ValidationError(
                    _('RSI Min (Buy) pháº£i nhá» hÆ¡n RSI Max (Sell). VÃ­ dá»¥: Buy Min = 45, Sell Max = 55')
                )
            
            if record.ma_short_period >= record.ma_long_period:
                raise ValidationError(
                    _('MA Short Period (50) must be less than MA Long Period (200)')
                )
            
            if record.ma_short_period != 50 or record.ma_long_period != 200:
                raise ValidationError(
                    _('MA periods must be fixed at 50 (short) and 200 (long) for Vietnamese market strategy')
                )
            
            if record.macd_fast_period >= record.macd_slow_period:
                raise ValidationError(
                    _('MACD Fast Period must be less than MACD Slow Period')
                )
            
            if record.volume_threshold <= 0:
                raise ValidationError(
                    _('Volume Threshold must be greater than 0')
                )
            
            if record.stoploss_pct >= 0:
                raise ValidationError(
                    _('Stop Loss must be negative (e.g., -5.0 for -5%%)')
                )
            
            if record.takeprofit_pct <= 0:
                raise ValidationError(
                    _('Take Profit must be positive (e.g., 10.0 for 10%%)')
                )
            

    
    @api.depends('ma_short_period', 'ma_long_period')  # Fixed: SMA 50-200
    def _compute_current_signal(self):
        """Compute current Golden Cross / Death Cross signal (placeholder - actual calculation in prediction)"""
        for record in self:
            record.current_signal = 'none'  # Will be computed during prediction generation

    def action_train_model(self):
        """Directly trigger training using strategy date range.
        
        Uses FinRL service for DRL models (ppo, a2c, sac, td3, ddpg)
        or legacy FreqAI pipeline for deprecated ML models.
        """
        self.ensure_one()

        if not self.from_date or not self.to_date:
            raise UserError(_('Please set From Date and To Date before training.'))
        if self.state == 'training':
            raise UserError(_('Training is already in progress for this strategy.'))

        training = self.env['ai.model.training'].create({
            'strategy_id': self.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
        })

        # Use FinRL service for DRL models
        return training.action_start_finrl_training()



    def _compute_counts(self):
        for record in self:
            record.training_count = self.env['ai.model.training'].search_count([('strategy_id', '=', record.id)])
            record.prediction_count = self.env['ai.prediction'].search_count([('strategy_id', '=', record.id)])

    def action_view_trainings(self):
        self.ensure_one()
        return {
            'name': _('Model Trainings'),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.model.training',
            'view_mode': 'list,form',
            'domain': [('strategy_id', '=', self.id)],
            'context': {'default_strategy_id': self.id},
        }

    def action_view_predictions(self):
        self.ensure_one()
        return {
            'name': _('Predictions'),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.prediction',
            'view_mode': 'list,form',
            'domain': [('strategy_id', '=', self.id)],
            'context': {'default_strategy_id': self.id},
        }

    def action_activate(self):
        """Activate strategy"""
        self.ensure_one()
        if self.state != 'trained':
            raise UserError(_('Strategy must be trained before activation'))
        self.write({'state': 'active'})

    def action_pause(self):
        """Pause strategy"""
        self.ensure_one()
        self.write({'state': 'paused'})

    @api.model
    def _cron_retrain_models(self):
        """Cron job to auto-retrain models"""
        strategies = self.search([
            ('state', '=', 'active'),
            ('config_id.auto_retrain', '=', True),
        ])

        for strategy in strategies:
            try:
                config = strategy.config_id
                if not config:
                    continue

                # Check if retrain is needed
                last_training = self.env['ai.model.training'].search([
                    ('strategy_id', '=', strategy.id),
                    ('state', '=', 'completed'),
                ], order='create_date desc', limit=1)

                if last_training:
                    days_since_training = (fields.Date.today() - last_training.create_date.date()).days
                    if days_since_training < config.retrain_interval_days:
                        continue

                # Create new training
                training = self.env['ai.model.training'].create({
                    'strategy_id': strategy.id,
                    'from_date': strategy.from_date,
                    'to_date': strategy.to_date,
                })

                # Start training (async would be better in production)
                training.action_start_training()

                _logger.info(f'Auto-retraining started for strategy {strategy.name}')

            except Exception as e:
                _logger.error(f'Failed to retrain strategy {strategy.name}: {e}')

    @api.model
    def _cron_generate_predictions(self):
        """Cron job to automatically generate predictions for active strategies"""
        _logger.info('=== Starting auto-prediction cron job ===')
        
        try:
            # Only process strategies with auto_generate_predictions enabled
            strategies = self.search([
                ('state', '=', 'active'),
                ('config_id.auto_generate_predictions', '=', True),
            ])

            if not strategies:
                _logger.info('No active strategies with auto_generate_predictions enabled.')
                return

            _logger.info(f'Found {len(strategies)} active strategy(ies) with auto_generate_predictions enabled')

            total_generated = 0
            
            for strategy in strategies:
                # Check if strategy has valid config
                if not strategy.config_id:
                    continue
                
                # Generate predictions (update mode)
                predictions = strategy._generate_predictions_for_strategy(raise_on_error=False)
                if predictions:
                    total_generated += len(predictions)
            
            _logger.info(f'=== Auto-prediction job completed. Total generated/updated: {total_generated} ===')
            
        except Exception as e:
            _logger.error(f'CRITICAL: Auto-prediction cron failed: {e}', exc_info=True)
            # FAIL-SAFE: Disable the cron job to prevent infinite error loops
            cron = self.env.ref('ai_trading_assistant.cron_ai_trading_generate_predictions', raise_if_not_found=False)
            if not cron:
                # Try searching by name if ref not found (dynamic creation)
                cron = self.env['ir.cron'].search([
                    ('name', '=', 'AI Trading: Auto Generate Predictions')
                ], limit=1)
            
            if cron:
                cron.active = False
                _logger.error('!!! Auto-prediction Cron has been DISABLED due to critical error !!!')
                
                # Notify admin/users via bus
                self.env['bus.bus']._sendone('ai_prediction_channel', 'notification', {
                    'type': 'system_error',
                    'message': f'Auto-prediction stopped due to error: {str(e)}'
                })

    def _extract_prediction_confidence(self, signal_confidence, prediction_result):
        """
        Extract and validate prediction confidence from signal or prediction result
        Returns float in range [0.0, 100.0]
        """
        # Try signal_confidence first (from TradingSignal)
        if signal_confidence is not None:
            try:
                conf = float(signal_confidence)
                return max(0.0, min(100.0, conf))  # Clamp to [0, 100]
            except (ValueError, TypeError):
                pass
        
        # Fallback to prediction_result confidence
        conf = prediction_result.get('confidence', 0.0)
        if conf is not None:
            try:
                conf = float(conf)
                return max(0.0, min(100.0, conf))  # Clamp to [0, 100]
            except (ValueError, TypeError):
                pass
        
        # Default to 0.0 if both fail
        _logger.warning(f'Failed to extract confidence, using 0.0. signal_confidence={signal_confidence}, prediction_result.confidence={prediction_result.get("confidence")}')
        return 0.0

    def _generate_predictions_for_strategy(self, raise_on_error=True):
        """Generate predictions for the current strategy (FinRL only)"""
        self.ensure_one()

        try:
            if not self.config_id or not self.config_id.ssi_config_id:
                raise UserError(_('Trading configuration or SSI configuration is missing.'))

            # Determine securities based on selection mode
            securities = self.effective_security_ids
            if not securities:
                # Fallback to all active securities in market if none selected
                securities = self.env['ssi.securities'].search([
                    ('market', '=', self.market),
                    ('is_active', '=', True)
                ])

            if not securities:
                if self.selection_mode == 'index':
                    raise UserError(_('No securities found in selected index. Please ensure index components are synced.'))
                else:
                    raise UserError(_('No securities available for prediction. Please select securities or sync SSI securities first.'))

            today = fields.Date.context_today(self)
            now = fields.Datetime.now()
            
            # Get minimum interval from config (default 5 minutes)
            min_interval_minutes = self.config_id.prediction_min_interval_minutes or 5
            min_interval = timedelta(minutes=min_interval_minutes)
            
            created_predictions = self.env['ai.prediction']
            finrl_service = self.env['ai.finrl.service']

            for security in securities:
                # Always update the existing prediction record for this strategy/security pair
                existing_prediction = self.env['ai.prediction'].search([
                    ('strategy_id', '=', self.id),
                    ('security_id', '=', security.id),
                ], order='prediction_date desc', limit=1)
                
                # Single Record Logic: Update existing if available, else create
                prediction = existing_prediction
                
                _logger.info(f'Generating prediction for {security.symbol}...')
                
                try:
                    # 1. Get AI Prediction from FinRL Service
                    ai_result = finrl_service.generate_prediction(self, security)
                    
                    # 2. Compute Technical Indicators (Lean + MA) for logging/visualization
                    lean_metrics = self._compute_lean_indicators(security)
                    lean_signal = self._evaluate_lean_signal(lean_metrics)
                    
                    current_price = ai_result.get('current_price', 0.0)
                    ma_metrics = self._compute_ma_signals(security, current_price)
                    
                    # 3. Use AI Signal directly
                    # ai_result['signal'] is 'buy', 'sell', 'hold'
                    raw_signal = ai_result.get('signal', 'hold')
                    final_signal = raw_signal
                    
                    buy_signal = final_signal == 'buy'
                    sell_signal = final_signal == 'sell'
                    hold_signal = final_signal == 'hold'
                    
                    prediction_vals = {
                        'strategy_id': self.id,
                        'security_id': security.id,
                        'prediction_date': fields.Datetime.now(),
                        'current_price': current_price,
                        'trend_ema_slope': lean_metrics.get('trend_ema_slope', 0.0),
                        'momentum_rsi': lean_metrics.get('momentum_rsi', 0.0),
                        'volatility_atr_pct': lean_metrics.get('volatility_atr_pct', 0.0),
                        'volume_anomaly': lean_metrics.get('volume_anomaly', 0.0),
                        'rsi_value': lean_metrics.get('rsi_val', 50.0), 
                        # Golden Cross / Death Cross (Moving Averages)
                        'sma_50_value': ma_metrics.get('sma_50', 0.0),
                        'sma_200_value': ma_metrics.get('sma_200', 0.0),
                        'ma_signal_type': ma_metrics.get('signal_type', 'none'),
                        'ma_cross_above': ma_metrics.get('cross_above', False),
                        'ma_cross_below': ma_metrics.get('cross_below', False),
                        # AI Signal
                        'buy_signal': buy_signal,
                        'sell_signal': sell_signal,
                        'hold_signal': hold_signal,
                    }

                    # Calculate Confidence
                    confidence = self._calculate_hybrid_confidence(
                        raw_signal,
                        ai_result.get('confidence', 0.0),
                        lean_metrics,
                        ma_metrics
                    )
                    prediction_vals['prediction_confidence'] = confidence
                    prediction_vals['lean_signal_state'] = lean_signal
                    prediction_vals['final_signal'] = final_signal
                    prediction_vals['action_value'] = ai_result.get('action_value', 0.0)
                    
                    # Additional Indicators
                    prediction_vals.update({
                        'macd_value': lean_metrics.get('macd_val', 0.0),
                        'macd_signal_value': lean_metrics.get('macd_signal', 0.0),
                        'macd_hist_value': lean_metrics.get('macd_hist', 0.0),
                        'macd_bullish': lean_metrics.get('macd_val', 0.0) > lean_metrics.get('macd_signal', 0.0),
                        'macd_bearish': lean_metrics.get('macd_val', 0.0) < lean_metrics.get('macd_signal', 0.0),
                        'volume_ratio': lean_metrics.get('volume_ratio', 0.0),
                        'volume_above_threshold': lean_metrics.get('volume_ratio', 0.0) > self.volume_threshold,
                    })

                    # Actionable Advice & Risk Management
                    atr_pct = lean_metrics.get('volatility_atr_pct', 0.02) or 0.02
                    
                    if final_signal == 'buy':
                        # Entry Range: Current Price +/- 0.5% (or 0.25 ATR)
                        # We use a tight range for algorithms
                        half_range = current_price * 0.005
                        prediction_vals['entry_price_min'] = current_price - half_range
                        prediction_vals['entry_price_max'] = current_price + half_range
                        
                        # Stop Loss: 2 ATR below
                        prediction_vals['stop_loss_price'] = current_price * (1 - (2 * atr_pct))
                        
                        # Take Profit: 4 ATR above (Risk:Reward 1:2)
                        prediction_vals['take_profit_price'] = current_price * (1 + (4 * atr_pct))
                        
                        # Allocation Sizing
                        # > 80% Confidence -> 25% Allocation
                        # > 65% Confidence -> 15% Allocation
                        # > 50% Confidence -> 10% Allocation
                        # <= 50% -> 5% Allocation (High Risk)
                        if confidence > 80:
                            prediction_vals['recommended_percent'] = 25.0
                        elif confidence > 65:
                            prediction_vals['recommended_percent'] = 15.0
                        elif confidence > 50:
                            prediction_vals['recommended_percent'] = 10.0
                        else:
                            prediction_vals['recommended_percent'] = 5.0
                    else:
                        prediction_vals['entry_price_min'] = 0.0
                        prediction_vals['entry_price_max'] = 0.0
                        prediction_vals['stop_loss_price'] = 0.0
                        prediction_vals['take_profit_price'] = 0.0
                        prediction_vals['recommended_percent'] = 0.0

                    if prediction:
                         prediction.write(prediction_vals)
                         _logger.info(f'Prediction updated for {security.symbol}')
                    else:
                         prediction = self.env['ai.prediction'].create(prediction_vals)
                         _logger.info(f'Prediction created for {security.symbol}')
                    
                    # Broadcast update via WebSocket
                    prediction._broadcast_update()

                    created_predictions |= prediction
                except MemoryError as mem_err:
                    error_msg = str(mem_err) if str(mem_err) else 'Insufficient memory'
                    _logger.error(f'Memory error generating prediction for {security.symbol}: {error_msg}', exc_info=True)
                    if raise_on_error:
                        raise UserError(_('Memory error generating prediction for %(symbol)s: %(error)s') % {
                            'symbol': security.symbol,
                            'error': error_msg
                        })
                    continue
                except Exception as security_error:
                    error_msg = str(security_error) or repr(security_error)
                    _logger.error(f'Failed to generate prediction for {security.symbol}: {error_msg}', exc_info=True)
                    if raise_on_error:
                         raise UserError(_('Failed to generate prediction for %(symbol)s: %(error)s') % {
                            'symbol': security.symbol,
                            'error': error_msg
                        })
                    continue

            if not created_predictions and raise_on_error:
                raise UserError(_('No predictions were generated. Please ensure market data is available and try again.'))

            return created_predictions

        except UserError:
            if raise_on_error:
                raise
            _logger.warning('Prediction generation skipped due to configuration issues.', exc_info=True)
            return self.env['ai.prediction']
        except Exception as e:
            _logger.error(f'Prediction generation failed for strategy {self.name}: {e}', exc_info=True)
            if raise_on_error:
                raise UserError(_('Failed to generate predictions: %s') % str(e))
            return self.env['ai.prediction']

    def action_generate_predictions(self):
        """Manual action to generate predictions and open prediction view"""
        self.ensure_one()
        if self.state not in ('trained', 'active'):
            raise UserError(_('Please train the strategy before generating predictions.'))

        predictions = self._generate_predictions_for_strategy(raise_on_error=True)
        if not predictions:
            raise UserError(_('No predictions were generated. Please check data availability and try again.'))

        # Return True - view navigation will be handled by view/controller
        return True

    def action_test_auto_prediction(self):
        """Test action to manually trigger auto-prediction cron job logic"""
        self.ensure_one()
        _logger.info(f'Manual test of auto-prediction for strategy: {self.name}')
        
        # Check conditions
        issues = []
        if self.state != 'active':
            issues.append(f'Strategy state is "{self.state}" but must be "active"')
        if not self.config_id:
            issues.append('Strategy has no configuration')
        elif not self.config_id.auto_generate_predictions:
            issues.append('Auto Generate Predictions is disabled in configuration')
        
        if issues:
            raise UserError(_('Cannot generate auto-predictions:\n\n%s') % '\n'.join(f'• {issue}' for issue in issues))
        
        # Run the generation
        predictions = self._generate_predictions_for_strategy(raise_on_error=False)
        
        if predictions:
            # Return True - notification will be handled by view/controller
            return True
        else:
            raise UserError(_('No predictions were generated. This may be because:\n'
                            '1. Predictions already exist within the minimum interval\n'
                            '2. No market data available\n'
                            '3. Securities not configured\n\n'
                            'Check the Odoo logs for more details.'))

    # -------------------------------------------------------------------------
    # Centralized Indicator Logic
    # -------------------------------------------------------------------------
    def calculate_indicators(self, df):
        """
        Calculate technical indicators for a given DataFrame.
        Expected columns: 'open', 'high', 'low', 'close', 'volume'.
        
        Returns:
            DataFrame with added indicator columns:
            - rsi
            - sma_short, sma_long
            - trend_ema_slope
            - volatility_atr_pct
            - volume_anomaly
            - momentum_rsi (same as rsi for now, but kept for compatibility)
            - macd, macd_signal, macd_hist
        """
        if df is None or df.empty:
            return df
        
        # Use pandas_ta if available
        if ta is None:
            _logger.warning("pandas_ta not installed. Indicators cannot be calculated.")
            return df

        # Create a copy to avoid SettingWithCopy warning
        df = df.copy()
        
        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # 1. RSI
        rsi_len = self.rsi_length or 14
        try:
            if ta:
                df['rsi'] = ta.rsi(df['close'], length=rsi_len)
            else:
                # Basic RSI implementation using pandas
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_len).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_len).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
            
            df['rsi'] = df['rsi'].fillna(50.0)
        except Exception:
            df['rsi'] = 50.0

        # 2. Moving Averages (Golden/Death Cross)
        short_period = self.ma_short_period or 50
        long_period = self.ma_long_period or 200
        
        try:
            if ta:
                df[f'sma_{short_period}'] = ta.sma(df['close'], length=short_period)
                df[f'sma_{long_period}'] = ta.sma(df['close'], length=long_period)
            else:
                df[f'sma_{short_period}'] = df['close'].rolling(window=short_period).mean()
                df[f'sma_{long_period}'] = df['close'].rolling(window=long_period).mean()
            
            # Alias for controller generic access
            df['sma_short'] = df[f'sma_{short_period}']
            df['sma_long'] = df[f'sma_{long_period}']
            
            # Fill NaNs for display consistency
            df['sma_short'] = df['sma_short'].bfill().ffill().fillna(df['close'])
            df['sma_long'] = df['sma_long'].bfill().ffill().fillna(df['close'])
        except Exception:
            df['sma_short'] = df['close']
            df['sma_long'] = df['close']

        # 3. MACD
        fast = self.macd_fast_period or 12
        slow = self.macd_slow_period or 26
        signal = self.macd_signal_period or 9
        try:
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            if macd is not None:
                # pandas_ta returns columns like MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
                # We rename them to standard names
                macd_col = f'MACD_{fast}_{slow}_{signal}'
                hist_col = f'MACDh_{fast}_{slow}_{signal}'
                signal_col = f'MACDs_{fast}_{slow}_{signal}'
                
                if macd_col in macd.columns:
                    df['macd'] = macd[macd_col]
                    df['macd_hist'] = macd[hist_col]
                    df['macd_signal'] = macd[signal_col]
                else:
                    # Fallback if column names differ
                    df['macd'] = macd.iloc[:, 0]
                    df['macd_hist'] = macd.iloc[:, 1]
                    df['macd_signal'] = macd.iloc[:, 2]
        except Exception:
            df['macd'] = 0.0
            df['macd_hist'] = 0.0
            df['macd_signal'] = 0.0

        # 4. Lean Indicators (VBao2 Strategy)
        try:
            # EMA 20 Slope
            ema20 = ta.ema(df['close'], length=20)
            df['trend_ema_slope'] = ema20.diff().fillna(0.0) if ema20 is not None else 0.0
            
            # ATR %
            atr = ta.atr(df['high'], df['low'], df['close'], length=14)
            df['volatility_atr_pct'] = (atr / df['close']).replace([float('inf'), -float('inf')], 0.0).fillna(0.0) if atr is not None else 0.0
            
            # Volume Anomaly (Vol / MA20 Vol)
            vol_ma20 = df['volume'].rolling(20).mean()
            df['volume_anomaly'] = (df['volume'] / vol_ma20).replace([float('inf'), -float('inf')], 0.0).fillna(0.0)
            
            # Momentum RSI
            df['momentum_rsi'] = df['rsi'] # Re-use RSI
            
        except Exception:
            df['trend_ema_slope'] = 0.0
            df['volatility_atr_pct'] = 0.0
            df['volume_anomaly'] = 0.0
            df['momentum_rsi'] = 50.0

        return df

    # -------------------------------------------------------------------------
    # Lean VBao2 indicator helpers (Refactored to use centralized logic)
    # -------------------------------------------------------------------------
    def _compute_lean_indicators(self, security):
        """Calculate Lean VBao2 indicators from intraday data using pandas_ta."""
        defaults = self._lean_indicator_defaults()
        if not security or ta is None:
            return defaults
        
        records = self.env['ssi.intraday.ohlc'].search([
            ('security_id', '=', security.id),
        ], order='date desc, time desc', limit=200) # Increased limit for accurate calculation
            
        if not records:
            return defaults

        rows = []
        for rec in records:
            rows.append({
                'open': rec.open_price or 0.0,
                'high': rec.high_price or 0.0,
                'low': rec.low_price or 0.0,
                'close': rec.close_price or 0.0,
                'volume': rec.volume or 0.0,
            })

        rows.reverse()
        df = pd.DataFrame(rows)

        if df.empty:
            return defaults

        # Calculate using pandas_ta
        # 1. EMA 20 & Slope
        ema_series = ta.ema(df['close'], length=20)
        
        # 2. RSI
        rsi_len = self.rsi_length or 14
        rsi_series = ta.rsi(df['close'], length=rsi_len)
        
        # 3. ATR
        atr_series = ta.atr(high=df['high'], low=df['low'], close=df['close'], length=14)
        
        # 4. Volume MA
        volume_ma_series = ta.sma(df['volume'], length=20)
        
        # 5. MACD (12, 26, 9)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        macd_val = 0.0
        macd_signal = 0.0
        macd_hist = 0.0
        if macd is not None:
            # pandas_ta returns columns like MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
            # Or mapped by index: 0=macd, 1=histogram, 2=signal (older versions) or 0=diff, 1=signal, 2=hist (standard)
            # Safe column access
            cols = macd.columns
            # Typically: MACD_12_26_9, MACDh_12_26_9 (hist), MACDs_12_26_9 (signal)
            macd_col = cols[0]
            hist_col = [c for c in cols if 'h' in c.lower() or 'hist' in c.lower()]
            signal_col = [c for c in cols if 's' in c.lower() and 'hist' not in c.lower()]
            
            if not hist_col: hist_col = [cols[1]] if len(cols)>1 else [] # Fallback
            if not signal_col: signal_col = [cols[2]] if len(cols)>2 else [] # Fallback

            macd_val = macd[macd_col].iloc[-1]
            macd_hist = macd[hist_col[0]].iloc[-1] if hist_col else 0.0
            macd_signal = macd[signal_col[0]].iloc[-1] if signal_col else 0.0

        current_price = df['close'].iloc[-1] if not df['close'].empty else 0.0
        current_volume = df['volume'].iloc[-1] if not df['volume'].empty else 0.0

        trend_ema_slope = 0.0
        if ema_series is not None:
            ema_values = ema_series.dropna().tail(2)
            if len(ema_values) == 2:
                trend_ema_slope = ema_values.iloc[-1] - ema_values.iloc[-2]
            elif not ema_values.empty:
                trend_ema_slope = ema_values.iloc[-1]

        momentum_rsi = rsi_series.dropna().iloc[-1] if rsi_series is not None and not rsi_series.dropna().empty else 50.0
        atr_value = atr_series.dropna().iloc[-1] if atr_series is not None and not atr_series.dropna().empty else 0.0
        volume_ma_value = volume_ma_series.dropna().iloc[-1] if volume_ma_series is not None and not volume_ma_series.dropna().empty else 0.0

        volatility_atr_pct = (atr_value / current_price) if current_price else 0.0
        volume_anomaly = (current_volume / volume_ma_value) if volume_ma_value else 0.0

        return {
            'trend_ema_slope': self._sanitize_indicator_value(trend_ema_slope),
            'momentum_rsi': self._sanitize_indicator_value(momentum_rsi),
            'volatility_atr_pct': self._sanitize_indicator_value(volatility_atr_pct),
            'volume_anomaly': self._sanitize_indicator_value(volume_anomaly),
            'rsi_val': self._sanitize_indicator_value(momentum_rsi), # Include raw RSI
            'macd_val': self._sanitize_indicator_value(macd_val),
            'macd_signal': self._sanitize_indicator_value(macd_signal),
            'macd_hist': self._sanitize_indicator_value(macd_hist),
            'volume_ratio': self._sanitize_indicator_value(volume_anomaly),
        }

    @staticmethod
    def _evaluate_lean_signal(metrics):
        """
        Lean ATC logic (Enhanced).
        Returns 'buy', 'sell', or 'wait' based on strictly defined criteria.
        """
        rsi = metrics.get('momentum_rsi', 50.0)
        vol_anomaly = metrics.get('volume_anomaly', 1.0)
        trend_slope = metrics.get('trend_ema_slope', 0.0)

        # BUY: Oversold (RSI < 30) + High Volume (>1.5x) + Reversal/Uptrend
        # International Standard: RSI Oversold is 30, not 35
        if rsi < 30 and vol_anomaly > 1.5:
            # Check if trend is not strongly bearish (slope > -0.05) or turning
            if trend_slope > -0.05:
                return 'buy'
            
        # SELL: Overbought (RSI > 70) + High Volume (>1.5x) + Reversal/Downtrend
        # International Standard: RSI Overbought is 70
        if rsi > 70 and vol_anomaly > 1.5:
            if trend_slope < 0.05:
                return 'sell'
            
        return 'wait'

    def _sigmoid(self, x):
        """Sigmoid activation function to squash values to 0-1 range."""
        return 1 / (1 + math.exp(-x))

    def _calculate_hybrid_confidence(self, ai_signal, ai_confidence, lean_metrics, ma_metrics):
        """
        Calculate hybrid confidence score (0.0 - 100.0) using Probabilistic Approach.
        
        International Standard Improvement:
        - Uses Sigmoid activation for non-linear probability mapping.
        - Penalizes score during high volatility (Risk Adjustment).
        - Combines Model Probability (AI) with Market Confluence (Technicals).
        """
        # 1. Base Score from AI Model (normalized to -1 to 1 for weighted sum)
        # ai_confidence is 0.0 - 1.0
        ai_score = 0.0
        if ai_signal == 'buy':
            ai_score = ai_confidence
        elif ai_signal == 'sell':
            ai_score = -ai_confidence
        else: # hold
            ai_score = 0.0

        # 2. Technical Confluence Score (-1 to 1)
        tech_score = 0.0
        
        # Trend (MA)
        sma_50 = ma_metrics.get('sma_50', 0)
        sma_200 = ma_metrics.get('sma_200', 0)
        if sma_50 > 0 and sma_200 > 0:
            trend_strength = (sma_50 - sma_200) / sma_200 # Percent diff
            # Cap trend impact between -1 and 1 (approx +/- 10% diff)
            tech_score += max(-1.0, min(1.0, trend_strength * 10))
        
        # Momentum (RSI) - Inverse logic (Oversold = Buy Signal)
        rsi = lean_metrics.get('rsi_val', 50.0)
        # RSI 30 -> +1 (Buy), RSI 70 -> -1 (Sell), RSI 50 -> 0
        rsi_score = (50 - rsi) / 20.0 
        rsi_score = max(-1.0, min(1.0, rsi_score))
        tech_score += rsi_score * 0.5 # RSI weight 0.5
        
        # Volume Confirmation
        vol_anomaly = lean_metrics.get('volume_anomaly', 1.0)
        # Standard Breakout Volume is often cited as > 150% of average
        if vol_anomaly > 1.5:
            tech_score *= 1.5 # Significant boost if volume supports the move
            
        # 3. Weighted Combination
        # AI Logic: 50%, Technicals: 50%
        raw_logit = (ai_score * 2.0) + (tech_score * 1.5) 
        
        # 4. Volatility Penalty (Risk Adjustment)
        # If ATR/Price is high (> 2%), reduce confidence
        volatility_pct = lean_metrics.get('volatility_atr_pct', 0.0)
        penalty = 0.0
        if volatility_pct > 0.02: # > 2% daily move is volatile
            penalty = (volatility_pct - 0.02) * 10 # Strong penalty
            
        # 5. Sigmoid Activation -> Probability
        probability = self._sigmoid(raw_logit - penalty)
        
        # Convert to 0-100 Confidence
        # Map 0.5 (neutral) to 0%, 1.0 (certain buy) to 100%, 0.0 (certain sell) to 100%
        # Actually direction is handled by 'final_signal', confidence is just magnitude
        
        # Determine final direction strength
        confidence = abs(probability - 0.5) * 2 * 100.0
        
        return min(99.9, max(1.0, confidence))


    def _compute_ma_signals(self, security, current_price):
        """Compute Moving Average signals using pandas_ta."""
        defaults = {
            'sma_50': 0.0,
            'sma_200': 0.0,
            'signal_type': 'none',
            'cross_above': False,
            'cross_below': False
        }
        
        if not security or ta is None:
            return defaults
            
        # Get configurable lengths
        sma_short_len = self.config_id.sma_short or 50
        sma_long_len = self.config_id.sma_long or 200

        # Need enough data for SMA 200
        records = self.env['ssi.intraday.ohlc'].search([
            ('security_id', '=', security.id),
        ], order='date desc, time desc', limit=int(sma_long_len * 1.5))

        if not records:
            return defaults

        rows = []
        for rec in records:
            rows.append({'close': rec.close_price or 0.0})
        
        rows.reverse()
        df = pd.DataFrame(rows)
        
        if len(df) < sma_long_len:
             return defaults

        # Calculate SMAs
        sma_short_series = ta.sma(df['close'], length=sma_short_len)
        sma_long_series = ta.sma(df['close'], length=sma_long_len)
        
        if sma_short_series is None or sma_long_series is None:
            return defaults
            
        sma_short_val = sma_short_series.iloc[-1]
        sma_long_val = sma_long_series.iloc[-1]
        
        # Check for Crosses
        cross_above = False
        cross_below = False
        
        if len(sma_short_series) >= 2 and len(sma_long_series) >= 2:
            prev_short = sma_short_series.iloc[-2]
            prev_long = sma_long_series.iloc[-2]
            curr_short = sma_short_series.iloc[-1]
            curr_long = sma_long_series.iloc[-1]
            
            # Golden Cross: Short crosses ABOVE Long
            if prev_short <= prev_long and curr_short > curr_long:
                cross_above = True
                
            # Death Cross: Short crosses BELOW Long
            if prev_short >= prev_long and curr_short < curr_long:
                cross_below = True

        signal_type = 'none'
        if cross_above:
            signal_type = 'golden_cross'
        elif cross_below:
            signal_type = 'death_cross'
        elif sma_short_val > sma_long_val:
             signal_type = 'uptrend'
        elif sma_short_val < sma_long_val:
             signal_type = 'downtrend'

        return {
            'sma_50': self._sanitize_indicator_value(sma_short_val),
            'sma_200': self._sanitize_indicator_value(sma_long_val),
            'signal_type': signal_type,
            'cross_above': cross_above,
            'cross_below': cross_below
        }

    @staticmethod
    def _resolve_final_signal(prediction_result, lean_signal, ma_metrics=None):
        """Combine AI prediction with Lean VBao2 and MA signals."""
        confidence = float(prediction_result.get('confidence', 0.0) or 0.0)

        if ma_metrics:
            signal_type = ma_metrics.get('signal_type')
            if signal_type == 'golden_cross':
                return create_entry_signal(
                    direction=SignalDirection.LONG,
                    strength=min(1.0, confidence / 100.0) if confidence else 0.75,
                    confidence=confidence,
                    reason="Golden Cross: MA Short crossed above MA Long",
                )
            if signal_type == 'death_cross':
                return create_exit_signal(
                    direction=SignalDirection.LONG,
                    exit_type=ExitType.EXIT_SIGNAL,
                    strength=min(1.0, confidence / 100.0) if confidence else 0.75,
                    confidence=confidence,
                    reason="Death Cross: MA Short crossed below MA Long",
                )

        buy_signal = prediction_result.get('buy_signal', False)
        sell_signal = prediction_result.get('sell_signal', False)

        if buy_signal:
            return create_entry_signal(
                direction=SignalDirection.LONG,
                strength=min(1.0, confidence / 100.0) if confidence else 0.5,
                confidence=confidence,
                reason="AI prediction: Buy signal",
            )
        if sell_signal:
            return create_exit_signal(
                direction=SignalDirection.LONG,
                exit_type=ExitType.EXIT_SIGNAL,
                strength=min(1.0, confidence / 100.0) if confidence else 0.5,
                confidence=confidence,
                reason="AI prediction: Sell signal",
            )

        signal = create_signal_from_legacy(
            buy_signal=lean_signal == 'buy',
            sell_signal=lean_signal == 'sell',
            confidence=confidence or (50.0 if lean_signal in ('buy', 'sell') else 0.0),
            reason=f"Lean VBao2: {lean_signal.upper()}" if lean_signal in ('buy', 'sell') else "",
        )
        if signal:
            return signal

        final_signal = prediction_result.get('final_signal')
        if final_signal in ('buy', 'sell'):
            return create_signal_from_legacy(
                buy_signal=final_signal == 'buy',
                sell_signal=final_signal == 'sell',
                confidence=confidence,
                reason="Final signal",
            )
        return None

    def _extract_prediction_confidence(self, signal_confidence, prediction_result):
        """
        Extract and validate prediction confidence from signal or prediction result
        Returns float in range [0.0, 100.0]
        """
        # Try signal_confidence first (from TradingSignal)
        if signal_confidence is not None:
            try:
                conf = float(signal_confidence)
                return max(0.0, min(100.0, conf))  # Clamp to [0, 100]
            except (ValueError, TypeError):
                pass
        
        # Fallback to prediction_result confidence
        conf = prediction_result.get('confidence', 0.0)
        if conf is not None:
            try:
                conf = float(conf)
                return max(0.0, min(100.0, conf))  # Clamp to [0, 100]
            except (ValueError, TypeError):
                pass
        
        # Default to 0.0 if both fail
        _logger.warning(f'Failed to extract confidence, using 0.0. signal_confidence={signal_confidence}, prediction_result.confidence={prediction_result.get("confidence")}')
        return 0.0

    @staticmethod
    def _lean_indicator_defaults():
        return {
            'trend_ema_slope': 0.0,
            'momentum_rsi': 0.0,
            'volatility_atr_pct': 0.0,
            'volume_anomaly': 0.0,
        }

    @staticmethod
    def _sanitize_indicator_value(value):
        if value is None:
            return 0.0
        try:
            num = float(value)
        except (TypeError, ValueError):
            return 0.0
        if math.isnan(num) or math.isinf(num):
            return 0.0
        return num

