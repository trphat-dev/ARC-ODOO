# Asset Management - Use Cases

## Tổng quan

Module Asset Management cung cấp giao diện xem và quản lý danh mục tài sản đầu tư.

## Actors

| Actor         | Mô tả                      |
| ------------- | -------------------------- |
| Investor User | Nhà đầu tư xem danh mục    |
| Fund Operator | Nhân viên giám sát tài sản |

## Use Cases

### UC-01: Xem danh mục đầu tư

**Actor**: Investor User  
**Precondition**: Có ít nhất 1 khoản đầu tư

**Flow**:

1. Truy cập Asset Management
2. Xem tổng quan:
   - Tổng giá trị danh mục
   - Tổng lãi/lỗ
3. Xem chi tiết từng CCQ:
   - Số unit
   - Giá mua trung bình
   - NAV hiện tại
   - Lãi/Lỗ

**Postcondition**:

- Nhà đầu tư nắm được tình hình tài sản

---

### UC-02: Xem phân bổ tài sản

**Actor**: Investor User  
**Precondition**: Có nhiều loại CCQ

**Flow**:

1. Xem biểu đồ tròn phân bổ
2. Mỗi phần thể hiện:
   - Tên CCQ
   - % giá trị trong danh mục
   - Giá trị tuyệt đối
3. Đánh giá độ đa dạng

**Postcondition**:

- Thấy được mức độ tập trung/đa dạng

---

### UC-03: Theo dõi hiệu suất

**Actor**: Investor User  
**Precondition**: Có lịch sử đầu tư

**Flow**:

1. Xem từng khoản đầu tư
2. So sánh:
   - Giá mua vs NAV hiện tại
   - % thay đổi
3. Xác định CCQ nào hiệu quả

**Postcondition**:

- Có cơ sở để quyết định mua/bán

## Asset View

```
┌─────────────────────────────────────────────────────────────┐
│                    TÀI SẢN CỦA TÔI                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────┐  ┌───────────────────────┐   │
│  │    TỔNG GIÁ TRỊ           │  │   LÃI/LỖ              │   │
│  │    150,000,000 VND        │  │   +15,000,000 VND     │   │
│  │                           │  │   (+11.1%)  🟢        │   │
│  └───────────────────────────┘  └───────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           CHI TIẾT DANH MỤC                          │   │
│  ├───────┬───────┬────────┬──────────┬─────────────────┤   │
│  │  CCQ  │ Units │ Avg Buy│ Current  │   P/L           │   │
│  ├───────┼───────┼────────┼──────────┼─────────────────┤   │
│  │ DCDS  │ 2,000 │ 23,000 │ 25,000   │ +4,000,000 🟢   │   │
│  │ DCBF  │ 1,500 │ 19,000 │ 20,000   │ +1,500,000 🟢   │   │
│  │ DCIP  │ 1,000 │ 22,000 │ 18,000   │ -4,000,000 🔴   │   │
│  └───────┴───────┴────────┴──────────┴─────────────────┘   │
│                                                             │
│  ┌─────────────────────┐                                   │
│  │   PHÂN BỔ           │                                   │
│  │   🥧 Pie Chart      │                                   │
│  │   DCDS: 50%         │                                   │
│  │   DCBF: 30%         │                                   │
│  │   DCIP: 20%         │                                   │
│  └─────────────────────┘                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
