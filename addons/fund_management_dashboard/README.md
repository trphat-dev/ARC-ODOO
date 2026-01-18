# Fund Management Dashboard Module

Module dashboard tổng quan cho nhân viên quỹ quản lý các giao dịch, tài khoản và biến động quỹ.

## Mô tả

Module này cung cấp dashboard tổng quan cho nhân viên quỹ với các tính năng:

- **Tổng số tài khoản**: Hiển thị tổng số tài khoản nhà đầu tư
- **Tổng số tiền đầu tư**: Tổng giá trị đầu tư và giá trị hiện tại
- **Giao dịch hôm nay**: Thống kê các giao dịch trong ngày
- **Biến động mua/bán**: Biến động mua bán của từng CCQ trong ngày
- **Top giao dịch**: Danh sách các giao dịch lớn nhất trong ngày

## Cài đặt

1. Copy module vào thư mục `addons` của Odoo
2. Cập nhật danh sách ứng dụng trong Odoo
3. Cài đặt module "Fund Management Dashboard"

## Sử dụng

Sau khi cài đặt, truy cập:
- Menu: **Fund Management Dashboard > Dashboard Tổng Quan**
- URL: `/fund-management-dashboard`

## Cấu trúc Module

```
fund_management_dashboard/
├── __init__.py
├── __manifest__.py
├── README.md
├── controller/
│   ├── __init__.py
│   └── dashboard_controller.py
├── models/
│   └── __init__.py
├── security/
│   └── ir.model.access.csv
├── static/
│   └── src/
│       ├── css/
│       │   └── dashboard.css
│       └── js/
│           └── dashboard/
│               ├── entrypoint.js
│               └── dashboard_widget.js
└── views/
    ├── dashboard/
    │   └── dashboard_page.xml
    └── menu_views.xml
```

## Dependencies

Module này phụ thuộc vào:
- `board`: Dashboard gốc của Odoo
- `investor_list`: Quản lý danh sách nhà đầu tư
- `overview_fund_management`: Tổng quan quản lý quỹ
- `transaction_list`: Quản lý danh sách giao dịch
- `fund_management`: Quản lý quỹ

## API Endpoints

### GET /fund-management-dashboard
Trang dashboard chính

### POST /api/fund-management-dashboard/data
Lấy dữ liệu dashboard real-time (JSON)
- Parameters:
  - `use_cached` (boolean): Có sử dụng dữ liệu từ database không

### POST /api/fund-management-dashboard/today
Lấy dữ liệu dashboard hôm nay từ database (JSON)

### POST /api/fund-management-dashboard/historical
Lấy dữ liệu dashboard lịch sử (JSON)
- Parameters:
  - `days` (integer): Số ngày lịch sử cần lấy (1-30, mặc định 7)

## Model: fund.dashboard.daily

Model lưu trữ dữ liệu dashboard theo ngày với các tính năng:

- **Tự động lưu**: Dữ liệu được tự động lưu mỗi khi truy cập dashboard
- **Lưu trữ JSON**: Lưu trữ chi tiết thống kê, biến động quỹ, top giao dịch dưới dạng JSON
- **Lịch sử**: Lưu trữ dữ liệu theo ngày để xem lại lịch sử
- **Unique constraint**: Mỗi ngày chỉ có 1 bản ghi cho mỗi công ty

### Methods:

- `get_or_create_today()`: Lấy hoặc tạo bản ghi cho hôm nay
- `update_today_dashboard(data)`: Cập nhật dữ liệu dashboard
- `get_today_data()`: Lấy dữ liệu dashboard hôm nay
- `get_historical_data(days)`: Lấy dữ liệu lịch sử
- `action_refresh_data()`: Làm mới dữ liệu từ controller

## Tính năng

### 1. Summary Cards
- Tổng số tài khoản
- Tổng số tiền đầu tư
- Giá trị hiện tại (với % lợi/lỗ)
- Giao dịch hôm nay

### 2. Today's Activity
- Số lượng và giá trị lệnh mua
- Số lượng và giá trị lệnh bán
- Tổng giá trị giao dịch

### 3. Account Statistics
- Thống kê tài khoản theo trạng thái:
  - Chờ KYC
  - KYC
  - VSD
  - Chưa cập nhật

### 4. Fund Movements
- Biến động mua/bán của từng CCQ trong ngày
- Hiển thị số lượng và giá trị mua/bán
- Tính toán ròng (Mua - Bán)

### 5. Top Transactions
- Danh sách các giao dịch lớn nhất trong ngày
- Hiển thị thông tin chi tiết: nhà đầu tư, quỹ, loại, số lượng, giá trị

## Tác giả

Your Company

## Giấy phép

LGPL-3

