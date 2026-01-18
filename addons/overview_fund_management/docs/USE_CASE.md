# Overview Fund Management - Use Cases

## Tổng quan

Module cung cấp trang tổng quan danh mục đầu tư cho nhà đầu tư, giúp họ theo dõi hiệu suất và giá trị các khoản đầu tư.

## Actors

| Actor         | Mô tả                     |
| ------------- | ------------------------- |
| Investor User | Nhà đầu tư đã có danh mục |

## Use Cases

### UC-01: Xem tổng quan danh mục

**Actor**: Investor User  
**Precondition**: Đã đăng nhập, có ít nhất 1 CCQ

**Flow**:

1. Truy cập `/my/overview`
2. Xem thông tin tổng quan:
   - Tổng giá trị danh mục
   - Tổng lợi nhuận (VND và %)
   - Số loại CCQ đang nắm giữ
3. Xem chi tiết từng CCQ trong danh mục

**Postcondition**:

- Nhà đầu tư biết được tình hình đầu tư

---

### UC-02: Xem phân bổ danh mục

**Actor**: Investor User  
**Precondition**: Có nhiều hơn 1 CCQ

**Flow**:

1. Xem biểu đồ tròn phân bổ
2. Mỗi phần thể hiện:
   - Tên CCQ
   - % giá trị trong danh mục
3. Hover để xem số liệu cụ thể

**Postcondition**:

- Thấy được danh mục đang đa dạng hay tập trung

---

### UC-03: Theo dõi lợi nhuận/lỗ

**Actor**: Investor User  
**Precondition**: Có giao dịch lịch sử

**Flow**:

1. Xem bảng chi tiết CCQ
2. Với mỗi CCQ:
   - Số unit nắm giữ
   - Giá mua trung bình
   - NAV hiện tại
   - Lợi nhuận = (NAV hiện tại - Giá mua) × Số unit
   - % thay đổi
3. Màu xanh = Lãi, Màu đỏ = Lỗ

**Postcondition**:

- Biết CCQ nào đang lãi/lỗ

---

### UC-04: Điều hướng đến giao dịch

**Actor**: Investor User  
**Precondition**: Đang ở trang Overview

**Flow**:

1. Click vào CCQ cần giao dịch
2. Hoặc click nút "Mua thêm" / "Bán"
3. Chuyển đến trang giao dịch tương ứng

**Postcondition**:

- Chuyển đến trang mua/bán CCQ

## Overview UI

```
┌─────────────────────────────────────────────────────────────┐
│                      📊 TỔNG QUAN ĐẦU TƯ                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   TỔNG GIÁ TRỊ  │  │   TỔNG LỢI NHUẬN │                  │
│  │                 │  │                  │                  │
│  │   50,500,000    │  │  +5,500,000      │                  │
│  │      VND        │  │   (+12.2%)  🟢   │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CHI TIẾT DANH MỤC                       │   │
│  ├──────────┬────────┬────────┬──────────┬─────────────┤   │
│  │   CCQ    │  Units │   NAV  │ Giá trị  │  Lợi nhuận  │   │
│  ├──────────┼────────┼────────┼──────────┼─────────────┤   │
│  │  DCDS    │ 1,000  │ 25,000 │ 25,000,000│ +2,500,000 🟢│   │
│  │  DCBF    │   800  │ 20,000 │ 16,000,000│ +1,500,000 🟢│   │
│  │  DCIP    │   500  │ 19,000 │  9,500,000│ +1,500,000 🟢│   │
│  └──────────┴────────┴────────┴──────────┴─────────────┘   │
│                                                             │
│  ┌────────────────────────┐                                │
│  │   PHÂN BỔ DANH MỤC     │                                │
│  │                        │                                │
│  │      🥧 Pie Chart      │                                │
│  │   DCDS: 49.5%          │                                │
│  │   DCBF: 31.7%          │                                │
│  │   DCIP: 18.8%          │                                │
│  │                        │                                │
│  └────────────────────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
