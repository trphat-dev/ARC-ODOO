from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 16


class Investment(models.Model):
    # Ke thua model goc, tranh khai bao trung _name gay loi registry
    _inherit = 'portfolio.investment'
    _description = "Investment"

    # Override fields with defaults for this module context
    name = fields.Char(string="Name", default=lambda self: self.env.user.name, tracking=True)
    user_id = fields.Many2one("res.users", string="User", required=True, default=lambda self: self.env.user)
    fund_id = fields.Many2one("portfolio.fund", string="Fund", required=True)
    units = fields.Float(string="Units", required=True)
    amount = fields.Float(string="Amount", required=True)
    
    description = fields.Text(string="Description", tracking=True)
    average_price = fields.Float(string="Average Price", compute='_compute_average_price', store=True)

    _sql_constraints = [
        ('investment_user_fund_uniq', 'unique(user_id, fund_id)', 'User and Fund combination must be unique.')
    ]

    @api.constrains('units', 'amount')
    def _check_positive_values(self):
        for record in self:
            if record.units < 0:
                raise ValidationError(_('Units cannot be negative'))
            if record.amount < 0:
                raise ValidationError(_('Amount cannot be negative'))

    @api.depends('amount', 'units')
    def _compute_average_price(self):
        for record in self:
            try:
                amount = Decimal(str(record.amount))
                units = Decimal(str(record.units))
                if units:
                    avg = (amount / units).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    avg = Decimal('0.00')
                record.average_price = float(avg)
            except Exception:
                record.average_price = 0.0

    def action_update_investment(self):
        self.ensure_one()
        # Trigger recompute of stored computed fields
        self._compute_average_price()
        self.write({'write_date': fields.Datetime.now()})
        return True

    @api.model
    def create(self, vals):
        investment = super(Investment, self).create(vals)
        return investment
