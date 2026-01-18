# User Permission Management - Use Cases

## Tổng quan

Module User Permission Management quản lý phân quyền người dùng, đảm bảo mỗi user chỉ truy cập được các chức năng phù hợp với vai trò của họ trong hệ thống HDC-FMS.

## Actors

| Actor         | Mô tả                              |
| ------------- | ---------------------------------- |
| System Admin  | Quản trị viên hệ thống, toàn quyền |
| Fund Operator | Nhân viên vận hành quỹ             |
| Investor User | Nhà đầu tư sử dụng hệ thống        |
| Market Maker  | Đối tác tạo lập thị trường         |

## Use Cases

### UC-01: Tạo tài khoản nhân viên mới

**Actor**: System Admin  
**Precondition**: Có quyền System Admin

**Flow**:

1. Truy cập User Permission Management
2. Click "Create"
3. Điền thông tin:
   - Name, Email, Password
   - Chọn Role: Fund Operator, Investor User, hoặc Market Maker
4. Save
5. Hệ thống tự động:
   - Tạo user trong Odoo
   - Gán vào groups tương ứng
   - Gửi email thông báo

**Postcondition**:

- User mới được tạo với quyền phù hợp
- User có thể đăng nhập và sử dụng hệ thống

---

### UC-02: Thay đổi vai trò người dùng

**Actor**: System Admin  
**Precondition**: User đã tồn tại trong hệ thống

**Flow**:

1. Tìm user cần thay đổi
2. Mở form chỉnh sửa
3. Thay đổi Role (VD: Investor User → Fund Operator)
4. Save
5. Hệ thống tự động:
   - Xóa khỏi groups cũ
   - Thêm vào groups mới

**Postcondition**:

- User có quyền mới
- Quyền cũ bị thu hồi ngay lập tức

---

### UC-03: Vô hiệu hóa tài khoản

**Actor**: System Admin  
**Precondition**: User đang hoạt động

**Flow**:

1. Tìm user cần vô hiệu hóa
2. Mở form chỉnh sửa
3. Đặt trạng thái = Inactive
4. Save

**Postcondition**:

- User không thể đăng nhập
- Dữ liệu lịch sử vẫn được giữ

---

### UC-04: Xử lý Access Denied

**Actor**: Guest/User không có quyền  
**Precondition**: User cố truy cập trang không có quyền

**Flow**:

1. User cố truy cập URL bị hạn chế
2. Hệ thống kiểm tra quyền
3. Nếu không có quyền:
   - Redirect đến `/access-denied`
   - Hiển thị thông báo thân thiện
4. User có thể quay về trang chủ hoặc đăng nhập

**Postcondition**:

- User không truy cập được tài nguyên bị hạn chế
- Hệ thống an toàn

---

### UC-05: Tự động fix Timezone

**Actor**: System (Cron Job)  
**Precondition**: Cron job được kích hoạt

**Flow**:

1. Cron job chạy theo lịch
2. Quét tất cả users
3. Kiểm tra timezone
4. Tự động điều chỉnh timezone không hợp lệ

**Postcondition**:

- Tất cả users có timezone đúng

## Ma trận phân quyền

| Chức năng         | System Admin | Fund Operator | Investor User | Market Maker |
| ----------------- | :----------: | :-----------: | :-----------: | :----------: |
| Quản lý Users     |      ✅      |      ❌       |      ❌       |      ❌      |
| Xử lý Giao dịch   |      ✅      |      ✅       |      ❌       |      ✅      |
| Quản lý NAV       |      ✅      |      ✅       |      ❌       |      ❌      |
| Cấu hình Hệ thống |      ✅      |      ❌       |      ❌       |      ❌      |
| Xem Báo cáo       |      ✅      |      ✅       |      ✅       |      ✅      |
| Mua/Bán CCQ       |      ❌      |      ❌       |      ✅       |      ✅      |
| Xem Danh mục      |      ✅      |      ✅       |      ✅       |      ✅      |

## Luồng phân quyền

```
┌─────────────┐
│   Login     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  Check      │────▶│  Access     │
│  Permission │ No  │  Denied     │
└──────┬──────┘     └─────────────┘
       │ Yes
       ▼
┌─────────────┐
│  Redirect   │
│  By Role    │
└─────────────┘
       │
       ├─── System Admin ──▶ Full Backend
       │
       ├─── Fund Operator ──▶ Transaction Processing
       │
       ├─── Investor User ──▶ Portfolio & Trading
       │
       └─── Market Maker ──▶ Order Matching
```
