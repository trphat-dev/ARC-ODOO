from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class NavTransaction(models.Model):
    _name = 'nav.transaction'
    _description = 'NAV Phiên giao dịch'
    _rec_name = 'transaction_session'
    _order = 'create_date desc'

    # Thông tin cơ bản
    fund_id = fields.Many2one('portfolio.fund', string='Quỹ', required=True)
    transaction_session = fields.Char(string='Phiên giao dịch', required=True)
    nav_value = fields.Float(string='Giá trị NAV', required=True, digits=(16, 2))
    create_date = fields.Datetime(string='Ngày tạo', default=fields.Datetime.now, readonly=True)
    
    # Thông tin bổ sung
    description = fields.Text(string='Mô tả')
    status = fields.Selection([
        ('active', 'Hoạt động'),
        ('inactive', 'Không hoạt động')
    ], string='Trạng thái', default='active')
    
    # Constraints
    @api.constrains('nav_value')
    def _check_nav_value(self):
        for record in self:
            if record.nav_value <= 0:
                raise ValidationError(_('Giá trị NAV phải lớn hơn 0.'))
    
    @api.constrains('transaction_session')
    def _check_unique_transaction_session(self):
        for record in self:
            if record.transaction_session:
                duplicate = self.search([
                    ('transaction_session', '=', record.transaction_session),
                    ('fund_id', '=', record.fund_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('Phiên giao dịch này đã tồn tại cho quỹ được chọn.'))
    
    def action_export_nav_data(self):
        """Xuất dữ liệu NAV phiên giao dịch"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/nav_management/export_nav_transaction/{self.fund_id.id}',
            'target': 'new',
        }
    
    @api.model
    def get_nav_data_by_fund(self, fund_id):
        """Lấy dữ liệu NAV theo quỹ"""
        return self.search([
            ('fund_id', '=', fund_id),
            ('status', '=', 'active')
        ])

    @api.model
    def get_nav_transactions_via_portfolio(self, fund_id=None, from_date=None, to_date=None, status_filter=None):
        """Lấy danh sách giao dịch (pending + approved) từ portfolio.transaction phục vụ NAV list.

        Trả về danh sách dict phù hợp với widget NAV phiên giao dịch.
        """
        # Base domain: lấy pending và completed (approved)
        domain = [('status', 'in', ['pending', 'completed'])]

        # Lọc theo quỹ
        if fund_id:
            try:
                fund_id_int = int(fund_id)
            except Exception:
                fund_id_int = fund_id
            domain.append(('fund_id', '=', fund_id_int))

        # Lọc theo trạng thái nếu truyền riêng (pending/approved/all/pending_remaining)
        if status_filter:
            if status_filter == 'pending':
                domain = [('status', '=', 'pending')] + [d for d in domain if not (isinstance(d, tuple) and d[0] == 'status')]
            elif status_filter == 'approved':
                domain = [('status', '=', 'completed')] + [d for d in domain if not (isinstance(d, tuple) and d[0] == 'status')]
            elif status_filter == 'all':
                # giữ nguyên domain
                pass
            elif status_filter == 'pending_remaining':
                domain = [('status', '=', 'pending')] + [d for d in domain if not (isinstance(d, tuple) and d[0] == 'status')]

        # Lọc theo khoảng ngày: sử dụng created_at (datetime) hoặc create_date
        # Chuẩn hoá để case Today không bị miss bản ghi trong ngày (do so sánh datetime)
        if from_date and to_date and from_date == to_date:
            # Filter đúng 1 ngày: 00:00:00 -> 23:59:59
            date_only = from_date
            domain += [
                # (created_at in day range) OR (create_date in day range)
                '|',
                '&', ('created_at', '>=', f"{date_only} 00:00:00"), ('created_at', '<=', f"{date_only} 23:59:59"),
                '&', ('create_date', '>=', f"{date_only} 00:00:00"), ('create_date', '<=', f"{date_only} 23:59:59")
            ]
        else:
            if from_date:
                domain += [
                    # (created_at >= from_date 00:00:00) OR (create_date >= from_date 00:00:00)
                    '|', ('created_at', '>=', f"{from_date} 00:00:00"), ('create_date', '>=', f"{from_date} 00:00:00")
                ]
            if to_date:
                domain += [
                    # (created_at <= to_date 23:59:59) OR (create_date <= to_date 23:59:59)
                    '|', ('created_at', '<=', f"{to_date} 23:59:59"), ('create_date', '<=', f"{to_date} 23:59:59")
                ]

        # Debug: In ra domain để kiểm tra
        print(f"[DEBUG] NAV Transaction Domain: {domain}")
        print(f"[DEBUG] Filter params - fund_id: {fund_id}, from_date: {from_date}, to_date: {to_date}, status_filter: {status_filter}")
        
        # Query bằng sudo để tránh lỗi phân quyền khi đọc giao dịch của các user khác
        portfolio_tx = self.env['portfolio.transaction'].sudo().search(domain, order='created_at desc')
        
        print(f"[DEBUG] Found {len(portfolio_tx)} transactions")
        
        # Debug: In ra một vài transaction để kiểm tra
        if len(portfolio_tx) > 0:
            for i, tx in enumerate(portfolio_tx[:3]):  # Chỉ in 3 transaction đầu
                print(f"[DEBUG] Transaction {i+1}: ID={tx.id}, Fund={tx.fund_id.name if tx.fund_id else 'None'}, "
                      f"Created={tx.created_at}, Status={tx.status}")
        else:
            print(f"[DEBUG] No transactions found for fund_id={fund_id}")

        results = []

        # Lấy bảng lãi suất theo kỳ hạn từ cấu hình (active)
        rate_by_month = {}
        try:
            TermRate = self.env['nav.term.rate'].sudo()
            rates = TermRate.search([('active', '=', True)])
            for r in rates:
                key = int(r.term_months or 0)
                if key <= 0:
                    continue
                rate_by_month[key] = r.interest_rate or 0.0
        except Exception:
            rate_by_month = {}
        for tx in portfolio_tx:
            # Nếu yêu cầu chỉ lấy lệnh còn lại sau khớp (remaining > 0), lọc tại đây
            if status_filter == 'pending_remaining':
                units = getattr(tx, 'units', 0) or 0
                matched = getattr(tx, 'matched_units', 0) or 0
                remaining = units - matched
                if remaining <= 0:
                    continue
            # Xác định thời điểm vào lệnh (ưu tiên created_at vì có cả giờ phút)
            entry_dt = getattr(tx, 'created_at', False) or tx.create_date
            entry_dt_str = entry_dt.strftime('%Y-%m-%d %H:%M:%S') if entry_dt else ''

            # Tạo mã/phiên giao dịch hiển thị: gồm loại lệnh + mã + thời điểm vào lệnh
            session_name = f"{(tx.transaction_type or '').upper()}_{tx.reference or tx.id}_{entry_dt_str.replace('-', '').replace(':', '').replace(' ', '')}"

            # Map trạng thái về frontend
            frontend_status = 'pending' if tx.status == 'pending' else 'approved' if tx.status == 'completed' else (tx.status or '')

            # Giá tham chiếu để tính LS quy đổi: ưu tiên giá lệnh của NĐT (tx.price), sau đó current_nav, cuối cùng cấu hình quỹ
            if getattr(tx, 'price', False):
                nav_value = tx.price
            elif getattr(tx, 'current_nav', False):
                nav_value = tx.current_nav
            elif tx.fund_id and tx.fund_id.certificate_id:
                # Lấy từ fund.certificate trong fund_management_control
                nav_value = tx.fund_id.certificate_id.initial_certificate_price or 0.0
            else:
                nav_value = 0.0

            # Ngày mua/bán hiển thị: ưu tiên created_at (ngày vào lệnh, có giờ), sau đó create_date
            if getattr(tx, 'created_at', False):
                created_str = tx.created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_str = tx.create_date.isoformat() if tx.create_date else ''

            # Kỳ hạn và lãi suất
            term_months = getattr(tx, 'term_months', None)
            if not term_months or not isinstance(term_months, (int, float)):
                term_months = 12  # fallback an toàn nếu không có trường
            try:
                term_months_int = int(term_months)
            except Exception:
                term_months_int = 12

            # Lãi suất: ưu tiên field trên transaction nếu có, sau đó mới lấy theo kỳ hạn
            tx_interest = getattr(tx, 'interest_rate', None)
            interest_rate = tx_interest if (tx_interest is not None) else rate_by_month.get(term_months_int)

            # Ngày đáo hạn = thời gian mua/bán (ưu tiên created_at) + kỳ hạn (tháng)
            maturity_date_iso = ''
            days_between = None
            try:
                from dateutil.relativedelta import relativedelta
                base_dt = getattr(tx, 'created_at', False) or tx.create_date
                if base_dt and term_months_int:
                    maturity_dt = base_dt + relativedelta(months=term_months_int)
                    maturity_date_iso = maturity_dt.isoformat() if hasattr(maturity_dt, 'isoformat') else ''
                    # Tính số ngày thực tế từ ngày đặt lệnh đến ngày đáo hạn (dùng phần ngày)
                    try:
                        base_date = base_dt.date() if hasattr(base_dt, 'date') else base_dt
                        maturity_date_only = maturity_dt.date() if hasattr(maturity_dt, 'date') else maturity_dt
                        days_between = (maturity_date_only - base_date).days
                    except Exception:
                        days_between = None
            except Exception:
                maturity_date_iso = ''
                days_between = None

            results.append({
                'id': tx.id,
                'fund_id': tx.fund_id.id if tx.fund_id else None,
                'fund_name': tx.fund_id.name if tx.fund_id else '',
                'fund_ticker': tx.fund_id.ticker if tx.fund_id else '',
                'transaction_session': session_name,
                'transaction_type': tx.transaction_type,
                'status': frontend_status,
                'db_status': tx.status,
                'active': getattr(tx, 'active', True),
                'investor_name': getattr(tx, 'investor_name', '') or '',
                'maturity_date': getattr(tx, 'maturity_date', None) or None,
                # Dữ liệu cho calculator
                'term_months': term_months_int,
                'interest_rate': interest_rate,
                'account_number': getattr(tx, 'account_number', '') or '',
                'units': tx.units or 0,
                'matched_units': getattr(tx, 'matched_units', 0) or 0,
                'remaining_units': (tx.units or 0) - (getattr(tx, 'matched_units', 0) or 0),
                'amount': tx.amount or 0,
                'currency': tx.currency_id.symbol if tx.currency_id else '',
                # Giá mua/bán tham chiếu cho LS quy đổi
                'nav_value': nav_value,
                'create_date': created_str,
                'transaction_date': tx.created_at.strftime('%Y-%m-%d') if getattr(tx, 'created_at', False) else '',
                'created_at': tx.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(tx, 'created_at', False) else '',
                'description': tx.description or '',
                'approved_by': tx.approved_by.name if tx.approved_by else '',
                'approved_at': tx.approved_at.isoformat() if tx.approved_at else '',
                'source': getattr(tx, 'source', 'portfolio') or 'portfolio',
                # Thông tin lợi tức/kỳ hạn
                'maturity_date': maturity_date_iso,
                'days': days_between,
                # Giá mua/bán: ưu tiên amount, fallback units * nav_value
                'trade_price': tx.amount if tx.amount else ((tx.units or 0) * (nav_value or 0)),
                # Tuỳ chọn: bước làm tròn cho price2 để tránh hardcode ở frontend
                'round_step': 50,
            })

        return results

    @api.model
    def get_active_cap_config(self):
        """Trả về cấu hình chặn trên / chặn dưới đang active (bản ghi mới nhất).

        Không hardcode giá trị mặc định. Nếu không có cấu hình, trả về success=False
        để tầng gọi (controller/frontend) tự xử lý UI/flow phù hợp.
        """
        try:
            Cap = self.env['nav.cap.config'].sudo()
            rec = Cap.search([('active', '=', True)], order='id desc', limit=1)
            if rec:
                return {
                    'success': True,
                    'cap_upper': float(rec.cap_upper or 0.0),
                    'cap_lower': float(rec.cap_lower or 0.0),
                }
            return {
                'success': False,
                'message': _('Không tìm thấy cấu hình chặn trên/chặn dưới đang hoạt động.'),
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }


class NavTermRate(models.Model):
    _name = 'nav.term.rate'
    _description = 'Cấu hình kỳ hạn / lãi suất NAV'
    _order = 'term_months'

    term_months = fields.Integer(string='Kỳ hạn (tháng)', required=True)
    interest_rate = fields.Float(string='Lãi suất (%)', required=True, digits=(16, 2))
    effective_date = fields.Date(string='Ngày hiệu lực', required=True, default=fields.Date.today)
    end_date = fields.Date(string='Ngày kết thúc', help='Để trống nếu không có ngày kết thúc')
    active = fields.Boolean(string='Kích hoạt', default=True)
    description = fields.Char(string='Mô tả')

    _sql_constraints = [
        ('uniq_term', 'unique(term_months)', 'Mỗi kỳ hạn chỉ được khai báo một lần!')
    ]

    @api.constrains('term_months', 'interest_rate', 'effective_date', 'end_date')
    def _check_values(self):
        for rec in self:
            if rec.term_months <= 0:
                raise ValidationError(_('Kỳ hạn (tháng) phải > 0.'))
            # lãi suất phần trăm hợp lệ 0..100
            if rec.interest_rate is None:
                raise ValidationError(_('Lãi suất là bắt buộc.'))
            if rec.interest_rate < 0 or rec.interest_rate > 100:
                raise ValidationError(_('Lãi suất phải nằm trong khoảng 0% đến 100%.'))
            
            # Kiểm tra ngày hiệu lực
            if rec.effective_date and rec.end_date:
                if rec.effective_date > rec.end_date:
                    raise ValidationError(_('Ngày hiệu lực không được lớn hơn ngày kết thúc.'))
            
            # Kiểm tra ngày hiệu lực không được trong quá khứ (trừ khi đang edit)
            if rec.effective_date and rec.effective_date < fields.Date.today():
                # Cho phép nếu đang edit record cũ
                if not self._origin or self._origin.effective_date != rec.effective_date:
                    raise ValidationError(_('Ngày hiệu lực không được trong quá khứ.'))

    @api.model
    def get_current_rate(self, term_months, check_date=None):
        """Lấy lãi suất hiện tại cho kỳ hạn cụ thể"""
        if check_date is None:
            check_date = fields.Date.today()
        
        domain = [
            ('term_months', '=', term_months),
            ('active', '=', True),
            ('effective_date', '<=', check_date)
        ]
        
        # Nếu có ngày kết thúc, phải còn hiệu lực
        rates = self.search(domain)
        if rates:
            # Lọc các rate còn hiệu lực (không có end_date hoặc end_date >= check_date)
            valid_rates = rates.filtered(lambda r: not r.end_date or r.end_date >= check_date)
            if valid_rates:
                # Lấy rate có ngày hiệu lực gần nhất
                return valid_rates.sorted('effective_date', reverse=True)[0]
        
        return self.env['nav.term.rate']

    @api.model
    def get_all_current_rates(self, check_date=None):
        """Lấy tất cả lãi suất hiện tại"""
        if check_date is None:
            check_date = fields.Date.today()
        
        domain = [
            ('active', '=', True),
            ('effective_date', '<=', check_date)
        ]
        
        rates = self.search(domain)
        # Lọc các rate còn hiệu lực
        valid_rates = rates.filtered(lambda r: not r.end_date or r.end_date >= check_date)
        
        # Nhóm theo term_months và lấy rate mới nhất
        result = {}
        for rate in valid_rates:
            if rate.term_months not in result or rate.effective_date > result[rate.term_months].effective_date:
                result[rate.term_months] = rate
        
        return list(result.values())


class NavCapConfig(models.Model):
    _name = 'nav.cap.config'
    _description = 'Cấu hình chặn trên / chặn dưới NAV'
    _order = 'id desc'

    cap_upper = fields.Float(string='Chặn trên (%)', default=2.0, digits=(16, 4), help='Ví dụ 2.0 = 2.0%')
    cap_lower = fields.Float(string='Chặn dưới (%)', default=0.10, digits=(16, 4), help='Ví dụ 0.10 = 0.10%')
    active = fields.Boolean(string='Kích hoạt', default=True)
    description = fields.Char(string='Mô tả')

    @api.constrains('cap_upper', 'cap_lower')
    def _check_caps(self):
        for rec in self:
            # cả hai phải trong 0..100
            if rec.cap_upper is None or rec.cap_lower is None:
                raise ValidationError(_('Chặn trên và chặn dưới là bắt buộc.'))
            if rec.cap_upper < 0 or rec.cap_upper > 100:
                raise ValidationError(_('Chặn trên phải nằm trong khoảng 0% đến 100%.'))
            if rec.cap_lower < 0 or rec.cap_lower > 100:
                raise ValidationError(_('Chặn dưới phải nằm trong khoảng 0% đến 100%.'))
            # chặn trên phải lớn hơn chặn dưới
            if rec.cap_upper <= rec.cap_lower:
                raise ValidationError(_('Chặn trên phải lớn hơn chặn dưới.'))