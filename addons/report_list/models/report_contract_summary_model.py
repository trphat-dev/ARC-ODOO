from odoo import models, fields, api

class ReportContractSummary(models.Model):
    _inherit = 'portfolio.transaction'
    _description = 'Report Contract Summary - Extended from Portfolio Transaction'
    
    # Computed fields to map data from portfolio.transaction
    contract_number_cs = fields.Char(string="Số Hợp đồng", compute='_compute_contract_number_cs', store=True)
    account_number_cs = fields.Char(string="Số TK", compute='_compute_account_number_cs', store=True)
    trading_account_cs = fields.Char(string="Số TK GDCK", compute='_compute_trading_account_cs', store=True)
    customer_name_cs = fields.Char(string="Khách hàng", compute='_compute_customer_name_cs', store=True)
    purchase_date_cs = fields.Date(string="Ngày mua", compute='_compute_purchase_date_cs', store=True)
    payment_date_cs = fields.Date(string="Ngày thanh toán", compute='_compute_payment_date_cs', store=True)
    quantity = fields.Float(string="Số lượng", compute='_compute_quantity', store=True)
    purchase_price = fields.Float(string="Giá mua", compute='_compute_purchase_price', store=True)
    total_value = fields.Float(string="Thành tiền", compute='_compute_total_value', store=True)
    term_period_cs = fields.Char(string="Kỳ hạn", compute='_compute_term_period_cs', store=True)
    interest_rate_cs = fields.Float(string="Lãi Suất", compute='_compute_interest_rate_cs', store=True)
    days_count = fields.Integer(string="Số Ngày", compute='_compute_days_count', store=True)
    expected_interest_cs = fields.Float(string="Tiền lãi dự kiến khi đến hạn", compute='_compute_expected_interest_cs', store=True)
    expected_sell_price = fields.Float(string="Giá bán lại dự kiến theo HĐ", compute='_compute_expected_sell_price', store=True)
    expected_principal_interest_cs = fields.Float(string="Gốc + lãi dự kiến khi đến hạn", compute='_compute_expected_principal_interest_cs', store=True)
    expected_sell_date = fields.Date(string="Ngày bán lại dự kiến theo HĐ", compute='_compute_expected_sell_date', store=True)
    maturity_date_cs = fields.Date(string="Ngày đến hạn", compute='_compute_maturity_date_cs', store=True)
    actual_sell_date = fields.Date(string="Ngày bán lại", compute='_compute_actual_sell_date', store=True)
    sell_payment_date = fields.Date(string="Ngày thanh toán bán lại", compute='_compute_sell_payment_date', store=True)
    sell_interest_rate = fields.Float(string="LS bán lại", compute='_compute_sell_interest_rate', store=True)
    actual_interest = fields.Float(string="Tiền lãi", compute='_compute_actual_interest', store=True)
    actual_principal_interest = fields.Float(string="Gốc + lãi", compute='_compute_actual_principal_interest', store=True)

    @api.depends('name')
    def _compute_contract_number_cs(self):
        """Compute contract number from name"""
        for record in self:
            record.contract_number_cs = record.name or ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_account_number_cs(self):
        """Compute account number from user"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            if partner:
                status_info = self.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                record.account_number_cs = status_info.account_number if status_info else partner.name
            else:
                record.account_number_cs = ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_trading_account_cs(self):
        """Compute trading account"""
        for record in self:
            record.trading_account_cs = ''

    @api.depends('user_id')
    def _compute_customer_name_cs(self):
        """Compute customer name"""
        for record in self:
            record.customer_name_cs = record.user_id.name if record.user_id else ''

    @api.depends('created_at')
    def _compute_purchase_date_cs(self):
        """Compute purchase date from created_at"""
        for record in self:
            if record.created_at:
                record.purchase_date_cs = record.created_at.date()
            else:
                record.purchase_date_cs = False

    @api.depends('created_at')
    def _compute_payment_date_cs(self):
        """Compute payment date"""
        for record in self:
            if record.created_at:
                record.payment_date_cs = record.created_at.date()
            else:
                record.payment_date_cs = False

    @api.depends('units')
    def _compute_quantity(self):
        """Compute quantity from units"""
        for record in self:
            record.quantity = record.units or 0.0

    @api.depends('calculated_amount', 'units')
    def _compute_purchase_price(self):
        """Compute purchase price from calculated_amount and units"""
        for record in self:
            if record.units and record.units > 0:
                record.purchase_price = record.calculated_amount / record.units
            else:
                record.purchase_price = 0.0

    @api.depends('amount')
    def _compute_total_value(self):
        """Compute total value from amount"""
        for record in self:
            record.total_value = record.amount or 0.0

    @api.depends('term_months')
    def _compute_term_period_cs(self):
        """Compute term period from term_months"""
        for record in self:
            record.term_period_cs = str(record.term_months) if record.term_months else '12'

    @api.depends('interest_rate')
    def _compute_interest_rate_cs(self):
        """Compute interest rate from interest_rate"""
        for record in self:
            record.interest_rate_cs = record.interest_rate if record.interest_rate else 8.5

    @api.depends('created_at', 'term_months')
    def _compute_days_count(self):
        """Compute days count - use nav_days if available"""
        for record in self:
            nav_days = getattr(record, 'nav_days', 0)
            if nav_days and nav_days > 0:
                record.days_count = nav_days
            elif record.created_at:
                from datetime import date
                today = date.today()
                transaction_date = record.created_at.date()
                delta = today - transaction_date
                record.days_count = delta.days
            else:
                record.days_count = 0

    @api.depends('nav_customer_receive', 'amount')
    def _compute_expected_interest_cs(self):
        """Compute expected interest at maturity - use NAV customer_receive if available"""
        for record in self:
            nav_customer_receive = getattr(record, 'nav_customer_receive', 0.0)
            if nav_customer_receive > 0 and record.amount:
                record.expected_interest_cs = nav_customer_receive - record.amount
            elif record.amount and record.interest_rate_cs and record.term_period_cs:
                try:
                    term_months = int(record.term_period_cs)
                    interest = record.amount * (record.interest_rate_cs / 100) * (term_months / 12)
                    record.expected_interest_cs = interest
                except:
                    record.expected_interest_cs = 0.0
            else:
                record.expected_interest_cs = 0.0

    @api.depends('nav_sell_price2', 'price')
    def _compute_expected_sell_price(self):
        """Compute expected sell price - use NAV sell_price2 if available"""
        for record in self:
            nav_sell_price2 = getattr(record, 'nav_sell_price2', 0.0)
            if nav_sell_price2 > 0:
                record.expected_sell_price = nav_sell_price2
            elif record.purchase_price and record.interest_rate_cs and record.term_period_cs:
                try:
                    term_months = int(record.term_period_cs)
                    sell_price = record.purchase_price * (1 + (record.interest_rate_cs / 100) * (term_months / 12))
                    record.expected_sell_price = sell_price
                except:
                    record.expected_sell_price = 0.0
            else:
                record.expected_sell_price = 0.0

    @api.depends('amount', 'expected_interest_cs')
    def _compute_expected_principal_interest_cs(self):
        """Compute expected principal plus interest at maturity"""
        for record in self:
            record.expected_principal_interest_cs = (record.amount or 0.0) + (record.expected_interest_cs or 0.0)

    @api.depends('created_at', 'term_months')
    def _compute_expected_sell_date(self):
        """Compute expected sell date - use nav_maturity_date if available"""
        for record in self:
            nav_maturity_date = getattr(record, 'nav_maturity_date', False)
            if nav_maturity_date:
                record.expected_sell_date = nav_maturity_date
            elif record.created_at and record.term_months:
                try:
                    from dateutil.relativedelta import relativedelta
                    transaction_date = record.created_at.date()
                    maturity_date = transaction_date + relativedelta(months=record.term_months)
                    record.expected_sell_date = maturity_date
                except:
                    if record.created_at:
                        record.expected_sell_date = record.created_at.date()
                    else:
                        record.expected_sell_date = False
            else:
                record.expected_sell_date = False

    @api.depends('expected_sell_date')
    def _compute_maturity_date_cs(self):
        """Compute maturity date"""
        for record in self:
            record.maturity_date_cs = record.expected_sell_date

    @api.depends('transaction_type', 'created_at')
    def _compute_actual_sell_date(self):
        """Compute actual sell date"""
        for record in self:
            if record.transaction_type == 'sell':
                if record.created_at:
                    record.actual_sell_date = record.created_at.date()
                else:
                    record.actual_sell_date = False
            else:
                record.actual_sell_date = False

    @api.depends('actual_sell_date')
    def _compute_sell_payment_date(self):
        """Compute sell payment date"""
        for record in self:
            if record.actual_sell_date:
                record.sell_payment_date = record.actual_sell_date
            else:
                record.sell_payment_date = False

    @api.depends('transaction_type')
    def _compute_sell_interest_rate(self):
        """Compute sell interest rate"""
        for record in self:
            if record.transaction_type == 'sell':
                record.sell_interest_rate = record.interest_rate_cs
            else:
                record.sell_interest_rate = 0.0

    @api.depends('transaction_type', 'expected_interest_cs')
    def _compute_actual_interest(self):
        """Compute actual interest"""
        for record in self:
            if record.transaction_type == 'sell':
                record.actual_interest = record.expected_interest_cs
            else:
                record.actual_interest = 0.0

    @api.depends('transaction_type', 'expected_principal_interest_cs')
    def _compute_actual_principal_interest(self):
        """Compute actual principal plus interest"""
        for record in self:
            if record.transaction_type == 'sell':
                record.actual_principal_interest = record.expected_principal_interest_cs
            else:
                record.actual_principal_interest = 0.0

    @api.model
    def get_report_data(self, domain=None, filters=None, search_values=None, limit=10, offset=0):
        """Get report data using real transaction data"""
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

            print(f"Report Contract Summary Domain: {domain}")
            print(f"Limit: {limit}, Offset: {offset}")
            
            total = self.search_count(domain)
            print(f"Total records found: {total}")
            
            records = self.search(domain, limit=limit, offset=offset, order='created_at desc')
            print(f"Records retrieved: {len(records)}")
            
            formatted_records = []
            for index, record in enumerate(records):
                formatted_records.append({
                    'stt': offset + index + 1,
                    'contract_number': record.contract_number_cs,
                    'account_number': record.account_number_cs,
                    'trading_account': record.trading_account_cs,
                    'customer_name': record.customer_name_cs,
                    'purchase_date': record.purchase_date_cs.strftime('%d/%m/%Y') if record.purchase_date_cs else '',
                    'payment_date': record.payment_date_cs.strftime('%d/%m/%Y') if record.payment_date_cs else '',
                    'quantity': record.quantity,
                    'purchase_price': record.purchase_price,
                    'total_value': record.total_value,
                    'term_period': record.term_period_cs,
                    'interest_rate': record.interest_rate_cs,
                    'days_count': record.days_count,
                    'expected_interest': record.expected_interest_cs,
                    'expected_sell_price': record.expected_sell_price,
                    'expected_principal_interest': record.expected_principal_interest_cs,
                    'expected_sell_date': record.expected_sell_date.strftime('%d/%m/%Y') if record.expected_sell_date else '',
                    'maturity_date': record.maturity_date_cs.strftime('%d/%m/%Y') if record.maturity_date_cs else '',
                    'actual_sell_date': record.actual_sell_date.strftime('%d/%m/%Y') if record.actual_sell_date else '',
                    'sell_payment_date': record.sell_payment_date.strftime('%d/%m/%Y') if record.sell_payment_date else '',
                    'sell_interest_rate': record.sell_interest_rate,
                    'actual_interest': record.actual_interest,
                    'actual_principal_interest': record.actual_principal_interest,
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
