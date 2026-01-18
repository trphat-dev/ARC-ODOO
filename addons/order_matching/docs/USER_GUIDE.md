# Order Matching - Hướng Dẫn Sử Dụng

## Giới thiệu

**Order Matching** là module hệ thống khớp lệnh giao dịch tự động theo thuật toán Price-Time Priority (FIFO), cung cấp:

- Khớp lệnh tự động
- Thông báo đáo hạn
- Sổ lệnh giao dịch
- Quản lý cặp lệnh đã khớp

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `bus`, `mail`, `portal`, `web`, `stock_trading`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Order Matching" → Install
```

## Hướng dẫn sử dụng

### 1. Sổ lệnh (Order Book)

**URL**: `/order-book`

Hiển thị các lệnh:

- **Lệnh mua**: Sắp xếp giá giảm dần
- **Lệnh bán**: Sắp xếp giá tăng dần

### 2. Các loại lệnh

#### Lệnh thường (Normal Orders)

**URL**: `/order-book/normal`

- Lệnh mua/bán CCQ thông thường
- Khớp theo phiên

#### Lệnh thỏa thuận (Negotiated Orders)

**URL**: `/order-book/negotiated`

- Lệnh giao dịch thỏa thuận
- Cần có đối tác cụ thể

#### Lệnh đã hoàn thành (Completed Orders)

**URL**: `/order-book/completed`

- Lệnh đã được khớp hoàn toàn
- Lịch sử giao dịch

### 3. Thông báo đáo hạn

- Hệ thống tự động gửi thông báo khi CCQ sắp đáo hạn
- Nhà đầu tư chọn: Tái đầu tư hoặc Rút tiền
- URL response: `/maturity-notification/{id}/respond`

### 4. Lệnh đã khớp (Matched Orders)

- Xem chi tiết cặp lệnh đã khớp
- Thông tin: Buyer, Seller, Price, Units, Time

## Thuật toán khớp lệnh

**Price-Time Priority (FIFO)**:

1. Ưu tiên giá tốt nhất
2. Cùng giá → Ưu tiên lệnh đến trước
3. Khớp tối đa khối lượng có thể

## Cấu trúc Views

```
views/
├── matched_orders_views.xml           # Lệnh đã khớp
├── maturity_notification_views.xml    # Thông báo đáo hạn
├── maturity_notification_log_views.xml
├── sent_orders_views.xml              # Lệnh đã gửi
├── menu_views.xml
└── pages/
    ├── order_book_page.xml
    ├── completed_orders_page.xml
    ├── negotiated_orders_page.xml
    ├── normal_orders_page.xml
    └── maturity_notification_response_page.xml
```

## Assets

```
static/src/
├── js/
│   ├── order_matching_actions.js
│   ├── auto_match_worker.js      # Worker tự động khớp lệnh
│   └── order_book/
│       ├── order_book_component.js
│       ├── completed_orders_component.js
│       ├── negotiated_orders_component.js
│       ├── normal_orders_component.js
│       └── entrypoint.js
└── css/
    └── order_book.css
```

## Auto Match Worker

- Chạy nền mỗi 1 giây
- Tự động khớp lệnh phù hợp
- Hoạt động trên mọi trang

## Lưu ý

- Khớp lệnh chỉ diễn ra trong giờ giao dịch
- Lệnh hết hạn sẽ tự động hủy
- Thông báo đáo hạn gửi trước 7 ngày
