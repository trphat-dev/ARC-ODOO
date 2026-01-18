# Fund Management Dashboard - Hướng Dẫn Sử Dụng

## Giới thiệu

**Fund Management Dashboard** là module dashboard tổng quan dành cho nhân viên quỹ, cung cấp:

- Tổng quan giao dịch nhà đầu tư
- Tổng số tài khoản
- Tổng số tiền đầu tư
- Biến động mua bán của từng CCQ trong ngày

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `mail`, `portal`, `web`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Fund Management Dashboard" → Install
```

## Hướng dẫn sử dụng

### 1. Truy cập Dashboard

**URL**: `/my/dashboard` hoặc qua Sidebar

### 2. Các thông tin hiển thị

#### Tổng quan

| Metric            | Mô tả                             |
| ----------------- | --------------------------------- |
| Tổng tài khoản    | Số lượng nhà đầu tư active        |
| Tổng đầu tư       | Tổng giá trị đầu tư toàn hệ thống |
| Giao dịch hôm nay | Số lệnh mua/bán trong ngày        |
| Lệnh chờ xử lý    | Số lệnh đang chờ khớp             |

#### Biến động theo CCQ

- Danh sách CCQ với:
  - Số lệnh mua / Tổng giá trị mua
  - Số lệnh bán / Tổng giá trị bán
  - Net flow (Mua - Bán)

#### Biểu đồ

- Biểu đồ giao dịch 7 ngày
- Biểu đồ phân bổ theo CCQ

### 3. Sidebar Panel

- Menu điều hướng nhanh
- Truy cập các chức năng:
  - Danh sách giao dịch
  - NAV Management
  - Báo cáo
  - Nhà đầu tư

## Cấu trúc Views

```
views/
├── dashboard/
│   └── dashboard_page.xml       # Trang dashboard chính
├── dashboard_detail_views.xml   # Chi tiết views
├── fund_dashboard_daily_views.xml # Daily views
└── menu_views.xml               # Menu
```

## Assets

```
static/src/
├── js/dashboard/
│   ├── dashboard_widget.js    # Widget dashboard
│   ├── sidebar_panel.js       # Sidebar component
│   └── entrypoint.js          # Entry point
└── scss/
    ├── sidebar.scss           # Sidebar styles
    └── dashboard.scss         # Dashboard styles
```

## Lưu ý

- Dashboard tự động refresh mỗi 30 giây
- Dữ liệu real-time từ database
- Sidebar Panel được share với các module khác
