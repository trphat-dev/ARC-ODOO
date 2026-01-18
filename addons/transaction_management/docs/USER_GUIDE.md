# Transaction Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**Transaction Management** là module quản lý giao dịch với 2 trang chính:

- Giao dịch chờ xử lý (Pending)
- Lịch sử giao dịch (Order History)

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `mail`, `portal`, `web`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Transaction Management" → Install
```

## Hướng dẫn sử dụng

### 1. Giao dịch chờ xử lý (Pending)

**Đường dẫn Backend**: Transaction Management → Pending

Hiển thị các giao dịch:

- Đang chờ duyệt
- Đang xử lý
- Chưa hoàn thành

**Actions**:

- Duyệt giao dịch
- Từ chối giao dịch
- Xem chi tiết

### 2. Lịch sử giao dịch (Order History)

**Đường dẫn Backend**: Transaction Management → Order History

Hiển thị tất cả giao dịch đã hoàn thành:

- Mua thành công
- Bán thành công
- Đã hủy/từ chối

**Features**:

- Filter theo ngày, loại, trạng thái
- Search
- Export

## Cấu trúc Views

```
views/
└── transaction_trading/
    ├── transaction_pending_page.xml   # Pending page
    ├── transaction_order_page.xml     # Order history page
    └── transaction_periodic_page.xml  # Periodic page
```

## Assets

```
static/src/
├── scss/
│   └── transaction_management.scss
└── js/transaction_management/
    ├── pending_widget.js
    ├── order_widget.js
    ├── periodic_widget.js
    └── entrypoint.js
```

## Lưu ý

- Giao dịch pending cần được xử lý trong ngày
- Order history được lưu vĩnh viễn
- SIP tự động trích theo lịch đã cấu hình
