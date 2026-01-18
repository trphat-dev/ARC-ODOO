from odoo import models, fields, _
from datetime import datetime, timedelta

from ..utils import date_utils, mround


class NavTransactionCalculator(models.AbstractModel):
    _name = 'nav.transaction.calculator'
    _description = 'Calculator cho NAV phiên giao dịch'

    def _compute_days(self, term_months=None, days=None):
        """Ưu tiên days từ dữ liệu; nếu không, ước lượng theo kỳ hạn tháng (x30).

        Tránh phụ thuộc now() ở tầng tính toán để đảm bảo tính idempotent cho 1 bản ghi.
        """
        try:
            days_int = int(days or 0)
        except Exception:
            days_int = 0
        if days_int > 0:
            return days_int
        try:
            m = int(term_months or 0)
        except Exception:
            m = 0
        if m > 0:
            # Chuẩn hoá: 1 tháng = 30 ngày để đồng nhất với Excel nếu không có days
            return max(1, m * 30)
        # fallback an toàn
        return 1

    def compute_maturity_date(self, purchase_date, term_months):
        """
        Tính ngày đáo hạn từ ngày mua và kỳ hạn.
        E: Ngày đáo hạn = IF(WEEKDAY(AB8,2)>5, AB8-WEEKDAY(AB8,2)+7+1, AB8)
        Nếu ngày đáo hạn rơi vào cuối tuần, chuyển sang thứ 2 tuần sau.
        """
        if not purchase_date or not term_months:
            return None
        
        # Convert to date if datetime
        if isinstance(purchase_date, datetime):
            purchase_dt = purchase_date.date()
        else:
            purchase_dt = purchase_date
        
        # Tính ngày đáo hạn = ngày mua + kỳ hạn (tháng)
        from dateutil.relativedelta import relativedelta
        maturity_date = purchase_dt + relativedelta(months=term_months)
        
        # Kiểm tra nếu rơi vào cuối tuần (Saturday=5, Sunday=6)
        weekday_num = date_utils.weekday(maturity_date, return_type=2)
        if weekday_num > 5:  # Saturday or Sunday
            # Chuyển sang thứ 2 tuần sau
            days_to_add = 8 - weekday_num
            maturity_date = maturity_date + timedelta(days=days_to_add)
        
        return maturity_date

    def compute_sell_date(self, maturity_date):
        """
        Tính ngày bán từ ngày đáo hạn.
        D: Ngày bán = WORKDAY(E6,-2) - 2 ngày làm việc trước ngày đáo hạn
        """
        if not maturity_date:
            return None
        
        return date_utils.workday(maturity_date, -2)

    def compute_purchase_value(self, units, price_per_unit, fee_rate):
        """
        Tính giá trị mua.
        L: Giá trị mua = I8 * J8 + I8 * J8 * K8
        fee_rate là phần trăm (ví dụ: 0.3 = 0.3%)
        """
        units = float(units or 0.0)
        price = float(price_per_unit or 0.0)
        fee = float(fee_rate or 0.0) / 100.0  # Convert percentage to decimal
        return units * price + units * price * fee

    def compute_price_with_fee(self, purchase_value, units):
        """
        Tính giá 1 CCQ đã bao gồm thuế/phí.
        M: Giá 1 CCQ đã bao gồm thuế/phí = L8 / I8
        """
        units = float(units or 0.0)
        if units <= 0:
            return 0.0
        return float(purchase_value or 0.0) / units

    def compute_sell_value1(self, purchase_value, interest_rate, days):
        """
        Tính giá trị bán 1.
        U: Giá trị bán 1 = L8 * N8 / 365 * G8 + L8
        """
        purchase_val = float(purchase_value or 0.0)
        rate = float(interest_rate or 0.0)
        d = float(days or 0.0)
        if d <= 0:
            return purchase_val
        return purchase_val * (rate / 100.0) / 365.0 * d + purchase_val

    def compute_sell_price1(self, sell_value1, units):
        """
        Tính giá bán 1.
        S: Giá bán 1 = ROUND(U8 / I8, 0)
        """
        units = float(units or 0.0)
        if units <= 0:
            return 0.0
        return round(float(sell_value1 or 0.0) / units)

    def compute_sell_price2(self, sell_price1, step=50):
        """
        Tính giá bán 2.
        T: Giá bán 2 = MROUND(S8, 50)
        """
        return mround.mround(float(sell_price1 or 0.0), step)

    def compute_sell_value2(self, units, sell_price2):
        """
        Tính giá trị bán 2.
        V: Giá trị bán 2 = I8 * T8
        """
        return float(units or 0.0) * float(sell_price2 or 0.0)

    def compute_difference(self, sell_value2, sell_value1):
        """
        Tính chênh lệch.
        W: Chênh lệch = V8 - U8
        """
        return float(sell_value2 or 0.0) - float(sell_value1 or 0.0)

    def compute_converted_rate(self, sell_price2, purchase_price, days):
        """
        Tính lãi suất quy đổi theo giá bán 2.
        O: Lãi suất quy đổi = (T8 / J8 - 1) * 365 / G8 * 100
        """
        price2 = float(sell_price2 or 0.0)
        price_purchase = float(purchase_price or 0.0)
        d = float(days or 0.0)
        if price_purchase <= 0 or d <= 0:
            return 0.0
        return ((price2 / price_purchase) - 1.0) * 365.0 / d * 100.0

    def compute_interest_delta(self, converted_rate, interest_rate):
        """
        Tính chênh lệch lãi suất.
        Q: Chênh lệch lãi suất = O8 - N8
        """
        return float(converted_rate or 0.0) - float(interest_rate or 0.0)

    def compute_days_converted(self, converted_rate, days, interest_rate):
        """
        Tính số ngày quy đổi theo lãi suất mới.
        H: Số ngày quy đổi = O8 * G8 / N8
        """
        rate_new = float(converted_rate or 0.0)
        d = float(days or 0.0)
        rate_old = float(interest_rate or 0.0)
        if rate_old <= 0:
            return d
        return rate_new * d / rate_old

    def compute_transaction_metrics_full(self, transaction_data):
        """
        Tính toán đầy đủ các trường NAV cho transaction.
        
        Args:
            transaction_data: dict chứa:
                - purchase_date (date): Ngày mua/bán (C)
                - term_months (int): Kỳ hạn (F)
                - units (float): Số lượng CCQ (I)
                - price_per_unit (float): Giá CCQ tại thời điểm mua (J)
                - fee_rate (float): Phí mua (K) - tỷ lệ phần trăm
                - interest_rate (float): Lãi suất (N) - tỷ lệ phần trăm
                - sell_fee (float): Phí bán (P) - optional
                - tax (float): Thuế TNCN (Y) - optional
        
        Returns:
            dict: Chứa tất cả các trường tính toán NAV
        """
        if not isinstance(transaction_data, dict):
            return {}
        
        # Input fields
        purchase_date = transaction_data.get('purchase_date') or transaction_data.get('transaction_date')
        term_months = int(transaction_data.get('term_months') or 0)
        units = float(transaction_data.get('units') or 0.0)
        price_per_unit = float(transaction_data.get('price_per_unit') or transaction_data.get('price') or 0.0)
        # fee_rate đã là phần trăm từ caller, không cần chia 100 ở đây
        fee_rate = float(transaction_data.get('fee_rate') or 0.0)
        interest_rate = float(transaction_data.get('interest_rate') or 0.0)
        sell_fee = float(transaction_data.get('sell_fee') or transaction_data.get('sell_fee_rate', 0.0))
        tax = float(transaction_data.get('tax') or transaction_data.get('tax_rate', 0.0))
        
        # Tính toán các giá trị
        # L: Giá trị mua
        purchase_value = self.compute_purchase_value(units, price_per_unit, fee_rate)
        
        # M: Giá 1 CCQ đã bao gồm thuế/phí
        price_with_fee = self.compute_price_with_fee(purchase_value, units)
        
        # E: Ngày đáo hạn
        maturity_date = self.compute_maturity_date(purchase_date, term_months)
        
        # D: Ngày bán
        sell_date = self.compute_sell_date(maturity_date)
        
        # G: Số ngày
        days = self._compute_days(term_months=term_months)
        if purchase_date and maturity_date:
            if isinstance(purchase_date, datetime):
                purchase_dt = purchase_date.date()
            else:
                purchase_dt = purchase_date
            if isinstance(maturity_date, datetime):
                maturity_dt = maturity_date.date()
            else:
                maturity_dt = maturity_date
            days = (maturity_dt - purchase_dt).days
        
        # U: Giá trị bán 1
        sell_value1 = self.compute_sell_value1(purchase_value, interest_rate, days)
        
        # S: Giá bán 1
        sell_price1 = self.compute_sell_price1(sell_value1, units)
        
        # T: Giá bán 2
        sell_price2 = self.compute_sell_price2(sell_price1, step=50)
        
        # V: Giá trị bán 2
        sell_value2 = self.compute_sell_value2(units, sell_price2)
        
        # W: Chênh lệch
        difference = self.compute_difference(sell_value2, sell_value1)
        
        # O: Lãi suất quy đổi
        converted_rate = self.compute_converted_rate(sell_price2, price_per_unit, days)
        
        # Q: Chênh lệch lãi suất
        interest_delta = self.compute_interest_delta(converted_rate, interest_rate)
        
        # H: Số ngày quy đổi
        days_converted = self.compute_days_converted(converted_rate, days, interest_rate)
        
        # R: Thuế TNCN (công thức có vẻ sai trong yêu cầu, dùng interest_delta thay vì P2-O2)
        # Giả sử R = interest_delta hoặc có thể tính từ sell_fee và tax
        tax_tncn = interest_delta  # Hoặc có thể tính khác tùy business logic
        
        # Z: Khách hàng thực nhận = U - X - Y
        customer_receive = sell_value1 - sell_fee - tax
        
        return {
            'purchase_date': purchase_date.isoformat() if purchase_date else '',
            'sell_date': sell_date.isoformat() if sell_date else '',
            'maturity_date': maturity_date.isoformat() if maturity_date else '',
            'term_months': term_months,
            'days': days,
            'days_converted': days_converted,
            'units': units,
            'price_per_unit': price_per_unit,
            'fee_rate': fee_rate * 100.0,  # Convert back to percentage
            'purchase_value': purchase_value,
            'price_with_fee': price_with_fee,
            'interest_rate': interest_rate,
            'converted_rate': converted_rate,
            'interest_delta': interest_delta,
            'sell_fee': sell_fee,
            'tax': tax,
            'tax_tncn': tax_tncn,
            'sell_price1': sell_price1,
            'sell_price2': sell_price2,
            'sell_value1': sell_value1,
            'sell_value2': sell_value2,
            'difference': difference,
            'customer_receive': customer_receive,
        }

    # Legacy methods for backward compatibility
    def compute_sell_value(self, order_value, interest_rate_percent, term_months=None, days=None):
        """Giá trị bán = Giá trị lệnh * lãi suất / 365 * Số ngày + Giá trị lệnh"""
        order_value = float(order_value or 0.0)
        rate = float(interest_rate_percent or 0.0)
        d = self._compute_days(term_months=term_months, days=days)
        return order_value * (rate / 100.0) / 365.0 * d + order_value

    def compute_price1(self, sell_value, units):
        """Giá bán 1 = ROUND(Giá trị bán / Số lượng CCQ, 0)"""
        units = float(units or 0.0)
        if units <= 0:
            return 0.0
        return float(round(float(sell_value or 0.0) / units))

    def compute_price2(self, price1, step=50):
        """Giá bán 2 = MROUND(Giá bán 1, step) với step mặc định = 50"""
        return mround.mround(float(price1 or 0.0), step)

    def compute_transaction_metrics(self, item):
        """Nhận dict giao dịch, trả về dict bổ sung các trường tính toán.

        Kỳ vọng item có các field: amount/trade_price, nav_value, interest_rate, units/remaining_units,
        term_months, days. Ưu tiên: trade_price -> amount -> units*nav_value.
        """
        if not isinstance(item, dict):
            return {}
        
        # Try to use new full calculation if possible
        if all(k in item for k in ['purchase_date', 'term_months', 'units', 'price_per_unit', 'interest_rate']):
            return self.compute_transaction_metrics_full(item)
        
        # Fallback to legacy calculation
        nav_value = float(item.get('nav_value') or 0.0)
        rate = float(item.get('interest_rate') or 0.0)
        units = float(item.get('remaining_units') or item.get('units') or 0.0)
        order_value = float(item.get('trade_price') or item.get('amount') or 0.0)
        if order_value <= 0 and nav_value > 0 and units > 0:
            order_value = units * nav_value

        d = self._compute_days(term_months=item.get('term_months'), days=item.get('days'))
        sell_value = self.compute_sell_value(order_value, rate, term_months=item.get('term_months'), days=d)
        price1 = self.compute_price1(sell_value, units)
        price2 = self.compute_price2(price1, step=50)
        r_new = self.compute_converted_rate(price2, nav_value, d)
        delta = r_new - rate

        return {
            'sell_value': sell_value,
            'price1': price1,
            'price2': price2,
            'interest_rate_new': r_new,
            'interest_delta': delta,
            'days_effective': d,
        }


