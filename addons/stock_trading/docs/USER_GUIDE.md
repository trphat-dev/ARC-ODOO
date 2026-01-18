# Stock Trading - Hướng Dẫn Sử Dụng

## Giới thiệu

**Stock Trading** là module quản lý giao dịch chứng khoán thông qua FastConnect Trading API của SSI, cung cấp:

- Đặt lệnh mua/bán (Stock & Derivatives)
- Quản lý lệnh (Sửa, Hủy)
- Xem số dư tài khoản & vị thế
- Quản lý tiền mặt
- Đăng ký quyền mua
- Chuyển khoản cổ phiếu
- Streaming real-time qua SignalR

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `mail`, `portal`, `web`, `stock_data`
- **Python packages**: `ssi-fctrading`
- **License**: LGPL-3

## Cài đặt

```bash
# Cài đặt Python package
pip install ssi-fctrading

# Cài đặt module
Odoo Settings → Apps → Search "Stock Trading" → Install
```

## Cấu hình

### Cấu hình API

1. Truy cập **Stock Trading → Configuration**
2. Điền thông tin SSI FastConnect:
   - Consumer ID
   - Consumer Secret
   - Private Key
3. Test connection
4. Save

## Hướng dẫn sử dụng

### 1. Đặt lệnh giao dịch

**URL**: `/trading/order`

**Các loại lệnh**:
| Loại | Mô tả |
|------|-------|
| LO (Limit Order) | Lệnh giới hạn |
| ATO | Lệnh tại giá mở cửa |
| ATC | Lệnh tại giá đóng cửa |
| MP | Lệnh thị trường |

### 2. Quản lý lệnh

- Xem danh sách lệnh
- Sửa lệnh (giá, khối lượng)
- Hủy lệnh

### 3. Xem số dư tài khoản

- Tiền mặt khả dụng
- Tổng tài sản
- Margin

### 4. Quản lý vị thế

- Danh sách cổ phiếu đang nắm giữ
- Giá vốn trung bình
- Lãi/Lỗ chưa thực hiện

### 5. Quản lý tiền mặt

- Nạp tiền
- Rút tiền
- Chuyển khoản nội bộ

### 6. Đăng ký quyền mua (ORS)

- Xem quyền mua
- Đăng ký/Hủy đăng ký

### 7. Chuyển khoản cổ phiếu

- Chuyển cổ phiếu giữa các tài khoản

## Cấu trúc Backend

```
views/
├── trading_config_views.xml      # Cấu hình API
├── trading_order_views.xml       # Đặt/Quản lý lệnh
├── trading_account_views.xml     # Tài khoản
├── trading_cash_views.xml        # Tiền mặt
├── trading_ors_views.xml         # Quyền mua
├── trading_stock_transfer_views.xml  # Chuyển cổ phiếu
├── trading_history_views.xml     # Lịch sử
├── trading_menus.xml             # Menu
└── trading_portal/
    └── trading_portal_templates.xml  # Frontend
```

## Cron Jobs

- Tự động đồng bộ trạng thái lệnh
- Cấu hình: `data/trading_cron.xml`

## Lưu ý

- Giao dịch trong giờ sàn: 9h-15h (HOSE, HNX)
- Phí giao dịch theo quy định SSI
- Cần có tài khoản SSI để sử dụng
