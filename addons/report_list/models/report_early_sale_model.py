from odoo import models, fields, api
from datetime import datetime, timedelta


class ReportEarlySale(models.Model):
    _name = 'report.early.sale'
    _description = 'Report Early Sale - Báo cáo bán trước hạn'
    
    # Fields for early sale report
    sequence_number = fields.Integer(string="STT")
    contract_number = fields.Char(string="Số Hợp đồng", required=True)
    account_number = fields.Char(string="Số TK", required=True)
    trading_account = fields.Char(string="Số TK GDCK")
    customer_name = fields.Char(string="Khách hàng", required=True)
    amount = fields.Float(string="Số tiền", digits=(16, 0), required=True)
    purchase_contract_date = fields.Date(string="Ngày HĐ mua", required=True)
    term_months = fields.Integer(string="Kỳ hạn (tháng)", required=True)
    interest_rate = fields.Float(string="Lãi suất (%)", digits=(5, 2), required=True)
    expected_sell_date = fields.Date(string="Ngày bán lại theo HĐ")
    maturity_date = fields.Date(string="Ngày đáo hạn", required=True)
    actual_sell_date = fields.Date(string="Ngày bán lại", required=True)
    payment_date = fields.Date(string="Ngày thanh toán")
    holding_days = fields.Integer(string="Số ngày duy trì", compute='_compute_holding_days', store=True)
    early_sale_days = fields.Integer(string="Số ngày bán trước hạn", compute='_compute_early_sale_days', store=True)
    early_interest_rate = fields.Float(string="Lãi suất trước hạn (%)", digits=(5, 2), compute='_compute_early_interest_rate', store=True)
    interest_amount = fields.Float(string="Tiền lãi", digits=(16, 0), compute='_compute_interest_amount', store=True)
    principal_plus_interest = fields.Float(string="Lãi + gốc", digits=(16, 0), compute='_compute_principal_plus_interest', store=True)
    
    @api.depends('purchase_contract_date', 'actual_sell_date')
    def _compute_holding_days(self):
        """Compute holding days"""
        for record in self:
            if record.purchase_contract_date and record.actual_sell_date:
                delta = record.actual_sell_date - record.purchase_contract_date
                record.holding_days = delta.days
            else:
                record.holding_days = 0
    
    @api.depends('actual_sell_date', 'maturity_date')
    def _compute_early_sale_days(self):
        """Compute early sale days"""
        for record in self:
            if record.actual_sell_date and record.maturity_date:
                delta = record.maturity_date - record.actual_sell_date
                record.early_sale_days = delta.days
            else:
                record.early_sale_days = 0
    
    @api.depends('interest_rate', 'early_sale_days', 'term_months')
    def _compute_early_interest_rate(self):
        """Compute early interest rate"""
        for record in self:
            if record.term_months > 0 and record.early_sale_days > 0:
                penalty_rate = (record.early_sale_days / (record.term_months * 30)) * 0.5
                record.early_interest_rate = max(0, record.interest_rate - penalty_rate)
            else:
                record.early_interest_rate = record.interest_rate
    
    @api.depends('amount', 'early_interest_rate', 'holding_days')
    def _compute_interest_amount(self):
        """Compute interest amount"""
        for record in self:
            if record.amount and record.early_interest_rate and record.holding_days:
                daily_rate = record.early_interest_rate / 365 / 100
                record.interest_amount = record.amount * daily_rate * record.holding_days
            else:
                record.interest_amount = 0
    
    @api.depends('amount', 'interest_amount')
    def _compute_principal_plus_interest(self):
        """Compute principal plus interest"""
        for record in self:
            record.principal_plus_interest = record.amount + record.interest_amount
    
    @api.model
    def get_early_sale_data(self, domain=None, search_values=None, limit=10, offset=0):
        """Get early sale data with pagination"""
        try:
            if not domain:
                domain = []
            elif isinstance(domain, dict):
                filter_domain = []
                for field, value in domain.items():
                    if value:
                        if field == 'term_months':
                            filter_domain.append(('term_months', '=', value))
                        elif field == 'purchase_date_from':
                            filter_domain.append(('purchase_contract_date', '>=', value))
                        elif field == 'purchase_date_to':
                            filter_domain.append(('purchase_contract_date', '<=', value))
                        elif field == 'sell_date_from':
                            filter_domain.append(('actual_sell_date', '>=', value))
                        elif field == 'sell_date_to':
                            filter_domain.append(('actual_sell_date', '<=', value))
                domain = filter_domain
            elif not isinstance(domain, list):
                domain = []

            if search_values:
                for field, value in search_values.items():
                    if value:
                        if field == 'contract_number':
                            domain.append(('contract_number', 'ilike', value))
                        elif field == 'account_number':
                            domain.append(('account_number', 'ilike', value))
                        elif field == 'customer_name':
                            domain.append(('customer_name', 'ilike', value))

            total = self.search_count(domain)
            records = self.search(domain, limit=limit, offset=offset, order='actual_sell_date desc')
            
            data = []
            for i, record in enumerate(records, 1):
                data.append({
                    'id': record.id,
                    'stt': i,
                    'contract_number': record.contract_number,
                    'account_number': record.account_number,
                    'trading_account': record.trading_account or '',
                    'customer_name': record.customer_name,
                    'amount': record.amount,
                    'purchase_contract_date': record.purchase_contract_date.strftime('%d/%m/%Y') if record.purchase_contract_date else '',
                    'term_months': record.term_months,
                    'interest_rate': record.interest_rate,
                    'expected_sell_date': record.expected_sell_date.strftime('%d/%m/%Y') if record.expected_sell_date else '',
                    'maturity_date': record.maturity_date.strftime('%d/%m/%Y') if record.maturity_date else '',
                    'actual_sell_date': record.actual_sell_date.strftime('%d/%m/%Y') if record.actual_sell_date else '',
                    'payment_date': record.payment_date.strftime('%d/%m/%Y') if record.payment_date else '',
                    'holding_days': record.holding_days,
                    'early_sale_days': record.early_sale_days,
                    'early_interest_rate': record.early_interest_rate,
                    'interest_amount': record.interest_amount,
                    'principal_plus_interest': record.principal_plus_interest,
                })
            
            return {
                'records': data,
                'total': total,
            }
            
        except Exception as e:
            print(f"Error in get_early_sale_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'records': [],
                'total': 0,
            }
    
    @api.model
    def get_terms(self):
        """Get distinct terms for filter dropdown"""
        try:
            terms = self.read_group([], ['term_months'], ['term_months'])
            products = []
            
            for term in terms:
                if term.get('term_months'):
                    term_value = term['term_months']
                    products.append({
                        'id': term_value, 
                        'name': f"{term_value} tháng"
                    })
            
            products.sort(key=lambda x: x['id'])
            return products
            
        except Exception as e:
            print(f"Error in get_terms: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
