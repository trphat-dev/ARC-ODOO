# NAV Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**NAV Management** là module quản lý NAV (Net Asset Value - Giá trị tài sản ròng) cho các quỹ đầu tư, bao gồm:

- NAV phiên giao dịch
- NAV tháng
- Kỳ hạn và lãi suất
- Cấu hình chặn trên/chặn dưới

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `mail`, `portal`, `web`, `fund_management`, `fund_management_control`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "NAV Management" → Install
```

## Hướng dẫn sử dụng

### 1. NAV Phiên giao dịch

**Đường dẫn Backend**: NAV Management → NAV Transaction

**Chức năng**:

- Hiển thị danh sách NAV của tất cả phiên giao dịch theo Quỹ
- Lọc theo khoảng thời gian
- Xuất file danh sách NAV

### 2. NAV Tháng

**Đường dẫn Backend**: NAV Management → NAV Monthly

**Chức năng**:

- Hiển thị NAV tháng theo Quỹ
- Thêm giá trị NAV tháng mới
- Tính toán NAV trung bình

### 3. Kỳ hạn và Lãi suất (Term Rate)

**Đường dẫn Backend**: NAV Management → Term Rate

| Trường   | Mô tả                     |
| -------- | ------------------------- |
| Kỳ hạn   | Số tháng (1, 3, 6, 12...) |
| Lãi suất | % lãi suất theo kỳ hạn    |
| Quỹ      | CCQ áp dụng               |

### 4. Cấu hình Cap (Chặn trên/dưới)

**Đường dẫn Backend**: NAV Management → CAP Config

- **Cap trên**: Giới hạn tăng NAV tối đa/ngày
- **Cap dưới**: Giới hạn giảm NAV tối đa/ngày

### 5. Tồn kho CCQ hàng ngày

**Đường dẫn Backend**: NAV Management → Daily Inventory

- Theo dõi số lượng CCQ khả dụng mỗi ngày
- Tự động tạo bởi cron job

## Cấu trúc Backend

```
views/
├── menu_views.xml                 # Menu chính
├── nav_term_rate_views.xml        # Kỳ hạn/Lãi suất
├── nav_cap_config_views.xml       # Chặn trên/dưới
├── nav_daily_inventory_views.xml  # Tồn kho hàng ngày
├── nav_transaction/
│   └── nav_transaction_page.xml   # Trang NAV phiên
└── nav_monthly/
    └── nav_monthly_page.xml       # Trang NAV tháng
```

## Cron Jobs

- **Daily NAV Cron**: Tự động tạo tồn kho CCQ hàng ngày
- Cấu hình: `data/nav_daily_cron.xml`

## Seed Data

- Dữ liệu mẫu: `data/nav_seed_data.xml`

## Lưu ý

- NAV được cập nhật cuối ngày giao dịch
- Công thức: NAV = (Tổng tài sản - Tổng nợ) / Số CCQ lưu hành
- Cap config giúp kiểm soát biến động bất thường
