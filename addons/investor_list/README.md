# Investor List Module

Module quản lý danh sách nhà đầu tư cho hệ thống Odoo.

## Mô tả

Module này cung cấp chức năng quản lý danh sách nhà đầu tư với các tính năng:
- Hiển thị danh sách quỹ đầu tư
- Theo dõi giao dịch gần nhất
- Tổng quan tài sản
- Biểu đồ phân bổ đầu tư
- So sánh hiệu suất

## Cài đặt

1. Copy module vào thư mục `addons` của Odoo
2. Cập nhật danh sách ứng dụng trong Odoo
3. Cài đặt module "Investor List"

## Sử dụng

Sau khi cài đặt, truy cập URL: `/investor_list` để xem trang danh sách nhà đầu tư.

## Cấu trúc Module

```
investor_list/
├── __init__.py
├── __manifest__.py
├── controller/
│   ├── __init__.py
│   └── investor_list_controller.py
├── models/
│   ├── __init__.py
│   ├── comparison.py
│   ├── fund.py
│   ├── investment.py
│   └── transaction.py
├── security/
│   └── ir.model.access.csv
├── static/
│   └── src/
│       ├── css/
│       │   └── header.css
│       └── js/
│           ├── components/
│           │   ├── entrypoint.js
│           │   └── header.js
│           └── investor_list/
│               ├── entrypoint.js
│               └── investor_list_widget.js
└── views/
    ├── comparison_views.xml
    ├── fund_views.xml
    ├── investment_views.xml
    ├── menu_views.xml
    ├── transaction_views.xml
    └── investor_list/
        └── investor_list_page.xml
```

## URL Routes

- `/investor_list` - Trang chính hiển thị danh sách nhà đầu tư

## Tác giả

Your Company

## Giấy phép

LGPL-3
