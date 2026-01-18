# Fund Management Dashboard - Use Cases

## Tổng quan

Module Dashboard cung cấp giao diện tổng quan cho nhân viên quỹ theo dõi hoạt động giao dịch và quản lý hàng ngày.

## Actors

| Actor         | Mô tả                  |
| ------------- | ---------------------- |
| Fund Operator | Nhân viên vận hành quỹ |

## Use Cases

### UC-01: Xem tổng quan hoạt động

**Actor**: Fund Operator  
**Precondition**: Đã đăng nhập với quyền nhân viên

**Flow**:

1. Truy cập Dashboard
2. Xem các KPIs:
   - Tổng số nhà đầu tư
   - Tổng giá trị đầu tư
   - Giao dịch hôm nay
   - Lệnh chờ xử lý
3. Có thể click vào từng KPI để xem chi tiết

**Postcondition**:

- Nhân viên nắm được tình hình tổng quan

---

### UC-02: Theo dõi biến động CCQ

**Actor**: Fund Operator  
**Precondition**: Có giao dịch trong ngày

**Flow**:

1. Xem bảng biến động theo CCQ
2. Với mỗi CCQ:
   - Số lệnh mua và tổng giá trị
   - Số lệnh bán và tổng giá trị
   - Net flow
3. Click vào CCQ để xem danh sách lệnh

**Postcondition**:

- Biết được CCQ nào đang hot

---

### UC-03: Điều hướng qua Sidebar

**Actor**: Fund Operator  
**Precondition**: Đang ở bất kỳ trang nào

**Flow**:

1. Click icon menu Sidebar
2. Sidebar mở ra với các menu:
   - Dashboard
   - Giao dịch
   - NAV
   - Báo cáo
   - Nhà đầu tư
3. Click menu cần truy cập
4. Trang mới được load

**Postcondition**:

- Điều hướng nhanh giữa các chức năng

---

### UC-04: Xem biểu đồ giao dịch

**Actor**: Fund Operator  
**Precondition**: Có dữ liệu giao dịch

**Flow**:

1. Scroll đến phần biểu đồ
2. Xem biểu đồ 7 ngày gần nhất:
   - Số lệnh mua (màu xanh)
   - Số lệnh bán (màu đỏ)
   - Tổng giá trị (line chart)
3. Hover để xem chi tiết từng ngày
4. Có thể thay đổi khoảng thời gian

**Postcondition**:

- Thấy được xu hướng giao dịch

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ┌──────────┐                                               │
│  │ SIDEBAR  │    FUND MANAGEMENT DASHBOARD                  │
│  │          │                                               │
│  │ Dashboard│   ┌─────────┬─────────┬─────────┬─────────┐   │
│  │ Giao dịch│   │  Total  │  Total  │ Today's │ Pending │   │
│  │ NAV      │   │Investors│  AUM    │ Orders  │ Orders  │   │
│  │ Báo cáo  │   │  1,234  │ 50.5B   │   45    │   12    │   │
│  │ NĐT      │   └─────────┴─────────┴─────────┴─────────┘   │
│  │          │                                               │
│  │          │   ┌─────────────────────────────────────────┐ │
│  │          │   │         CCQ MOVEMENTS TODAY             │ │
│  │          │   ├─────────┬─────────┬─────────┬───────────┤ │
│  │          │   │   CCQ   │   BUY   │  SELL   │  NET FLOW │ │
│  │          │   ├─────────┼─────────┼─────────┼───────────┤ │
│  │          │   │ DCDS    │ 10/5B   │ 3/1.2B  │   +3.8B   │ │
│  │          │   │ DCBF    │ 8/3B    │ 5/2B    │   +1B     │ │
│  │          │   │ DCIP    │ 5/2B    │ 8/3B    │   -1B     │ │
│  │          │   └─────────┴─────────┴─────────┴───────────┘ │
│  │          │                                               │
│  │          │   ┌─────────────────────────────────────────┐ │
│  │          │   │         7-DAY TRANSACTION CHART         │ │
│  │          │   │    📊 Bar/Line Chart                    │ │
│  │          │   │                                         │ │
│  │          │   └─────────────────────────────────────────┘ │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────┘
```
