# Order Matching - Use Cases

## Tổng quan

Module Order Matching thực hiện khớp lệnh tự động giữa lệnh mua và lệnh bán theo thuật toán Price-Time Priority.

## Actors

| Actor         | Mô tả                 |
| ------------- | --------------------- |
| Investor User | Đặt lệnh mua/bán      |
| Market Maker  | Đặt lệnh đối ứng      |
| Fund Operator | Giám sát và can thiệp |
| System        | Khớp lệnh tự động     |

## Use Cases

### UC-01: Khớp lệnh tự động

**Actor**: System  
**Precondition**: Có lệnh mua và lệnh bán thỏa điều kiện

**Flow**:

1. Auto Match Worker chạy mỗi 1 giây
2. Lấy lệnh mua giá cao nhất
3. Lấy lệnh bán giá thấp nhất
4. Nếu giá mua >= giá bán:
   - Tính khối lượng khớp = min(buy_qty, sell_qty)
   - Tạo Matched Order record
   - Cập nhật trạng thái lệnh
5. Tiếp tục với lệnh tiếp theo

**Postcondition**:

- Lệnh được khớp
- Thông báo đến investor

---

### UC-02: Xem sổ lệnh

**Actor**: Fund Operator  
**Precondition**: Có lệnh trong hệ thống

**Flow**:

1. Truy cập Order Book
2. Xem lệnh mua (sorted by price DESC)
3. Xem lệnh bán (sorted by price ASC)
4. Có thể filter theo CCQ, thời gian
5. Click vào lệnh để xem chi tiết

**Postcondition**:

- Thấy được tình hình sổ lệnh

---

### UC-03: Xử lý thông báo đáo hạn

**Actor**: Investor User  
**Precondition**: CCQ sắp đáo hạn

**Flow**:

1. Nhận thông báo email/SMS
2. Click link trong thông báo
3. Xem chi tiết CCQ đáo hạn:
   - Số unit
   - Giá trị ước tính
   - Ngày đáo hạn
4. Chọn action:
   - Tái đầu tư
   - Rút tiền về tài khoản
5. Xác nhận

**Postcondition**:

- Lựa chọn được ghi nhận
- Hệ thống xử lý vào ngày đáo hạn

---

### UC-04: Xem lệnh đã khớp

**Actor**: Fund Operator  
**Precondition**: Có lệnh đã khớp

**Flow**:

1. Truy cập Matched Orders
2. Xem danh sách cặp lệnh:
   - Buy Order ID
   - Sell Order ID
   - Matched Price
   - Matched Units
   - Matched Time
3. Export nếu cần

**Postcondition**:

- Thông tin khớp lệnh được xem

---

### UC-05: Hủy lệnh chưa khớp

**Actor**: Fund Operator  
**Precondition**: Lệnh chưa khớp hoàn toàn

**Flow**:

1. Tìm lệnh trong Order Book
2. Click "Hủy lệnh"
3. Nhập lý do
4. Xác nhận
5. Hệ thống giải phóng tiền/CCQ

**Postcondition**:

- Lệnh bị hủy
- Tài sản được giải phóng

## Matching Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│              ORDER MATCHING ALGORITHM                        │
│                (Price-Time Priority)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ BUY ORDERS (Price DESC)        SELL ORDERS (Price ASC)     │
│ ┌─────────────────────┐       ┌─────────────────────┐      │
│ │ ① 25,500 x 100     │       │ ① 25,300 x 80      │      │
│ │ ② 25,400 x 50      │ ←───→ │ ② 25,400 x 120     │      │
│ │ ③ 25,300 x 200     │       │ ③ 25,500 x 50      │      │
│ └─────────────────────┘       └─────────────────────┘      │
│                                                             │
│ MATCHING RULES:                                             │
│ 1. Buy Price >= Sell Price → MATCH                         │
│ 2. Match Price = Sell Price (bên đến sau)                  │
│ 3. Match Qty = MIN(buy_qty, sell_qty)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Maturity Notification Flow

```
┌────────────┐   ┌────────────┐   ┌────────────┐
│  7 days    │──▶│   Send     │──▶│  Investor  │
│  before    │   │  Notif     │   │  Response  │
│  maturity  │   │            │   │            │
└────────────┘   └────────────┘   └─────┬──────┘
                                        │
                      ┌─────────────────┤
                      │                 │
                      ▼                 ▼
               ┌────────────┐   ┌────────────┐
               │ Reinvest   │   │  Withdraw  │
               │ (Auto Buy) │   │  (Cash Out)│
               └────────────┘   └────────────┘
```
