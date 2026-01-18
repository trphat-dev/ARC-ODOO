from odoo import models, fields, api
from datetime import datetime

class ReportTransaction(models.Model):
    _inherit = 'portfolio.transaction'
    _description = 'Report Transaction - Extended from Portfolio Transaction'
    
    # Computed fields to map data from portfolio.transaction
    account_number_report = fields.Char(string="Số tài khoản", compute='_compute_account_number_report', store=True)
    investor_name_report = fields.Char(string="Nhà đầu tư", compute='_compute_investor_name_report', store=True)
    id_number_report = fields.Char(string="ĐKSH", compute='_compute_id_number_report', store=True)
    fund_name = fields.Char(string="Quỹ", compute='_compute_fund_name', store=True)
    program_name = fields.Char(string="Chương trình", compute='_compute_program_name', store=True)
    trading_session = fields.Date(string="Phiên giao dịch", compute='_compute_trading_session', store=True)
    transaction_code = fields.Char(string="Mã giao dịch", compute='_compute_transaction_code', store=True)
    order_type = fields.Selection([
        ('buy', 'Lệnh mua'),
        ('sell', 'Lệnh bán'),
    ], string="Loại lệnh", compute='_compute_order_type', store=True)
    ccq_quantity = fields.Float(string="Số CCQ", compute='_compute_ccq_quantity', store=True)
    unit_price = fields.Float(string="Giá tiền", compute='_compute_unit_price', store=True)
    total_amount = fields.Float(string="Tổng số tiền", compute='_compute_total_amount', store=True)
    program_ticker = fields.Char(string="Chương trình Ticker", compute='_compute_program_ticker', store=True)

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_account_number_report(self):
        """Compute account number from user"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            if partner:
                status_info = self.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                record.account_number_report = status_info.account_number if status_info else partner.name
            else:
                record.account_number_report = ''

    @api.depends('user_id')
    def _compute_investor_name_report(self):
        """Compute investor name"""
        for record in self:
            record.investor_name_report = record.user_id.name if record.user_id else ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_id_number_report(self):
        """Compute ID number from investor_profile_management"""
        for record in self:
            if record.user_id and record.user_id.partner_id:
                # Find investor profile
                investor_profile = self.env['investor.profile'].sudo().search([
                    ('partner_id', '=', record.user_id.partner_id.id)
                ], limit=1)
                if investor_profile and investor_profile.id_number:
                    record.id_number_report = str(investor_profile.id_number)
                else:
                    record.id_number_report = "-"
            else:
                record.id_number_report = "-"

    @api.depends('fund_id')
    def _compute_fund_name(self):
        """Compute fund name"""
        for record in self:
            record.fund_name = record.fund_id.name if record.fund_id else ''

    @api.depends('fund_id')
    def _compute_program_name(self):
        """Compute program name from fund"""
        for record in self:
            record.program_name = record.fund_id.name if record.fund_id else ''

    @api.depends('created_at')
    def _compute_trading_session(self):
        """Compute trading session from created_at"""
        for record in self:
            if record.created_at:
                record.trading_session = record.created_at.date()
            else:
                record.trading_session = False

    @api.depends('name')
    def _compute_transaction_code(self):
        """Compute transaction code from name"""
        for record in self:
            record.transaction_code = record.name or ''

    @api.depends('transaction_type')
    def _compute_order_type(self):
        """Compute order type from transaction_type"""
        for record in self:
            if record.transaction_type == 'buy':
                record.order_type = 'buy'
            elif record.transaction_type == 'sell':
                record.order_type = 'sell'
            else:
                record.order_type = 'buy'

    @api.depends('units')
    def _compute_ccq_quantity(self):
        """Compute CCQ quantity from units"""
        for record in self:
            record.ccq_quantity = record.units or 0.0

    @api.depends('calculated_amount', 'units')
    def _compute_unit_price(self):
        """Compute unit price from calculated_amount and units"""
        for record in self:
            if record.units and record.units > 0:
                record.unit_price = record.calculated_amount / record.units
            else:
                record.unit_price = 0.0

    @api.depends('amount')
    def _compute_total_amount(self):
        """Compute total amount from amount"""
        for record in self:
            record.total_amount = record.amount or 0.0

    @api.depends('fund_id')
    def _compute_program_ticker(self):
        """Compute ticker from fund"""
        for record in self:
            record.program_ticker = record.fund_id.ticker if record.fund_id and record.fund_id.ticker else ''



