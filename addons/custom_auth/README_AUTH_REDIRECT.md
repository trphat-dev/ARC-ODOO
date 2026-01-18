# Custom Auth Redirect Module

## Tổng quan

Module này xử lý điều hướng người dùng sau khi đăng nhập dựa trên loại tài khoản:

- **Portal Users** (group_portal): Được điều hướng đến `/investment_dashboard`
- **Internal Users** (group_user): Được điều hướng đến `/investor_list`

## Tính năng chính

### 1. Điều hướng sau khi đăng nhập
- Xử lý điều hướng người dùng dựa trên loại tài khoản
- Xử lý cả HTTP và JSON endpoints
- Điều hướng tự động sau khi đăng nhập thành công

### 2. Chặn URL không mong muốn
- Chặn truy cập vào `/my`, `/my/home`, `/my/account`
- Chặn truy cập vào `/odoo`
- Tự động điều hướng người dùng về trang phù hợp

### 3. Xử lý Client-side
- JavaScript chặn các link không mong muốn
- Xử lý navigation history
- Điều hướng dựa trên loại người dùng

## Cấu trúc Files

### Controllers
- `auth_redirect.py`: Xử lý điều hướng sau khi đăng nhập
- `url_blocker.py`: Chặn các URL không mong muốn

### Models
- `auth_redirect.py`: Model để xử lý logic điều hướng

### JavaScript
- `auth_redirect.js`: Xử lý điều hướng ở client-side
- `login_override.js`: Override login behavior

## Cách hoạt động

### 1. Khi đăng nhập
1. Người dùng đăng nhập qua form login của Odoo
2. Sau khi đăng nhập thành công, Odoo điều hướng đến `/web` hoặc `/odoo`
3. JavaScript phát hiện và xử lý điều hướng
4. Kiểm tra loại người dùng và điều hướng đến trang tương ứng:
   - Portal users → `/investment_dashboard`
   - Internal users → `/investor_list`

### 2. Khi truy cập URL bị chặn
1. Controller `URLBlockerController` chặn các URL không mong muốn
2. Kiểm tra loại người dùng
3. Điều hướng về trang phù hợp

### 3. Xử lý Client-side
1. JavaScript `auth_redirect.js` được load
2. Chặn các link đến URL bị cấm
3. Xử lý navigation history
4. Điều hướng tự động khi cần thiết

## Cài đặt và Sử dụng

1. Cài đặt module `custom_auth`
2. Restart Odoo server
3. Đăng nhập với tài khoản portal hoặc internal
4. Hệ thống sẽ tự động điều hướng đến trang phù hợp

## Lưu ý

- Module này sử dụng các route `/investment_dashboard` và `/investor_list` có sẵn từ các module khác
- Không tạo template riêng để tránh conflict
- Các URL bị chặn sẽ được điều hướng tự động
- JavaScript chỉ hoạt động ở backend (sau khi đăng nhập)

## Troubleshooting

### Nếu không điều hướng được
1. Kiểm tra quyền người dùng (portal vs internal)
2. Kiểm tra log Odoo để xem lỗi
3. Đảm bảo module được cài đặt đúng cách
4. Kiểm tra các route `/investment_dashboard` và `/investor_list` có tồn tại không

### Nếu JavaScript không hoạt động
1. Kiểm tra console browser để xem lỗi
2. Đảm bảo file JavaScript được load
3. Kiểm tra quyền truy cập session

## Thay đổi so với phiên bản trước

- Không tạo template và controller riêng cho dashboard
- Sử dụng các route có sẵn từ module khác
- Đơn giản hóa cấu trúc module
- Tập trung vào chức năng điều hướng và chặn URL
- Thêm chặn URL `/odoo`
- Bỏ chặn URL `/odoo/discuss` 