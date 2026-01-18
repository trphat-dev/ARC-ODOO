from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 16


class Investment(models.Model):
    # Kế thừa model gốc, tránh khai báo trùng _name gây lỗi registry
    _inherit = 'portfolio.investment'
    _description = "Investment"

    name = fields.Char(string="Name", default=lambda self: self.env.user.name, tracking=True)
    user_id = fields.Many2one("res.users", string="User", required=True, default=lambda self: self.env.user)
    fund_id = fields.Many2one("portfolio.fund", string="Fund", required=True)
    units = fields.Float(string="Units", required=True)
    amount = fields.Float(string="Amount", required=True)
    investment_type = fields.Selection([
        ('stock', 'Stock'),
        ('bond', 'Bond'),
        ('real_estate', 'Real Estate'),
        ('crypto', 'Cryptocurrency'),
        ('fund_certificate', 'Fund Certificate'),
        ('deposit', 'Deposit'),
        ('etf', 'ETF'),
        ('other', 'Other')
    ], string="Investment Type", required=True, default='fund_certificate', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed')
    ], string="Status", default='active', required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, tracking=True, default=lambda self: self.env.company.currency_id)
    average_price = fields.Float(string="Average Price", compute='_compute_average_price', store=True)
    current_value = fields.Float(string="Current Value", compute='_compute_current_value', store=True, tracking=True)
    profit_loss = fields.Float(string="Profit/Loss", compute='_compute_profit_loss', store=True)
    profit_loss_percentage = fields.Float(string="Profit/Loss %", compute='_compute_profit_loss_percentage', store=True)

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

    @api.depends('units', 'amount')
    def _compute_current_value(self):
        for record in self:
            # Sử dụng giá trị thực tế từ form thay vì current_nav
            if record.units > 0:
                # Tính từ amount thực tế thay vì current_nav
                record.current_value = record.amount
            else:
                record.current_value = 0.0

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

    @api.constrains('average_price', 'current_value')
    def _check_computed_values(self):
        for record in self:
            if record.average_price < 0:
                raise ValidationError(_('Average price cannot be negative'))
            if record.current_value < 0:
                raise ValidationError(_('Current value cannot be negative'))

    @api.depends('amount', 'current_value')
    def _compute_profit_loss(self):
        for record in self:
            try:
                current_value = Decimal(str(record.current_value))
                amount = Decimal(str(record.amount))
                pl = (current_value - amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                record.profit_loss = float(pl)
            except Exception:
                record.profit_loss = 0.0

    @api.depends('amount', 'profit_loss')
    def _compute_profit_loss_percentage(self):
        for record in self:
            try:
                amount = Decimal(str(record.amount))
                profit_loss = Decimal(str(record.profit_loss))
                if amount:
                    percent = ((profit_loss / amount) * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    percent = Decimal('0.00')
                record.profit_loss_percentage = float(percent)
            except Exception:
                record.profit_loss_percentage = 0.0

    def action_update_investment(self):
        self.ensure_one()
        # Cập nhật giá trị hiện tại
        self._compute_profit_loss()
        self._compute_profit_loss_percentage()
        # Cập nhật thời gian
        self.write({'write_date': fields.Datetime.now()})
        return True

    @api.model
    def create(self, vals):
        investment = super(Investment, self).create(vals)
        return investment
