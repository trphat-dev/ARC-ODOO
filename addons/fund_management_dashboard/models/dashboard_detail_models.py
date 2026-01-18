# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import json


class DashboardAccountStat(models.TransientModel):
    """Model tạm thời để hiển thị thống kê tài khoản"""
    _name = 'dashboard.account.stat'
    _description = 'Dashboard Account Statistics'
    _order = 'status'
    _rec_name = 'status'

    dashboard_id = fields.Many2one('fund.dashboard.daily', string='Dashboard', required=True, ondelete='cascade')
    status = fields.Char(string='Trạng thái', required=True)
    count = fields.Integer(string='Số lượng', default=0)


class DashboardFundMovement(models.TransientModel):
    """Model tạm thời để hiển thị biến động quỹ"""
    _name = 'dashboard.fund.movement'
    _description = 'Dashboard Fund Movement'
    _order = 'fund_ticker'
    _rec_name = 'fund_ticker'

    dashboard_id = fields.Many2one('fund.dashboard.daily', string='Dashboard', required=True, ondelete='cascade')
    fund_id = fields.Integer(string='Fund ID')
    fund_ticker = fields.Char(string='Mã CCQ', required=True)
    fund_name = fields.Char(string='Tên Quỹ')
    buy_count = fields.Integer(string='Lệnh mua', default=0)
    sell_count = fields.Integer(string='Lệnh bán', default=0)
    buy_units = fields.Float(string='Số lượng mua', digits=(16, 2), default=0.0)
    sell_units = fields.Float(string='Số lượng bán', digits=(16, 2), default=0.0)
    buy_amount = fields.Monetary(string='Giá trị mua', default=0.0, currency_field='currency_id')
    sell_amount = fields.Monetary(string='Giá trị bán', default=0.0, currency_field='currency_id')
    net_units = fields.Float(string='Ròng (CCQ)', digits=(16, 2), default=0.0)
    net_amount = fields.Monetary(string='Ròng (Giá trị)', default=0.0, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='dashboard_id.currency_id', readonly=True)


class DashboardTransaction(models.TransientModel):
    """Model tạm thời để hiển thị giao dịch"""
    _name = 'dashboard.transaction'
    _description = 'Dashboard Transaction'
    _order = 'create_date desc'
    _rec_name = 'name'

    dashboard_id = fields.Many2one('fund.dashboard.daily', string='Dashboard', required=True, ondelete='cascade')
    transaction_id = fields.Integer(string='Transaction ID')
    name = fields.Char(string='Tên giao dịch')
    investor_name = fields.Char(string='Nhà đầu tư')
    account_number = fields.Char(string='Số tài khoản')
    fund_name = fields.Char(string='Tên Quỹ')
    fund_ticker = fields.Char(string='Mã CCQ')
    transaction_type = fields.Selection([
        ('buy', 'Mua'),
        ('sell', 'Bán'),
    ], string='Loại giao dịch')
    units = fields.Float(string='Số lượng', digits=(16, 2), default=0.0)
    price = fields.Float(string='Giá', digits=(16, 2), default=0.0)
    amount = fields.Monetary(string='Giá trị', default=0.0, currency_field='currency_id')
    status = fields.Selection([
        ('pending', 'Chờ duyệt'),
        ('completed', 'Đã hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái')
    source = fields.Char(string='Nguồn')
    matched_units = fields.Float(string='Số lượng khớp', digits=(16, 2), default=0.0)
    remaining_units = fields.Float(string='Số lượng còn lại', digits=(16, 2), default=0.0)
    create_date = fields.Datetime(string='Ngày tạo')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='dashboard_id.currency_id', readonly=True)


class DashboardNavOpening(models.TransientModel):
    """Model tạm thời để hiển thị NAV đầu ngày"""
    _name = 'dashboard.nav.opening'
    _description = 'Dashboard NAV Opening Data'
    _order = 'opening_price desc'
    _rec_name = 'fund_ticker'

    dashboard_id = fields.Many2one('fund.dashboard.daily', string='Dashboard', required=True, ondelete='cascade')
    fund_id = fields.Integer(string='Fund ID')
    fund_ticker = fields.Char(string='Mã CCQ', required=True)
    fund_name = fields.Char(string='Tên Quỹ')
    opening_ccq = fields.Float(string='Số lượng CCQ', digits=(16, 2), default=0.0)
    opening_price = fields.Monetary(string='Giá CCQ đầu ngày', default=0.0, currency_field='currency_id')
    opening_value = fields.Monetary(string='Giá trị đầu ngày', default=0.0, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='dashboard_id.currency_id', readonly=True)

