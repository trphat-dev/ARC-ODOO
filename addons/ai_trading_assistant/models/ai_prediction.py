# -*- coding: utf-8 -*-

import logging
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .trading_signal import TradingSignal

_logger = logging.getLogger(__name__)


class AIPrediction(models.Model):
    """AI Model Predictions"""
    _name = 'ai.prediction'
    _description = 'AI Prediction'
    _order = 'prediction_date desc, create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Prediction Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )

    def _broadcast_update(self):
        """Broadcast prediction update to WebSocket channel and create notifications"""
        for record in self:
            payload = {
                'type': 'prediction_update',
                'prediction_id': record.id,
                'symbol': record.symbol,
                'market': record.market,
                'signal': record.final_signal,
                'confidence': record.prediction_confidence,
                'current_price': record.current_price,
                'date': fields.Datetime.to_string(record.prediction_date),
            }
            # Broadcast to general channel
            self.env['bus.bus']._sendone(
                'ai_prediction_channel',
                'notification',
                payload
            )
            
            # Create notifications for users with this security in watchlist
            if record.final_signal in ['buy', 'sell'] and record.security_id:
                watchlist_items = self.env['ai.chatbot.watchlist'].sudo().search([
                    ('security_id', '=', record.security_id.id),
                    ('is_active', '=', True),
                ])
                
                for item in watchlist_items:
                    # Check if notification already exists for this prediction
                    existing = self.env['ai.chatbot.notification'].sudo().search([
                        ('user_id', '=', item.user_id.id),
                        ('prediction_id', '=', record.id),
                    ], limit=1)
                    
                    if not existing:
                        self.env['ai.chatbot.notification'].sudo().create({
                            'user_id': item.user_id.id,
                            'prediction_id': record.id,
                            'signal_type': record.final_signal,
                        })
                        
                        # Send WebSocket notification to specific user
                        signal_payload = {
                            'type': 'signal_notification',
                            'prediction_id': record.id,
                            'symbol': record.symbol,
                            'signal_type': record.final_signal,
                            'confidence': record.prediction_confidence,
                            'current_price': record.current_price,
                        }
                        self.env['bus.bus']._sendone(
                            f'ai_signal_{item.user_id.id}',
                            'notification',
                            signal_payload
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

    # Prediction Data
    prediction_date = fields.Datetime(
        string='Prediction Date',
        required=True,
        default=fields.Datetime.now
    )

    security_id = fields.Many2one(
        'ssi.securities',
        string='Security'
    )
    
    symbol = fields.Char(
        related='security_id.symbol',
        string='Symbol',
        readonly=True,
        store=True
    )

    market = fields.Selection(
        related='strategy_id.market',
        string='Market',
        readonly=True,
        store=True
    )

    # Market Data at Prediction Time
    current_price = fields.Float(
        string='Current Price',
        readonly=True
    )

    trend_ema_slope = fields.Float(
        string='EMA20 Slope',
        readonly=True
    )

    momentum_rsi = fields.Float(
        string='Lean RSI 14',
        readonly=True
    )

    volatility_atr_pct = fields.Float(
        string='ATR / Price',
        readonly=True
    )

    volume_anomaly = fields.Float(
        string='Volume / MA20',
        readonly=True
    )

    rsi_value = fields.Float(
        string='RSI Value',
        readonly=True
    )

    # Golden Cross / Death Cross (SMA 50-200)
    sma_50_value = fields.Float(
        string='SMA 50 Value',
        readonly=True
    )

    sma_200_value = fields.Float(
        string='SMA 200 Value',
        readonly=True
    )

    ma_signal_type = fields.Selection([
        ('golden_cross', 'Golden Cross'),
        ('death_cross', 'Death Cross'),
        ('uptrend', 'Uptrend'),
        ('downtrend', 'Downtrend'),
        ('none', 'No Signal'),
    ], string='MA Signal Type', readonly=True)
    
    ma_cross_above = fields.Boolean(
        string='MA Cross Above',
        readonly=True
    )
    
    ma_cross_below = fields.Boolean(
        string='MA Cross Below',
        readonly=True
    )
    
    # MACD Confirmation
    macd_value = fields.Float(
        string='MACD Value',
        readonly=True
    )

    macd_signal_value = fields.Float(
        string='MACD Signal Value',
        readonly=True
    )

    macd_hist_value = fields.Float(
        string='MACD Histogram Value',
        readonly=True
    )

    macd_bullish = fields.Boolean(
        string='MACD Bullish',
        readonly=True
    )

    macd_bearish = fields.Boolean(
        string='MACD Bearish',
        readonly=True
    )

    # Volume Filter
    volume_ratio = fields.Float(
        string='Volume Ratio',
        readonly=True
    )

    volume_above_threshold = fields.Boolean(
        string='Volume Above Threshold',
        readonly=True
    )

    # AI Prediction
    buy_signal = fields.Boolean(
        string='Buy Signal',
        readonly=True
    )

    sell_signal = fields.Boolean(
        string='Sell Signal',
        readonly=True
    )

    hold_signal = fields.Boolean(
        string='Hold Signal',
        readonly=True
    )

    lean_signal_state = fields.Selection([
        ('buy', 'BUY ATC'),
        ('sell', 'SELL ATC'),
        ('wait', 'WAIT'),
    ], string='Lean Signal', readonly=True)

    action_value = fields.Float(
        string='Raw Action',
        readonly=True,
        help='Raw action value mapped from the FinRL agent.'
    )

    prediction_confidence = fields.Float(
        string='Confidence',
        readonly=True
    )

    # Actionable Advice
    entry_price_min = fields.Float(string='Entry Min', readonly=True)
    entry_price_max = fields.Float(string='Entry Max', readonly=True)
    stop_loss_price = fields.Float(string='Stop Loss', readonly=True)
    take_profit_price = fields.Float(string='Take Profit', readonly=True)
    recommended_percent = fields.Float(string='Recommended Allocation (%)', readonly=True, digits=(16, 2))


    # Strategy Logic Signals
    strategy_buy_signal = fields.Boolean(
        string='Strategy Buy Signal',
        compute='_compute_strategy_signals',
        store=True,
        readonly=True
    )

    strategy_sell_signal = fields.Boolean(
        string='Strategy Sell Signal',
        compute='_compute_strategy_signals',
        store=True,
        readonly=True
    )

    @api.depends('current_price', 'rsi_value', 'sma_50_value', 'sma_200_value',
                 'ma_signal_type', 'macd_bullish', 'macd_bearish', 'volume_above_threshold',
                 'strategy_id.rsi_buy_level', 'strategy_id.rsi_sell_level')
    def _compute_strategy_signals(self):
        """Compute strategy signals based on Vietnamese Market Strategy"""
        for record in self:
            if not record.strategy_id:
                record.strategy_buy_signal = False
                record.strategy_sell_signal = False
                continue

            # BUY Condition: Golden Cross AND RSI > rsiBuyMin AND MACD > Signal AND Volume OK
            buy_condition = (
                record.ma_signal_type == 'golden_cross' and
                record.rsi_value > record.strategy_id.rsi_buy_level and  # RSI phải > 45 (mạnh)
                record.macd_bullish and  # MACD > Signal
                record.volume_above_threshold  # Volume cao
            )

            # SELL Condition: Death Cross OR RSI < rsiSellMax
            sell_condition = (
                record.ma_signal_type == 'death_cross' or
                record.rsi_value < record.strategy_id.rsi_sell_level  # RSI < 55 (yếu đi)
            )

            record.strategy_buy_signal = buy_condition
            record.strategy_sell_signal = sell_condition

    # Final Decision
    final_signal = fields.Selection([
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('hold', 'Hold'),
    ], string='Final Signal', readonly=True)

    # Raw Prediction Data (JSON)
    raw_prediction = fields.Text(
        string='Raw Prediction (JSON)',
        readonly=True
    )

    # Action Taken
    order_placed = fields.Boolean(
        string='Order Placed',
        readonly=True
    )



    # ============================================
    # RISK METRICS
    # ============================================
    
    risk_reward_ratio = fields.Float(
        string='Risk/Reward Ratio',
        compute='_compute_risk_metrics',
        store=False,
        readonly=True
    )
    
    expected_profit = fields.Float(
        string='Expected Profit (%)',
        compute='_compute_risk_metrics',
        store=False,
        readonly=True,
        help='Expected profit percentage based on strategy ROI'
    )
    
    max_loss = fields.Float(
        string='Max Loss (%)',
        compute='_compute_risk_metrics',
        store=False,
        readonly=True,
        help='Maximum loss percentage based on stoploss'
    )
    
    position_size_value = fields.Float(
        string='Position Size (VND)',
        compute='_compute_position_size',
        store=False,
        readonly=True,
        help='Calculated position size in VND based on risk management'
    )
    
    position_size_quantity = fields.Integer(
        string='Position Size (Quantity)',
        compute='_compute_position_size',
        store=False,
        readonly=True,
        help='Calculated position quantity (lots) based on risk management'
    )
    
    # Notes
    notes = fields.Text(string='Notes')
    
    @api.depends('current_price', 'strategy_id', 'config_id')
    def _compute_risk_metrics(self):
        """Compute risk metrics for prediction"""
        for record in self:
            if not record.current_price or not record.strategy_id or not record.config_id:
                record.risk_reward_ratio = 0.0
                record.expected_profit = 0.0
                record.max_loss = 0.0
                continue
            
            config = record.config_id
            
            # Get minimal ROI (expected profit)
            roi_dict = config.get_minimal_roi_dict()
            if roi_dict:
                # Use first ROI value (immediate ROI)
                record.expected_profit = float(list(roi_dict.values())[0]) * 100  # Convert to percentage
            else:
                record.expected_profit = 10.0  # Default 10%
            
            # Get stoploss (max loss)
            stoploss = config.stoploss
            record.max_loss = abs(stoploss) * 100  # Convert to positive percentage
            
            # Calculate risk/reward ratio
            if record.max_loss > 0:
                record.risk_reward_ratio = record.expected_profit / record.max_loss
            else:
                record.risk_reward_ratio = 0.0
    
    @api.depends('current_price', 'strategy_id', 'config_id')
    def _compute_position_size(self):
        """Compute position size based on risk management"""
        for record in self:
            if not record.current_price or not record.strategy_id or not record.config_id:
                record.position_size_value = 0.0
                record.position_size_quantity = 0
                continue
            
            config = record.config_id
            
            # Get available balance (simplified - in real scenario, get from account)
            # For now, use dry_run_wallet or default
            try:
                # 1. Try to get REAL balance from connected Trading Account
                real_balance = 0.0
                if config.trading_config_id and config.trading_config_id.account:
                     # Search for balance record
                     balance_rec = self.env['trading.account.balance'].search([
                         ('config_id', '=', config.trading_config_id.id),
                         ('account', '=', config.trading_config_id.account)
                     ], order='create_date desc', limit=1)
                     
                if balance_rec:
                     # Use purchasing power if available, else cash balance
                     real_balance = balance_rec.purchasing_power or balance_rec.available_cash or balance_rec.cash_balance
                
                # STRICT: No mock data allowed.
                available_balance = real_balance
            except (json.JSONDecodeError, ValueError, TypeError, Exception):
                available_balance = 0.0
            
            # Calculate position size
            position_info = config.calculate_position_size(
                security_price=record.current_price,
                available_balance=available_balance
            )
            
            record.position_size_value = position_info['value']
            record.position_size_quantity = position_info['quantity']

    # Removed action_place_order, _determine_buy_sell_signal, _validate_order_conditions, _prepare_trading_order_values




    @api.model
    def create(self, vals):
        """Generate sequence and compute final signal"""
        if vals.get('name', _('New')) == _('New'):
            try:
                sequence_code = 'ai.prediction'
                sequence = self.env['ir.sequence'].search([
                    ('code', '=', sequence_code)
                ], limit=1)
                
                if sequence:
                    vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or _('New')
                else:
                    _logger.warning(f'Sequence {sequence_code} not found, using fallback naming')
                    existing_count = self.search_count([])
                    vals['name'] = f'PRED-{str(existing_count + 1).zfill(5)}'
            except Exception as e:
                _logger.error(f'Error generating sequence: {e}', exc_info=True)
                existing_count = self.search_count([])
                vals['name'] = f'PRED-{str(existing_count + 1).zfill(5)}'

        # Compute final signal
        if 'final_signal' not in vals:
            buy_signal = vals.get('buy_signal', False)
            sell_signal = vals.get('sell_signal', False)
            if buy_signal:
                vals['final_signal'] = 'buy'
            elif sell_signal:
                vals['final_signal'] = 'sell'
            else:
                vals['final_signal'] = 'hold'

        records = super().create(vals)
        records._notify_investor_channels()
        return records

    def _notify_investor_channels(self):
        """Push prediction updates to investor bus channels"""
        bus = self.env['bus.bus'].sudo()
        intraday_model = self.env['ssi.intraday.ohlc'].sudo()

        for prediction in self:
            user = prediction.strategy_id.user_id
            security = prediction.security_id
            if not user or not security:
                continue

            today = fields.Date.context_today(prediction)
            intraday_records = intraday_model.search([
                ('security_id', '=', security.id),
                ('date', '=', today),
            ], order='time desc', limit=2)

            if not intraday_records:
                continue

            latest = intraday_records[0]
            previous = intraday_records[1] if len(intraday_records) > 1 else None

            last_close = float(latest.close_price or 0.0)
            prev_close = float(previous.close_price or 0.0) if previous else None
            if prev_close and prev_close != 0:
                change_percent = ((last_close - prev_close) / prev_close) * 100.0
            else:
                change_percent = 0.0

            direction = 'flat'
            if prev_close:
                if last_close > prev_close:
                    direction = 'up'
                elif last_close < prev_close:
                    direction = 'down'

            payload = {
                'type': 'investor_signal_update',
                'user_id': user.id,
                'security_id': security.id,
                'symbol': security.symbol,
                'market': security.market or '',
                'company_name': getattr(security, 'stock_name_vn', False) or getattr(security, 'stock_name_en', '') or '',
                'prediction': {
                    'id': prediction.id,
                    'final_signal': prediction.final_signal or 'hold',
                    'confidence': float(prediction.prediction_confidence or 0.0),
                    'generated_at': prediction.prediction_date.isoformat() if prediction.prediction_date else None,
                },
                'ohlc': {
                    'open': float(latest.open_price or 0.0),
                    'high': float(latest.high_price or 0.0),
                    'low': float(latest.low_price or 0.0),
                    'close': last_close,
                    'volume': float(latest.volume or 0.0),
                },
                'change_percent': change_percent,
                'trend_direction': direction,
                'timestamp': prediction.prediction_date.isoformat() if prediction.prediction_date else None,
            }

            channel = f'ai.investor.signal.{user.id}'
            try:
                bus._sendone(channel, payload)
            except Exception as err:
                _logger.warning("Failed to push investor signal update for %s: %s", security.symbol, err)

    def action_view_chart(self):
        """Open technical chart for the symbol"""
        self.ensure_one()
        if not self.symbol:
            return
            
        return {
            "type": "ir.actions.client",
            "tag": "ai_trading_assistant.technical_chart_action",
            "name": f"Technical Chart - {self.symbol}",
            "params": {
                "prediction_id": self.id,
                "symbol": self.symbol,
                "market": self.market,
                "days": 60,
            }
        }

