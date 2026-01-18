# PayOS Gateway - Use Cases

## Tổng quan

Module PayOS Gateway xử lý thanh toán online cho các giao dịch mua CCQ thông qua cổng PayOS.

## Actors

| Actor         | Mô tả                 |
| ------------- | --------------------- |
| Investor User | Nhà đầu tư thanh toán |
| System        | Xử lý webhook         |
| System Admin  | Cấu hình PayOS        |

## Use Cases

### UC-01: Cấu hình PayOS

**Actor**: System Admin  
**Precondition**: Có tài khoản PayOS

**Flow**:

1. Đăng nhập PayOS Dashboard
2. Lấy credentials:
   - Client ID
   - API Key
   - Checksum Key
3. Trong Odoo, vào PayOS → Config
4. Nhập credentials
5. Chọn môi trường
6. Test connection
7. Save

**Postcondition**:

- PayOS sẵn sàng sử dụng

---

### UC-02: Thanh toán mua CCQ

**Actor**: Investor User  
**Precondition**: Đã đặt lệnh mua

**Flow**:

1. Nhà đầu tư hoàn tất form mua CCQ
2. Chọn phương thức: Thanh toán online
3. Hệ thống tạo payment link từ PayOS
4. Redirect đến trang thanh toán PayOS
5. Nhà đầu tư chọn ngân hàng
6. Thực hiện thanh toán
7. PayOS callback về Odoo
8. Odoo xử lý và confirm order

**Postcondition**:

- **Thành công**: Lệnh mua được xử lý
- **Thất bại**: Lệnh bị hủy, thông báo lỗi

---

### UC-03: Xử lý Webhook

**Actor**: System  
**Precondition**: Nhận callback từ PayOS

**Flow**:

1. PayOS gọi webhook endpoint
2. System nhận request
3. Verify signature:
   - Lấy data từ request
   - Tính HMAC-SHA256 với Checksum Key
   - So sánh với signature
4. Nếu valid:
   - Parse transaction data
   - Cập nhật order status
   - Trigger next actions
5. Response 200 OK

**Postcondition**:

- Giao dịch được ghi nhận
- Order được xử lý tương ứng

---

### UC-04: Kiểm tra trạng thái thanh toán

**Actor**: System  
**Precondition**: Có orderCode cần kiểm tra

**Flow**:

1. Gọi API PayOS check status
2. Trả về trạng thái:
   - PENDING
   - PAID
   - CANCELLED
   - EXPIRED
3. Cập nhật database

**Postcondition**:

- Có trạng thái mới nhất

## Payment Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    PAYMENT FLOW                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐       │
│  │  User  │───▶│ Create │───▶│ PayOS  │───▶│  Bank  │       │
│  │ Order  │    │  Link  │    │Checkout│    │ Payment│       │
│  └────────┘    └────────┘    └────────┘    └───┬────┘       │
│                                                │             │
│       ┌────────────────────────────────────────┘             │
│       │                                                      │
│       ▼                                                      │
│  ┌────────┐    ┌────────┐    ┌────────┐                     │
│  │ PayOS  │───▶│ Verify │───▶│ Update │                     │
│  │Webhook │    │  Sig   │    │ Order  │                     │
│  └────────┘    └────────┘    └────────┘                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Payment Statuses

```
┌────────────────────────────────────────────┐
│            PAYMENT STATUSES                │
├──────────┬─────────────────────────────────┤
│ PENDING  │ Chờ thanh toán                  │
├──────────┼─────────────────────────────────┤
│ PAID     │ Đã thanh toán thành công        │
├──────────┼─────────────────────────────────┤
│CANCELLED │ Người dùng hủy                  │
├──────────┼─────────────────────────────────┤
│ EXPIRED  │ Hết thời gian thanh toán        │
└──────────┴─────────────────────────────────┘
```
