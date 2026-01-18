# Stock Trading - Use Cases

## Tổng quan

Module Stock Trading tích hợp SSI FastConnect Trading API để thực hiện các giao dịch chứng khoán trực tiếp từ hệ thống.

## Actors

| Actor   | Mô tả                       |
| ------- | --------------------------- |
| Trader  | Người giao dịch chứng khoán |
| System  | Hệ thống tự động            |
| SSI API | Dịch vụ SSI FastConnect     |

## Use Cases

### UC-01: Đặt lệnh mua cổ phiếu

**Actor**: Trader  
**Precondition**: Có đủ tiền trong tài khoản

**Flow**:

1. Truy cập Trading Portal
2. Chọn mã cổ phiếu
3. Chọn loại lệnh (LO/MP/ATO/ATC)
4. Nhập giá (nếu LO)
5. Nhập khối lượng
6. Click "Đặt mua"
7. Xác nhận lệnh
8. Hệ thống gửi lệnh đến SSI

**Postcondition**:

- Lệnh được gửi đến sàn
- Trạng thái: Chờ khớp

---

### UC-02: Hủy lệnh

**Actor**: Trader  
**Precondition**: Lệnh chưa được khớp hoàn toàn

**Flow**:

1. Vào danh sách lệnh
2. Chọn lệnh cần hủy
3. Click "Hủy lệnh"
4. Xác nhận
5. Hệ thống gửi yêu cầu hủy đến SSI

**Postcondition**:

- Lệnh bị hủy
- Tiền/CP được giải phóng

---

### UC-03: Xem số dư tài khoản

**Actor**: Trader  
**Precondition**: Đã cấu hình API

**Flow**:

1. Truy cập Account Info
2. Hệ thống gọi SSI API lấy số dư
3. Hiển thị:
   - Tiền mặt: Available/Pending
   - Tài sản: Stock value
   - NAV: Tổng tài sản ròng
   - Margin: Tỷ lệ ký quỹ

**Postcondition**:

- Thông tin tài khoản được hiển thị

---

### UC-04: Rút tiền

**Actor**: Trader  
**Precondition**: Có tiền khả dụng

**Flow**:

1. Vào Cash Management
2. Chọn "Rút tiền"
3. Nhập số tiền
4. Chọn tài khoản ngân hàng
5. Xác nhận
6. Hệ thống gửi yêu cầu rút tiền

**Postcondition**:

- Yêu cầu rút tiền được tạo
- Chờ xử lý T+1

---

### UC-05: Sync trạng thái lệnh

**Actor**: System (Cron)  
**Precondition**: Có lệnh đang chờ

**Flow**:

1. Cron chạy mỗi 30 giây
2. Lấy danh sách lệnh pending
3. Gọi SSI API kiểm tra trạng thái
4. Cập nhật database:
   - Khớp một phần
   - Khớp hoàn toàn
   - Bị hủy

**Postcondition**:

- Trạng thái lệnh cập nhật

## Luồng đặt lệnh

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Input  │──▶│ Validate│──▶│  Send   │──▶│   SSI   │
│  Order  │   │  Order  │   │ to API  │   │  Server │
└─────────┘   └─────────┘   └─────────┘   └────┬────┘
                                               │
    ┌──────────────────────────────────────────┘
    │
    ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Pending │──▶│ Matched │──▶│ Settled │
│         │   │(Partial)│   │  (T+2)  │
└─────────┘   └─────────┘   └─────────┘
    │
    ▼
┌─────────┐
│Cancelled│
└─────────┘
```

## Order Types

```
┌────────────────────────────────────────────┐
│           ORDER TYPES                       │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────┐    ┌──────────────┐     │
│  │      LO      │    │      MP      │     │
│  │ Limit Order  │    │Market Price  │     │
│  │ Chỉ định giá │    │ Giá thị trường│     │
│  └──────────────┘    └──────────────┘     │
│                                            │
│  ┌──────────────┐    ┌──────────────┐     │
│  │     ATO      │    │     ATC      │     │
│  │  At Open     │    │  At Close    │     │
│  │  Giá mở cửa  │    │ Giá đóng cửa │     │
│  └──────────────┘    └──────────────┘     │
│                                            │
└────────────────────────────────────────────┘
```
