# Fund Management Control - Use Cases

## Tổng quan

Module Fund Management Control cung cấp các chức năng quản trị cấu hình hệ thống quỹ, chỉ dành cho Admin và Back-office.

## Actors

| Actor        | Mô tả                  |
| ------------ | ---------------------- |
| System Admin | Quản trị viên hệ thống |
| Fund Manager | Quản lý quỹ            |

## Use Cases

### UC-01: Thêm mới Chứng chỉ quỹ

**Actor**: System Admin  
**Precondition**: Có quyền quản trị CCQ

**Flow**:

1. Truy cập Fund Certificate Management
2. Click "Thêm mới"
3. Điền thông tin:
   - Mã CCQ
   - Tên CCQ
   - Mô tả
   - NAV khởi điểm
   - Ngày bắt đầu
4. Cấu hình regulations
5. Save

**Postcondition**: CCQ mới được tạo và có thể giao dịch

---

### UC-02: Cập nhật Biểu phí

**Actor**: Fund Manager  
**Precondition**: CCQ đã tồn tại

**Flow**:

1. Truy cập Fee Schedule
2. Chọn CCQ cần cập nhật phí
3. Chỉnh sửa:
   - Phí mua (% hoặc cố định)
   - Phí bán (% hoặc cố định)
   - Phí quản lý
4. Chọn ngày áp dụng
5. Save

**Postcondition**:

- Biểu phí mới có hiệu lực từ ngày chỉ định
- Giao dịch cũ không bị ảnh hưởng

---

### UC-03: Cấu hình SIP (Đầu tư định kỳ)

**Actor**: Fund Manager  
**Precondition**: CCQ đã active

**Flow**:

1. Truy cập SIP Settings
2. Tạo cấu hình SIP cho CCQ
3. Điền thông tin:
   - Số tiền tối thiểu
   - Ngày trích hàng tháng
   - Phí SIP (nếu có)
4. Kích hoạt

**Postcondition**:

- Nhà đầu tư có thể đăng ký SIP cho CCQ này

---

### UC-04: Quản lý ngày lễ

**Actor**: System Admin  
**Precondition**: None

**Flow**:

1. Truy cập Holiday Management
2. Thêm ngày lễ:
   - Ngày
   - Tên ngày lễ
   - Loại (quốc gia/tôn giáo)
3. Năm áp dụng
4. Save

**Postcondition**:

- Ngày này không có giao dịch
- Hệ thống tự động skip

---

### UC-05: Cập nhật dữ liệu ngân hàng

**Actor**: System Admin  
**Precondition**: None

**Flow**:

1. Truy cập Bank Management
2. Thêm/Sửa ngân hàng:
   - Tên ngân hàng
   - Mã viết tắt
   - SWIFT code
   - Logo
3. Thêm chi nhánh (nếu cần)
4. Save

**Postcondition**:

- Nhà đầu tư có thể chọn ngân hàng này khi thêm tài khoản

---

### UC-06: Đồng bộ dữ liệu CCQ

**Actor**: System (Cron)  
**Precondition**: Cấu hình API đồng bộ

**Flow**:

1. Cron job chạy theo lịch
2. Gọi API nguồn dữ liệu
3. So sánh với dữ liệu hiện có
4. Cập nhật thay đổi:
   - NAV mới
   - Trạng thái
   - Thông tin khác
5. Log kết quả

**Postcondition**:

- Dữ liệu CCQ được cập nhật
- Có log để audit

## Ma trận quản lý

```
┌─────────────────────────────────────────────────────────────┐
│                  Fund Management Control                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    CCQ      │  │  Scheme     │  │    Fee      │         │
│  │ Certificate │  │   Type      │  │  Schedule   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────┬───────┴────────┬───────┘                │
│                  │                │                         │
│                  ▼                ▼                         │
│         ┌─────────────┐  ┌─────────────┐                   │
│         │   Scheme    │  │    SIP      │                   │
│         │             │  │  Settings   │                   │
│         └─────────────┘  └─────────────┘                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Reference Data                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Holiday │ │  Bank   │ │ Country │ │   Tax   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```
