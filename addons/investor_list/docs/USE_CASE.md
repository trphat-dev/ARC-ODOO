# Investor List - Use Cases

## Tổng quan

Module Investor List cung cấp giao diện quản lý danh sách nhà đầu tư, cho phép nhân viên quỹ theo dõi và quản lý thông tin cơ bản của tất cả nhà đầu tư trong hệ thống.

## Actors

| Actor         | Mô tả                  |
| ------------- | ---------------------- |
| Fund Operator | Nhân viên vận hành quỹ |

## Use Cases

### UC-01: Xem danh sách nhà đầu tư

**Actor**: Fund Operator  
**Precondition**: Đã đăng nhập với quyền phù hợp

**Flow**:

1. Truy cập trang `/investor-list`
2. Hệ thống load danh sách nhà đầu tư
3. Hiển thị dạng bảng với các cột:
   - Mã nhà đầu tư
   - Họ tên
   - Email
   - Số điện thoại
   - Trạng thái eKYC
   - Ngày đăng ký

**Postcondition**:

- Danh sách nhà đầu tư được hiển thị

---

### UC-02: Tìm kiếm nhà đầu tư

**Actor**: Fund Operator  
**Precondition**: Đang ở trang danh sách

**Flow**:

1. Nhập từ khóa vào ô tìm kiếm
2. Hệ thống tìm kiếm theo:
   - Mã nhà đầu tư
   - Họ tên
   - Email
   - Số điện thoại
3. Hiển thị kết quả phù hợp

**Postcondition**:

- Danh sách được lọc theo từ khóa

---

### UC-03: Lọc nhà đầu tư theo trạng thái

**Actor**: Fund Operator  
**Precondition**: Đang ở trang danh sách

**Flow**:

1. Click vào bộ lọc trạng thái
2. Chọn trạng thái cần lọc:
   - Tất cả
   - Đã xác thực eKYC
   - Chưa xác thực
   - Đang chờ duyệt
3. Hệ thống lọc và hiển thị kết quả

**Postcondition**:

- Danh sách được lọc theo trạng thái

---

### UC-04: Xem chi tiết nhà đầu tư

**Actor**: Fund Operator  
**Precondition**: Có nhà đầu tư trong danh sách

**Flow**:

1. Click vào dòng nhà đầu tư cần xem
2. Hệ thống hiển thị thông tin chi tiết:
   - Thông tin cá nhân
   - Số tài khoản ngân hàng
   - Trạng thái eKYC
   - Lịch sử giao dịch
3. Có thể chuyển đến trang quản lý hồ sơ

**Postcondition**:

- Thông tin chi tiết được hiển thị

---

### UC-05: Xuất danh sách nhà đầu tư

**Actor**: Fund Operator  
**Precondition**: Có quyền xuất dữ liệu

**Flow**:

1. Click nút "Xuất Excel"
2. Chọn các cột cần xuất
3. Chọn định dạng (Excel/CSV)
4. Hệ thống tạo file và download

**Postcondition**:

- File danh sách được tải về

## Luồng nghiệp vụ

```
┌─────────────────┐
│  Investor List  │
│     Page        │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│Search │ │Filter │
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│  Filtered List  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│Detail │ │Export │
│ View  │ │ Excel │
└───────┘ └───────┘
```
