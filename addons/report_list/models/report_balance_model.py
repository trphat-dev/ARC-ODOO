from odoo import models, fields, api

class ReportBalance(models.Model):
    _inherit = 'portfolio.investment'
    _description = 'Report Balance - Extended from Portfolio Investment'
    
    # Computed fields to map data from portfolio.investment
    account_number = fields.Char(string="Số tài khoản", compute='_compute_account_number', store=True)
    investor_name = fields.Char(string="Nhà đầu tư", compute='_compute_investor_name', store=True)
    phone_number = fields.Char(string="Số điện thoại", compute='_compute_phone_number', store=True)
    id_number = fields.Char(string="ĐKSH", compute='_compute_id_number', store=True)
    email = fields.Char(string="Email", compute='_compute_email', store=True)
    investor_type = fields.Selection([
        ('direct', 'Trực tiếp'),
        ('nominee', 'Ký danh'),
    ], string="Loại nhà đầu tư", default='direct')
    fund_name = fields.Char(string="Quỹ", compute='_compute_fund_name', store=True)
    program_name = fields.Char(string="Chương trình", compute='_compute_program_name', store=True)
    program_ticker = fields.Char(string="Chương trình Ticker", compute='_compute_program_ticker', store=True)
    print_date = fields.Date(string="Ngày in", default=fields.Date.today)
    ccq_quantity = fields.Float(string="Số CCQ", compute='_compute_ccq_quantity', store=True)
    
    @api.depends('user_id', 'user_id.partner_id')
    def _compute_account_number(self):
        """Compute account number from user"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            if partner:
                status_info = self.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                record.account_number = status_info.account_number if status_info else partner.name
            else:
                record.account_number = ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_investor_name(self):
        """Compute investor name"""
        for record in self:
            record.investor_name = record.user_id.name if record.user_id else ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_phone_number(self):
        """Compute phone number"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            record.phone_number = partner.phone if partner else ''

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_id_number(self):
        """Compute ID number from investor_profile_management"""
        for record in self:
            if record.user_id and record.user_id.partner_id:
                # Find investor profile
                investor_profile = self.env['investor.profile'].sudo().search([
                    ('partner_id', '=', record.user_id.partner_id.id)
                ], limit=1)
                if investor_profile and investor_profile.id_number:
                    record.id_number = str(investor_profile.id_number)
                else:
                    record.id_number = "-"
            else:
                record.id_number = "-"

    @api.depends('user_id', 'user_id.partner_id')
    def _compute_email(self):
        """Compute email"""
        for record in self:
            partner = record.user_id.partner_id if record.user_id else False
            record.email = partner.email if partner else ''

    @api.depends('fund_id')
    def _compute_fund_name(self):
        """Compute fund name"""
        for record in self:
            record.fund_name = record.fund_id.name if record.fund_id else ''

    @api.depends('fund_id')
    def _compute_program_name(self):
        """Compute program name from fund"""
        for record in self:
            record.program_name = record.fund_id.name if record.fund_id else ''

    @api.depends('fund_id')
    def _compute_program_ticker(self):
        """Compute program ticker"""
        for record in self:
            record.program_ticker = record.fund_id.ticker if record.fund_id and record.fund_id.ticker else ''

    @api.model
    def get_balance_report_rows(self, domain):
        """Aggregate transactions to build balance rows."""
        Transaction = self.env['portfolio.transaction']

        grouped = Transaction.read_group(
            domain,
            ['units:sum', 'create_date:max'],
            ['user_id', 'fund_id', 'transaction_type'],
            lazy=False
        )

        aggregates = {}
        for row in grouped:
            user = row.get('user_id')
            fund = row.get('fund_id')
            if not user or not fund:
                continue

            key = (user[0], fund[0])
            entry = aggregates.setdefault(key, {
                'user_id': user[0],
                'user_name': user[1],
                'fund_id': fund[0],
                'fund_name': fund[1],
                'buy_units': 0.0,
                'sell_units': 0.0,
                'last_date': None,
            })

            units = row.get('units_sum') or 0.0
            t_type = row.get('transaction_type')
            if t_type == 'buy':
                entry['buy_units'] += units
            elif t_type == 'sell':
                entry['sell_units'] += units

            last_date = row.get('create_date_max')
            if last_date:
                # read_group returns string or datetime depending on Odoo version/config
                # Safe convert to datetime
                last_dt = fields.Datetime.to_datetime(last_date)
                if not entry['last_date'] or (last_dt and last_dt > entry['last_date']):
                    entry['last_date'] = last_dt

        if not aggregates:
            return []

        user_ids = [u_id for (u_id, _) in aggregates.keys()]
        fund_ids = [f_id for (_, f_id) in aggregates.keys()]

        Users = self.env['res.users'].browse(list(set(user_ids)))
        user_map = {user.id: user for user in Users}

        partner_ids = [user.partner_id.id for user in Users if user.partner_id]
        status_infos = self.env['status.info'].search([('partner_id', 'in', partner_ids)])
        status_map = {info.partner_id.id: info for info in status_infos}

        profiles = self.env['investor.profile'].search([('partner_id', 'in', partner_ids)])
        profile_map = {prof.partner_id.id: prof for prof in profiles}

        funds = self.env['portfolio.fund'].browse(list(set(fund_ids)))
        fund_map = {fund.id: fund for fund in funds}

        balances = self.env['trading.account.balance'].search(
            [('user_id', 'in', list(set(user_ids)))],
            order='last_sync desc, write_date desc, id desc'
        )
        balance_map = {}
        for bal in balances:
            balance_map.setdefault(bal.user_id.id, bal)

        rows = []
        for (user_id, fund_id), info in aggregates.items():
            net_units = (info['buy_units'] - info['sell_units'])
            if net_units <= 0:
                continue

            user = user_map.get(user_id)
            partner = user.partner_id if user else False
            status_info = status_map.get(partner.id) if partner else False
            profile = profile_map.get(partner.id) if partner else False
            fund = fund_map.get(fund_id)

            account_number = ''
            if status_info and status_info.account_number:
                account_number = status_info.account_number
            elif partner and partner.ref:
                account_number = partner.ref
            elif partner:
                account_number = partner.name or ''

            trading_balance = balance_map.get(user_id)
            trading_account = trading_balance.account if trading_balance and trading_balance.account else ''

            # Determine investor type (CN/TC)
            investor_type = 'truc_tiep'
            if partner and partner.company_type == 'company':
                investor_type = 'ky_danh'

            nationality = ''
            tn_nn = ''
            if profile and profile.nationality:
                nationality = profile.nationality.name
                country_code = (profile.nationality.code or '').upper()
                if country_code in ('VN', 'VNM', 'VIETNAM', 'Viet Nam', 'VIỆT NAM') or 'việt nam' in nationality.lower():
                    tn_nn = 'TN'
                else:
                    tn_nn = 'NN'
            else:
                tn_nn = 'TN'

            nvcs = status_info.rm_id.name if status_info and status_info.rm_id else ''
            fund_name = fund.name if fund else ''
            fund_ticker = fund.ticker if fund and fund.ticker else fund_name
            currency_name = fund.currency_id.name if fund and fund.currency_id else 'VND'
            amount_value = net_units * (fund.current_nav or 0.0) if fund else 0.0

            rows.append({
                'id': f"{user_id}-{fund_id}",
                'account_number': account_number,
                'trading_account': trading_account or account_number,
                'investor_name': partner.name if partner else info['user_name'],
                'phone_number': partner.phone if partner else '',
                'id_number': profile.id_number if profile and profile.id_number else '',
                'email': partner.email if partner else '',
                'investor_type': investor_type,
                'nationality': tn_nn,
                'sales_staff': nvcs,
                'fund_name': fund_name,
                'program_name': fund_name,
                'program_ticker': fund_ticker,
                'print_date': info['last_date'].strftime('%d/%m/%Y') if info['last_date'] else '',
                'ccq_quantity': net_units,
                'currency': currency_name,
                'amount': amount_value,
                'status': 'active',
                'last_update': info['last_date'] or fields.Datetime.now(),
            })

        return rows
    
