# Overview Fund Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**Overview Fund Management** là module cung cấp trang tổng quan quỹ đầu tư cho nhà đầu tư, hiển thị danh mục đầu tư và hiệu suất tổng thể.

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `bus`, `mail`, `portal`, `web`, `fund_management`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Overview Fund Management" → Install
```

## Hướng dẫn sử dụng

### 1. Truy cập trang tổng quan

**URL**: `/my/overview`

### 2. Các thông tin hiển thị

#### Tổng quan danh mục

| Thông tin    | Mô tả                                |
| ------------ | ------------------------------------ |
| Tổng giá trị | Tổng giá trị tất cả CCQ đang nắm giữ |
| Lợi nhuận    | Tổng lợi nhuận (số tiền và %)        |
| Số CCQ       | Số loại CCQ đang nắm giữ             |

#### Chi tiết từng CCQ

- Tên CCQ
- Số unit nắm giữ
- NAV hiện tại
- Giá trị hiện tại
- Lợi nhuận/Lỗ

#### Biểu đồ phân bổ

- Pie chart phân bổ theo CCQ
- % của mỗi CCQ trong danh mục

### 3. Components

#### Header

- Logo, tên người dùng
- Menu điều hướng

#### Footer

- Thông tin liên hệ
- Links hữu ích

#### Loader

- Hiển thị khi đang load dữ liệu
- Animation loading

## Cấu trúc Views

```
views/
└── overview_fund_management/
    └── overview_fund_management_page.xml
```

## Assets

```
static/src/
├── js/
│   ├── components/
│   │   ├── header.js        # Header component
│   │   ├── footer.js        # Footer component
│   │   ├── loader.js        # Loader component
│   │   └── entrypoint.js
│   └── overview_fund_management/
│       ├── overview_fund_management_widget.js
│       └── entrypoint.js
└── scss/
    ├── header.scss
    ├── footer.scss
    ├── loader.scss
    └── overview_fund_management.scss  # Premium styles
```

## Lưu ý

- Dữ liệu được cập nhật theo NAV mới nhất
- Lợi nhuận được tính dựa trên giá mua trung bình
- Trang sử dụng Premium UI với animations
