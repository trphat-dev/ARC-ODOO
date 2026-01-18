# NAV Management Module

Module quản lý NAV (Net Asset Value) cho hệ thống quản lý quỹ đầu tư.

## Tính năng chính

### 1. NAV Phiên giao dịch
- Hiển thị danh sách giá trị NAV của tất cả các phiên giao dịch theo Quỹ được chọn
- Có thể xuất file danh sách NAV (CSV)
- Giao diện hiện đại với thống kê tổng quan
- Tìm kiếm và lọc dữ liệu theo nhiều tiêu chí

### 2. NAV Tháng
- Hiển thị danh sách NAV tháng theo Quỹ được chọn
- Có thể thêm giá trị NAV tháng mới
- Tính toán tự động thay đổi NAV và phần trăm thay đổi
- Xuất file danh sách NAV tháng (CSV)
- Xóa NAV tháng không cần thiết

## Cấu trúc Module

```
nav_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── nav_transaction.py      # Model NAV phiên giao dịch
│   └── nav_monthly.py          # Model NAV tháng
├── controllers/
│   ├── __init__.py
│   └── nav_management_controller.py  # API endpoints
├── views/
│   ├── menu_views.xml          # Menu chính
│   ├── nav_transaction_views.xml     # Views backend NAV phiên giao dịch
│   ├── nav_monthly_views.xml         # Views backend NAV tháng
│   ├── nav_transaction/
│   │   └── nav_transaction_page.xml  # Trang web NAV phiên giao dịch
│   └── nav_monthly/
│       └── nav_monthly_page.xml      # Trang web NAV tháng
├── security/
│   └── ir.model.access.csv     # Phân quyền truy cập
└── static/
    └── src/
        ├── js/
        │   ├── nav_transaction/
        │   │   ├── nav_transaction_widget.js  # Widget NAV phiên giao dịch
        │   │   └── entrypoint.js              # Entrypoint NAV phiên giao dịch
        │   └── nav_monthly/
        │       ├── nav_monthly_widget.js      # Widget NAV tháng
        │       └── entrypoint.js              # Entrypoint NAV tháng
        └── css/
            └── nav_management.css    # CSS chính cho module
```

## Models

### NavTransaction (nav.transaction)
- `fund_id`: Quỹ (Many2one)
- `transaction_session`: Phiên giao dịch (Char)
- `nav_value`: Giá trị NAV (Float)
- `create_date`: Ngày tạo (Datetime)
- `description`: Mô tả (Text)
- `status`: Trạng thái (Selection)

### NavMonthly (nav.monthly)
- `fund_id`: Quỹ (Many2one)
- `period`: Thời gian MM/YYYY (Char)
- `nav_beginning`: NAV đầu kỳ (Float)
- `nav_ending`: NAV cuối kỳ (Float)
- `nav_change`: Thay đổi NAV (Float, computed)
- `nav_change_percent`: % Thay đổi NAV (Float, computed)
- `upload_date`: Ngày upload (Datetime)
- `description`: Mô tả (Text)
- `status`: Trạng thái (Selection)

## API Endpoints

### NAV Phiên giao dịch
- `GET /nav_management/api/nav_transaction?fund_id={id}`: Lấy dữ liệu NAV phiên giao dịch
- `GET /nav_management/export_nav_transaction/{fund_id}`: Xuất file CSV

### NAV Tháng
- `GET /nav_management/api/nav_monthly?fund_id={id}`: Lấy dữ liệu NAV tháng
- `POST /nav_management/api/nav_monthly`: Tạo NAV tháng mới
- `PUT /nav_management/api/nav_monthly/{id}`: Cập nhật NAV tháng
- `DELETE /nav_management/api/nav_monthly/{id}`: Xóa NAV tháng
- `GET /nav_management/export_nav_monthly/{fund_id}`: Xuất file CSV

## Cài đặt và Sử dụng

1. **Cài đặt module**:
   - Copy module vào thư mục addons của Odoo
   - Cập nhật danh sách apps
   - Cài đặt module "NAV Management"

2. **Sử dụng**:
   - Truy cập menu "NAV Management" trong Odoo
   - Chọn "NAV phiên giao dịch" hoặc "NAV tháng"
   - Chọn quỹ từ dropdown để xem dữ liệu
   - Sử dụng các chức năng thêm, sửa, xóa, xuất file

3. **Giao diện Web**:
   - Truy cập `/nav_management/nav_transaction` cho NAV phiên giao dịch
   - Truy cập `/nav_management/nav_monthly` cho NAV tháng

## Tính năng nổi bật

- **Giao diện hiện đại**: Sử dụng OWL framework với thiết kế responsive
- **Tích hợp header**: Sử dụng header từ module `investor_list` thông qua `headermana-container`
- **Thống kê trực quan**: Hiển thị các chỉ số quan trọng dưới dạng cards
- **Tìm kiếm và lọc**: Hỗ trợ tìm kiếm theo nhiều tiêu chí
- **Xuất dữ liệu**: Xuất file CSV với encoding UTF-8
- **Validation**: Kiểm tra dữ liệu đầu vào chặt chẽ
- **Responsive**: Tương thích với mọi thiết bị
- **Loading states**: Hiển thị spinner và error handling

## Dependencies

- `base`: Module cơ bản của Odoo
- `web`: Giao diện web
- `mail`: Hệ thống thông báo
- `overview_fund_management`: Module quản lý quỹ (cần có model `portfolio.fund`)
- `investor_list`: Module cung cấp header component (tùy chọn)

## Lưu ý

- Module yêu cầu có model `portfolio.fund` từ module `overview_fund_management`
- Định dạng thời gian cho NAV tháng: MM/YYYY (ví dụ: 12/2021)
- Giá trị NAV phải lớn hơn 0
- Mỗi phiên giao dịch/NAV tháng phải unique theo quỹ
