from odoo import api, fields, models

from ..utils import constants


class Fund(models.Model):
    _name = "portfolio.fund"
    _description = "Fund"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Link tới master Fund Certificate ở module fund_management_control
    certificate_id = fields.Many2one(
        comodel_name="fund.certificate",
        string="Fund Certificate (master)",
        help="Chọn chứng chỉ quỹ từ trang master để đồng bộ thông tin",
    )

    name = fields.Char(string="Name", required=True)
    ticker = fields.Char(string="Ticker", required=True)
    description = fields.Text(string="Description")
    inception_date = fields.Date(string="Inception Date", required=True)
    current_nav = fields.Float(string="Current NAV", required=True)
    # Thay thế các trường cũ bằng low/high/open để đồng bộ với fund_management_control
    low_price = fields.Float(string="Low Price")
    high_price = fields.Float(string="High Price")
    open_price = fields.Float(string="Open Price")
    
    # Reference prices for color coding
    reference_price = fields.Float(string="Reference Price")
    ceiling_price = fields.Float(string="Ceiling Price")
    floor_price = fields.Float(string="Floor Price")
    
    investment_type = fields.Selection(
        constants.FUND_INVESTMENT_TYPES,
        string="Investment Type",
        required=True
    )
    is_shariah = fields.Boolean(string="Is Shariah")
    # Dạng JSON tiện cho ace editor ở module overview
    ytd_history_json = fields.Text(string="YTD History JSON")
    nav_history_json = fields.Text(string="NAV History JSON")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    status = fields.Selection(
        constants.FUND_STATUSES,
        string="Status",
        default=constants.DEFAULT_FUND_STATUS
    )
    # Thống kê mở rộng phục vụ overview_fund_management (để tránh lỗi view khi cột tồn tại)
    investment_count = fields.Integer(string="Investment Count", default=0)
    total_units = fields.Float(string="Total Units", default=0.0)
    total_investment = fields.Float(string="Total Investment", default=0.0)
    current_value = fields.Float(string="Current Value", default=0.0)
    profit_loss = fields.Float(string="Profit/Loss", default=0.0)
    profit_loss_percentage = fields.Float(string="Profit/Loss %", default=0.0)
    last_update = fields.Datetime(string="Last Update")
    color = fields.Char(string="Color", default="#2B4BFF")
    # Market dynamics
    change = fields.Float(string="Change", default=0.0)
    change_percent = fields.Float(string="Change %", default=0.0)
    volume = fields.Float(string="Volume", default=0.0)

    # Relations
    investment_ids = fields.One2many('portfolio.investment', 'fund_id', string='Investments')

    # --- Sync helpers (simplified) ---
    def _map_fund_type(self, fund_type_value):
        """Map fund type to investment type"""
        return constants.FUND_TYPE_MAPPING.get(
            fund_type_value or '',
            self.investment_type or constants.FUND_INVESTMENT_TYPE_GROWTH
        )
