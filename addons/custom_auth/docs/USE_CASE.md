# Custom Auth - Use Cases

## Tổng quan

Module Custom Auth cung cấp giao diện xác thực tùy chỉnh cho hệ thống HDC-FMS, đảm bảo trải nghiệm người dùng nhất quán và chuyên nghiệp từ bước đầu tiên.

## Actors

| Actor           | Mô tả                      |
| --------------- | -------------------------- |
| Guest User      | Người dùng chưa đăng nhập  |
| Registered User | Người dùng đã có tài khoản |
| System          | Hệ thống Odoo              |

## Use Cases

### UC-01: Đăng nhập hệ thống

**Actor**: Registered User  
**Precondition**:

- Người dùng đã có tài khoản trong hệ thống
- Truy cập trang đăng nhập

**Flow**:

1. Người dùng truy cập `/web/login`
2. Hệ thống hiển thị form đăng nhập tùy chỉnh
3. Người dùng nhập email và mật khẩu
4. Click nút "Đăng nhập"
5. Hệ thống xác thực thông tin

**Postcondition**:

- **Thành công**: Redirect đến trang chủ/dashboard
- **Thất bại**: Hiển thị thông báo lỗi

---

### UC-02: Đăng ký tài khoản mới

**Actor**: Guest User  
**Precondition**:

- Chức năng đăng ký được bật trong hệ thống
- Người dùng chưa có tài khoản

**Flow**:

1. Người dùng truy cập `/web/signup`
2. Hệ thống hiển thị form đăng ký tùy chỉnh
3. Người dùng điền thông tin:
   - Họ tên
   - Email
   - Mật khẩu
   - Xác nhận mật khẩu
4. Click nút "Đăng ký"
5. Hệ thống tạo tài khoản và gửi email xác nhận

**Postcondition**:

- Tài khoản được tạo
- Email xác nhận được gửi đến người dùng

---

### UC-03: Đặt lại mật khẩu

**Actor**: Registered User  
**Precondition**:

- Người dùng quên mật khẩu
- Email đã được đăng ký trong hệ thống

**Flow**:

1. Người dùng truy cập `/web/reset_password`
2. Hệ thống hiển thị form reset password
3. Người dùng nhập email đã đăng ký
4. Click nút "Gửi yêu cầu"
5. Hệ thống gửi email với link reset password
6. Người dùng click link trong email
7. Nhập mật khẩu mới và xác nhận

**Postcondition**:

- Mật khẩu được cập nhật
- Người dùng có thể đăng nhập với mật khẩu mới

---

### UC-04: Redirect sau đăng nhập

**Actor**: System  
**Precondition**: Người dùng vừa đăng nhập thành công

**Flow**:

1. Hệ thống xác định vai trò người dùng
2. Dựa vào vai trò, redirect đến trang phù hợp:
   - **Portal User**: Redirect đến `/my/overview`
   - **Internal User**: Redirect đến `/web` (backend)
   - **Admin**: Redirect đến dashboard quản trị

**Postcondition**:

- Người dùng được chuyển đến trang phù hợp với quyền của họ

## Luồng xác thực

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Login     │────▶│  Validate   │────▶│  Redirect   │
│   Form      │     │  Credentials│     │  By Role    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   Signup    │     │   Error     │
│   Form      │     │   Message   │
└─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│   Reset     │
│   Password  │
└─────────────┘
```
