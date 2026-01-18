# Investor Profile Management - Use Cases

## Tổng quan

Module quản lý hồ sơ nhà đầu tư với tích hợp eKYC, cho phép nhà đầu tư tự cập nhật thông tin cá nhân và xác thực danh tính trực tuyến.

## Actors

| Actor         | Mô tả                               |
| ------------- | ----------------------------------- |
| Investor User | Nhà đầu tư đăng ký sử dụng hệ thống |
| Fund Operator | Nhân viên duyệt hồ sơ               |
| eKYC System   | Hệ thống xác thực eKYC bên thứ 3    |

## Use Cases

### UC-01: Đăng ký thông tin cá nhân

**Actor**: Investor User  
**Precondition**: Đã đăng nhập, chưa có thông tin cá nhân

**Flow**:

1. Truy cập `/my/personal-profile`
2. Upload ảnh CMND/CCCD
3. Hệ thống OCR tự động điền thông tin:
   - Họ tên
   - Số CMND/CCCD
   - Ngày sinh
   - Địa chỉ
4. Kiểm tra và chỉnh sửa nếu cần
5. Submit

**Postcondition**:

- Thông tin cá nhân được lưu
- Chuyển sang bước tiếp theo

---

### UC-02: Thêm tài khoản ngân hàng

**Actor**: Investor User  
**Precondition**: Đã hoàn thành thông tin cá nhân

**Flow**:

1. Truy cập `/my/bank-info`
2. Click "Thêm tài khoản"
3. Điền thông tin:
   - Tên ngân hàng
   - Chi nhánh
   - Số tài khoản
   - Tên chủ tài khoản
4. Submit
5. Hệ thống xác thực tài khoản

**Postcondition**:

- Tài khoản ngân hàng được thêm
- Sẵn sàng cho giao dịch

---

### UC-03: Xác thực eKYC

**Actor**: Investor User  
**Precondition**:

- Đã có thông tin cá nhân và ngân hàng
- Có CMND/CCCD và camera

**Flow**:

1. Truy cập `/my/verification`
2. Upload ảnh CMND mặt trước
3. Upload ảnh CMND mặt sau
4. Cho phép truy cập camera
5. Chụp ảnh selfie theo hướng dẫn:
   - Nhìn thẳng
   - Quay trái
   - Quay phải
6. Hệ thống gửi đến eKYC API
7. Chờ kết quả xác thực (1-2 phút)

**Postcondition**:

- **Đạt**: Tài khoản được kích hoạt đầy đủ
- **Không đạt**: Yêu cầu thực hiện lại

---

### UC-04: Cập nhật địa chỉ

**Actor**: Investor User  
**Precondition**: Đã đăng nhập

**Flow**:

1. Truy cập `/my/address-info`
2. Chọn loại địa chỉ cần cập nhật:
   - Địa chỉ thường trú
   - Địa chỉ tạm trú
   - Địa chỉ liên hệ
3. Điền thông tin:
   - Tỉnh/Thành phố
   - Quận/Huyện
   - Phường/Xã
   - Địa chỉ chi tiết
4. Save

**Postcondition**:

- Địa chỉ được cập nhật

---

### UC-05: Admin duyệt hồ sơ

**Actor**: Fund Operator  
**Precondition**:

- Có hồ sơ chờ duyệt
- eKYC đã pass

**Flow**:

1. Truy cập danh sách hồ sơ chờ duyệt
2. Xem chi tiết hồ sơ:
   - Thông tin cá nhân
   - Ảnh CMND
   - Kết quả eKYC
3. Quyết định: Duyệt hoặc Từ chối
4. Nếu Từ chối: Nhập lý do
5. Confirm

**Postcondition**:

- **Duyệt**: Nhà đầu tư có thể giao dịch
- **Từ chối**: Thông báo nhà đầu tư chỉnh sửa

## Luồng đăng ký nhà đầu tư

```
┌──────────────┐
│   Register   │
│   Account    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Personal   │◀──┐
│   Profile    │   │ OCR Auto-fill
└──────┬───────┘   │ from CMND
       │           │
       └───────────┘
       │
       ▼
┌──────────────┐
│   Bank       │
│   Account    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Address    │
│   Info       │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│    eKYC      │────▶│   Admin      │
│ Verification │     │   Review     │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│   Pending    │     │   Approved/  │
│   Status     │     │   Rejected   │
└──────────────┘     └──────────────┘
```

## eKYC Flow Detail

```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ CMND    │  │ CMND    │  │ Selfie  │  │ API     │
│ Front   │─▶│ Back    │─▶│ Camera  │─▶│ Verify  │
└─────────┘  └─────────┘  └─────────┘  └────┬────┘
                                            │
                          ┌─────────────────┤
                          │                 │
                          ▼                 ▼
                    ┌─────────┐       ┌─────────┐
                    │  PASS   │       │  FAIL   │
                    │ (Match) │       │(No Match)│
                    └─────────┘       └─────────┘
```
