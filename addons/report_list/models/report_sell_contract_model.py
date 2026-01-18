from odoo import models, fields, api

class ReportSellContract(models.Model):
    _inherit = 'portfolio.transaction'
    _description = 'Report Sell Contract - Extended from Portfolio Transaction'
    
    # Computed fields to map data from portfolio.transaction  
    contract_number = fields.Char(string="Số Hợp đồng", compute='_compute_contract_number', store=True)
    account_number_sc = fields.Char(string="Số TK", compute='_compute_account_number_sc', store=True)
    trading_account = fields.Char(string="Số TK GDCK", compute='_compute_trading_account', store=True)
    customer_name = fields.Char(string="Khách hàng", compute='_compute_customer_name', store=True)
    amount_value = fields.Float(string="Số tiền", compute='_compute_amount_value', store=True)
    contract_date = fields.Date(string="Ngày HĐ bán", compute='_compute_contract_date', store=True)
    sell_date = fields.Date(string="Ngày bán", compute='_compute_sell_date', store=True)
    payment_date = fields.Date(string="Ngày thanh toán", compute='_compute_payment_date', store=True)
    holding_days = fields.Integer(string="Số ngày duy trì", compute='_compute_holding_days', store=True)
    interest_amount = fields.Float(string="Tiền lãi", compute='_compute_interest_amount', store=True)
    principal_plus_interest = fields.Float(string="Gốc + lãi", compute='_compute_principal_plus_interest', store=True)

    @api.depends('name')
    def _compute_contract_number(self):
        """Compute contract number from name"""
        for record in self:
            record.contract_number = record.name or ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_account_number_sc(self):
        """Compute account number from user"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            if partner:
                status_info = self.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                record.account_number_sc = status_info.account_number if status_info else partner.name
            else:
                record.account_number_sc = ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_trading_account(self):
        """Compute trading account"""
        for record in self:
            record.trading_account = ''

    @api.depends('user_id')
    def _compute_customer_name(self):
        """Compute customer name"""
        for record in self:
            record.customer_name = record.user_id.name if record.user_id else ''

    @api.depends('amount')
    def _compute_amount_value(self):
        """Compute amount from amount"""
        for record in self:
            record.amount_value = record.amount or 0.0

    @api.depends('created_at')
    def _compute_contract_date(self):
        """Compute contract date from created_at"""
        for record in self:
            if record.created_at:
                record.contract_date = record.created_at.date()
            else:
                record.contract_date = False

    @api.depends('created_at')
    def _compute_sell_date(self):
        """Compute sell date from created_at"""
        for record in self:
            if record.created_at:
                record.sell_date = record.created_at.date()
            else:
                record.sell_date = False

    @api.depends('created_at')
    def _compute_payment_date(self):
        """Compute payment date"""
        for record in self:
            if record.created_at:
                record.payment_date = record.created_at.date()
            else:
                record.payment_date = False

    @api.depends('created_at', 'term_months')
    def _compute_holding_days(self):
        """Compute holding days - use nav_days if available, fallback to calculation"""
        for record in self:
            nav_days = getattr(record, 'nav_days', 0)
            if nav_days and nav_days > 0:
                record.holding_days = nav_days
            elif record.created_at:
                from datetime import date
                today = date.today()
                transaction_date = record.created_at.date()
                delta = today - transaction_date
                record.holding_days = delta.days
            else:
                record.holding_days = 0

    @api.depends('nav_customer_receive', 'amount')
    def _compute_interest_amount(self):
        """Compute actual interest - use NAV customer_receive if available"""
        for record in self:
            nav_customer_receive = getattr(record, 'nav_customer_receive', 0.0)
            if nav_customer_receive > 0 and record.amount:
                record.interest_amount = nav_customer_receive - record.amount
            elif record.holding_days and record.amount:
                annual_rate = record.interest_rate or 8.5
                interest = record.amount * (annual_rate / 100) * (record.holding_days / 365)
                record.interest_amount = interest
            else:
                record.interest_amount = 0.0

    @api.depends('amount', 'interest_amount')
    def _compute_principal_plus_interest(self):
        """Compute principal plus interest"""
        for record in self:
            record.principal_plus_interest = (record.amount or 0.0) + (record.interest_amount or 0.0)

    @api.model
    def get_report_data(self, domain=None, filters=None, search_values=None, limit=10, offset=0):
        """Get report data using real transaction data - only sell transactions"""
        try:
            if not domain:
                domain = []
            elif isinstance(domain, dict):
                filter_domain = []
                for field, value in domain.items():
                    if value:
                        if field == 'fund_id.name':
                            filter_domain.append(('fund_id.name', '=', value))
                        elif field == 'transaction_date':
                            filter_domain.append(('transaction_date', '>=', value))
                        elif field == 'transaction_date_to':
                            filter_domain.append(('transaction_date', '<=', value))
                domain = filter_domain
            elif not isinstance(domain, list):
                domain = []

            # Only sell transactions
            domain.append(('transaction_type', '=', 'sell'))

            if filters:
                for field, value in filters.items():
                    if value:
                        if field == 'customer':
                            domain.append(('user_id.name', 'ilike', value))
                        elif field == 'contract':
                            domain.append(('name', 'ilike', value))
                        elif field == 'date_from':
                            domain.append(('transaction_date', '>=', value))
                        elif field == 'date_to':
                            domain.append(('transaction_date', '<=', value))

            if search_values:
                for field, value in search_values.items():
                    if value:
                        field_mapping = {
                            'contract_number': 'name',
                            'account_number': 'user_id.partner_id.name',
                            'customer_name': 'user_id.name',
                        }
                        actual_field = field_mapping.get(field, field)
                        domain.append((actual_field, 'ilike', value))

            print(f"Report Sell Contract Domain: {domain}")
            print(f"Limit: {limit}, Offset: {offset}")
            
            total = self.search_count(domain)
            print(f"Total records found: {total}")
            
            records = self.search(domain, limit=limit, offset=offset, order='created_at desc')
            print(f"Records retrieved: {len(records)}")
            
            formatted_records = []
            for index, record in enumerate(records):
                formatted_records.append({
                    'stt': offset + index + 1,
                    'contract_number': record.contract_number,
                    'account_number': record.account_number_sc,
                    'trading_account': record.trading_account,
                    'customer_name': record.customer_name,
                    'amount': record.amount_value,
                    'contract_date': record.contract_date.strftime('%d/%m/%Y') if record.contract_date else '',
                    'sell_date': record.sell_date.strftime('%d/%m/%Y') if record.sell_date else '',
                    'payment_date': record.payment_date.strftime('%d/%m/%Y') if record.payment_date else '',
                    'holding_days': record.holding_days,
                    'interest_amount': record.interest_amount,
                    'principal_plus_interest': record.principal_plus_interest,
                })
            
            result = {
                'records': formatted_records,
                'total': total,
            }
            print(f"Returning result: {result}")
            return result
            
        except Exception as e:
            print(f"Error in get_report_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'records': [],
                'total': 0,
            }
