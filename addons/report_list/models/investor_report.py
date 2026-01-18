# -*- coding: utf-8 -*-
from odoo import models, fields, api

class InvestorReport(models.Model):
    _name = 'investor.report'
    _description = 'Báo cáo Danh sách Nhà đầu tư'
    _order = 'create_date desc, id desc'

    account_number = fields.Char(string='Số TK', required=True, index=True)
    trading_account = fields.Char(string='TK GDCK')
    customer_name = fields.Char(string='Khách hàng', required=True, index=True)
    id_number = fields.Char(string='Số CCCD/CC/GPKD')
    id_issue_date = fields.Date(string='Ngày cấp')
    id_issue_place = fields.Char(string='Nơi cấp')
    permanent_address = fields.Char(string='Địa chỉ thường trú')
    contact_address = fields.Char(string='Địa chỉ liên hệ')
    phone_number = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Email')

    status = fields.Selection([
        ('active', 'Đang hoạt động'),
        ('inactive', 'Ngừng hoạt động'),
        ('pending', 'Chờ duyệt'),
    ], string='Trạng thái', default='pending', required=True)

    customer_type = fields.Selection([
        ('personal', 'Cá nhân'),
        ('organization', 'Tổ chức'),
    ], string='Loại KH (CN/TC)')

    nationality_type = fields.Selection([
        ('domestic', 'Trong nước'),
        ('foreign', 'Nước ngoài'),
    ], string='Quốc tịch (TN/NN)')

    account_manager_id = fields.Many2one('res.users', string='Nhân viên chăm sóc (NVCS)')
    unit = fields.Char(string='Đơn vị')
    
    @api.model
    def _build_domain(self, filters):
        """Helper method to build a search domain from filter dictionary."""
        domain = []
        if filters.get('date_from'):
            domain.append(('create_date', '>=', filters['date_from']))
        if filters.get('date_to'):
            domain.append(('create_date', '<=', filters['date_to']))
        if filters.get('status') and filters['status'] != 'all':
            domain.append(('status', '=', filters['status']))
        if filters.get('customer_type') and filters['customer_type'] != 'all':
            domain.append(('customer_type', '=', filters['customer_type']))
        if filters.get('nationality_type') and filters['nationality_type'] != 'all':
            domain.append(('nationality_type', '=', filters['nationality_type']))
        
        # Search term logic
        if filters.get('search_term'):
            search_term = filters['search_term']
            domain.append('|', ('account_number', 'ilike', search_term),
                          '|', ('customer_name', 'ilike', search_term),
                               ('id_number', 'ilike', search_term))
        return domain

    @api.model
    def get_investor_data(self, filters, page=1, limit=10):
        """Fetch paginated report data."""
        domain = self._build_domain(filters)
        total_records = self.search_count(domain)
        offset = (page - 1) * limit
        
        records = self.search(domain, limit=limit, offset=offset)

        records_data = []
        stt_start = offset + 1
        for idx, rec in enumerate(records):
            records_data.append({
                'id': rec.id,
                'stt': stt_start + idx,
                'account_number': rec.account_number,
                'trading_account': rec.trading_account,
                'customer_name': rec.customer_name,
                'id_number': rec.id_number,
                'id_issue_date': rec.id_issue_date.strftime('%d/%m/%Y') if rec.id_issue_date else '',
                'id_issue_place': rec.id_issue_place,
                'permanent_address': rec.permanent_address,
                'contact_address': rec.contact_address,
                'phone_number': rec.phone_number,
                'email': rec.email,
                'status': dict(rec._fields['status'].selection).get(rec.status),
                'customer_type': dict(rec._fields['customer_type'].selection).get(rec.customer_type),
                'nationality_type': dict(rec._fields['nationality_type'].selection).get(rec.nationality_type),
                'account_manager': rec.account_manager_id.name or '',
                'unit': rec.unit or '',
            })

        return {
            'records': records_data,
            'total': total_records
        }

    @api.model
    def get_investor_export_data(self, filters):
        """Fetch all data for export, ignoring pagination."""
        domain = self._build_domain(filters)
        records = self.search(domain)
        
        export_data = []
        for idx, rec in enumerate(records):
             export_data.append({
                'stt': idx + 1,
                'account_number': rec.account_number,
                'trading_account': rec.trading_account,
                'customer_name': rec.customer_name,
                'id_number': rec.id_number,
                'id_issue_date': rec.id_issue_date.strftime('%d/%m/%Y') if rec.id_issue_date else '',
                'id_issue_place': rec.id_issue_place,
                'permanent_address': rec.permanent_address,
                'contact_address': rec.contact_address,
                'phone_number': rec.phone_number,
                'email': rec.email,
                'status': dict(rec._fields['status'].selection).get(rec.status),
                'customer_type': dict(rec._fields['customer_type'].selection).get(rec.customer_type),
                'nationality_type': dict(rec._fields['nationality_type'].selection).get(rec.nationality_type),
                'account_manager': rec.account_manager_id.name or '',
                'unit': rec.unit or '',
            })
        return export_data
