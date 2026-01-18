# Transaction List Module

Module quản lý danh sách lệnh giao dịch của nhà đầu tư với 2 tab chính: Pending và Approved.

## Tính năng chính

### 1. Tab Pending
- Hiển thị danh sách lệnh được đặt từ kênh sale portal nhưng chưa được duyệt
- Có thể xuất file danh sách lệnh
- Có thể duyệt lệnh giao dịch

### 2. Tab Approved
- Hiển thị danh sách lệnh giao dịch đã được đặt trực tiếp trên trang của Nhà đầu tư
- Hiển thị các lệnh được đặt ở kênh sale portal đã được duyệt
- Có thể xuất file danh sách lệnh
- Có thể xóa lệnh giao dịch

## Cấu trúc module

```
transaction_list/
├── __init__.py
├── __manifest__.py
├── README.md
├── controller/
│   ├── __init__.py
│   └── transaction_list_controller.py
├── models/
│   ├── __init__.py
│   └── transaction_list_model.py
├── security/
│   └── ir.model.access.csv
├── static/
│   └── src/
│       ├── css/
│       │   ├── header.css
│       │   └── transaction_list.css
│       └── js/
│           ├── components/
│           │   ├── entrypoint.js
│           │   └── header.js
│           └── transaction_list/
│               ├── entrypoint.js
│               └── transaction_list_widget.js
└── views/
    ├── menu_views.xml
    ├── transaction_list_views.xml
    └── transaction_list/
        └── transaction_list_page.xml
```

## Cài đặt và sử dụng

### 1. Cài đặt module
1. Copy module vào thư mục `addons/`
2. Cập nhật danh sách ứng dụng trong Odoo
3. Cài đặt module "Transaction List"

### 2. Đồng bộ dữ liệu từ transaction_management
Sau khi cài đặt, bạn cần đồng bộ dữ liệu từ module `transaction_management`:

```python
# Trong Odoo shell hoặc thông qua API
env['transaction.list'].sync_from_transaction_management()
```

### 3. Truy cập module
- URL: `/transaction-list`
- Menu: Danh sách lệnh > Danh sách lệnh giao dịch

## API Endpoints

### 1. Lấy dữ liệu giao dịch
```
POST /api/transaction-list/data
Parameters:
- status_filter: 'pending' | 'approved' | 'completed' | 'cancelled'
- source_filter: 'portal' | 'sale'
```

### 2. Lấy thống kê
```
POST /api/transaction-list/stats
```

### 3. Duyệt giao dịch
```
POST /api/transaction-list/approve
Parameters:
- transaction_id: ID của giao dịch
```

### 4. Xóa giao dịch
```
POST /api/transaction-list/delete
Parameters:
- transaction_id: ID của giao dịch
```

### 5. Xuất dữ liệu
```
POST /api/transaction-list/export
Parameters:
- status_filter: 'pending' | 'approved'
- source_filter: 'portal' | 'sale'
```

### 6. Tạo dữ liệu test
```
POST /api/transaction-list/create-random
Tạo 10 transaction ngẫu nhiên để test
```

### 7. Khớp lệnh giao dịch
```
POST /api/transaction-list/match-orders
Sử dụng Fund Calculation Engine để khớp lệnh
```

### 8. Tính toán NAV
```
GET /api/transaction-list/calc-nav
Tính toán NAV cho các kỳ hạn khác nhau
```

### 9. Tính toán NAV chi tiết
```
POST /api/transaction-list/calc-nav-detail
Tính toán NAV cho một kỳ hạn cụ thể
```

### 10. Mô phỏng khớp lệnh
```
POST /api/transaction-list/simulate-match
Mô phỏng khớp lệnh không lưu database
```

### 11. Lịch sử khớp lệnh
```
GET /api/transaction-list/match-history
Lấy lịch sử khớp lệnh
```

## Model Fields

### transaction.list
- `name`: Tên giao dịch (computed)
- `user_id`: Người dùng
- `partner_id`: Nhà đầu tư (related)
- `fund_id`: Quỹ
- `transaction_type`: Loại giao dịch (buy/sell/exchange)
- `units`: Số lượng đơn vị
- `destination_fund_id`: Quỹ đích
- `destination_units`: Số lượng đơn vị đích
- `amount`: Số tiền
- `currency_id`: Tiền tệ
- `created_at`: Ngày tạo
- `status`: Trạng thái (pending/approved/completed/cancelled)
- `investment_type`: Loại đầu tư
- `transaction_date`: Ngày giao dịch
- `description`: Mô tả
- `reference`: Mã tham chiếu
- `source`: Nguồn (portal/sale)
- `approved_by`: Người duyệt
- `approved_at`: Ngày duyệt
- `calculated_amount`: Số tiền tính toán (computed)
- `original_transaction_id`: Liên kết với giao dịch gốc

## Phân quyền

- **User**: Đọc, ghi, tạo (không xóa)
- **Manager**: Đọc, ghi, tạo, xóa

## Tích hợp với các module khác

### Tích hợp với transaction_management
Module này tích hợp với module `transaction_management` thông qua:
- Đồng bộ dữ liệu từ `portfolio.transaction`
- Cập nhật trạng thái giao dịch gốc khi duyệt
- Liên kết dữ liệu qua field `original_transaction_id`

### Tích hợp với fund_calculation_engine
Module này tích hợp với module `fund_calculation_engine` thông qua:
- Sử dụng Order Matching Engine để khớp lệnh giao dịch
- Sử dụng Fund Calculation Engine để tính toán NAV
- Gọi API từ fund_calculation_engine thay vì implement logic riêng
- Hỗ trợ mô phỏng khớp lệnh và lịch sử khớp lệnh

## Giao diện

Module sử dụng OWL framework với:
- Header component cho navigation
- Transaction list widget cho hiển thị dữ liệu
- Responsive design với Bootstrap 5
- Modern UI với animations và hover effects

## Tích hợp với Fund Calculation Engine

Module `transaction_list` đã được tích hợp với `fund_calculation_engine` để sử dụng các API tính toán và khớp lệnh. **Tất cả logic xử lý đều được ủy thác cho `fund_calculation_engine`**, đảm bảo tính nhất quán và dễ bảo trì.

### Kiến trúc tích hợp

```
Transaction List Controller
         ↓ (API calls)
Fund Calculation Engine
         ↓ (Business Logic)
Database & Response
```

### Lợi ích của kiến trúc này

1. **Tách biệt trách nhiệm**: `transaction_list` chỉ làm proxy, `fund_calculation_engine` xử lý logic
2. **Dễ bảo trì**: Khi sửa logic ở `fund_calculation_engine`, không cần sửa `transaction_list`
3. **Tái sử dụng**: Các module khác có thể sử dụng trực tiếp API của `fund_calculation_engine`
4. **Nhất quán**: Tất cả logic tính toán đều ở một nơi
5. **Tránh lỗi JSON serialization**: Không cần xử lý datetime objects ở `transaction_list`

### API Endpoints tích hợp

- `POST /api/transaction-list/match-orders` - Khớp lệnh (hỗ trợ `use_time_priority`)
- `POST /api/transaction-list/simulate-match` - Mô phỏng khớp lệnh
- `GET /api/transaction-list/calc-nav` - Tính toán NAV
- `POST /api/transaction-list/calc-nav-detail` - Tính toán NAV chi tiết
- `GET /api/transaction-list/match-history` - Lịch sử khớp lệnh

## Hỗ trợ

Nếu có vấn đề hoặc cần hỗ trợ, vui lòng liên hệ team phát triển. 