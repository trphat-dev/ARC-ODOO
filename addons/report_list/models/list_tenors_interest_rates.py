# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import expression

class ListTenorsInterestRate(models.Model):
    _name = 'list.tenors.interest.rate'
    _description = 'Danh sách Kỳ hạn và Lãi suất'
    _order = 'effective_date desc, id desc'

    product_name = fields.Char(string='Sản phẩm (SP)', required=True, index=True)
    product_creation_date = fields.Date(string='Ngày tạo SP', required=True, default=fields.Date.context_today)
    effective_date = fields.Date(string='Ngày hiệu lực', required=True, index=True)
    end_date = fields.Date(string='Ngày kết thúc')
    term = fields.Char(string='Kỳ hạn', required=True)
    interest_rate = fields.Float(string='Lãi suất (%)', digits=(12, 4), required=True)
    
    @api.model
    def _build_domain(self, filters):
        """Xây dựng domain tìm kiếm từ các bộ lọc."""
        domain = []
        if filters.get('effective_date_from'):
            domain = expression.AND([domain, [('effective_date', '>=', filters['effective_date_from'])]])
        if filters.get('effective_date_to'):
            domain = expression.AND([domain, [('effective_date', '<=', filters['effective_date_to'])]])

        if filters.get('term') and filters['term'] != 'all':
            domain = expression.AND([domain, [('term', '=', filters['term'])]])
        if filters.get('interest_rate') and filters['interest_rate'] != 'all':
            try:
                rate = float(filters['interest_rate'])
                domain = expression.AND([domain, [('interest_rate', '=', rate)]])
            except (ValueError, TypeError):
                pass
        
        if filters.get('search_term'):
            search_term = filters['search_term']
            # *** FIX: Search on the name of the related user (create_uid.name) ***
            search_domain = [
                '|',
                ('product_name', 'ilike', search_term),
                ('create_uid.name', 'ilike', search_term) # Sửa lỗi tìm kiếm theo tên người tạo
            ]
            domain = expression.AND([domain, search_domain])
            
        return domain

    @api.model
    def get_report_data(self, filters, page=1, limit=15):
        """Lấy dữ liệu báo cáo có phân trang."""
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
                'product_name': rec.product_name,
                'product_creation_date': rec.product_creation_date.strftime('%d/%m/%Y') if rec.product_creation_date else '',
                'effective_date': rec.effective_date.strftime('%d/%m/%Y') if rec.effective_date else '',
                'end_date': rec.end_date.strftime('%d/%m/%Y') if rec.end_date else '',
                'term': rec.term,
                'interest_rate': f"{rec.interest_rate:.2f}%",
                'creator_name': rec.create_uid.name or 'N/A',
            })

        return {
            'records': records_data,
            'total': total_records
        }

    @api.model
    def get_export_data(self, filters):
        """Lấy toàn bộ dữ liệu để xuất file, không phân trang."""
        domain = self._build_domain(filters)
        records = self.search(domain)
        
        export_data = []
        for idx, rec in enumerate(records):
            export_data.append({
                'stt': idx + 1,
                'product_name': rec.product_name,
                'product_creation_date': rec.product_creation_date.strftime('%d/%m/%Y') if rec.product_creation_date else '',
                'effective_date': rec.effective_date.strftime('%d/%m/%Y') if rec.effective_date else '',
                'end_date': rec.end_date.strftime('%d/%m/%Y') if rec.end_date else '',
                'term': rec.term,
                'interest_rate': f"{rec.interest_rate:.2f}%",
                'creator_name': rec.create_uid.name or 'N/A',
            })
        return export_data
        
    @api.model
    def get_filter_options(self):
        """Lấy các giá trị duy nhất cho bộ lọc dropdown."""
        terms = self.search_read([], ['term'], order='term')
        unique_terms = sorted(list(set(d['term'] for d in terms if d['term'])))

        rates = self.search_read([], ['interest_rate'], order='interest_rate')
        unique_rates = sorted(list(set(d['interest_rate'] for d in rates if d['interest_rate'])))

        return {
            'terms': unique_terms,
            'interest_rates': unique_rates,
        }
