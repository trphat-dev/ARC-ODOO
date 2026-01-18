# User Permission Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**User Permission Management** là module quản lý phân quyền người dùng trong hệ thống HDC-FMS. Module cung cấp:

- Quản lý phân quyền System Admin, Investor User, Fund Operator
- Tự động đồng bộ với Odoo groups
- Giao diện quản lý user permission

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `mail`, `portal`, `web`, `auth_signup`, `fund_management_dashboard`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "User Permission Management" → Install
```

## Cấu hình

### Các vai trò trong hệ thống

| Vai trò           | Mô tả                      | Quyền                       |
| ----------------- | -------------------------- | --------------------------- |
| **System Admin**  | Quản trị viên hệ thống     | Toàn quyền quản lý hệ thống |
| **Fund Operator** | Nhân viên vận hành quỹ     | Xử lý giao dịch, NAV        |
| **Investor User** | Nhà đầu tư                 | Xem danh mục, mua/bán CCQ   |
| **Market Maker**  | Đối tác tạo lập thị trường | Khớp lệnh, giao dịch        |

## Hướng dẫn sử dụng

### 1. Xem danh sách người dùng

- Truy cập menu **User Permission** trong backend
- Xem danh sách tất cả users với vai trò hiện tại

### 2. Thêm người dùng mới

1. Click nút "Create"
2. Điền thông tin người dùng
3. Chọn vai trò (Role)
4. Hệ thống tự động đồng bộ với Odoo groups

### 3. Chỉnh sửa quyền người dùng

1. Chọn user cần chỉnh sửa
2. Thay đổi vai trò
3. Save - hệ thống tự động cập nhật groups

### 4. Trang Access Denied

- Khi user không có quyền truy cập, hiển thị trang thông báo thân thiện
- URL: `/access-denied`

## Cấu trúc Views

```
views/
├── user_permission/
│   ├── user_permission_backend_views.xml  # Backend form/list
│   ├── res_users_inherit_views.xml        # Inherit res.users
│   └── user_permission_page.xml           # Frontend page
└── access_denied/
    └── access_denied_page.xml             # Access denied page
```

## Cron Jobs

- **Timezone Fix**: Tự động điều chỉnh timezone cho users
- Cấu hình: `data/timezone_fix_cron.xml`

## Lưu ý

- Module này inherit và mở rộng model `res.users` của Odoo
- Đảm bảo đồng bộ với Odoo groups để tránh xung đột quyền
- Sidebar Panel được load từ `fund_management_dashboard`
