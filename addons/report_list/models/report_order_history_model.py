from odoo import models, fields, api
from datetime import datetime

class ReportOrderHistory(models.Model):
    _name = 'report.order.history'
    _description = 'Report Order History - Sổ lệnh lịch sử giao dịch'
    _order = 'order_time desc'
    
    # Fields for order history report
    order_time = fields.Datetime(string="Giờ đặt", required=True)
    status = fields.Selection([
        ('pending', 'Chờ khớp'),
        ('matched', 'Đã khớp'),
        ('cancelled', 'Đã hủy'),
        ('partial', 'Khớp một phần'),
    ], string="Trạng thái", default='pending')
    account_number = fields.Char(string="Số TK", required=True)
    trading_account = fields.Char(string="Số TK GDCK")
    customer_name = fields.Char(string="Khách hàng", required=True)
    sales_staff = fields.Char(string="NVCS")
    order_type = fields.Selection([
        ('buy', 'Lệnh mua'),
        ('sell', 'Lệnh bán'),
    ], string="Loại lệnh", required=True)
    order_code = fields.Char(string="Lệnh", required=True)
    security_code = fields.Char(string="Mã CK", required=True)
    order_quantity = fields.Float(string="KL đặt", digits=(16, 0))
    order_price = fields.Float(string="Giá đặt", digits=(16, 2))
    matched_quantity = fields.Float(string="KL khớp", digits=(16, 0))
    matched_price = fields.Float(string="Giá khớp", digits=(16, 2))
    pending_quantity = fields.Float(string="KL chờ", digits=(16, 0))
    pending_price = fields.Float(string="Giá chờ", digits=(16, 2))
    order_reference = fields.Char(string="SHL")
    
    @api.model
    def get_order_history_data(self, domain=None, search_values=None, limit=10, offset=0):
        """Get order history data with pagination"""
        try:
            if not domain:
                domain = []
            elif isinstance(domain, dict):
                filter_domain = []
                for field, value in domain.items():
                    if value:
                        if field == 'security_code':
                            filter_domain.append(('security_code', '=', value))
                        elif field == 'order_time_from':
                            filter_domain.append(('order_time', '>=', value))
                        elif field == 'order_time_to':
                            filter_domain.append(('order_time', '<=', value))
                        elif field == 'status':
                            filter_domain.append(('status', '=', value))
                domain = filter_domain
            elif not isinstance(domain, list):
                domain = []

            if search_values:
                for field, value in search_values.items():
                    if value:
                        if field == 'account_number':
                            domain.append(('account_number', 'ilike', value))
                        elif field == 'customer_name':
                            domain.append(('customer_name', 'ilike', value))
                        elif field == 'security_code':
                            domain.append(('security_code', 'ilike', value))
                        elif field == 'order_code':
                            domain.append(('order_code', 'ilike', value))

            total = self.search_count(domain)
            records = self.search(domain, limit=limit, offset=offset, order='order_time desc')
            
            data = []
            for record in records:
                data.append({
                    'id': record.id,
                    'order_time': record.order_time.strftime('%d/%m/%Y %H:%M:%S') if record.order_time else '',
                    'status': record.status,
                    'account_number': record.account_number,
                    'trading_account': record.trading_account or '',
                    'customer_name': record.customer_name,
                    'sales_staff': record.sales_staff or '',
                    'order_type': record.order_type,
                    'order_code': record.order_code,
                    'security_code': record.security_code,
                    'order_quantity': record.order_quantity,
                    'order_price': record.order_price,
                    'matched_quantity': record.matched_quantity,
                    'matched_price': record.matched_price,
                    'pending_quantity': record.pending_quantity,
                    'pending_price': record.pending_price,
                    'order_reference': record.order_reference or '',
                })
            
            return {
                'records': data,
                'total': total,
            }
            
        except Exception as e:
            print(f"Error in get_order_history_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'records': [],
                'total': 0,
            }
    
    @api.model
    def get_securities(self):
        """Get distinct securities for filter dropdown"""
        try:
            securities = self.read_group([], ['security_code'], ['security_code'])
            products = []
            
            for security in securities:
                if security.get('security_code'):
                    security_value = security['security_code'][1] if isinstance(security['security_code'], tuple) else security['security_code']
                    products.append({
                        'id': security_value, 
                        'name': security_value
                    })
            
            products.sort(key=lambda x: x['name'])
            return products
            
        except Exception as e:
            print(f"Error in get_securities: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
