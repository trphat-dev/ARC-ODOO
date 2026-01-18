from odoo import http
from odoo.http import request
import json
from datetime import datetime, timedelta
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access
from ..utils.timezone_utils import format_datetime_user_tz, format_date_user_tz

try:
    # Prefer relativedelta như @nav_management dùng
    from dateutil.relativedelta import relativedelta
except Exception:
    relativedelta = None

class TransactionPeriodicController(http.Controller):

    @http.route('/transaction_management/periodic', type='http', auth='user', website=True)
    @require_module_access('transaction_management')
    def transaction_periodic_page(self, **kw):
        # Lấy dữ liệu thật từ model portfolio.transaction của user hiện tại - chỉ lấy các giao dịch completed
        transactions = request.env['portfolio.transaction'].search([
            ('investment_type', '=', 'fund_certificate'),
            ('status', '=', 'completed'),
            ('user_id', '=', request.env.user.id)
        ], order='create_date desc')

        # Helper: MROUND tương tự nav.calculator (bước 50)
        def mround(value, step=50):
            try:
                step = float(step or 0)
                v = float(value or 0)
                if step <= 0:
                    return v
                return float(round(v / step) * step)
            except Exception:
                return value

        # Helper: lấy lãi suất theo kỳ hạn như @nav_management
        def get_interest_rate_for_months(months):
            try:
                TermRate = request.env['nav.term.rate'].sudo()
                recs = TermRate.search([('active', '=', True)])
                months_int = int(months or 0)
                # chọn record theo đúng kỳ hạn, ưu tiên effective gần nhất
                candidates = recs.filtered(lambda r: int(r.term_months or 0) == months_int)
                if candidates:
                    # sort by effective_date desc
                    return candidates.sorted('effective_date', reverse=True)[0].interest_rate or 0.0
            except Exception:
                pass
            return None

        orders = []
        for tx in transactions:
            # Số tài khoản (nếu cần thiết cho hiển thị phụ)
            partner = request.env.user.partner_id
            account_number = ''
            if partner:
                status_info = request.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                account_number = status_info.account_number if status_info else ''

            # Kỳ hạn: ưu tiên field trên transaction, fallback 12
            try:
                tenor_months = int(getattr(tx, 'term_months', 0) or 0) or 12
            except Exception:
                tenor_months = 12

            # Lãi suất: ưu tiên field trên transaction, sau đó lấy theo kỳ hạn từ nav.term.rate
            ir = getattr(tx, 'interest_rate', None)
            if ir is None:
                rate = get_interest_rate_for_months(tenor_months)
                ir = rate if rate is not None else 0.0

            # Ngày đáo hạn: dùng created_at (có giờ) hoặc transaction_date, cộng tenor_months
            base_dt = getattr(tx, 'created_at', False) or tx.transaction_date or tx.create_date
            maturity_dt = None
            if base_dt:
                if relativedelta:
                    try:
                        maturity_dt = base_dt + relativedelta(months=tenor_months)
                    except Exception:
                        maturity_dt = self._calculate_maturity_date(base_dt, tenor_months)
                else:
                    maturity_dt = self._calculate_maturity_date(base_dt, tenor_months)

            # Số ngày còn lại
            days_left = None
            try:
                if base_dt and maturity_dt:
                    base_date = base_dt.date() if hasattr(base_dt, 'date') else base_dt
                    maturity_date_only = maturity_dt.date() if hasattr(maturity_dt, 'date') else maturity_dt
                    days_left = (maturity_date_only - base_date).days
            except Exception:
                days_left = None

            # Số tiền đăng ký đầu tư: dùng amount (trade_price), format giống @nav_management khi render
            amount_value = float(tx.amount or 0.0)

            # Áp dụng MROUND(50) cho giá đơn vị tính toán phụ (không hiển thị) để tương thích logic
            unit_price = 0.0
            try:
                if (tx.units or 0) > 0:
                    unit_price = float(amount_value) / float(tx.units)
            except Exception:
                unit_price = 0.0
            price2 = mround(unit_price, 50)  # giữ để đồng nhất logic, không sử dụng ở UI

            orders.append({
                'account_number': account_number,
                'fund_name': tx.fund_id.name,
                'order_date': format_datetime_user_tz(request.env, tx.created_at if getattr(tx, 'created_at', False) else (tx.create_date if tx.create_date else None), '%d/%m/%Y, %H:%M') or '',
                'order_code': tx.name or f"TX{tx.id:06d}",
                # Số tiền đăng ký đầu tư
                'amount': f"{amount_value:,.0f}",
                'currency': tx.currency_id.symbol or 'đ',
                # Kỳ đầu tư tiếp theo: hiển thị ngày đáo hạn (cột "Kỳ đầu tư tiếp theo")
                'session_date': format_date_user_tz(request.env, maturity_dt, '%d/%m/%Y') if maturity_dt else 'N/A',
                # Thông tin hiển thị khác
                'status': 'Định kỳ',
                'status_detail': tx.description or 'Tự động',
                'transaction_type': 'Mua',  # chỉ lấy buy ở domain
                'units': f"{tx.units:,.0f}",
                'fund_ticker': tx.fund_id.ticker or '',
                # Thông tin kỳ hạn
                'tenor_months': tenor_months,
                'interest_rate': f"{ir:.2f}%",
                'maturity_date': format_date_user_tz(request.env, maturity_dt, '%d/%m/%Y') if maturity_dt else 'N/A',
                'days_to_maturity': days_left if days_left is not None else 'N/A',
                # Trạng thái đầu tư
                'invest_status': 'Đang tham gia',
                'invest_status_detail': '',
            })

        orders_json = json.dumps(orders, ensure_ascii=False)
        return request.render('transaction_management.transaction_periodic_page', {
            'orders_json': orders_json,
        })
    
    def _calculate_maturity_date(self, purchase_date, tenor_months):
        """Tính ngày đáo hạn từ ngày mua + số kỳ hạn"""
        if isinstance(purchase_date, str):
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d %H:%M:%S')
        
        end_date = purchase_date + timedelta(days=tenor_months * 30)
        
        # Bỏ qua thứ 7 và chủ nhật
        while end_date.weekday() in (5, 6):  # 5=Thứ 7, 6=CN
            end_date += timedelta(days=1)
        
        return end_date
    
    def _calculate_days(self, purchase_date, maturity_date):
        """Tính số ngày giữa ngày mua và ngày đáo hạn"""
        if isinstance(purchase_date, str):
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d %H:%M:%S')
        
        return (maturity_date - purchase_date).days 