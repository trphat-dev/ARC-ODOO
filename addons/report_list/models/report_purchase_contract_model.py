from odoo import models, fields, api

class ReportPurchaseContract(models.Model):
    _inherit = 'portfolio.transaction'
    _description = 'Report Purchase Contract - Extended from Portfolio Transaction'
    
    # Computed fields to map data from portfolio.transaction
    contract_number_pc = fields.Char(string="Số Hợp đồng", compute='_compute_contract_number_pc', store=True)
    account_number_pc = fields.Char(string="Số TK", compute='_compute_account_number_pc', store=True)
    trading_account_pc = fields.Char(string="Số TK GDCK", compute='_compute_trading_account_pc', store=True)
    customer_name_pc = fields.Char(string="Khách hàng", compute='_compute_customer_name_pc', store=True)
    amount_value_pc = fields.Float(string="Số tiền", compute='_compute_amount_value_pc', store=True)
    purchase_contract_date = fields.Date(string="Ngày HĐ mua", compute='_compute_purchase_contract_date', store=True)
    purchase_date = fields.Date(string="Ngày mua", compute='_compute_purchase_date', store=True)
    payment_date_pc = fields.Date(string="Ngày thanh toán", compute='_compute_payment_date_pc', store=True)
    term_period = fields.Char(string="Kỳ hạn", compute='_compute_term_period', store=True)
    interest_rate_value = fields.Float(string="Lãi suất", compute='_compute_interest_rate_value', store=True)
    participation_days = fields.Integer(string="Số ngày tham gia", compute='_compute_participation_days', store=True)
    expected_interest = fields.Float(string="Tiền lãi dự kiến khi đến hạn", compute='_compute_expected_interest', store=True)
    expected_principal_interest = fields.Float(string="Gốc + lãi dự kiến khi đến hạn", compute='_compute_expected_principal_interest', store=True)

    @api.depends('name')
    def _compute_contract_number_pc(self):
        """Compute contract number from name"""
        for record in self:
            record.contract_number_pc = record.name or ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_account_number_pc(self):
        """Compute account number from user"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            if partner:
                status_info = self.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                record.account_number_pc = status_info.account_number if status_info else partner.name
            else:
                record.account_number_pc = ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_trading_account_pc(self):
        """Compute trading account"""
        for record in self:
            record.trading_account_pc = ''

    @api.depends('user_id')
    def _compute_customer_name_pc(self):
        """Compute customer name"""
        for record in self:
            record.customer_name_pc = record.user_id.name if record.user_id else ''

    @api.depends('amount')
    def _compute_amount_value_pc(self):
        """Compute amount from amount"""
        for record in self:
            record.amount_value_pc = record.amount or 0.0

    @api.depends('created_at')
    def _compute_purchase_contract_date(self):
        """Compute purchase contract date from created_at"""
        for record in self:
            if record.created_at:
                record.purchase_contract_date = record.created_at.date()
            else:
                record.purchase_contract_date = False

    @api.depends('created_at')
    def _compute_purchase_date(self):
        """Compute purchase date from created_at"""
        for record in self:
            if record.created_at:
                record.purchase_date = record.created_at.date()
            else:
                record.purchase_date = False

    @api.depends('created_at')
    def _compute_payment_date_pc(self):
        """Compute payment date"""
        for record in self:
            if record.created_at:
                record.payment_date_pc = record.created_at.date()
            else:
                record.payment_date_pc = False

    @api.depends('term_months')
    def _compute_term_period(self):
        """Compute term period from term_months"""
        for record in self:
            record.term_period = str(record.term_months) if record.term_months else '12'

    @api.depends('interest_rate')
    def _compute_interest_rate_value(self):
        """Compute interest rate from interest_rate"""
        for record in self:
            record.interest_rate_value = record.interest_rate if record.interest_rate else 8.5

    @api.depends('created_at', 'term_months')
    def _compute_participation_days(self):
        """Compute participation days - use nav_days if available"""
        for record in self:
            nav_days = getattr(record, 'nav_days', 0)
            if nav_days and nav_days > 0:
                record.participation_days = nav_days
            elif record.created_at:
                from datetime import date
                today = date.today()
                transaction_date = record.created_at.date()
                delta = today - transaction_date
                record.participation_days = delta.days
            else:
                record.participation_days = 0

    @api.depends('nav_customer_receive', 'amount')
    def _compute_expected_interest(self):
        """Compute expected interest at maturity - use NAV customer_receive if available"""
        for record in self:
            nav_customer_receive = getattr(record, 'nav_customer_receive', 0.0)
            if nav_customer_receive > 0 and record.amount:
                record.expected_interest = nav_customer_receive - record.amount
            elif record.amount and record.interest_rate_value and record.term_period:
                try:
                    term_months = int(record.term_period)
                    interest = record.amount * (record.interest_rate_value / 100) * (term_months / 12)
                    record.expected_interest = interest
                except:
                    record.expected_interest = 0.0
            else:
                record.expected_interest = 0.0

    @api.depends('amount', 'expected_interest')
    def _compute_expected_principal_interest(self):
        """Compute expected principal plus interest at maturity"""
        for record in self:
            record.expected_principal_interest = (record.amount or 0.0) + (record.expected_interest or 0.0)

    @api.model
    def get_report_data(self, domain=None, filters=None, search_values=None, limit=10, offset=0):
        """Get report data using real transaction data - only buy transactions"""
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

            # Only buy transactions
            domain.append(('transaction_type', '=', 'buy'))

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

            print(f"Report Purchase Contract Domain: {domain}")
            print(f"Limit: {limit}, Offset: {offset}")
            
            total = self.search_count(domain)
            print(f"Total records found: {total}")
            
            records = self.search(domain, limit=limit, offset=offset, order='created_at desc')
            print(f"Records retrieved: {len(records)}")
            
            formatted_records = []
            for index, record in enumerate(records):
                formatted_records.append({
                    'stt': offset + index + 1,
                    'contract_number': record.contract_number_pc,
                    'account_number': record.account_number_pc,
                    'trading_account': record.trading_account_pc,
                    'customer_name': record.customer_name_pc,
                    'amount': record.amount_value_pc,
                    'purchase_contract_date': record.purchase_contract_date.strftime('%d/%m/%Y') if record.purchase_contract_date else '',
                    'purchase_date': record.purchase_date.strftime('%d/%m/%Y') if record.purchase_date else '',
                    'payment_date': record.payment_date_pc.strftime('%d/%m/%Y') if record.payment_date_pc else '',
                    'term_period': record.term_period,
                    'interest_rate': record.interest_rate_value,
                    'participation_days': record.participation_days,
                    'expected_interest': record.expected_interest,
                    'expected_principal_interest': record.expected_principal_interest,
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
