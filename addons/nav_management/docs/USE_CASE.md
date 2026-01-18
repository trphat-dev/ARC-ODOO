# NAV Management - Use Cases

## Tổng quan

Module NAV Management quản lý giá trị tài sản ròng (NAV) của các quỹ, phục vụ cho việc tính toán giá trị đầu tư và khớp lệnh.

## Actors

| Actor         | Mô tả                           |
| ------------- | ------------------------------- |
| System Admin  | Cấu hình NAV, Term Rate, Cap    |
| Fund Operator | Cập nhật và giám sát NAV        |
| System        | Tự động tính toán NAV hàng ngày |

## Use Cases

### UC-01: Xem NAV phiên giao dịch

**Actor**: Fund Operator  
**Precondition**: Có dữ liệu NAV

**Flow**:

1. Truy cập NAV Management → NAV Transaction
2. Chọn Quỹ cần xem
3. Chọn khoảng thời gian
4. Xem danh sách NAV theo phiên:
   - Ngày giao dịch
   - NAV đầu phiên
   - NAV cuối phiên
   - % thay đổi
5. Có thể xuất Excel/CSV

**Postcondition**:

- Thấy được diễn biến NAV của quỹ

---

### UC-02: Thêm NAV tháng

**Actor**: Fund Operator  
**Precondition**: Kết thúc tháng

**Flow**:

1. Truy cập NAV Monthly
2. Click "Thêm mới"
3. Nhập thông tin:
   - Quỹ
   - Tháng/Năm
   - NAV cuối tháng
   - Số CCQ lưu hành
4. Save

**Postcondition**:

- NAV tháng được lưu
- Dùng cho báo cáo

---

### UC-03: Cấu hình Kỳ hạn / Lãi suất

**Actor**: System Admin  
**Precondition**: Có CCQ cần cấu hình

**Flow**:

1. Truy cập Term Rate
2. Click "Thêm mới"
3. Nhập:
   - Quỹ
   - Kỳ hạn (tháng)
   - Lãi suất (%/năm)
   - Ngày hiệu lực
4. Save

**Postcondition**:

- Kỳ hạn được áp dụng cho giao dịch mới

---

### UC-04: Cấu hình NAV Cap

**Actor**: System Admin  
**Precondition**: Cần kiểm soát biến động

**Flow**:

1. Truy cập CAP Config
2. Thêm/Sửa cấu hình:
   - Quỹ
   - Cap trên: +X%
   - Cap dưới: -Y%
3. Save

**Postcondition**:

- NAV không vượt quá cap khi cập nhật

---

### UC-05: Tự động tạo tồn kho hàng ngày

**Actor**: System (Cron)  
**Precondition**: Ngày giao dịch mới

**Flow**:

1. Cron chạy đầu mỗi ngày làm việc
2. Lấy danh sách CCQ active
3. Tính tồn kho:
   - Tồn ngày hôm trước
   - - Mua đã khớp
   - - Bán đã khớp
4. Tạo record Daily Inventory

**Postcondition**:

- Có dữ liệu tồn kho cho ngày mới

## NAV Calculation

```
┌─────────────────────────────────────────────────────────────┐
│                   NAV CALCULATION                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              Total Assets - Total Liabilities               │
│   NAV  =  ─────────────────────────────────────            │
│                 Number of Units Outstanding                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Daily Inventory Flow

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Previous   │ + │   Matched   │ - │   Matched   │
│  Inventory  │   │   Buy Orders│   │  Sell Orders│
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────────┬┴─────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ Today Inventory │
               └─────────────────┘
```
