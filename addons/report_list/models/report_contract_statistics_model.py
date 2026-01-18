from odoo import models, fields, api


class ReportContractStatistics(models.Model):
    _name = 'report.contract.statistics'
    _description = 'Report Contract Statistics - Thống kê HĐ theo kỳ hạn'
    
    # Fields for contract statistics report
    sequence_number = fields.Integer(string="STT")
    contract_number = fields.Char(string="Số Hợp đồng", required=True)
    account_number = fields.Char(string="Số TK", required=True)
    trading_account = fields.Char(string="Số TK GDCK")
    customer_name = fields.Char(string="Khách hàng", required=True)
    term_months = fields.Integer(string="Kỳ hạn (tháng)", required=True)
    amount = fields.Float(string="Số tiền", digits=(16, 0), required=True)
    contract_date = fields.Date(string="Ngày Hợp đồng", required=True)
    maturity_date = fields.Date(string="Ngày đến hạn", required=True)
    sales_staff = fields.Char(string="NVCS")
    branch = fields.Char(string="Đơn vị")
    
    @api.model
    def get_contract_statistics_data(self, domain=None, search_values=None, limit=10, offset=0):
        """Get contract statistics data with pagination"""
        try:
            if not domain:
                domain = []
            elif isinstance(domain, dict):
                filter_domain = []
                for field, value in domain.items():
                    if value:
                        if field == 'term_months':
                            filter_domain.append(('term_months', '=', value))
                        elif field == 'contract_date_from':
                            filter_domain.append(('contract_date', '>=', value))
                        elif field == 'contract_date_to':
                            filter_domain.append(('contract_date', '<=', value))
                        elif field == 'branch':
                            filter_domain.append(('branch', '=', value))
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
                        elif field == 'sales_staff':
                            domain.append(('sales_staff', 'ilike', value))

            total = self.search_count(domain)
            records = self.search(domain, limit=limit, offset=offset, order='contract_date desc')
            
            data = []
            for i, record in enumerate(records, 1):
                data.append({
                    'id': record.id,
                    'stt': i,
                    'contract_number': record.contract_number,
                    'account_number': record.account_number,
                    'trading_account': record.trading_account or '',
                    'customer_name': record.customer_name,
                    'term_months': record.term_months,
                    'amount': record.amount,
                    'contract_date': record.contract_date.strftime('%d/%m/%Y') if record.contract_date else '',
                    'maturity_date': record.maturity_date.strftime('%d/%m/%Y') if record.maturity_date else '',
                    'sales_staff': record.sales_staff or '',
                    'branch': record.branch or '',
                })
            
            return {
                'records': data,
                'total': total,
            }
            
        except Exception as e:
            print(f"Error in get_contract_statistics_data: {str(e)}")
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
