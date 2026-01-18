# Investor List - Hướng Dẫn Sử Dụng

## Giới thiệu

**Investor List** là module quản lý danh sách nhà đầu tư trong hệ thống HDC-FMS. Module cung cấp giao diện hiển thị và quản lý thông tin cơ bản của tất cả nhà đầu tư.

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `bus`, `mail`, `portal`, `web`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Investor List" → Install
```

## Hướng dẫn sử dụng

### 1. Xem danh sách nhà đầu tư

- Truy cập URL: `/investor-list`
- Giao diện hiển thị danh sách tất cả nhà đầu tư
- Hỗ trợ tìm kiếm và lọc

### 2. Tính năng chính

| Tính năng | Mô tả                                   |
| --------- | --------------------------------------- |
| Danh sách | Hiển thị danh sách nhà đầu tư dạng bảng |
| Tìm kiếm  | Tìm kiếm theo tên, email, mã nhà đầu tư |
| Lọc       | Lọc theo trạng thái, ngày đăng ký       |
| Chi tiết  | Xem thông tin chi tiết từng nhà đầu tư  |

## Cấu trúc Views

```
views/
├── menu_views.xml              # Menu chính
├── investor_list_views.xml     # Backend list/form views
└── investor_list/
    └── investor_list_page.xml  # Frontend page
```

## Assets

```
static/src/
├── scss/
│   ├── investor_list.scss    # Styles chính
│   └── _header.scss          # Header styles
└── js/
    └── components/
        ├── header.js         # Header component
        └── entrypoint.js     # Entry point
    └── investor_list/
        ├── investor_list_widget.js  # Widget chính
        └── entrypoint.js            # Entry point
```

## Lưu ý

- Module này hiển thị danh sách nhà đầu tư từ model `res.partner`
- Để quản lý chi tiết hồ sơ, sử dụng module `investor_profile_management`
