from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountBalance(models.Model):
    _name = "portfolio.account_balance"
    _description = "Account Balance"

    user_id = fields.Many2one("res.users", string="User", required=True)
    balance = fields.Float(string="Balance", required=True)
    frozen_balance = fields.Float(
        string="Frozen Balance",
        default=0.0,
        help="Amount frozen by pending buy orders"
    )
    available_balance = fields.Float(
        string="Available Balance",
        compute='_compute_available_balance',
        store=True,
        help="Balance minus frozen amount — actual spendable balance"
    )

    @api.depends('balance', 'frozen_balance')
    def _compute_available_balance(self):
        for rec in self:
            rec.available_balance = max(0.0, rec.balance - rec.frozen_balance)

    def freeze_for_buy(self, amount):
        """Freeze balance when a buy order is placed.
        Raises ValidationError if insufficient available balance.
        """
        self.ensure_one()
        if self.available_balance < amount:
            raise ValidationError(
                _('Insufficient available balance. Available: %s, Required: %s')
                % (self.available_balance, amount)
            )
        self.frozen_balance += amount

    def unfreeze_for_buy(self, amount):
        """Unfreeze balance when a buy order is cancelled."""
        self.ensure_one()
        self.frozen_balance = max(0.0, self.frozen_balance - amount)

    def complete_buy(self, amount):
        """Deduct balance and release freeze when buy order is completed."""
        self.ensure_one()
        self.frozen_balance = max(0.0, self.frozen_balance - amount)
        self.balance = max(0.0, self.balance - amount)
        # Log to balance history
        self.env['portfolio.balance_history'].sudo().create({
            'user_id': self.user_id.id,
            'balance': self.balance,
            'change': -amount,
            'change_type': 'Investment',
        })

    def complete_sell(self, amount):
        """Credit balance when sell order is completed."""
        self.ensure_one()
        self.balance += amount
        # Log to balance history
        self.env['portfolio.balance_history'].sudo().create({
            'user_id': self.user_id.id,
            'balance': self.balance,
            'change': amount,
            'change_type': 'Divestment',
        })
