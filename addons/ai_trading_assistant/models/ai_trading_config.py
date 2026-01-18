# -*- coding: utf-8 -*-

import logging
import json
import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AITradingConfig(models.Model):
    """Configuration for AI Trading Assistant"""
    _name = 'ai.trading.config'
    _description = 'AI Trading Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        help='Configuration name for identification'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Only active configurations are used'
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True,
        help='User who owns this configuration'
    )

    strategy_count = fields.Integer(compute='_compute_strategy_count', string='Strategies')

    def _compute_strategy_count(self):
        for record in self:
            record.strategy_count = self.env['ai.strategy'].search_count([('config_id', '=', record.id)])

    def action_view_strategies(self):
        self.ensure_one()
        action = self.env.ref('ai_trading_assistant.action_ai_strategy').read()[0]
        action['domain'] = [('config_id', '=', self.id)]
        action['context'] = {'default_config_id': self.id}
        return action

    # Technical Indicator Config
    rsi_length = fields.Integer(string='RSI Length', default=14)
    macd_fast = fields.Integer(string='MACD Fast', default=12)
    macd_slow = fields.Integer(string='MACD Slow', default=26)
    macd_signal = fields.Integer(string='MACD Signal', default=9)
    sma_short = fields.Integer(string='SMA Sum (Short)', default=50)
    sma_long = fields.Integer(string='SMA Long', default=200)

    # SSI Configuration (Data Source)
    ssi_config_id = fields.Many2one(
        'ssi.api.config',
        string='SSI API Configuration',
        required=True,
        help='SSI FastConnect API configuration for Vietnamese stock market data'
    )

    # Trading Configuration (for placing orders)
    trading_config_id = fields.Many2one(
        'trading.config',
        string='Trading API Configuration',
        domain="[('user_id', '=', user_id), ('active', '=', True)]",
        help='Trading API configuration from stock_trading module for placing orders'
    )

    # ============================================
    # FinRL CONFIGURATION (Deep Reinforcement Learning)
    # ============================================
    
    finrl_model_dir = fields.Char(
        string='FinRL Model Directory',
        default='~/.finrl/models',
        help='Directory for saving trained FinRL models'
    )
    
    finrl_tensorboard_log = fields.Char(
        string='TensorBoard Log Directory',
        default='~/.finrl/logs',
        help='Directory for TensorBoard training logs'
    )
    
    drl_algorithm = fields.Selection([
        ('ppo', 'PPO - Proximal Policy Optimization'),
        ('a2c', 'A2C - Advantage Actor Critic'),
        ('sac', 'SAC - Soft Actor Critic'),
        ('td3', 'TD3 - Twin Delayed DDPG'),
        ('ddpg', 'DDPG - Deep Deterministic Policy Gradient'),
        ('ensemble', 'Ensemble - Voting Strategy (PPO + A2C + DDPG)'),
    ], string='DRL Algorithm', default='ppo',
       help='Deep Reinforcement Learning algorithm. Ensemble combines multiple agents for better stability.')
    
    training_timesteps = fields.Integer(
        string='Training Timesteps',
        default=0,
        help='Training timesteps. Set to 0 for Full Data mode (recommended - trains on entire dataset).'
    )
    
    learning_rate = fields.Float(
        string='Learning Rate',
        default=0.0003,
        digits=(16, 6),
        help='Learning rate for the DRL algorithm. Default: 0.0003 (3e-4)'
    )
    
    action_space_type = fields.Selection([
        ('discrete', 'Discrete (Buy/Hold/Sell)'),
        ('continuous', 'Continuous (Position Sizing)'),
    ], string='Action Space', default='discrete',
       help='Discrete: Simple buy/hold/sell actions. Continuous: Position sizing from -1 to +1.')
    
    finrl_batch_size = fields.Integer(
        string='Batch Size',
        default=64,
        help='Batch size for training. Used for PPO/A2C algorithms.'
    )
    
    finrl_n_steps = fields.Integer(
        string='N Steps',
        default=2048,
        help='Number of steps per training update. Used for PPO/A2C algorithms.'
    )
    
    finrl_gamma = fields.Float(
        string='Gamma (Discount Factor)',
        default=0.99,
        digits=(16, 4),
        help='Discount factor for future rewards. Higher = more weight on future rewards.'
    )

    # Optuna Hyperparameter Tuning
    enable_optuna = fields.Boolean(
        string='Enable Optuna Tuning',
        default=False,
        help='Automatically tune hyperparameters using Optuna BEFORE training.'
    )

    optuna_trials = fields.Integer(
        string='Optimization Trials',
        default=10,
        help='Number of optimization trials. Higher = better params but much longer time.'
    )

    optuna_timesteps = fields.Integer(
        string='Tuning Timesteps',
        default=20000,
        help='Timesteps per trial. Usually lower than final training timesteps.'
    )


    # Trading Mode
    trading_mode = fields.Selection([
        ('dry_run', 'Dry Run'),
        ('live', 'Live Trading'),
    ], string='Trading Mode', required=True, default='dry_run',
       help='Trading mode: Dry Run (simulation) or Live Trading')

    # Data Update Settings
    auto_update_data = fields.Boolean(
        string='Auto Update Data',
        default=True,
        help='Automatically update OHLCV data daily'
    )

    auto_retrain = fields.Boolean(
        string='Auto Retrain Model',
        default=False,
        help='Automatically retrain model when new data is available'
    )

    retrain_interval_days = fields.Integer(
        string='Retrain Interval (Days)',
        default=7,
        help='Number of days between model retraining'
    )

    # Prediction Generation Settings
    auto_generate_predictions = fields.Boolean(
        string='Auto Generate Predictions',
        default=True,
        help='Automatically generate predictions continuously for active strategies'
    )

    default_order_quantity = fields.Integer(
        string='Default Order Quantity',
        default=100,
        help='Quantity used when creating trading orders automatically from predictions'
    )
    
    prediction_interval_minutes = fields.Integer(
        string='Prediction Interval (Minutes)',
        default=1,
        help='Interval in minutes between prediction generations (e.g., 1 = every 1 minute). Lower value = more frequent predictions. Default: 1 minute for continuous predictions.'
    )

    prediction_min_interval_minutes = fields.Integer(
        string='Min Interval Between Predictions (Minutes)',
        default=1,
        help='Minimum interval in minutes before generating new prediction for same symbol (prevents duplicates). Set to 1 for maximum frequency. Default: 1 minute.'
    )

    # Chatbot Configuration
    enable_chatbot = fields.Boolean(
        string='Enable Chatbot',
        default=False,
        help='Enable AI chatbot for investment advisory'
    )

    is_investor_config = fields.Boolean(
        string='Investor Copilot Config',
        default=False,
        help='Configuration auto-generated for Investor Copilot portal users'
    )

    # ============================================
    # RISK MANAGEMENT SETTINGS (Based on FreqTrade)
    # ============================================
    
    # Position Sizing
    max_open_trades = fields.Integer(
        string='Max Open Trades',
        default=3,
        help='Maximum number of concurrent open trades. Based on FreqTrade max_open_trades.'
    )
    
    stake_amount = fields.Float(
        string='Stake Amount (VND)',
        default=10000000.0,  # 10M VND default
        help='Fixed amount per trade in VND. Set to 0 for unlimited (use tradable_balance_ratio instead).'
    )
    
    stake_amount_unlimited = fields.Boolean(
        string='Unlimited Stake Amount',
        default=False,
        help='If enabled, stake_amount is unlimited and uses tradable_balance_ratio instead.'
    )
    
    tradable_balance_ratio = fields.Float(
        string='Tradable Balance Ratio',
        default=0.99,
        digits=(16, 4),
        help='Ratio of available balance to use per trade (0.0-1.0). Example: 0.99 = 99%% of available balance.'
    )
    
    # Stoploss Configuration
    stoploss = fields.Float(
        string='Stoploss (%)',
        default=-0.10,
        digits=(16, 4),
        help='Stoploss percentage (negative value, e.g., -0.10 = -10%%). Based on FreqTrade stoploss.'
    )
    
    stoploss_on_exchange = fields.Boolean(
        string='Stoploss On Exchange',
        default=False,
        help='Place stoploss order directly on exchange (if supported by SSI). Otherwise, use off-exchange stoploss.'
    )
    
    stoploss_on_exchange_interval = fields.Integer(
        string='Stoploss Check Interval (seconds)',
        default=60,
        help='Interval in seconds to check and update stoploss on exchange.'
    )
    
    # Trailing Stoploss
    trailing_stop = fields.Boolean(
        string='Enable Trailing Stop',
        default=False,
        help='Enable trailing stoploss that moves up with price.'
    )
    
    trailing_stop_positive = fields.Float(
        string='Trailing Stop Positive (%)',
        default=0.02,
        digits=(16, 4),
        help='Trailing stoploss activates after this profit percentage (e.g., 0.02 = 2%%).'
    )
    
    trailing_stop_positive_offset = fields.Float(
        string='Trailing Stop Positive Offset (%)',
        default=0.01,
        digits=(16, 4),
        help='Offset from trailing_stop_positive to start trailing (e.g., 0.01 = 1%%).'
    )
    
    trailing_only_offset_is_reached = fields.Boolean(
        string='Trailing Only After Offset',
        default=False,
        help='Only activate trailing stop after trailing_stop_positive_offset is reached.'
    )
    
    # ROI (Return on Investment) Configuration
    minimal_roi = fields.Text(
        string='Minimal ROI (JSON)',
        default='{"0": 0.10, "60": 0.05, "120": 0.02, "240": 0}',
        help='Minimal ROI table in JSON format: {"time_in_minutes": roi_percentage}. Example: {"0": 0.10, "60": 0.05} means 10%% ROI required immediately, 5%% after 60 minutes.'
    )
    
    # ============================================
    # ORDER MANAGEMENT SETTINGS (Based on FreqTrade)
    # ============================================
    
    # Entry Pricing
    entry_pricing = fields.Selection([
        ('limit', 'Limit Order'),
        ('market', 'Market Order'),
        ('other', 'Other (ATO/ATC)'),
    ], string='Entry Pricing', default='limit',
       help='Order type for entry: Limit (better price control) or Market (faster execution).'
    )
    
    entry_pricing_price_side = fields.Selection([
        ('same', 'Same Side (bid/ask)'),
        ('other', 'Other Side'),
        ('other_side', 'Other Side (explicit)'),
    ], string='Entry Price Side', default='same',
       help='Price side for limit orders: same (bid for buy, ask for sell) or other.'
    )
    
    entry_pricing_check_depth_of_market = fields.Boolean(
        string='Check Depth of Market',
        default=False,
        help='Check order book depth before placing entry order (for better price).'
    )
    
    entry_pricing_use_order_book = fields.Boolean(
        string='Use Order Book',
        default=False,
        help='Use order book data to determine optimal entry price.'
    )
    
    # Exit Pricing
    exit_pricing = fields.Selection([
        ('limit', 'Limit Order'),
        ('market', 'Market Order'),
        ('other', 'Other (ATO/ATC)'),
    ], string='Exit Pricing', default='limit',
       help='Order type for exit: Limit (better price control) or Market (faster execution).'
    )
    
    exit_pricing_price_side = fields.Selection([
        ('same', 'Same Side (bid/ask)'),
        ('other', 'Other Side'),
        ('other_side', 'Other Side (explicit)'),
    ], string='Exit Price Side', default='same',
       help='Price side for limit orders: same (bid for buy, ask for sell) or other.'
    )
    
    # Order Time in Force (Vietnamese Market)
    order_time_in_force = fields.Selection([
        ('GTC', 'GTC - Good Till Cancel'),
        ('IOC', 'IOC - Immediate Or Cancel'),
        ('FOK', 'FOK - Fill Or Kill'),
        ('DAY', 'DAY - Day Order (VN Market)'),
    ], string='Order Time in Force', default='DAY',
       help='Order time in force: GTC (valid until cancelled), IOC (immediate or cancel), FOK (fill or kill), DAY (valid for trading day).'
    )
    
    # Vietnamese Market Specific Order Types
    use_ato_order = fields.Boolean(
        string='Use ATO Orders',
        default=False,
        help='Allow using ATO (At The Open) orders for market opening.'
    )
    
    use_atc_order = fields.Boolean(
        string='Use ATC Orders',
        default=False,
        help='Allow using ATC (At The Close) orders for market closing.'
    )
    
    # ============================================
    # TRADING RULES & PROTECTIONS (Vietnamese Market)
    # ============================================
    
    # Market Hours Validation
    validate_market_hours = fields.Boolean(
        string='Validate Market Hours',
        default=True,
        help='Only place orders during Vietnamese stock market trading hours (9:00-11:30, 13:00-15:00).'
    )
    
    market_open_time = fields.Char(
        string='Market Open Time',
        default='09:00',
        help='Market opening time (HH:MM format, Vietnam timezone).'
    )
    
    market_close_time = fields.Char(
        string='Market Close Time',
        default='15:00',
        help='Market closing time (HH:MM format, Vietnam timezone).'
    )
    
    # Position Limits (Vietnamese Market Regulations)
    max_position_per_security = fields.Float(
        string='Max Position Per Security (%)',
        default=100.0,
        digits=(16, 2),
        help='Maximum position size per security as percentage of portfolio (0-100). Vietnamese regulations may apply.'
    )
    
    max_position_value = fields.Float(
        string='Max Position Value (VND)',
        default=0.0,
        help='Maximum position value in VND per security. Set to 0 for unlimited.'
    )
    
    # Drawdown Protection
    max_drawdown = fields.Float(
        string='Max Drawdown (%)',
        default=0.20,
        digits=(16, 4),
        help='Maximum allowed drawdown percentage. Trading will pause if drawdown exceeds this value.'
    )
    
    # Cooldown Periods
    entry_cooldown_minutes = fields.Integer(
        string='Entry Cooldown (minutes)',
        default=0,
        help='Cooldown period in minutes after exiting a position before re-entering the same security.'
    )
    
    # ============================================
    # FEE & SLIPPAGE SETTINGS
    # ============================================
    
    trading_fee_percent = fields.Float(
        string='Trading Fee (%)',
        default=0.15,
        digits=(16, 4),
        help='Trading fee percentage (e.g., 0.15 = 0.15%%). Vietnamese market typical fee: 0.15%% per trade.'
    )
    
    slippage_percent = fields.Float(
        string='Slippage (%)',
        default=0.10,
        digits=(16, 4),
        help='Expected slippage percentage for backtesting (e.g., 0.10 = 0.10%%).'
    )
    
    # ============================================
    # ADVANCED SETTINGS
    # ============================================
    
    cancel_open_orders_on_exit = fields.Boolean(
        string='Cancel Open Orders On Exit',
        default=False,
        help='Cancel all open orders when bot exits (for safety).'
    )
    
    ignore_roi_if_entry_signal = fields.Boolean(
        string='Ignore ROI If Entry Signal',
        default=False,
        help='Ignore ROI and hold position if entry signal is still active.'
    )
    
    force_entry_enable = fields.Boolean(
        string='Force Entry Enable',
        default=False,
        help='Allow force entry even if max_open_trades limit is reached.'
    )
    
    # Notes
    notes = fields.Text(string='Notes')

    def action_check_auto_prediction_status(self):
        """Check and fix auto-prediction configuration"""
        self.ensure_one()
        
        issues = []
        fixes = []
        
        # Check if auto_generate_predictions is enabled
        if not self.auto_generate_predictions:
            issues.append('Auto Generate Predictions is disabled')
            fixes.append('Enable "Auto Generate Predictions" in Data Update tab')
            # Auto-fix
            self.auto_generate_predictions = True
            fixes.append('✓ Auto-enabled "Auto Generate Predictions"')
        
        # Check cron job
        cron = self.env['ir.cron'].search([
            ('name', '=', 'AI Trading: Auto Generate Predictions')
        ], limit=1)
        
        if not cron:
            issues.append('Cron job "AI Trading: Auto Generate Predictions" not found')
            fixes.append('Please update the module to create the cron job')
        elif not cron.active:
            issues.append('Cron job exists but is not active')
            fixes.append('Activating cron job...')
            cron.active = True
            fixes.append('✓ Cron job activated')
        
        # Check active strategies
        strategies = self.env['ai.strategy'].search([
            ('config_id', '=', self.id),
            ('state', '=', 'active')
        ])
        
        if not strategies:
            issues.append(f'No active strategies found for configuration "{self.name}"')
            fixes.append('Activate at least one strategy to enable auto-predictions')
        else:
            fixes.append(f'✓ Found {len(strategies)} active strategy(ies)')
            for strategy in strategies:
                fixes.append(f'  - {strategy.name}')
        
        # Build message
        if issues:
            message = _('Found %d issue(s):\n\n') % len(issues)
            for issue in issues:
                message += f'• {issue}\n'
            message += '\n' + _('Fixes applied:\n')
            for fix in fixes:
                message += f'• {fix}\n'
            
            # Return True - notification will be handled by view/controller
            return True
        else:
            # Return True - notification will be handled by view/controller
            return True

    def action_trigger_auto_prediction_now(self):
        """Manually trigger auto-prediction cron job"""
        self.ensure_one()
        
        if not self.auto_generate_predictions:
            raise UserError(_('Auto Generate Predictions is disabled. Please enable it first.'))
        
        # Trigger the cron job manually
        strategies = self.env['ai.strategy'].search([
            ('config_id', '=', self.id),
            ('state', '=', 'active')
        ])
        
        if not strategies:
            raise UserError(_('No active strategies found for this configuration.'))
        
        # Call the cron method directly
        try:
            self.env['ai.strategy']._cron_generate_predictions()
            message = _('Auto-prediction triggered successfully!\n\n')
            message += _('Check the Predictions menu to see new predictions.\n')
            message += _('Check Odoo logs for detailed information.')
            
        except Exception as e:
            raise UserError(_('Failed to trigger auto-prediction: %s\n\nCheck Odoo logs for details.') % str(e))

    def action_start_auto_prediction(self):
        """Start the Auto-Prediction Cron Job"""
        self.ensure_one()
        
        # 1. Enable flag on config
        self.write({'auto_generate_predictions': True})
        
        # 2. Find or Create Cron Job
        cron_name = 'AI Trading: Auto Generate Predictions'
        cron = self.env['ir.cron'].search([('name', '=', cron_name)], limit=1)
        
        if not cron:
            # Create Cron Programmatically
            cron = self.env['ir.cron'].create({
                'name': cron_name,
                'model_id': self.env.ref('ai_trading_assistant.model_ai_strategy').id,
                'state': 'code',
                'code': 'model._cron_generate_predictions()',
                'interval_number': 1,
                'interval_type': 'minutes',
                'active': True,
                'user_id': self.env.ref('base.user_root').id,
            })
            _logger.info(f"Created new auto-prediction cron: {cron.name}")
        else:
            if not cron.active:
                cron.write({'active': True})
                _logger.info(f"Activated existing auto-prediction cron: {cron.name}")
            else:
                 _logger.info(f"Auto-prediction cron already active: {cron.name}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-Prediction Started'),
                'message': _('The prediction loop is now running every minute.'),
                'type': 'success',
            }
        }

    def action_stop_auto_prediction(self):
        """Stop the Auto-Prediction Cron Job"""
        self.ensure_one()
        
        # 1. Disable flag
        self.write({'auto_generate_predictions': False})
        
        # 2. Find and Deactivate Cron
        cron_name = 'AI Trading: Auto Generate Predictions'
        cron = self.env['ir.cron'].search([('name', '=', cron_name)], limit=1)
        
        if cron and cron.active:
            cron.write({'active': False})
            _logger.info(f"Deactivated auto-prediction cron: {cron.name}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-Prediction Stopped'),
                'message': _('The prediction loop has been stopped.'),
                'type': 'warning',
            }
        }

    _sql_constraints = [
        ('user_config_unique', 'unique(user_id, name)',
         'Configuration name must be unique per user!')
    ]

    @api.constrains('ssi_config_id', 'stoploss', 'tradable_balance_ratio',
                    'max_open_trades', 'max_drawdown', 'trading_fee_percent', 'slippage_percent',
                    'minimal_roi', 'max_position_per_security')
    def _check_configuration(self):
        """Validate configuration"""
        for record in self:
            if not record.ssi_config_id:
                raise ValidationError(
                    _('SSI API Configuration is required')
                )
            
            # Validate risk management settings
            if record.stoploss > 0:
                raise ValidationError(
                    _('Stoploss must be negative (e.g., -0.10 for -10%%)')
                )
            
            if record.tradable_balance_ratio < 0 or record.tradable_balance_ratio > 1:
                raise ValidationError(
                    _('Tradable Balance Ratio must be between 0.0 and 1.0')
                )
            
            if record.max_open_trades < 1:
                raise ValidationError(
                    _('Max Open Trades must be at least 1')
                )
            
            if record.max_drawdown < 0 or record.max_drawdown > 1:
                raise ValidationError(
                    _('Max Drawdown must be between 0.0 and 1.0 (0%% to 100%%)')
                )
            
            if record.trading_fee_percent < 0:
                raise ValidationError(
                    _('Trading Fee must be non-negative')
                )
            
            if record.slippage_percent < 0:
                raise ValidationError(
                    _('Slippage must be non-negative')
                )
            
            # Validate minimal_roi JSON
            if record.minimal_roi:
                try:
                    roi_dict = json.loads(record.minimal_roi)
                    if not isinstance(roi_dict, dict):
                        raise ValidationError(
                            _('Minimal ROI must be a JSON object/dictionary')
                        )
                    for key, value in roi_dict.items():
                        try:
                            int(key)  # Time must be integer
                            float(value)  # ROI must be float
                        except (ValueError, TypeError):
                            raise ValidationError(
                                _('Minimal ROI format error: keys must be integers (minutes), values must be floats (ROI percentage)')
                            )
                except json.JSONDecodeError as e:
                    raise ValidationError(
                        _('Minimal ROI JSON is invalid: %s') % str(e)
                    )
            
            if record.max_position_per_security < 0 or record.max_position_per_security > 100:
                raise ValidationError(
                    _('Max Position Per Security must be between 0 and 100 (percentage)')
                    )

    @api.model
    def default_get(self, fields_list):
        """Set default trading_config_id from stock_trading."""
        res = super().default_get(fields_list)
        
        # Auto-get trading config from stock_trading for current user
        if 'trading_config_id' in fields_list and not res.get('trading_config_id'):
            user_id = res.get('user_id') or self.env.user.id
            trading_config = self.env['trading.config'].search([
                ('user_id', '=', user_id),
                ('active', '=', True)
            ], limit=1)
            if trading_config:
                res['trading_config_id'] = trading_config.id
        
        return res
    
    def get_stake_amount(self, available_balance=0.0):
        """
        Calculate stake amount for a trade based on configuration
        
        Args:
            available_balance: Available balance in VND
            
        Returns:
            float: Stake amount in VND
        """
        self.ensure_one()
        
        if self.stake_amount_unlimited or self.stake_amount <= 0:
            # Use tradable_balance_ratio
            return available_balance * self.tradable_balance_ratio
        else:
            # Use fixed stake_amount, but don't exceed available balance
            return min(self.stake_amount, available_balance * self.tradable_balance_ratio)
    
    def get_minimal_roi_dict(self):
        """
        Get minimal ROI as dictionary
        
        Returns:
            dict: {time_in_minutes: roi_percentage}
        """
        self.ensure_one()
        import json
        if not self.minimal_roi:
            return {"0": 0.10}  # Default: 10% ROI required
        
        try:
            return json.loads(self.minimal_roi)
        except (json.JSONDecodeError, TypeError):
            return {"0": 0.10}  # Fallback to default
    
    def check_roi(self, trade_profit_percent, time_in_minutes):
        """
        Check if trade meets minimal ROI requirement
        
        Args:
            trade_profit_percent: Current profit percentage (e.g., 0.05 = 5%)
            time_in_minutes: Time since entry in minutes
            
        Returns:
            bool: True if ROI requirement is met
        """
        self.ensure_one()
        roi_dict = self.get_minimal_roi_dict()
        
        # Find applicable ROI threshold
        applicable_roi = 0.0
        for time_key in sorted([int(k) for k in roi_dict.keys()], reverse=True):
            if time_in_minutes >= time_key:
                applicable_roi = roi_dict[str(time_key)]
                break
        
        return trade_profit_percent >= applicable_roi
    
    def is_market_hours(self, check_time=None):
        """
        Check if current time is within market hours
        
        Args:
            check_time: datetime object to check (default: now)
            
        Returns:
            bool: True if within market hours
        """
        self.ensure_one()
        
        if not self.validate_market_hours:
            return True  # Skip validation if disabled
        
        from datetime import datetime, time
        if check_time is None:
            check_time = fields.Datetime.now()
        
        # Parse market hours
        try:
            open_hour, open_min = map(int, self.market_open_time.split(':'))
            close_hour, close_min = map(int, self.market_close_time.split(':'))
        except (ValueError, AttributeError):
            # Default Vietnamese market hours
            open_hour, open_min = 9, 0
            close_hour, close_min = 15, 0
        
        current_time = check_time.time()
        morning_open = time(open_hour, open_min)
        morning_close = time(11, 30)  # Morning session ends at 11:30
        afternoon_open = time(13, 0)  # Afternoon session starts at 13:00
        afternoon_close = time(close_hour, close_min)
        
        # Check if within morning or afternoon session
        return (morning_open <= current_time <= morning_close) or \
               (afternoon_open <= current_time <= afternoon_close)
    
    def calculate_position_size(self, security_price, available_balance=0.0):
        """
        Calculate position size based on risk management settings
        
        Args:
            security_price: Current price of security
            available_balance: Available balance in VND
            
        Returns:
            dict: {
                'quantity': int,
                'value': float,
                'stake_amount': float,
            }
        """
        self.ensure_one()
        
        if security_price <= 0:
            return {'quantity': 0, 'value': 0.0, 'stake_amount': 0.0}
        
        # Get stake amount
        stake_amount = self.get_stake_amount(available_balance)
        
        # Apply max position value limit
        if self.max_position_value > 0:
            stake_amount = min(stake_amount, self.max_position_value)
        
        # Calculate quantity (must be integer, Vietnamese market uses lots)
        # Vietnamese market: 1 lot = 100 shares
        quantity = int((stake_amount / security_price) // 100) * 100  # Round down to nearest lot
        
        # Recalculate actual value
        actual_value = quantity * security_price
        
        return {
            'quantity': quantity,
            'value': actual_value,
            'stake_amount': stake_amount,
        }

    @api.model
    def get_user_config(self, user_id=None):
        """Get active configuration for user"""
        if not user_id:
            user_id = self.env.user.id
        config = self.search([
            ('user_id', '=', user_id),
            ('active', '=', True)
        ], limit=1)
        return config

    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Auto-set trading_config_id when user changes"""
        if self.user_id:
            trading_config = self.env['trading.config'].search([
                ('user_id', '=', self.user_id.id),
                ('active', '=', True)
            ], limit=1)
            if trading_config:
                self.trading_config_id = trading_config
            else:
                self.trading_config_id = False

    @api.model
    def _cron_update_data(self):
        """Cron job to auto-update data for active configurations"""
        configs = self.search([
            ('active', '=', True),
            ('auto_update_data', '=', True),
        ])

        for config in configs:
            try:
                # Get active strategies for this config
                strategies = self.env['ai.strategy'].search([
                    ('config_id', '=', config.id),
                    ('state', '=', 'active'),
                ])

                for strategy in strategies:
                    try:
                        # Get securities to update
                        if strategy.security_ids:
                            securities = strategy.security_ids
                        else:
                            # Get all active securities from market
                            securities = self.env['ssi.securities'].search([
                                ('market', '=', strategy.market),
                                ('is_active', '=', True)
                            ])
                        
                        # Import SSI client - try multiple import paths
                        try:
                            from ..ssi_client import SSIClient
                        except ImportError:
                            try:
                                # Try importing from ssi_client module directly
                                from . import ssi_client
                                SSIClient = ssi_client.SSIClient
                            except (ImportError, AttributeError):
                                try:
                                    # Try absolute import as last resort
                                    from odoo.addons.ai_trading_assistant.models.ssi_client import SSIClient
                                except ImportError as e:
                                    _logger.error(f'Failed to import SSIClient: {e}', exc_info=True)
                                    raise UserError(_('Failed to import SSIClient. Please restart Odoo server and upgrade the module. Error: %s') % str(e))
                        client = SSIClient(config=config.ssi_config_id, env=self.env)
                        
                        # Download latest data for all securities
                        from datetime import datetime, timedelta
                        to_date = datetime.now().date()
                        from_date = to_date - timedelta(days=7)  # Last 7 days
                        
                        for security in securities:
                            try:
                                client.get_daily_ohlc(
                                    symbol=security.symbol,
                                    from_date=from_date,
                                    to_date=to_date,
                                    market=security.market,
                                )
                            except Exception as e:
                                _logger.warning(f'Failed to update data for {security.symbol}: {e}')

                        _logger.info(f'Data updated for strategy {strategy.name} ({len(securities)} securities)')

                    except Exception as e:
                        _logger.error(f'Failed to update data for strategy {strategy.name}: {e}')

            except Exception as e:
                _logger.error(f'Failed to update data for config {config.name}: {e}')

