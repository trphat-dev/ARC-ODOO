# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TrainModelWizard(models.TransientModel):
    """Wizard for training AI model"""
    _name = 'train.model.wizard'
    _description = 'Train Model Wizard'

    strategy_id = fields.Many2one(
        'ai.strategy',
        string='Strategy',
        required=True,
        readonly=True
    )

    from_date = fields.Date(
        string='From Date',
        required=True,
        help='Start date for training data'
    )

    to_date = fields.Date(
        string='To Date',
        required=True,
        help='End date for training data'
    )

    model_type = fields.Selection(
        related='strategy_id.model_type',
        string='Model Type',
        readonly=True
    )

    symbol = fields.Char(
        related='strategy_id.symbol',
        string='Symbol',
        readonly=True
    )

    market = fields.Selection(
        related='strategy_id.market',
        string='Market',
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        res = super().default_get(fields_list)
        if self.env.context.get('default_strategy_id'):
            strategy = self.env['ai.strategy'].browse(
                self.env.context['default_strategy_id']
            )
            res['strategy_id'] = strategy.id
            res['from_date'] = strategy.from_date
            res['to_date'] = strategy.to_date
        return res

    def action_train(self):
        """Start model training.
        
        Uses FinRL service for DRL models (ppo, a2c, sac, td3, ddpg)
        or legacy FreqAI for deprecated ML models.
        """
        self.ensure_one()

        # Validate dates
        if self.from_date >= self.to_date:
            raise UserError(_('From Date must be before To Date'))

        # Create training record
        training = self.env['ai.model.training'].create({
            'strategy_id': self.strategy_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
        })

        # Start training - method selection based on model type
        if self.strategy_id.is_finrl_model:
            training.action_start_finrl_training()
        else:
            # Legacy FreqAI training - deprecated
            _logger.warning(f'Using deprecated FreqAI training for model type: {self.strategy_id.model_type}')
            training.action_start_training()

        # After training, continue to prediction generation/view
        return self.strategy_id.action_generate_predictions()

