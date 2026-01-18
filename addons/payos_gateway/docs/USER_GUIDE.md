# PayOS Gateway - Hướng Dẫn Sử Dụng

## Giới thiệu

**PayOS Gateway** là module tích hợp cổng thanh toán PayOS, cung cấp:

- Tạo payment link
- Webhook verify thanh toán
- Quản lý credentials

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `web`
- **Python packages**: `requests`, `Crypto`
- **License**: LGPL-3

## Cài đặt

```bash
# Cài đặt packages
pip install requests pycryptodome

# Cài đặt module
Odoo Settings → Apps → Search "PayOS Gateway" → Install
```

## Cấu hình

### Cấu hình PayOS Credentials

1. Truy cập **PayOS → Configuration**
2. Nhập thông tin từ PayOS Dashboard:
   - Client ID
   - API Key
   - Checksum Key
3. Chọn môi trường:
   - Sandbox (test)
   - Production
4. Save

## Hướng dẫn sử dụng

### 1. Tạo Payment Link

**API Endpoint**: `/payos/create-payment`

**Request**:

```json
{
  "amount": 1000000,
  "description": "Mua CCQ DCDS",
  "orderCode": "ORD123456",
  "returnUrl": "https://...",
  "cancelUrl": "https://..."
}
```

**Response**:

```json
{
  "checkoutUrl": "https://pay.payos.vn/...",
  "paymentLinkId": "..."
}
```

### 2. Webhook Verify

**Endpoint**: `/payos/webhook`

PayOS sẽ gọi endpoint này khi:

- Thanh toán thành công
- Thanh toán thất bại
- Thanh toán bị hủy

**Verify signature**:

- Sử dụng Checksum Key
- Kiểm tra HMAC-SHA256

### 3. Kiểm tra trạng thái

**API**: `/payos/payment-status/{orderCode}`

Trả về trạng thái thanh toán hiện tại.

## Cấu trúc Views

```
views/
├── payos_settings.xml       # Settings page
└── payos_config_views.xml   # Config views
```

## Data

- `data/payos_credentials_data.xml` - Default credentials

## Integration Flow

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Odoo    │──▶│ PayOS   │──▶│  Bank   │──▶│ PayOS   │
│ Create  │   │ Checkout│   │ Payment │   │ Webhook │
│ Link    │   │   Page  │   │         │   │         │
└─────────┘   └─────────┘   └─────────┘   └────┬────┘
                                               │
                                               ▼
                                         ┌─────────┐
                                         │  Odoo   │
                                         │ Process │
                                         │  Order  │
                                         └─────────┘
```

## Lưu ý

- Luôn verify signature từ webhook
- Sử dụng Sandbox để test trước
- Mỗi orderCode chỉ dùng 1 lần
- Credentials phải bảo mật
