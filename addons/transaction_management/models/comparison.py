from odoo import api, fields, models

class Comparison(models.Model):
    _name = "portfolio.comparison"
    _description = "Fund Comparison"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True, tracking=True)
    user_id = fields.Many2one("res.users", string="User", required=True, default=lambda self: self.env.user, tracking=True)
    fund_ids = fields.Many2many("portfolio.fund", string="Funds", required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    create_date = fields.Datetime(string="Created At", readonly=True)
    write_date = fields.Datetime(string="Last Updated", readonly=True)
    comparison_type = fields.Selection([
        ('performance', 'Performance'),
        ('risk', 'Risk'),
        ('cost', 'Cost'),
        ('custom', 'Custom')
    ], string="Comparison Type", default='performance', required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    description = fields.Text(string="Description")
    is_public = fields.Boolean(string="Is Public", default=False)
    last_update = fields.Datetime(string="Last Update", default=fields.Datetime.now)
    comparison_data = fields.Text(string="Comparison Data (JSON)")
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed')
    ], string="Status", default='active', required=True, tracking=True)
    total_investment = fields.Float(string="Total Investment", compute='_compute_total_investment', store=True)
    total_return = fields.Float(string="Total Return", compute='_compute_total_return', store=True)
    return_percentage = fields.Float(string="Return %", compute='_compute_return_percentage', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New Comparison') == 'New Comparison':
                vals['name'] = self.env['ir.sequence'].next_by_code('portfolio.comparison') or 'New Comparison'
        return super().create(vals_list)

    def write(self, vals):
        vals['write_date'] = fields.Datetime.now()
        return super(Comparison, self).write(vals)

    @api.depends('fund_ids', 'start_date', 'end_date')
    def _compute_total_investment(self):
        for record in self:
            total = 0.0
            for fund in record.fund_ids:
                investments = self.env['portfolio.investment'].search([
                    ('fund_id', '=', fund.id),
                    ('date', '>=', record.start_date),
                    ('date', '<=', record.end_date)
                ])
                total += sum(investments.mapped('amount'))
            record.total_investment = total

    @api.depends('fund_ids', 'start_date', 'end_date')
    def _compute_total_return(self):
        for record in self:
            total = 0.0
            for fund in record.fund_ids:
                investments = self.env['portfolio.investment'].search([
                    ('fund_id', '=', fund.id),
                    ('date', '>=', record.start_date),
                    ('date', '<=', record.end_date)
                ])
                total += sum(investments.mapped('profit_loss'))
            record.total_return = total

    @api.depends('total_investment', 'total_return')
    def _compute_return_percentage(self):
        for record in self:
            if record.total_investment:
                record.return_percentage = (record.total_return / record.total_investment) * 100
            else:
                record.return_percentage = 0.0

    def action_update_comparison(self):
        self.ensure_one()
        # Cập nhật thời gian cập nhật cuối cùng
        self.last_update = fields.Datetime.now()
        # Cập nhật các giá trị tính toán
        self._compute_total_investment()
        self._compute_total_return()
        self._compute_return_percentage() 