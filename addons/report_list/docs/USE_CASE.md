# Report List - Use Cases

## Tổng quan

Module Report List cung cấp 12 loại báo cáo phục vụ cho việc quản lý và giám sát hoạt động quỹ.

## Actors

| Actor         | Mô tả                    |
| ------------- | ------------------------ |
| Fund Operator | Nhân viên xuất báo cáo   |
| System Admin  | Quản lý cấu hình báo cáo |
| Auditor       | Kiểm toán xem báo cáo    |

## Use Cases

### UC-01: Xuất báo cáo số dư

**Actor**: Fund Operator  
**Precondition**: Có dữ liệu trong hệ thống

**Flow**:

1. Truy cập Balance Report
2. Chọn ngày/khoảng thời gian
3. Chọn CCQ (hoặc tất cả)
4. Click "Xem báo cáo"
5. Preview trên màn hình
6. Click "Export PDF" để tải về

**Postcondition**:

- Có file PDF báo cáo số dư

---

### UC-02: Xuất báo cáo giao dịch

**Actor**: Fund Operator  
**Precondition**: Có giao dịch trong khoảng thời gian

**Flow**:

1. Truy cập Transaction Report
2. Chọn khoảng thời gian
3. Filter:
   - Loại giao dịch (Buy/Sell/All)
   - CCQ
   - Trạng thái
4. Xem kết quả
5. Export PDF/Excel

**Postcondition**:

- Có báo cáo giao dịch theo yêu cầu

---

### UC-03: Báo cáo thống kê hợp đồng

**Actor**: Auditor  
**Precondition**: Cần thống kê cho kiểm toán

**Flow**:

1. Truy cập Contract Statistics
2. Chọn kỳ báo cáo (tháng/quý/năm)
3. Xem thống kê:
   - Số hợp đồng mới
   - Giá trị theo loại
   - Tỷ lệ đáo hạn/bán sớm
4. Export báo cáo

**Postcondition**:

- Có số liệu thống kê cho kiểm toán

---

### UC-04: Báo cáo nhà đầu tư

**Actor**: Fund Operator  
**Precondition**: Cần danh sách nhà đầu tư

**Flow**:

1. Truy cập Investor Report
2. Filter:
   - Trạng thái eKYC
   - Ngày đăng ký
   - Có/không có giao dịch
3. Xem danh sách
4. Export

**Postcondition**:

- Có danh sách nhà đầu tư theo tiêu chí

## Report Categories

```
┌─────────────────────────────────────────────────────────────┐
│                     REPORT CATEGORIES                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐         │
│  │   FINANCIAL         │  │   OPERATIONAL       │         │
│  ├─────────────────────┤  ├─────────────────────┤         │
│  │ • Balance Report    │  │ • Transaction Report│         │
│  │ • Purchase Contract │  │ • Order History     │         │
│  │ • Sell Contract     │  │ • Early Sale        │         │
│  │ • Tenors/Rates      │  │ • Contract Summary  │         │
│  └─────────────────────┘  └─────────────────────┘         │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐         │
│  │   INVESTOR          │  │   ADMINISTRATIVE    │         │
│  ├─────────────────────┤  ├─────────────────────┤         │
│  │ • Investor Report   │  │ • User List Report  │         │
│  │ • AOC Report        │  │ • Contract Stats    │         │
│  └─────────────────────┘  └─────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
