# Fund Management - Use Cases

## Tổng quan

Module Fund Management cung cấp các chức năng chính để nhà đầu tư có thể mua/bán chứng chỉ quỹ (CCQ) một cách an toàn và tiện lợi.

## Actors

| Actor         | Mô tả                       |
| ------------- | --------------------------- |
| Investor User | Nhà đầu tư đã xác thực eKYC |
| Fund Operator | Nhân viên xử lý giao dịch   |
| Market Maker  | Đối tác tạo lập thị trường  |
| System        | Hệ thống tự động            |

## Use Cases

### UC-01: Mua chứng chỉ quỹ

**Actor**: Investor User  
**Precondition**:

- Đã xác thực eKYC
- Có số dư trong tài khoản

**Flow**:

1. Truy cập danh sách quỹ `/fund`
2. Chọn quỹ muốn mua
3. Click "Mua"
4. Nhập số tiền đầu tư
5. Hệ thống tính toán:
   - Phí mua
   - Số unit ước tính
   - Tổng tiền thanh toán
6. Xem và đồng ý điều khoản
7. Ký hợp đồng số (vẽ chữ ký)
8. Nhập OTP xác thực
9. Xác nhận giao dịch

**Postcondition**:

- Lệnh mua được tạo với trạng thái "Chờ khớp"
- Số dư bị trừ

---

### UC-02: Bán chứng chỉ quỹ

**Actor**: Investor User  
**Precondition**:

- Đã có CCQ của quỹ
- CCQ không bị khóa

**Flow**:

1. Vào danh mục đầu tư
2. Chọn quỹ muốn bán
3. Click "Bán"
4. Nhập số unit cần bán (hoặc % danh mục)
5. Xem giá trị ước tính và phí
6. Nhập OTP xác thực
7. Xác nhận giao dịch

**Postcondition**:

- Lệnh bán được tạo
- CCQ bị khóa chờ khớp

---

### UC-03: So sánh hiệu suất quỹ

**Actor**: Investor User  
**Precondition**: Đang ở trang quỹ

**Flow**:

1. Click "So sánh quỹ"
2. Chọn 2-4 quỹ để so sánh
3. Hệ thống hiển thị:
   - Biểu đồ NAV theo thời gian
   - Lợi nhuận 1M/3M/6M/1Y
   - Độ biến động
   - Phí quản lý
4. Có thể thay đổi khoảng thời gian

**Postcondition**:

- Nhà đầu tư có thông tin để quyết định

---

### UC-04: Xem số dư tài khoản

**Actor**: Investor User  
**Precondition**: Đã đăng nhập

**Flow**:

1. Truy cập `/my/account-balance`
2. Xem thông tin:
   - Số dư khả dụng
   - Số dư đang chờ xử lý
   - Tổng giá trị đầu tư
3. Xem lịch sử số dư

**Postcondition**:

- Nhà đầu tư biết được số dư hiện tại

---

### UC-05: Ký hợp đồng số

**Actor**: Investor User  
**Precondition**: Đang trong quá trình mua quỹ

**Flow**:

1. Hệ thống hiển thị modal chữ ký
2. Nhà đầu tư vẽ chữ ký bằng chuột/touch
3. Có thể Clear và vẽ lại
4. Click "Xác nhận"
5. Chữ ký được lưu và gắn vào hợp đồng

**Postcondition**:

- Hợp đồng được ký số
- Có giá trị pháp lý

---

### UC-06: Xác thực Smart OTP

**Actor**: Investor User  
**Precondition**: Cần xác thực giao dịch

**Flow**:

1. Hệ thống gửi OTP qua SMS/Email
2. Nhà đầu tư nhập 6 chữ số OTP
3. Click "Xác nhận"
4. Hệ thống kiểm tra OTP
5. Nếu sai: Cho phép thử lại (tối đa 3 lần)

**Postcondition**:

- **Đúng**: Giao dịch được thực hiện
- **Sai 3 lần**: Giao dịch bị hủy

## Luồng mua quỹ

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Chọn   │──▶│  Nhập   │──▶│  Xem    │──▶│  Đồng ý │
│  Quỹ    │   │ Số tiền │   │  Phí    │   │ Điều khoản│
└─────────┘   └─────────┘   └─────────┘   └────┬────┘
                                               │
              ┌─────────┐   ┌─────────┐        │
              │  Hoàn   │◀──│   OTP   │◀───────┘
              │  Tất    │   │  Verify │
              └─────────┘   └─────────┘
                   │
                   ▼
              ┌─────────────────┐
              │  Chờ khớp lệnh  │
              │  (Next session) │
              └─────────────────┘
```

## Luồng bán quỹ

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Chọn   │──▶│  Nhập   │──▶│  Xem    │──▶│   OTP   │
│   CCQ   │   │  Units  │   │ Ước tính│   │  Verify │
└─────────┘   └─────────┘   └─────────┘   └────┬────┘
                                               │
                                               ▼
                                         ┌─────────┐
                                         │  Hoàn   │
                                         │  Tất    │
                                         └────┬────┘
                                               │
                                               ▼
                                    ┌─────────────────┐
                                    │  CCQ bị khóa    │
                                    │  Chờ khớp lệnh  │
                                    └─────────────────┘
```
