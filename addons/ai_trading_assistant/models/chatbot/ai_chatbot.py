# -*- coding: utf-8 -*-

import logging
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)


class AIChatbotConversation(models.Model):
    """AI Chatbot Conversations"""
    _name = 'ai.chatbot.conversation'
    _description = 'AI Chatbot Conversation'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Conversation Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True,
        help='User who owns this conversation'
    )

    config_id = fields.Many2one(
        'ai.trading.config',
        string='Configuration',
        help='AI Trading configuration (for context)'
    )

    # Conversation Data
    messages = fields.One2many(
        'ai.chatbot.message',
        'conversation_id',
        string='Messages',
        help='Messages in this conversation'
    )

    message_count = fields.Integer(
        string='Message Count',
        compute='_compute_message_count',
        store=True
    )

    @api.depends('messages')
    def _compute_message_count(self):
        """Compute message count"""
        for record in self:
            record.message_count = len(record.messages)

    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Active conversations are shown in chatbot interface'
    )

    # Notes
    notes = fields.Text(string='Notes')

    @api.model
    def chat_wrapper(self, message=None, context=None, conversation_id=None, **kwargs):
        """Wrapper to be called via ORM Service from frontend"""
        try:
            if context is None:
                context = kwargs.get('context', {})

            # Handle both direct params and JSON payload
            message = message or kwargs.get('message')
            conversation_id = conversation_id or context.get('conversation_id') or kwargs.get('conversation_id')
            
            if not message:
                return {'success': False, 'error': _('Message is required')}

            conversation = None
            if conversation_id:
                conversation = self.browse(int(conversation_id))
                if not conversation.exists() or conversation.user_id != self.env.user:
                    return {'success': False, 'error': _('Conversation not found')}
            else:
                conversation = self.create({
                    'user_id': self.env.user.id,
                    'config_id': context.get('config_id') if context else False,
                })

            assistant_message = conversation.action_send_message(message, context=context or {})
            
            messages_payload = [
                {'role': 'user', 'content': message},
                {'role': assistant_message.role, 'content': assistant_message.content, 'is_error': assistant_message.is_error},
            ]
            
            # Include reasoning details if available
            if assistant_message.reasoning_details:
                messages_payload[1]['reasoning_details'] = assistant_message.reasoning_details

            return {
                'success': True,
                'data': {
                    'conversation_id': conversation.id,
                    'conversation_name': conversation.name,
                    'messages': messages_payload,
                }
            }
        except Exception as e:
            _logger.error('chat_wrapper error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ==========================================
    # Watchlist & Notification Methods
    # ==========================================
    
    @api.model
    def get_watchlist(self):
        """Get current user's watchlist"""
        return self.env['ai.chatbot.watchlist'].get_user_watchlist()

    @api.model
    def add_to_watchlist(self, security_id):
        """Add a security to current user's watchlist"""
        try:
            watchlist_id = self.env['ai.chatbot.watchlist'].add_security(security_id)
            return {'success': True, 'watchlist_id': watchlist_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def remove_from_watchlist(self, security_id):
        """Remove a security from current user's watchlist"""
        try:
            result = self.env['ai.chatbot.watchlist'].remove_security(security_id)
            return {'success': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def get_pending_notifications(self):
        """Get current user's pending signal notifications"""
        notifications = self.env['ai.chatbot.notification'].get_pending_notifications()
        unread_count = self.env['ai.chatbot.notification'].get_unread_count()
        return {
            'notifications': notifications,
            'unread_count': unread_count,
        }

    @api.model
    def confirm_trade(self, notification_id, quantity=100):
        """Confirm trade for a notification"""
        notification = self.env['ai.chatbot.notification'].browse(notification_id)
        if not notification.exists() or notification.user_id != self.env.user:
            return {'success': False, 'error': _('Notification not found')}
        return notification.confirm_trade(quantity)

    @api.model
    def dismiss_notification(self, notification_id):
        """Dismiss a notification"""
        notification = self.env['ai.chatbot.notification'].browse(notification_id)
        if not notification.exists() or notification.user_id != self.env.user:
            return {'success': False, 'error': _('Notification not found')}
        notification.dismiss()
        return {'success': True}

    @api.model
    def get_available_securities(self, search_term='', limit=20):
        """Get list of securities available to add to watchlist"""
        # Find securities that belong to active strategies that are trained
        active_strategies = self.env['ai.strategy'].search([
            ('user_id', '=', self.env.user.id),
            ('state', 'in', ['trained', 'active']),
        ])
        
        allowed_security_ids = []
        for strategy in active_strategies:
            allowed_security_ids.extend(strategy.security_ids.ids)
                
        domain = [('id', 'in', list(set(allowed_security_ids)))]
        
        if search_term:
            domain.append(('symbol', 'ilike', search_term))
        
        securities = self.env['ssi.securities'].search(domain, limit=limit)
        return [{
            'id': s.id,
            'symbol': s.symbol,
            'name': s.stock_name_vn or s.stock_name_en, # Use correct field names from Securities model
            'market': s.market,
        } for s in securities]


    def action_send_message(self, message_text, context=None):
        """Send message to chatbot and get response"""
        self.ensure_one()

        # Create user message
        user_message = self.env['ai.chatbot.message'].create({
            'conversation_id': self.id,
            'role': 'user',
            'content': message_text,
        })

        try:
            # Get chatbot response
            response = self._get_chatbot_response(message_text, extra_context=context or {})

            # Extract content and reasoning_details if available (for OpenRouter)
            content = response
            reasoning_details_json = None
            
            if isinstance(response, dict):
                content = response.get('content', str(response))
                if 'reasoning_details' in response:
                    import json
                    reasoning_details_json = json.dumps(response['reasoning_details'])

            # Create assistant message
            assistant_message = self.env['ai.chatbot.message'].create({
                'conversation_id': self.id,
                'role': 'assistant',
                'content': content,
                'reasoning_details': reasoning_details_json,
            })

            return assistant_message

        except Exception as e:
            _logger.error(f'Chatbot error: {e}', exc_info=True)
            error_message = self.env['ai.chatbot.message'].create({
                'conversation_id': self.id,
                'role': 'assistant',
                'content': _('Sorry, I encountered an error: %s') % str(e),
                'is_error': True,
            })
            return error_message

    def _get_chatbot_response(self, message_text, extra_context=None):
        """Get response from chatbot"""
        config = self.config_id or self.env['ai.trading.config'].get_user_config()

        if not config or not config.enable_chatbot:
            return _('Chatbot is not enabled. Please configure it in AI Trading Settings.')

        # Get context from user's strategies and predictions
        context = self._build_chatbot_context()
        if extra_context:
            context['investor_context'] = extra_context

        # Call OpenRouter chatbot API
        return self._call_openrouter_chatbot(message_text, context)

        return context

    def _build_chatbot_context(self):
        """Build context for chatbot from user's data and FinRL metrics"""
        context = {
            'strategies': [],
            'recent_predictions': [],
            'recent_orders': [],
            'finrl_metrics': [],
        }

        watchlist_security_ids = self._get_watchlist_security_ids()
        watchlist_symbols = []
        if watchlist_security_ids:
            watchlist_symbols = self.env['ssi.securities'].sudo().browse(watchlist_security_ids).mapped('symbol')

        # Get user's strategies
        strategy_domain = [
            ('user_id', '=', self.user_id.id),
            ('state', '=', 'active'),
        ]
        if watchlist_security_ids:
            strategy_domain.append(('security_ids', 'in', watchlist_security_ids))

        strategies = self.env['ai.strategy'].search(strategy_domain, limit=5)

        for strategy in strategies:
            symbols = [s.symbol for s in strategy.security_ids] if strategy.security_ids else ['All securities']
            if watchlist_symbols:
                symbols = [symbol for symbol in symbols if symbol in watchlist_symbols]
                if not symbols:
                    continue

            # Fetch latest training result for FinRL insights
            last_training = self.env['ai.model.training'].search([
                ('strategy_id', '=', strategy.id),
                ('state', '=', 'completed')
            ], order='create_date desc', limit=1)

            finrl_data = {}
            if last_training:
                finrl_data = {
                    'reward': last_training.cumulative_reward,
                    'sharpe_ratio': last_training.sharpe_ratio,
                    'max_drawdown': last_training.max_drawdown,
                }

            context['strategies'].append({
                'name': strategy.name,
                'symbols': symbols,
                'symbol': strategy.symbol,  # First symbol for backward compatibility
                'market': strategy.market,
                'model_accuracy': strategy.model_accuracy,
                'model_type': strategy.model_type,
                'finrl_stats': finrl_data,
            })

        # Get recent predictions
        prediction_domain = [
            ('strategy_id.user_id', '=', self.user_id.id),
        ]
        if watchlist_security_ids:
            prediction_domain.append(('security_id', 'in', watchlist_security_ids))

        predictions = self.env['ai.prediction'].search(prediction_domain, order='prediction_date desc', limit=5)

        for prediction in predictions:
            context['recent_predictions'].append({
                'symbol': prediction.symbol,
                'date': prediction.prediction_date.strftime('%Y-%m-%d %H:%M:%S'),
                'signal': prediction.final_signal,
                'confidence': prediction.prediction_confidence,
                'entry_min': prediction.entry_price_min,
                'entry_max': prediction.entry_price_max,
                'stop_loss': prediction.stop_loss_price,
                'take_profit': prediction.take_profit_price,
                'alloc_pct': prediction.recommended_percent,
            })

        # Get recent orders
        orders = []


        # Add Portfolio Context
        try:
            # 1. Account Balance
            balance_rec = self.env['trading.account.balance'].search([
                ('user_id', '=', self.user_id.id)
            ], order='create_date desc', limit=1)

            if balance_rec:
                context['portfolio_balance'] = {
                    'account': balance_rec.account,
                    'cash_balance': balance_rec.cash_balance,
                    'purchasing_power': balance_rec.purchasing_power or balance_rec.cash_balance, # Ensure PP available
                    'last_sync': balance_rec.last_sync,
                }

                # 2. Positions (linked via config_id)
                if balance_rec.config_id:
                    position_recs = self.env['trading.position'].search([
                        ('config_id', '=', balance_rec.config_id.id)
                    ], order='create_date desc', limit=5) # Limit to avoid token overflow
                    
                    positions = []
                    for pos in position_recs:
                        try:
                            if pos.raw_response:
                                data = json.loads(pos.raw_response)
                                # Simple extraction if it is standard SSI format
                                # If it's a list directly
                                if isinstance(data, list):
                                    positions.extend(data)
                                # If it's dict with data key
                                elif isinstance(data, dict) and 'data' in data:
                                    if isinstance(data['data'], list):
                                        positions.extend(data['data'])
                                    else:
                                        positions.append(data['data'])
                                else:
                                    positions.append(data)
                        except Exception:
                            continue
                    
                    # Sanitize positions to save tokens
                    sanitized_positions = []
                    for p in positions:
                        if isinstance(p, dict):
                            # Try to extract common fields
                            symbol = p.get('instrumentCode') or p.get('symbol') or p.get('stockCode')
                            qty = p.get('quantity') or p.get('totalShare') or p.get('onHand')
                            avg_price = p.get('avgPrice') or p.get('averagePrice') or p.get('costPrice')
                            market_price = p.get('marketPrice') or p.get('currentPrice')
                            
                            if symbol:
                                sanitized_positions.append({
                                    'symbol': symbol,
                                    'quantity': qty,
                                    'avg_price': avg_price,
                                    'market_price': market_price,
                                })
                    
                    context['portfolio_positions'] = sanitized_positions

        except Exception as e:
            _logger.warning("Error fetching portfolio context: %s", e)

        return context

    def _get_watchlist_security_ids(self):
        """Load watchlist securities for this user from investor config"""
        icp = self.env['ir.config_parameter'].sudo()
        key = f'ai_trading_assistant.chatbot_config.{self.user_id.id}'
        raw = icp.get_param(key, '')
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except Exception:
            return []
        selected_ids = data.get('selected_security_ids') or []
        return [int(sec_id) for sec_id in selected_ids if sec_id]

    def _call_openrouter_chatbot(self, message_text, context):
        """Call OpenRouter chatbot API using global configuration"""
        global_config = self.env['ai.chatbot.global.config'].sudo().get_active_config()

        if not global_config or not global_config.api_key:
            raise UserError(_('Chatbot API key is not configured. Please contact your administrator.'))

        try:
            from openai import OpenAI
            
            # Initialize OpenRouter client with base_url
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=global_config.api_key,
            )

            # Build system prompt
            system_prompt = self._build_system_prompt(context)
            
            # Prepare messages with conversation history if available
            messages = [
                {'role': 'system', 'content': system_prompt},
            ]
            
            # Add conversation history from previous messages
            if self.messages:
                for msg in self.messages.sorted('create_date'):
                    if msg.role in ['user', 'assistant']:
                        message_dict = {
                            'role': msg.role,
                            'content': msg.content,
                        }
                        # Preserve reasoning_details if available (for models that support it)
                        if msg.reasoning_details:
                            try:
                                import json
                                reasoning_details = json.loads(msg.reasoning_details)
                                message_dict['reasoning_details'] = reasoning_details
                            except (json.JSONDecodeError, TypeError):
                                pass
                        messages.append(message_dict)
            
            # Add current user message
            messages.append({'role': 'user', 'content': message_text})
            
            # Call OpenRouter API with reasoning support for compatible models
            model = global_config.model_name or 'xiaomi/mimo-v2-flash:free'
            extra_body = {}
            
            # Enable reasoning/usage for models that support it
            if 'xiaomi' in model.lower() or 'mimo' in model.lower():
                extra_body = {"include_usage": True}
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                extra_body=extra_body if extra_body else None,
            )
            
            # Extract response
            assistant_message_obj = response.choices[0].message
            
            # Store reasoning_details if available for next message
            reasoning_details = None
            if hasattr(assistant_message_obj, 'reasoning_details') and assistant_message_obj.reasoning_details:
                reasoning_details = assistant_message_obj.reasoning_details
                _logger.debug(f'Received reasoning_details from OpenRouter: {reasoning_details}')
        
            # Return content and reasoning_details as dict for message creation
            result = {
                'content': assistant_message_obj.content,
            }
            if reasoning_details:
                result['reasoning_details'] = reasoning_details
            
            return result

        except ImportError:
            raise UserError(_('OpenAI library is not installed. Please install it: pip install openai\nNote: OpenRouter uses the OpenAI Python SDK for compatibility.'))
        except Exception as e:
            _logger.error(f'OpenRouter API error: {e}', exc_info=True)
            raise UserError(_('OpenRouter API error: %s') % str(e))

    _prompt_template_cache = None

    def _build_system_prompt(self, context):
        """Build system prompt for chatbot"""
        prompt = self._get_prompt_template()
        
        prompt += "\n\n=== FINRL STRATEGY CONTEXT ===\n"
        for strategy in context.get('strategies', []):
            prompt += f"\nStrategy: {strategy['name']} [{strategy['model_type']}] ({strategy['market']})\n"
            prompt += f"Accuracy: {strategy.get('model_accuracy', 0):.2f}%\n"
            
            stats = strategy.get('finrl_stats', {})
            if stats:
                prompt += f"Training Metrics:\n"
                prompt += f"  - Cumulative Reward: {stats.get('reward', 0):.2f}\n"
                prompt += f"  - Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}\n"
                prompt += f"  - Max Drawdown: {stats.get('max_drawdown', 0):.2f}\n"
                prompt += f"  - Entropy (Exploration): {stats.get('entropy', 0):.4f}\n"
                prompt += f"  - Explained Variance: {stats.get('explained_variance', 0):.4f}\n"

        prompt += "\n=== RECENT AI PREDICTIONS ===\n"
        for pred in context.get('recent_predictions', []):
            prompt += f"- {pred['symbol']} ({pred['date']}): {pred['signal']} (Confidence: {pred.get('confidence', 0):.2f}%)\n"
            if pred.get('signal') == 'buy':
                 prompt += f"  * ACTION: Buy Range {pred.get('entry_min', 0):,.2f}-{pred.get('entry_max', 0):,.2f}\n"
                 prompt += f"  * TARGETS: SL {pred.get('stop_loss', 0):,.2f} | TP {pred.get('take_profit', 0):,.2f}\n"
                 prompt += f"  * ALLOCATION: {pred.get('alloc_pct', 0)}% of Purchasing Power\n"
                 
            if pred.get('feature_importance'):
                 prompt += f"  Key Factors: {pred['feature_importance']}\n"

        prompt += "\n=== RECENT ORDERS ===\n"
        for order in context.get('recent_orders', []):
             prompt += f"- {order['symbol']}: {order['type']} {order['quantity']} shares @ {order.get('executed_price', 'N/A')}\n"

        purchasing_power = 0.0
        if context.get('portfolio_balance'):
            bal = context['portfolio_balance']
            prompt += "\n=== PORTFOLIO & PURCHASING POWER ===\n"
            prompt += f"Account: {bal.get('account')}\n"
            prompt += f"Cash Balance: {bal.get('cash_balance', 0):,.0f}\n"
            purchasing_power = bal.get('purchasing_power', 0)
            prompt += f"Purchasing Power: {purchasing_power:,.0f}\n"
        
        if context.get('portfolio_positions'):
            prompt += "\n=== CURRENT POSITIONS ===\n"
            for pos in context['portfolio_positions']:
                prompt += f"- {pos['symbol']}: {pos['quantity']} shares (Avg: {pos['avg_price']}, Mkt: {pos['market_price']})\n"

        prompt += (
            "\n\nROLE: You are an expert FinRL Algorithmic Trading Consultant.\n"
            "Analyze the 'Training Metrics' to explain WHY the agent acts this way.\n"
            "IMPORTANT: When recommending a BUY based on a 'buy' signal:\n"
        )
        
        if purchasing_power > 0:
            prompt += (
                "1. Calculate Quantity = (Purchasing Power * Allocation%) / Entry Price.\n"
                "2. Suggest specific Entry Range, Stop Loss, and Take Profit levels provided in the context.\n"
                "Example: 'I recommend buying ~1000 shares of VIC between 50.0-50.5 (Allocation 15%). SL: 48, TP: 55.'\n"
            )
        else:
            prompt += (
                "1. Suggest specific Entry Range, Stop Loss, and Take Profit levels.\n"
                "2. NOTICE: Actual Purchasing Power is NOT available (User has not linked trading account).\n"
                "3. You MUST ask the user to link their securities account to receive specific quantity/volume recommendations.\n"
                "Example: 'I recommend buying in 50.0-50.5 range (Allocation 15%). SL: 48, TP: 55. Please link your securities account to get specific volume advice.'\n"
            )

        prompt += "Always include a risk disclaimer."
        return prompt

    def _get_prompt_template(self):
        """Load system prompt template from text file"""
        if AIChatbotConversation._prompt_template_cache:
            return AIChatbotConversation._prompt_template_cache

        default_template = (
            "You are an AI trading assistant integrated with FreqTrade and FreqAI.\n"
            "Use only the provided context to answer. If data is missing, ask the user for more information."
        )

        template_path = get_module_resource('ai_trading_assistant', 'data', 'chatbot_system_prompt.txt')
        if not template_path:
            AIChatbotConversation._prompt_template_cache = default_template
            return AIChatbotConversation._prompt_template_cache

        try:
            with open(template_path, 'r', encoding='utf-8') as template_file:
                content = template_file.read().strip()
                AIChatbotConversation._prompt_template_cache = content or default_template
        except Exception as err:
            _logger.warning("Failed to load chatbot system prompt template: %s", err)
            AIChatbotConversation._prompt_template_cache = default_template

        return AIChatbotConversation._prompt_template_cache

    @api.model
    def create(self, vals):
        """Generate sequence for conversation reference"""
        if vals.get('name', _('New')) == _('New'):
            try:
                sequence_code = 'ai.chatbot.conversation'
                sequence = self.env['ir.sequence'].search([
                    ('code', '=', sequence_code)
                ], limit=1)
                
                if sequence:
                    vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or _('New')
                else:
                    _logger.warning(f'Sequence {sequence_code} not found, using fallback naming')
                    existing_count = self.search_count([])
                    vals['name'] = f'CHAT-{str(existing_count + 1).zfill(5)}'
            except Exception as e:
                _logger.error(f'Error generating sequence: {e}', exc_info=True)
                existing_count = self.search_count([])
                vals['name'] = f'CHAT-{str(existing_count + 1).zfill(5)}'
        
        return super().create(vals)


class AIChatbotMessage(models.Model):
    """AI Chatbot Messages"""
    _name = 'ai.chatbot.message'
    _description = 'AI Chatbot Message'
    _order = 'create_date asc'

    conversation_id = fields.Many2one(
        'ai.chatbot.conversation',
        string='Conversation',
        required=True,
        ondelete='cascade'
    )

    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ], string='Role', required=True)

    content = fields.Text(
        string='Content',
        required=True,
        help='Message content'
    )

    is_error = fields.Boolean(
        string='Is Error',
        default=False,
        help='Whether this message is an error message'
    )

    # Chart data (if message includes chart)
    chart_data = fields.Text(
        string='Chart Data (JSON)',
        help='Chart data in JSON format for visualization'
    )

    # Reasoning details (for OpenRouter models that support reasoning)
    reasoning_details = fields.Text(
        string='Reasoning Details (JSON)',
        help='Reasoning details from models that support reasoning (e.g., Grok)'
    )

    create_date = fields.Datetime(
        string='Created On',
        default=fields.Datetime.now,
        readonly=True
    )

