# Transaction List - Use Cases

## Tổng quan

Module Transaction List cung cấp giao diện quản lý và theo dõi tất cả lệnh giao dịch trong hệ thống.

## Actors

| Actor         | Mô tả                        |
| ------------- | ---------------------------- |
| Fund Operator | Nhân viên giám sát giao dịch |
| Investor      | Nhà đầu tư xem lệnh của mình |

## Use Cases

### UC-01: Xem lệnh chờ xử lý

**Actor**: Fund Operator  
**Precondition**: Có lệnh pending trong hệ thống

**Flow**:

1. Truy cập Transaction List
2. Chọn Tab "Pending"
3. Xem danh sách lệnh chờ:
   - Mã lệnh
   - Nhà đầu tư
   - Loại (Buy/Sell)
   - CCQ
   - Số tiền/Unit
   - Thời gian
4. Click để xem chi tiết

**Postcondition**:

- Thấy được các lệnh cần xử lý

---

### UC-02: Xem lệnh đã xử lý

**Actor**: Fund Operator  
**Precondition**: Có lệnh đã hoàn thành

**Flow**:

1. Chọn Tab "Approved"
2. Xem danh sách lệnh đã xử lý
3. Thông tin thêm:
   - Matched Units
   - Match Price
   - Match Time
4. Filter theo ngày, CCQ, trạng thái

**Postcondition**:

- Thấy được lịch sử giao dịch

---

### UC-03: Tìm kiếm giao dịch

**Actor**: Fund Operator  
**Precondition**: Cần tìm giao dịch cụ thể

**Flow**:

1. Nhập từ khóa vào ô Search
2. Tìm theo:
   - Mã lệnh
   - Tên nhà đầu tư
   - Mã CCQ
3. Kết quả được filter realtime

**Postcondition**:

- Tìm được giao dịch cần thiết

---

### UC-04: Xuất danh sách giao dịch

**Actor**: Fund Operator  
**Precondition**: Cần báo cáo

**Flow**:

1. Chọn tab và filter phù hợp
2. Click "Export"
3. Chọn định dạng (Excel/CSV)
4. File được tải về

**Postcondition**:

- Có file báo cáo giao dịch

## Transaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   TRANSACTION FLOW                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │  New    │──▶│ Pending │──▶│Matching │──▶│ Matched │     │
│  │  Order  │   │         │   │         │   │         │     │
│  └─────────┘   └────┬────┘   └─────────┘   └─────────┘     │
│                     │                                       │
│                     ▼                                       │
│               ┌─────────┐                                   │
│               │Cancelled│                                   │
│               └─────────┘                                   │
│                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                             │
│  TAB: PENDING              TAB: APPROVED                    │
│  ┌──────────────────┐     ┌──────────────────┐             │
│  │ • New Orders     │     │ • Matched Orders │             │
│  │ • Processing     │     │ • Cancelled      │             │
│  └──────────────────┘     └──────────────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
