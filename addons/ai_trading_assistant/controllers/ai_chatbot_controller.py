# -*- coding: utf-8 -*-

import logging
import json
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import http, _, fields
from odoo.exceptions import UserError
from odoo.http import request



_logger = logging.getLogger(__name__)


class AIChatbotController(http.Controller):
    """Controller for AI Chatbot"""

    @http.route('/ai_chatbot/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, conversation_id=None, message=None):
        """Send message to chatbot"""
        try:
            if not message:
                return {'success': False, 'error': 'Message is required'}

            # Get or create conversation
            if conversation_id:
                conversation = request.env['ai.chatbot.conversation'].browse(conversation_id)
                if not conversation.exists() or conversation.user_id != request.env.user:
                    return {'success': False, 'error': 'Conversation not found'}
            else:
                # Create new conversation
                conversation = request.env['ai.chatbot.conversation'].create({
                    'user_id': request.env.user.id,
                })

            # Send message and get response
            assistant_message = conversation.action_send_message(message)

            return {
                'success': True,
                'data': {
                    'conversation_id': conversation.id,
                    'message_id': assistant_message.id,
                    'content': assistant_message.content,
                    'role': assistant_message.role,
                    'is_error': assistant_message.is_error,
                }
            }

        except Exception as e:
            _logger.error(f'Send message error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/ai_chatbot/conversations', type='json', auth='user', methods=['GET', 'POST'], csrf=False)
    def get_conversations(self, limit=10, **kwargs):
        """Get user conversations"""
        try:
            if isinstance(kwargs.get('limit'), int):
                limit = kwargs['limit']

            conversations = request.env['ai.chatbot.conversation'].search([
                ('user_id', '=', request.env.user.id),
                ('active', '=', True),
            ], order='create_date desc', limit=limit)

            return {
                'success': True,
                'data': [{
                    'id': c.id,
                    'name': c.name,
                    'message_count': c.message_count,
                    'create_date': c.create_date.isoformat(),
                } for c in conversations]
            }

        except Exception as e:
            _logger.error(f'Get conversations error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/ai_chatbot/messages', type='json', auth='user', methods=['GET', 'POST'], csrf=False)
    def get_messages(self, conversation_id=None, **kwargs):
        """Get messages from conversation"""
        try:
            conversation_id = conversation_id or kwargs.get('conversation_id')
            if not conversation_id:
                return {'success': False, 'error': _('Conversation ID is required')}

            conversation = request.env['ai.chatbot.conversation'].browse(conversation_id)
            if not conversation.exists() or conversation.user_id != request.env.user:
                return {'success': False, 'error': 'Conversation not found'}

            messages = conversation.messages

            return {
                'success': True,
                'data': [{
                    'id': m.id,
                    'role': m.role,
                    'content': m.content,
                    'is_error': m.is_error,
                    'create_date': m.create_date.isoformat(),
                } for m in messages]
            }

        except Exception as e:
            _logger.error(f'Get messages error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}

    # --- Investor Chatbot Experience ---
    @http.route('/ai_chatbot/investor/chat', type='json', auth='user', methods=['POST'], csrf=False)
    def investor_chat(self, message=None, context=None, conversation_id=None, **kwargs):
        """Chat endpoint for Website Popup"""
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
                conversation = request.env['ai.chatbot.conversation'].sudo().browse(int(conversation_id))
                if not conversation.exists() or conversation.user_id != request.env.user:
                    return {'success': False, 'error': _('Conversation not found')}
            else:
                conversation = request.env['ai.chatbot.conversation'].sudo().create({
                'user_id': request.env.user.id,
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
            _logger.error('investor_chat error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

