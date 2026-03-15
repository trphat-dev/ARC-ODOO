from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
import logging
from datetime import datetime

from ..utils import constants, investment_utils


class Transaction(models.Model):
    _name = "portfolio.transaction"
    _description = "Transaction"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Đồng bộ kiểu dữ liệu với các module khác: dùng res.users để có partner_id
    user_id = fields.Many2one("res.users", string="User", required=True)
    # Tên giao dịch để tương thích các @depends ngoại mô-đun
    name = fields.Char(string="Name", compute='_compute_name', store=True)
    description = fields.Text(string="Description")
    reference = fields.Char(string="Reference")
    fund_id = fields.Many2one("portfolio.fund", string="Fund", required=True)
    transaction_type = fields.Selection(
        constants.TRANSACTION_TYPES,
        string="Transaction Type",
        required=True
    )
    units = fields.Float(string="Units", required=True)
    # Trường phục vụ giao dịch chuyển đổi (exchange) tương thích view
    destination_fund_id = fields.Many2one('portfolio.fund', string='Destination Fund')
    destination_units = fields.Float(string="Destination Units")
    amount = fields.Float(string="Amount", required=True)
    fee = fields.Float(string="Phí mua", default=0.0, help="Phí mua cho giao dịch này")
    created_at = fields.Datetime(string="Created At", required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(string="Date End At")
    # Trả về trực tiếp file hợp đồng (base64) lấy từ fund.signed.contract
    contract_file = fields.Binary(string="Contract File", compute='_compute_contract_file', store=False, attachment=False)
    contract_filename = fields.Char(string="Contract Filename", compute='_compute_contract_file', store=False)
    current_nav = fields.Float(string="NAV")
    price = fields.Monetary(string="Giá đơn vị", required=True, tracking=True, help="Giá đơn vị cho giao dịch này", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    status = fields.Selection(
        constants.TRANSACTION_STATUSES,
        string="Status",
        default=constants.DEFAULT_TRANSACTION_STATUS,
        tracking=True
    )

    # Bổ sung để tương thích các view/search đang group/filter theo investment_type
    investment_type = fields.Selection(
        constants.INVESTMENT_TYPES,
        string="Investment Type",
        default=constants.DEFAULT_INVESTMENT_TYPE
    )

    # Tương thích các @depends ở module khác
    calculated_amount = fields.Monetary(
        string="Calculated Amount",
        compute='_compute_calculated_amount',
        store=True,
        currency_field='currency_id'
    )

    # Added fields for NAV Management integration
    term_months = fields.Integer(
        string="Kỳ hạn (tháng)",
        default=constants.DEFAULT_TERM_MONTHS
    )
    interest_rate = fields.Float(string="Lãi suất (%)", digits=(16, 2))

    # Source field for transaction origin
    source = fields.Selection(
        constants.TRANSACTION_SOURCES,
        string="Source",
        default=constants.DEFAULT_TRANSACTION_SOURCE,
        tracking=True
    )

    # ==========================================================================
    # ORDER MODE & TYPE - Phân biệt lệnh thường vs lệnh thỏa thuận
    # ==========================================================================
    order_mode = fields.Selection(
        constants.ORDER_MODES,
        string="Loại đầu tư",
        default=constants.DEFAULT_ORDER_MODE,
        tracking=True,
        help="Đặt lệnh thường: gửi trực tiếp lên sàn. Đặt lệnh thỏa thuận: khớp nội bộ trước."
    )
    
    order_type_detail = fields.Selection(
        constants.ORDER_TYPE_DETAILS,
        string="Loại lệnh",
        default=constants.DEFAULT_ORDER_TYPE_DETAIL,
        help="MTL/ATO/ATC/LO - chỉ áp dụng cho lệnh thường"
    )
    
    market = fields.Selection(
        constants.MARKETS,
        string="Sàn",
        compute='_compute_market_from_fund',
        store=True,
        readonly=False,
        help="Sàn niêm yết của CCQ (lấy từ fund.certificate)"
    )

    # Session Tracking for Reconciliation
    order_session = fields.Selection([
        ('ato', 'Phiên ATO'),
        ('continuous', 'Khớp lệnh liên tục'),
        ('atc', 'Phiên ATC'),
        ('periodic', 'Khớp lệnh định kỳ'),
        ('pre_market', 'Trước giờ giao dịch'),
        ('after_market', 'Sau giờ giao dịch'),
        ('unknown', 'Không xác định')
    ], string="Phiên đặt lệnh", default='unknown', help="Phiên tại thời điểm đặt lệnh (theo giờ hệ thống)")
    
    # ==========================================================================
    # EXCHANGE TRACKING - Theo dõi trạng thái lệnh trên sàn (cho lệnh thường)
    # ==========================================================================
    exchange_order_id = fields.Char(
        string="Exchange Order ID",
        readonly=True,
        help="ID lệnh trên sàn (từ trading.order)"
    )
    
    exchange_status = fields.Selection(
        constants.EXCHANGE_STATUSES,
        string="Trạng thái sàn",
        default=constants.DEFAULT_EXCHANGE_STATUS,
        tracking=True,
        help="Trạng thái lệnh trên sàn (chỉ cho lệnh thường)"
    )
    
    exchange_filled_quantity = fields.Float(
        string="SL đã khớp trên sàn",
        readonly=True,
        help="Số lượng đã khớp trên sàn"
    )
    
    exchange_filled_price = fields.Float(
        string="Giá khớp trên sàn",
        readonly=True,
        help="Giá khớp trung bình trên sàn"
    )
    
    exchange_sent_at = fields.Datetime(
        string="Thời gian gửi sàn",
        readonly=True,
        help="Thời điểm gửi lệnh lên sàn"
    )
    
    exchange_filled_at = fields.Datetime(
        string="Thời gian khớp",
        readonly=True,
        help="Thời điểm khớp lệnh trên sàn"
    )

    t2_date = fields.Date(
        string="Ngày hàng về (T+2)",
        compute='_compute_t2_date',
        store=True,
        help="Ngày dự kiến hàng/tiền về (T+2)"
    )

    t2_skipped = fields.Boolean(
        string="Bỏ qua T+2",
        default=False,
        tracking=True,
        help="Nếu bật, CCQ từ giao dịch này được coi là đã về tài khoản (bỏ qua kiểm tra T+2)"
    )

    @api.depends('created_at', 'transaction_type', 'order_mode')
    def _compute_t2_date(self):
        """Calculate T+2 date based on created_at - applies to ALL transactions"""
        from datetime import timedelta
        for record in self:
            if record.created_at:
                # T+2 applies to ALL order types (normal & negotiated) and ALL transaction types (buy & sell)
                base_date = record.created_at.date()
                
                # Calculate T+2 skipping weekends
                current = base_date
                days_to_add = 2
                while days_to_add > 0:
                    current += timedelta(days=1)
                    if current.weekday() < 5:  # Mon=0, Fri=4, Sat=5, Sun=6
                        days_to_add -= 1
                
                record.t2_date = current
            else:
                record.t2_date = False

    # NAV Calculation fields (computed)
    nav_maturity_date = fields.Date(
        string="Ngày đáo hạn (E)",
        compute='_compute_nav_calculation',
        store=False,
        help="Ngày đáo hạn tính từ ngày mua và kỳ hạn"
    )
    nav_sell_date = fields.Date(
        string="Ngày bán (D)",
        compute='_compute_nav_calculation',
        store=False,
        help="Ngày bán = WORKDAY(ngày đáo hạn, -2)"
    )
    nav_days = fields.Integer(
        string="Số ngày (G)",
        compute='_compute_nav_calculation',
        store=False,
        help="Số ngày = Ngày đáo hạn - Ngày mua"
    )
    nav_days_converted = fields.Float(
        string="Số ngày quy đổi (H)",
        compute='_compute_nav_calculation',
        store=False,
        digits=(16, 2),
        help="Số ngày quy đổi theo lãi suất mới"
    )
    nav_purchase_value = fields.Monetary(
        string="Giá trị mua (L)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Giá trị mua = Units * Price + Units * Price * Fee"
    )
    nav_price_with_fee = fields.Monetary(
        string="Giá 1 CCQ đã bao gồm thuế/phí (M)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Giá 1 CCQ đã bao gồm thuế/phí = Giá trị mua / Units"
    )
    nav_converted_rate = fields.Float(
        string="Lãi suất quy đổi (O)",
        compute='_compute_nav_calculation',
        store=False,
        digits=(16, 4),
        help="Lãi suất quy đổi theo giá bán 2"
    )
    nav_interest_delta = fields.Float(
        string="Chênh lệch lãi suất (Q)",
        compute='_compute_nav_calculation',
        store=False,
        digits=(16, 4),
        help="Chênh lệch lãi suất = Lãi suất quy đổi - Lãi suất"
    )
    nav_tax_tncn = fields.Float(
        string="Thuế TNCN (R)",
        compute='_compute_nav_calculation',
        store=False,
        digits=(16, 2),
        help="Thuế TNCN"
    )
    nav_sell_price1 = fields.Monetary(
        string="Giá bán 1 (S)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Giá bán 1 = ROUND(Giá trị bán 1 / Units, 0)"
    )
    nav_sell_price2 = fields.Monetary(
        string="Giá bán 2 (T)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Giá bán 2 = MROUND(Giá bán 1, 50)"
    )
    nav_sell_value1 = fields.Monetary(
        string="Giá trị bán 1 (U)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Giá trị bán 1 = Giá trị mua * Lãi suất / 365 * Số ngày + Giá trị mua"
    )
    nav_sell_value2 = fields.Monetary(
        string="Giá trị bán 2 (V)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Giá trị bán 2 = Units * Giá bán 2"
    )
    nav_difference = fields.Monetary(
        string="Chênh lệch (W)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Chênh lệch = Giá trị bán 2 - Giá trị bán 1"
    )
    nav_sell_fee = fields.Monetary(
        string="Phí bán (X)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Phí bán"
    )
    nav_tax = fields.Monetary(
        string="Thuế (Y)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Thuế"
    )
    nav_customer_receive = fields.Monetary(
        string="Khách hàng thực nhận (Z)",
        compute='_compute_nav_calculation',
        store=False,
        currency_field='currency_id',
        help="Khách hàng thực nhận = Giá trị bán 1 - Phí bán - Thuế"
    )

    # Formatted date fields for display (dd/MM/yyyy)
    nav_sell_date_formatted = fields.Char(
        string="Ngày bán (D)",
        compute='_compute_nav_calculation',
        store=False,
        help="Ngày bán = WORKDAY(ngày đáo hạn, -2) - Format: dd/MM/yyyy"
    )
    nav_maturity_date_formatted = fields.Char(
        string="Ngày đáo hạn (E)",
        compute='_compute_nav_calculation',
        store=False,
        help="Ngày đáo hạn tính từ ngày mua và kỳ hạn - Format: dd/MM/yyyy"
    )
    transaction_date_formatted = fields.Char(
        string="Ngày mua/bán (C)",
        compute='_compute_nav_calculation',
        store=False,
        help="Ngày mua/bán - Format: dd/MM/yyyy"
    )
    
    # Formatted datetime fields for display (dd/MM/yyyy HH:mm:ss)
    created_at_formatted = fields.Char(
        string="Ngày tạo",
        compute='_compute_datetime_formatted',
        store=False,
        help="Ngày tạo - Format: dd/MM/yyyy HH:mm:ss"
    )
    date_end_formatted = fields.Char(
        string="Ngày kết thúc",
        compute='_compute_datetime_formatted',
        store=False,
        help="Ngày kết thúc - Format: dd/MM/yyyy HH:mm:ss"
    )

    _logger = logging.getLogger(__name__)

    # ==========================================================================
    # COMPUTE METHODS FOR ORDER MODE / MARKET
    # ==========================================================================
    @api.depends('fund_id', 'fund_id.certificate_id')
    def _compute_market_from_fund(self):
        """Lấy thông tin sàn từ fund.certificate (nếu có field market)"""
        for record in self:
            if record.fund_id and record.fund_id.certificate_id:
                cert = record.fund_id.certificate_id
                # Ưu tiên lấy market từ certificate nếu có field market
                market_val = getattr(cert, 'market', None) if hasattr(cert, 'market') else None
                if market_val and market_val in [m[0] for m in constants.MARKETS]:
                    record.market = market_val
                else:
                    record.market = constants.MARKET_HOSE  # Default HOSE
            else:
                record.market = constants.MARKET_HOSE  # Default HOSE
    
    # ==========================================================================
    # VALIDATION CONSTRAINTS FOR ORDER MODE
    # ==========================================================================
    @api.constrains('order_mode', 'order_type_detail', 'market')
    def _check_order_type_market_constraint(self):
        """Validate order type is allowed for the market"""
        for record in self:
            if record.order_mode != constants.ORDER_MODE_NORMAL:
                continue
            
            if not record.order_type_detail or not record.market:
                continue
            
            allowed_types = constants.ORDER_TYPES_BY_MARKET.get(record.market, [])
            if record.order_type_detail not in allowed_types:
                raise ValidationError(
                    _(f'Loại lệnh {record.order_type_detail} không được hỗ trợ trên sàn {record.market}. '
                      f'Các loại lệnh cho phép: {", ".join(allowed_types)}')
                )
    
    @api.constrains('order_mode', 'units')
    def _check_lot_size_constraint(self):
        """Validate lot size (chỉ áp dụng cho lệnh thỏa thuận - phải chia hết cho 100)"""
        for record in self:
            # Fix: Only apply lot size validtion for NEGOTIATED, not Normal
            if record.order_mode != constants.ORDER_MODE_NEGOTIATED:
                continue
            
            if record.units and record.units > 0:
                if record.units % constants.LOT_SIZE != 0:
                    raise ValidationError(
                        _(f'Số lượng CCQ lệnh thỏa thuận phải theo lô {constants.LOT_SIZE}. '
                          f'Số lượng hiện tại: {record.units}')
                    )

    # ===== Basic calculation methods =====
    def _compute_days(self, term_months=None, days=None):
        """Calculate days from term_months or days"""
        return investment_utils.InvestmentHelper.compute_days(term_months, days)

    def compute_sell_value(self, order_value, interest_rate_percent, term_months=None, days=None):
        """Calculate sell value based on interest rate and term"""
        return investment_utils.InvestmentHelper.compute_sell_value(
            order_value, interest_rate_percent, term_months, days
        )

    @api.depends('fund_id', 'transaction_type', 'units', 'created_at')
    def _compute_name(self):
        for record in self:
            if record.fund_id and record.transaction_type and record.units and record.created_at:
                transaction_date = record.created_at.date() if record.created_at else None
                if transaction_date:
                    record.name = f"{record.transaction_type.upper()} - {record.fund_id.name} - {record.units} units - {transaction_date}"
                else:
                    record.name = "New Transaction"
            else:
                record.name = "New Transaction"

    @api.onchange('term_months')
    def _onchange_term_months_set_interest(self):
        """Auto-set interest_rate from nav.term.rate (active). Fallback giữ giá trị cũ nếu không tìm thấy."""
        for rec in self:
            try:
                if not rec.term_months:
                    continue
                TermRate = self.env['nav.term.rate'].sudo()
                rate = TermRate.search([('active', '=', True), ('term_months', '=', int(rec.term_months))], limit=1)
                if rate:
                    rec.interest_rate = rate.interest_rate
                else:
                    rec.interest_rate = rec.interest_rate or 0.0
            except Exception:
                rec.interest_rate = rec.interest_rate or 0.0

    @api.depends('amount', 'units')
    def _compute_calculated_amount(self):
        for record in self:
            record.calculated_amount = record.amount or 0.0

    @api.depends('created_at', 'term_months', 'units', 'price', 'fee', 'interest_rate')
    def _compute_nav_calculation(self):
        """Tính toán các trường NAV cho transaction"""
        for record in self:
            # Reset all fields
            record.nav_maturity_date = False
            record.nav_sell_date = False
            record.nav_days = 0
            record.nav_days_converted = 0.0
            record.nav_purchase_value = 0.0
            record.nav_price_with_fee = 0.0
            record.nav_converted_rate = 0.0
            record.nav_interest_delta = 0.0
            record.nav_tax_tncn = 0.0
            record.nav_sell_price1 = 0.0
            record.nav_sell_price2 = 0.0
            record.nav_sell_value1 = 0.0
            record.nav_sell_value2 = 0.0
            record.nav_difference = 0.0
            record.nav_sell_fee = 0.0
            record.nav_tax = 0.0
            record.nav_customer_receive = 0.0
            record.nav_sell_date_formatted = ''
            record.nav_maturity_date_formatted = ''
            record.transaction_date_formatted = ''
            
            # Lấy ngày giao dịch từ created_at
            purchase_date = record.created_at.date() if record.created_at else None
            
            # Chỉ tính toán nếu có đủ thông tin
            if not purchase_date or not record.term_months or not record.units or not record.price or not record.interest_rate:
                continue
            
            try:
                # Sử dụng calculator từ nav_management
                calculator = self.env['nav.transaction.calculator']
                
                # Tính fee_rate từ fee và amount (fee là số tiền, cần chuyển sang phần trăm)
                purchase_amount = float(record.units or 0.0) * float(record.price or 0.0)
                fee_amount = float(record.fee or 0.0)
                fee_rate = (fee_amount / purchase_amount * 100.0) if purchase_amount > 0 else 0.0
                
                # Chuẩn bị dữ liệu đầu vào
                transaction_data = {
                    'purchase_date': purchase_date,
                    'term_months': record.term_months,
                    'units': record.units,
                    'price_per_unit': record.price,
                    'fee_rate': fee_rate,  # Fee rate tính từ fee amount
                    'interest_rate': record.interest_rate or 0.0,
                    'sell_fee': 0.0,  # Có thể thêm field sau
                    'tax': 0.0,  # Có thể thêm field sau
                }
                
                # Tính toán
                metrics = calculator.compute_transaction_metrics_full(transaction_data)
                
                # Gán kết quả vào các field
                if metrics.get('maturity_date'):
                    maturity_str = metrics['maturity_date']
                    try:
                        if isinstance(maturity_str, str):
                            # Parse ISO format date string using Odoo's fields.Date
                            if 'T' in maturity_str:
                                maturity_str = maturity_str.split('T')[0]
                            maturity_date = fields.Date.from_string(maturity_str)
                            record.nav_maturity_date = maturity_date
                            # Format thành dd/MM/yyyy
                            if maturity_date:
                                record.nav_maturity_date_formatted = maturity_date.strftime('%d/%m/%Y')
                        elif hasattr(maturity_str, 'date'):
                            maturity_date = maturity_str.date() if isinstance(maturity_str, datetime) else maturity_str
                            record.nav_maturity_date = maturity_date
                            if maturity_date:
                                record.nav_maturity_date_formatted = maturity_date.strftime('%d/%m/%Y')
                        else:
                            record.nav_maturity_date = maturity_str
                            if maturity_str:
                                record.nav_maturity_date_formatted = maturity_str.strftime('%d/%m/%Y') if hasattr(maturity_str, 'strftime') else str(maturity_str)
                    except Exception:
                        record.nav_maturity_date = False
                        record.nav_maturity_date_formatted = ''
                        
                if metrics.get('sell_date'):
                    sell_str = metrics['sell_date']
                    try:
                        if isinstance(sell_str, str):
                            # Parse ISO format date string using Odoo's fields.Date
                            if 'T' in sell_str:
                                sell_str = sell_str.split('T')[0]
                            sell_date = fields.Date.from_string(sell_str)
                            record.nav_sell_date = sell_date
                            # Format thành dd/MM/yyyy
                            if sell_date:
                                record.nav_sell_date_formatted = sell_date.strftime('%d/%m/%Y')
                        elif hasattr(sell_str, 'date'):
                            sell_date = sell_str.date() if isinstance(sell_str, datetime) else sell_str
                            record.nav_sell_date = sell_date
                            if sell_date:
                                record.nav_sell_date_formatted = sell_date.strftime('%d/%m/%Y')
                        else:
                            record.nav_sell_date = sell_str
                            if sell_str:
                                record.nav_sell_date_formatted = sell_str.strftime('%d/%m/%Y') if hasattr(sell_str, 'strftime') else str(sell_str)
                    except Exception:
                        record.nav_sell_date = False
                        record.nav_sell_date_formatted = ''
                
                # Format purchase_date (từ created_at) thành dd/MM/yyyy
                if purchase_date:
                    try:
                        record.transaction_date_formatted = purchase_date.strftime('%d/%m/%Y')
                    except Exception:
                        record.transaction_date_formatted = ''
                record.nav_days = int(metrics.get('days', 0))
                record.nav_days_converted = float(metrics.get('days_converted', 0.0))
                record.nav_purchase_value = float(metrics.get('purchase_value', 0.0))
                record.nav_price_with_fee = float(metrics.get('price_with_fee', 0.0))
                record.nav_converted_rate = float(metrics.get('converted_rate', 0.0))
                record.nav_interest_delta = float(metrics.get('interest_delta', 0.0))
                record.nav_tax_tncn = float(metrics.get('tax_tncn', 0.0))
                record.nav_sell_price1 = float(metrics.get('sell_price1', 0.0))
                record.nav_sell_price2 = float(metrics.get('sell_price2', 0.0))
                record.nav_sell_value1 = float(metrics.get('sell_value1', 0.0))
                record.nav_sell_value2 = float(metrics.get('sell_value2', 0.0))
                record.nav_difference = float(metrics.get('difference', 0.0))
                record.nav_sell_fee = float(metrics.get('sell_fee', 0.0))
                record.nav_tax = float(metrics.get('tax', 0.0))
                record.nav_customer_receive = float(metrics.get('customer_receive', 0.0))
            except Exception as e:
                self._logger.warning(f"Failed to compute NAV calculation for transaction {record.id}: {e}")

    @api.depends('created_at', 'date_end')
    def _compute_datetime_formatted(self):
        """Format datetime fields thành dd/MM/yyyy HH:mm:ss với timezone của user"""
        import pytz
        
        # Lấy timezone của user, mặc định là Asia/Ho_Chi_Minh
        user_tz_name = self.env.user.tz or 'Asia/Ho_Chi_Minh'
        try:
            user_tz = pytz.timezone(user_tz_name)
        except Exception:
            user_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
        utc_tz = pytz.UTC
        
        for record in self:
            # Format created_at
            if record.created_at:
                try:
                    dt = record.created_at
                    if isinstance(dt, str):
                        dt = fields.Datetime.from_string(dt)
                    
                    if isinstance(dt, datetime):
                        # Convert từ UTC sang user timezone
                        if dt.tzinfo is None:
                            dt = utc_tz.localize(dt)
                        local_dt = dt.astimezone(user_tz)
                        record.created_at_formatted = local_dt.strftime('%d/%m/%Y %H:%M:%S')
                    else:
                        record.created_at_formatted = ''
                except Exception:
                    record.created_at_formatted = ''
            else:
                record.created_at_formatted = ''
            
            # Format date_end
            if record.date_end:
                try:
                    dt = record.date_end
                    if isinstance(dt, str):
                        dt = fields.Datetime.from_string(dt)
                    
                    if isinstance(dt, datetime):
                        # Convert từ UTC sang user timezone
                        if dt.tzinfo is None:
                            dt = utc_tz.localize(dt)
                        local_dt = dt.astimezone(user_tz)
                        record.date_end_formatted = local_dt.strftime('%d/%m/%Y %H:%M:%S')
                    else:
                        record.date_end_formatted = ''
                except Exception:
                    record.date_end_formatted = ''
            else:
                record.date_end_formatted = ''

    def _compute_contract_file(self):
        """Compute contract file from signed contract"""
        Signed = self.env['fund.signed.contract'].sudo()
        Investment = self.env['portfolio.investment'].sudo()
        
        for rec in self:
            rec.contract_file = False
            rec.contract_filename = False
            
            try:
                signed = False
                
                # Priority 1: Get by transaction_id
                if rec.id:
                    signed = Signed.get_contract_by_transaction(rec.id)
                
                # Priority 2: Get by investment (same user and fund)
                # Chỉ tìm theo investment nếu chưa tìm thấy theo transaction_id
                if not signed:
                    candidate_inv = Investment.search([
                        ('user_id', '=', rec.user_id.id if rec.user_id else 0),
                        ('fund_id', '=', rec.fund_id.id if rec.fund_id else 0),
                    ], limit=1, order='id desc')
                    
                    if candidate_inv:
                        signed = Signed.get_contract_by_investment(candidate_inv.id)
                
                # Priority 3: Get by partner
                # Chỉ tìm theo partner nếu vẫn chưa tìm thấy
                if not signed and rec.user_id and rec.user_id.partner_id:
                    signed = Signed.get_contract_by_partner(rec.user_id.partner_id.id)
                
                if signed and signed.file_data:
                    rec.contract_file = signed.file_data
                    rec.contract_filename = signed.filename or f"contract_{rec.id}.pdf"
            except Exception as e:
                self._logger.warning(f"Failed to compute contract file for transaction {rec.id}: {e}")
                rec.contract_file = False
                rec.contract_filename = False

    # ===== Investment handling =====
    def _get_effective_units(self):
        """Số units hiệu lực để cập nhật Investment: ưu tiên matched_units nếu có."""
        self.ensure_one()
        matched_units = float(getattr(self, 'matched_units', 0) or 0)
        if matched_units > 0:
            return matched_units
        return float(getattr(self, 'units', 0) or 0)

    def _update_investment(self):
        """Cập nhật Investment khi giao dịch đã completed.
        - Mua: gộp vào bản ghi hiện có cùng (user_id, fund_id) nếu có; nếu không thì tạo mới.
        - Bán: trừ units ở Investment đang active; đóng nếu về 0.
        """
        Investment = self.env['portfolio.investment'].sudo()
        for tx in self:
            if tx.status != 'completed' or not tx.fund_id or not tx.user_id:
                continue

            effective_units = tx._get_effective_units()
            unit_price = float(tx.price or tx.current_nav or tx.fund_id.current_nav or 0.0)

            if tx.transaction_type == constants.TRANSACTION_TYPE_BUY:
                amount_delta = effective_units * unit_price
                domain = [
                    ('user_id', '=', tx.user_id.id),
                    ('fund_id', '=', tx.fund_id.id),
                ]
                existing_inv = Investment.search(domain, limit=1, order='id desc')

                def _write_purchase(inv_record):
                    new_units = float(inv_record.units or 0.0) + effective_units
                    new_amount = max(0.0, float(inv_record.amount or 0.0) + amount_delta)
                    inv_record.write({
                        'units': new_units,
                        'amount': new_amount,
                        'status': 'active',
                    })

                if existing_inv:
                    _write_purchase(existing_inv)
                else:
                    inv_vals = {
                        'user_id': tx.user_id.id,
                        'fund_id': tx.fund_id.id,
                        'units': effective_units,
                        'amount': amount_delta,
                        'status': 'active',
                    }
                    try:
                        with self.env.cr.savepoint():
                            Investment.create(inv_vals)
                    except IntegrityError:
                        # Nếu cạnh tranh unique, fallback sang update
                        fallback_inv = Investment.search(domain, limit=1, order='id desc')
                        if fallback_inv:
                            _write_purchase(fallback_inv)

            elif tx.transaction_type == constants.TRANSACTION_TYPE_SELL:
                active_inv = Investment.search([
                    ('user_id', '=', tx.user_id.id),
                    ('fund_id', '=', tx.fund_id.id),
                    ('status', '=', 'active'),
                ], limit=1)
                if active_inv:
                    remaining_units = max(0.0, float(active_inv.units or 0.0) - effective_units)
                    active_inv.write({
                        'units': remaining_units,
                        'status': (
                            constants.INVESTMENT_STATUS_CLOSED
                            if remaining_units <= 0
                            else constants.INVESTMENT_STATUS_ACTIVE
                        ),
                    })

    def write(self, vals):
        """Cập nhật Investment khi trạng thái chuyển sang completed.
        Có thể bỏ qua bằng context: bypass_investment_update=True
        """
        prev_status_map = {rec.id: rec.status for rec in self}
        res = super().write(vals)

        if self.env.context.get('bypass_investment_update'):
            return res

        for rec in self:
            prev_status = prev_status_map.get(rec.id)
            if prev_status != constants.STATUS_COMPLETED and rec.status == constants.STATUS_COMPLETED:
                rec._update_investment()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Create transactions with basic validation"""
        return super().create(vals_list)

    def action_complete(self):
        """Complete transaction - change status to completed"""
        for record in self:
            if record.status == constants.DEFAULT_TRANSACTION_STATUS:  # pending
                record.write({
                    'status': constants.STATUS_COMPLETED,
                })
                # Update investment when transaction is completed
                record._update_investment()
        return True

    def action_cancel(self):
        """Cancel transaction - change status to cancelled"""
        for record in self:
            if record.status == constants.DEFAULT_TRANSACTION_STATUS:  # pending
                record.write({
                    'status': constants.STATUS_CANCELLED,
                })
        return True

