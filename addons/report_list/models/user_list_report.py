# -*- coding: utf-8 -*-
from odoo import api, fields, models

class UserListReport(models.Model):
    """
    Model này là một model độc lập, có bảng CSDL riêng (user_list_report)
    để lưu trữ dữ liệu cho báo cáo danh sách người dùng.
    Nó KHÔNG kế thừa từ bất kỳ model nào khác của Odoo.
    """
    _name = 'user.list.report'
    _description = 'Báo cáo Danh sách Người dùng'
    _order = 'full_name'

    user_login = fields.Char('User', required=True, index=True)
    full_name = fields.Char('Họ và tên', required=True, index=True)
    employee_code = fields.Char('Mã nhân viên', index=True)
    department = fields.Char('Phòng ban/Bộ phận', index=True)

    @api.model
    def get_report_data(self, filters, page=1, limit=10, for_export=False):
        """
        Phương thức chính để truy vấn dữ liệu bằng Odoo ORM, thay thế cho SQL thuần.
        """
        # SỬA LỖI: Đảm bảo search_term luôn là một chuỗi trước khi gọi .strip()
        # Nếu filters.get('search_term') trả về None, nó sẽ được chuyển thành chuỗi rỗng ''.
        search_term = (filters.get('search_term') or '').strip()
        domain = []

        if search_term:
            # Tìm kiếm OR trên các trường được index
            domain = [
                '|', ('user_login', 'ilike', search_term),
                '|', ('full_name', 'ilike', search_term),
                '|', ('employee_code', 'ilike', search_term),
                     ('department', 'ilike', search_term)
            ]

        # Lấy tổng số bản ghi phù hợp với bộ lọc
        total_records = self.search_count(domain)

        # Lấy dữ liệu cho trang hiện tại hoặc cho việc xuất file
        records_orm = []
        if for_export:
            # Lấy tất cả bản ghi khi xuất file
            records_orm = self.search(domain, order='full_name')
        else:
            # Phân trang khi hiển thị trên web
            offset = (page - 1) * limit
            records_orm = self.search(domain, limit=limit, offset=offset, order='full_name')

        # Chuyển đổi dữ liệu sang định dạng dict và thêm STT
        records_list = []
        stt_start = 1 if for_export else ((page - 1) * limit) + 1
        for i, rec in enumerate(records_orm):
            records_list.append({
                'id': rec.id,
                'stt': stt_start + i,
                'user': rec.user_login, # Đổi tên key 'user_login' -> 'user' để khớp với frontend
                'full_name': rec.full_name,
                'employee_code': rec.employee_code,
                'department': rec.department,
            })

        if for_export:
             return records_list

        return {'records': records_list, 'total': total_records}
