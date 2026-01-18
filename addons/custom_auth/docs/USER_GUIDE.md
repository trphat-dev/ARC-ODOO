# Custom Auth - Hướng Dẫn Sử Dụng

## Giới thiệu

**Custom Auth Pages** là module tùy biến giao diện các trang xác thực của Odoo bao gồm:

- Trang đăng nhập (Login)
- Trang đăng ký (Signup)
- Trang đặt lại mật khẩu (Reset Password)

Module sử dụng Bootstrap và SCSS để tạo giao diện hiện đại, thân thiện với người dùng.

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `auth_signup`, `base`, `web`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Custom Auth Pages" → Install
```

## Cấu hình

Module này không yêu cầu cấu hình đặc biệt. Sau khi cài đặt, các trang xác thực sẽ tự động sử dụng giao diện mới.

## Giao diện được tùy biến

### 1. Trang đăng nhập

- URL: `/web/login`
- Template: `views/custom_login_template.xml`
- Giao diện login với branding HDC-FMS

### 2. Trang đăng ký

- URL: `/web/signup`
- Template: `views/custom_signup_template.xml`
- Form đăng ký tài khoản mới

### 3. Trang đặt lại mật khẩu

- URL: `/web/reset_password`
- Template: `views/custom_reset_password_template.xml`
- Gửi email reset password

## Cấu trúc SCSS

```
static/src/scss/
├── _variables.scss      # Biến CSS (màu sắc, font, spacing)
└── _auth_common.scss    # Styles chung cho các trang auth
```

## Lưu ý

- **Redirect Logic**: Logic redirect được xử lý server-side trong `auth_redirect.py` và `url_blocker.py` (không sử dụng Backend JS)
- Module này chỉ thay đổi giao diện, không thay đổi logic xác thực của Odoo
- Tương thích với module `auth_signup` của Odoo
