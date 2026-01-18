# Transaction Management - Use Cases

## Tổng quan

Module Transaction Management cung cấp các trang quản lý giao dịch cho nhân viên quỹ.

## Actors

| Actor         | Mô tả                     |
| ------------- | ------------------------- |
| Fund Operator | Nhân viên xử lý giao dịch |
| System        | Tự động xử lý SIP         |

## Use Cases

### UC-01: Duyệt giao dịch pending

**Actor**: Fund Operator  
**Precondition**: Có giao dịch chờ duyệt

**Flow**:

1. Truy cập Pending page
2. Xem danh sách giao dịch chờ
3. Chọn giao dịch cần duyệt
4. Kiểm tra thông tin:
   - Nhà đầu tư đã eKYC
   - Số dư đủ (với lệnh mua)
   - CCQ đủ (với lệnh bán)
5. Click "Duyệt" hoặc "Từ chối"
6. Nếu từ chối: Nhập lý do

**Postcondition**:

- Giao dịch được duyệt → chuyển khớp lệnh
- Giao dịch bị từ chối → thông báo nhà đầu tư

---

### UC-02: Xem lịch sử giao dịch

**Actor**: Fund Operator  
**Precondition**: Có giao dịch đã hoàn thành

**Flow**:

1. Truy cập Order History page
2. Filter theo:
   - Khoảng thời gian
   - Loại giao dịch
   - Trạng thái
   - CCQ
3. Xem danh sách kết quả
4. Click để xem chi tiết từng giao dịch

**Postcondition**:

- Có thông tin lịch sử giao dịch

---

### UC-03: Quản lý SIP

**Actor**: Fund Operator  
**Precondition**: Có SIP đang active

**Flow**:

1. Truy cập Periodic page
2. Xem danh sách SIP:
   - Nhà đầu tư
   - CCQ
   - Số tiền định kỳ
   - Ngày trích
   - Trạng thái
3. Có thể:
   - Xem lịch sử trích
   - Tạm dừng SIP
   - Hủy SIP

**Postcondition**:

- SIP được quản lý theo yêu cầu

---

### UC-04: Tự động xử lý SIP

**Actor**: System  
**Precondition**: Đến ngày trích SIP

**Flow**:

1. System check danh sách SIP đến hạn
2. Với mỗi SIP:
   - Kiểm tra số dư
   - Nếu đủ → Tạo lệnh mua
   - Nếu không đủ → Log và thông báo
3. Gửi thông báo cho nhà đầu tư

**Postcondition**:

- Lệnh mua được tạo tự động
- Nhà đầu tư nhận thông báo

## Transaction Statuses

```
┌────────────────────────────────────────────────────────────┐
│                 TRANSACTION STATUSES                        │
├──────────────┬─────────────────────────────────────────────┤
│   PENDING    │ Chờ duyệt, chưa được xử lý                  │
├──────────────┼─────────────────────────────────────────────┤
│  PROCESSING  │ Đang xử lý, chờ khớp lệnh                   │
├──────────────┼─────────────────────────────────────────────┤
│   MATCHED    │ Đã khớp hoàn toàn                           │
├──────────────┼─────────────────────────────────────────────┤
│   PARTIAL    │ Đã khớp một phần                            │
├──────────────┼─────────────────────────────────────────────┤
│  CANCELLED   │ Đã hủy                                      │
├──────────────┼─────────────────────────────────────────────┤
│   REJECTED   │ Bị từ chối                                  │
└──────────────┴─────────────────────────────────────────────┘
```
