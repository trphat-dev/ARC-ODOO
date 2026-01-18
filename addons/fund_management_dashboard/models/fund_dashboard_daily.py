# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json
from datetime import datetime, timedelta


class FundDashboardDaily(models.Model):
    """
    Model lưu trữ dữ liệu dashboard tổng quan theo ngày
    Kế thừa từ board.board của Odoo để tích hợp với dashboard system
    """
    _name = 'fund.dashboard.daily'
    _description = 'Fund Management Dashboard Daily Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'date'

    name = fields.Char(
        string='Tên Dashboard',
        compute='_compute_name',
        store=True,
        readonly=True
    )
    
    date = fields.Date(
        string='Ngày',
        required=True,
        default=fields.Date.today,
        index=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Công ty',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    
    # Summary Statistics
    total_accounts = fields.Integer(
        string='Tổng số tài khoản',
        default=0,
        tracking=True
    )
    
    total_investment = fields.Monetary(
        string='Tổng số tiền đầu tư',
        default=0.0,
        currency_field='currency_id',
        tracking=True
    )
    
    total_current_value = fields.Monetary(
        string='Giá trị hiện tại',
        default=0.0,
        currency_field='currency_id',
        tracking=True
    )
    
    total_profit_loss = fields.Monetary(
        string='Lợi/Lỗ',
        compute='_compute_profit_loss',
        store=True,
        currency_field='currency_id'
    )
    
    total_profit_loss_percentage = fields.Float(
        string='% Lợi/Lỗ',
        compute='_compute_profit_loss',
        store=True,
        digits=(16, 2)
    )
    
    # Today's Transactions
    today_transactions_count = fields.Integer(
        string='Số giao dịch hôm nay',
        default=0
    )
    
    today_pending_count = fields.Integer(
        string='Số giao dịch chờ duyệt',
        default=0
    )
    
    today_completed_count = fields.Integer(
        string='Số giao dịch đã hoàn thành',
        default=0
    )
    
    today_total_amount = fields.Monetary(
        string='Tổng giá trị giao dịch hôm nay',
        default=0.0,
        currency_field='currency_id'
    )
    
    today_buy_count = fields.Integer(
        string='Số lệnh mua',
        default=0
    )
    
    today_sell_count = fields.Integer(
        string='Số lệnh bán',
        default=0
    )
    
    today_buy_amount = fields.Monetary(
        string='Giá trị mua',
        default=0.0,
        currency_field='currency_id'
    )
    
    today_sell_amount = fields.Monetary(
        string='Giá trị bán',
        default=0.0,
        currency_field='currency_id'
    )
    
    # Account Statistics (stored as JSON)
    account_stats_json = fields.Text(
        string='Thống kê tài khoản (JSON)',
        help='Lưu trữ thống kê tài khoản theo trạng thái'
    )
    
    # Fund Movements (stored as JSON)
    fund_movements_json = fields.Text(
        string='Biến động quỹ (JSON)',
        help='Lưu trữ biến động mua/bán của từng CCQ'
    )
    
    # Top Transactions (stored as JSON)
    top_transactions_json = fields.Text(
        string='Top giao dịch (JSON)',
        help='Lưu trữ danh sách top giao dịch lớn nhất'
    )
    
    # All Transactions (stored as JSON)
    transactions_json = fields.Text(
        string='Tất cả giao dịch (JSON)',
        help='Lưu trữ danh sách tất cả giao dịch trong ngày'
    )
    
    # NAV Opening Data (stored as JSON)
    nav_opening_data_json = fields.Text(
        string='NAV Đầu Ngày (JSON)',
        help='Lưu trữ dữ liệu NAV đầu ngày: tổng CCQ và giá CCQ từng quỹ'
    )
    
    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )
    
    # Computed fields for easy access
    account_stats = fields.Json(
        string='Thống kê tài khoản',
        compute='_compute_json_fields',
        store=False
    )
    
    fund_movements = fields.Json(
        string='Biến động quỹ',
        compute='_compute_json_fields',
        store=False
    )
    
    top_transactions = fields.Json(
        string='Top giao dịch',
        compute='_compute_json_fields',
        store=False
    )
    
    transactions = fields.Json(
        string='Giao dịch',
        compute='_compute_json_fields',
        store=False
    )
    
    # One2many fields for views - không dùng compute, sẽ tạo records khi cần
    account_stat_ids = fields.One2many(
        'dashboard.account.stat',
        'dashboard_id',
        string='Thống kê tài khoản',
        readonly=True
    )
    
    fund_movement_ids = fields.One2many(
        'dashboard.fund.movement',
        'dashboard_id',
        string='Biến động quỹ',
        readonly=True
    )
    
    transaction_ids = fields.One2many(
        'dashboard.transaction',
        'dashboard_id',
        string='Giao dịch',
        readonly=True
    )
    
    # NAV Opening Data - One2many field
    nav_opening_ids = fields.One2many(
        'dashboard.nav.opening',
        'dashboard_id',
        string='CCQ Đầu Ngày',
        readonly=True
    )
    
    # Status
    is_today = fields.Boolean(
        string='Là hôm nay',
        compute='_compute_is_today',
        store=False
    )
    
    last_updated = fields.Datetime(
        string='Cập nhật lần cuối',
        default=fields.Datetime.now,
        tracking=True
    )

    @api.depends('date')
    def _compute_name(self):
        """Tạo tên dashboard từ ngày"""
        for record in self:
            if record.date:
                record.name = f"Dashboard {record.date.strftime('%d/%m/%Y')}"
            else:
                record.name = _('Dashboard mới')

    @api.depends('total_investment', 'total_current_value')
    def _compute_profit_loss(self):
        """Tính toán lợi/lỗ"""
        for record in self:
            record.total_profit_loss = record.total_current_value - record.total_investment
            if record.total_investment > 0:
                record.total_profit_loss_percentage = (
                    (record.total_profit_loss / record.total_investment) * 100
                )
            else:
                record.total_profit_loss_percentage = 0.0

    @api.depends('account_stats_json', 'fund_movements_json', 'top_transactions_json', 'transactions_json')
    def _compute_json_fields(self):
        """Parse JSON fields thành dict"""
        for record in self:
            try:
                record.account_stats = json.loads(record.account_stats_json) if record.account_stats_json else {}
            except (json.JSONDecodeError, TypeError):
                record.account_stats = {}
            
            try:
                record.fund_movements = json.loads(record.fund_movements_json) if record.fund_movements_json else []
            except (json.JSONDecodeError, TypeError):
                record.fund_movements = []
            
            try:
                record.top_transactions = json.loads(record.top_transactions_json) if record.top_transactions_json else []
            except (json.JSONDecodeError, TypeError):
                record.top_transactions = []
            
            try:
                record.transactions = json.loads(record.transactions_json) if record.transactions_json else []
            except (json.JSONDecodeError, TypeError):
                record.transactions = []

    def _prepare_detail_records(self):
        """Tạo các record trong detail models từ JSON - gọi khi cần"""
        AccountStat = self.env['dashboard.account.stat'].sudo()
        FundMovement = self.env['dashboard.fund.movement'].sudo()
        Transaction = self.env['dashboard.transaction'].sudo()
        NavOpening = self.env['dashboard.nav.opening'].sudo()
        
        for record in self:
            # Xóa các record cũ
            AccountStat.search([('dashboard_id', '=', record.id)]).unlink()
            FundMovement.search([('dashboard_id', '=', record.id)]).unlink()
            Transaction.search([('dashboard_id', '=', record.id)]).unlink()
            NavOpening.search([('dashboard_id', '=', record.id)]).unlink()
            
            # Tạo account stats
            if record.account_stats_json:
                try:
                    account_stats = json.loads(record.account_stats_json)
                    by_status = account_stats.get('by_status', {})
                    for status, count in by_status.items():
                        AccountStat.create({
                            'dashboard_id': record.id,
                            'status': status,
                            'count': count
                        })
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Tạo fund movements
            if record.fund_movements_json:
                try:
                    fund_movements = json.loads(record.fund_movements_json)
                    for movement in fund_movements:
                        FundMovement.create({
                            'dashboard_id': record.id,
                            'fund_id': movement.get('fund_id', 0),
                            'fund_ticker': movement.get('fund_ticker', ''),
                            'fund_name': movement.get('fund_name', ''),
                            'buy_count': movement.get('buy_count', 0),
                            'sell_count': movement.get('sell_count', 0),
                            'buy_units': movement.get('buy_units', 0.0),
                            'sell_units': movement.get('sell_units', 0.0),
                            'buy_amount': movement.get('buy_amount', 0.0),
                            'sell_amount': movement.get('sell_amount', 0.0),
                            'net_units': movement.get('net_units', 0.0),
                            'net_amount': movement.get('net_amount', 0.0),
                        })
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Tạo transactions
            transaction_records = []
            if record.transactions_json:
                try:
                    transactions = json.loads(record.transactions_json)
                    for tx in transactions:
                        tx_record = Transaction.create({
                            'dashboard_id': record.id,
                            'transaction_id': tx.get('id', 0),
                            'name': tx.get('name', ''),
                            'investor_name': tx.get('investor_name', ''),
                            'account_number': tx.get('account_number', ''),
                            'fund_name': tx.get('fund_name', ''),
                            'fund_ticker': tx.get('fund_ticker', ''),
                            'transaction_type': tx.get('transaction_type', ''),
                            'units': tx.get('units', 0.0),
                            'price': tx.get('price', 0.0),
                            'amount': tx.get('amount', 0.0),
                            'status': tx.get('status', ''),
                            'source': tx.get('source', ''),
                            'matched_units': tx.get('matched_units', 0.0),
                            'remaining_units': tx.get('remaining_units', 0.0),
                            'create_date': self._parse_datetime(tx.get('created_at', '')),
                        })
                        transaction_records.append(tx_record)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Tạo NAV opening data
            if record.nav_opening_data_json:
                try:
                    nav_data = json.loads(record.nav_opening_data_json)
                    funds = nav_data.get('funds', [])
                    for fund in funds:
                        NavOpening.create({
                            'dashboard_id': record.id,
                            'fund_id': fund.get('fund_id', 0),
                            'fund_ticker': fund.get('fund_ticker', ''),
                            'fund_name': fund.get('fund_name', ''),
                            'opening_ccq': fund.get('opening_ccq', 0.0),
                            'opening_price': fund.get('opening_price', 0.0),
                            'opening_value': fund.get('opening_value', 0.0),
                        })
                except (json.JSONDecodeError, TypeError):
                    pass

    def _parse_datetime(self, datetime_str):
        """Parse datetime string thành datetime object"""
        if not datetime_str:
            return False
        try:
            from datetime import datetime
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create để tự động tạo detail records"""
        records = super().create(vals_list)
        records._prepare_detail_records()
        return records

    def write(self, vals):
        """Override write để tự động tạo detail records khi JSON thay đổi"""
        result = super().write(vals)
        # Chỉ tạo lại nếu JSON fields thay đổi
        if any(key in vals for key in ['account_stats_json', 'fund_movements_json', 'transactions_json', 'top_transactions_json']):
            self._prepare_detail_records()
        return result

    def read(self, fields=None, load='_classic_read'):
        """Override read để đảm bảo detail records được tạo trước khi đọc"""
        # Tạo detail records nếu chưa có
        for record in self:
            if (record.account_stats_json or record.fund_movements_json or record.transactions_json or record.nav_opening_data_json):
                # Kiểm tra xem đã có records chưa
                if (not record.account_stat_ids and record.account_stats_json) or \
                   (not record.fund_movement_ids and record.fund_movements_json) or \
                   (not record.transaction_ids and record.transactions_json) or \
                   (not record.nav_opening_ids and record.nav_opening_data_json):
                    record._prepare_detail_records()
                    break
        return super().read(fields=fields, load=load)

    @api.depends('date')
    def _compute_is_today(self):
        """Kiểm tra xem có phải hôm nay không"""
        today = fields.Date.today()
        for record in self:
            record.is_today = (record.date == today)

    @api.constrains('date', 'company_id')
    def _check_unique_date_company(self):
        """Đảm bảo mỗi ngày chỉ có 1 bản ghi cho mỗi công ty"""
        for record in self:
            duplicate = self.search([
                ('date', '=', record.date),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ])
            if duplicate:
                raise ValidationError(
                    _('Đã tồn tại bản ghi dashboard cho ngày %s của công ty này.') % record.date.strftime('%d/%m/%Y')
                )

    @api.model
    def get_or_create_today(self):
        """Lấy hoặc tạo bản ghi dashboard cho hôm nay"""
        today = fields.Date.today()
        company = self.env.company
        
        dashboard = self.search([
            ('date', '=', today),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not dashboard:
            dashboard = self.create({
                'date': today,
                'company_id': company.id,
            })
        
        return dashboard

    @api.model
    def update_today_dashboard(self, dashboard_data):
        """
        Cập nhật dữ liệu dashboard cho hôm nay
        
        Args:
            dashboard_data: Dict chứa dữ liệu dashboard từ controller
        """
        dashboard = self.get_or_create_today()
        
        # Cập nhật summary statistics
        summary = dashboard_data.get('summary', {})
        update_vals = {
            'total_accounts': summary.get('total_accounts', 0),
            'total_investment': summary.get('total_investment', 0.0),
            'total_current_value': summary.get('total_current_value', 0.0),
            'today_transactions_count': summary.get('today_transactions_count', 0),
            'today_pending_count': summary.get('today_pending_count', 0),
            'today_completed_count': summary.get('today_completed_count', 0),
            'today_total_amount': summary.get('today_total_amount', 0.0),
            'today_buy_count': summary.get('today_buy_count', 0),
            'today_sell_count': summary.get('today_sell_count', 0),
            'today_buy_amount': summary.get('today_buy_amount', 0.0),
            'today_sell_amount': summary.get('today_sell_amount', 0.0),
            'last_updated': fields.Datetime.now(),
        }
        
        # Lưu JSON data
        try:
            update_vals.update({
                'account_stats_json': json.dumps(
                    dashboard_data.get('accounts', {}),
                    ensure_ascii=False,
                    default=str
                ),
                'fund_movements_json': json.dumps(
                    dashboard_data.get('fund_movements', []),
                    ensure_ascii=False,
                    default=str
                ),
                'top_transactions_json': json.dumps(
                    dashboard_data.get('top_transactions', []),
                    ensure_ascii=False,
                    default=str
                ),
                'transactions_json': json.dumps(
                    dashboard_data.get('transactions', []),
                    ensure_ascii=False,
                    default=str
                ),
                'nav_opening_data_json': json.dumps(
                    dashboard_data.get('nav_opening_data', {}),
                    ensure_ascii=False,
                    default=str
                ),
            })
        except Exception as json_error:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Lỗi khi serialize JSON: {str(json_error)}")
        
        dashboard.write(update_vals)
        
        return dashboard

    @api.model
    def get_today_data(self):
        """Lấy dữ liệu dashboard cho hôm nay"""
        today = fields.Date.today()
        company = self.env.company
        
        dashboard = self.search([
            ('date', '=', today),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not dashboard:
            return None
        
        # Parse JSON fields
        return {
            'summary': {
                'total_accounts': dashboard.total_accounts,
                'total_investment': dashboard.total_investment,
                'total_current_value': dashboard.total_current_value,
                'total_profit_loss': dashboard.total_profit_loss,
                'total_profit_loss_percentage': dashboard.total_profit_loss_percentage,
                'today_transactions_count': dashboard.today_transactions_count,
                'today_pending_count': dashboard.today_pending_count,
                'today_completed_count': dashboard.today_completed_count,
                'today_total_amount': dashboard.today_total_amount,
                'today_buy_count': dashboard.today_buy_count,
                'today_sell_count': dashboard.today_sell_count,
                'today_buy_amount': dashboard.today_buy_amount,
                'today_sell_amount': dashboard.today_sell_amount,
            },
            'accounts': dashboard.account_stats,
            'fund_movements': dashboard.fund_movements,
            'top_transactions': dashboard.top_transactions,
            'transactions': dashboard.transactions,
        }

    @api.model
    def get_historical_data(self, days=7):
        """
        Lấy dữ liệu dashboard lịch sử
        
        Args:
            days: Số ngày lịch sử cần lấy (mặc định 7 ngày)
        """
        end_date = fields.Date.today()
        start_date = end_date - timedelta(days=days - 1)
        company = self.env.company
        
        dashboards = self.search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('company_id', '=', company.id)
        ], order='date desc')
        
        result = []
        for dashboard in dashboards:
            result.append({
                'date': dashboard.date.strftime('%Y-%m-%d'),
                'total_accounts': dashboard.total_accounts,
                'total_investment': dashboard.total_investment,
                'total_current_value': dashboard.total_current_value,
                'total_profit_loss': dashboard.total_profit_loss,
                'total_profit_loss_percentage': dashboard.total_profit_loss_percentage,
                'today_transactions_count': dashboard.today_transactions_count,
                'today_total_amount': dashboard.today_total_amount,
            })
        
        return result

    def action_refresh_data(self):
        """
        Làm mới dữ liệu dashboard từ controller
        Method này được gọi từ server action
        """
        self.ensure_one()
        
        # Import controller
        from odoo.addons.fund_management_dashboard.controller.dashboard_controller import FundManagementDashboardController
        
        # Tạo instance controller và lấy dữ liệu
        controller = FundManagementDashboardController()
        dashboard_data = controller._get_dashboard_data()
        
        # Cập nhật dashboard hiện tại
        summary = dashboard_data.get('summary', {})
        update_vals = {
            'total_accounts': summary.get('total_accounts', 0),
            'total_investment': summary.get('total_investment', 0.0),
            'total_current_value': summary.get('total_current_value', 0.0),
            'today_transactions_count': summary.get('today_transactions_count', 0),
            'today_pending_count': summary.get('today_pending_count', 0),
            'today_completed_count': summary.get('today_completed_count', 0),
            'today_total_amount': summary.get('today_total_amount', 0.0),
            'today_buy_count': summary.get('today_buy_count', 0),
            'today_sell_count': summary.get('today_sell_count', 0),
            'today_buy_amount': summary.get('today_buy_amount', 0.0),
            'today_sell_amount': summary.get('today_sell_amount', 0.0),
            'last_updated': fields.Datetime.now(),
        }
        
        # Lưu JSON data
        try:
            update_vals.update({
                'account_stats_json': json.dumps(
                    dashboard_data.get('accounts', {}),
                    ensure_ascii=False,
                    default=str
                ),
                'fund_movements_json': json.dumps(
                    dashboard_data.get('fund_movements', []),
                    ensure_ascii=False,
                    default=str
                ),
                'top_transactions_json': json.dumps(
                    dashboard_data.get('top_transactions', []),
                    ensure_ascii=False,
                    default=str
                ),
                'transactions_json': json.dumps(
                    dashboard_data.get('transactions', []),
                    ensure_ascii=False,
                    default=str
                ),
                'nav_opening_data_json': json.dumps(
                    dashboard_data.get('nav_opening_data', {}),
                    ensure_ascii=False,
                    default=str
                ),
            })
        except Exception as json_error:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Lỗi khi serialize JSON: {str(json_error)}")
        
        self.write(update_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã làm mới dữ liệu dashboard thành công.'),
                'type': 'success',
                'sticky': False,
            }
        }

