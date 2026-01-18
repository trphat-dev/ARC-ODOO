# Investor Profile Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**Investor Profile Management** là module quản lý hồ sơ nhà đầu tư toàn diện với tích hợp eKYC. Module cung cấp:

- Quản lý thông tin cá nhân với OCR auto-fill
- Quản lý tài khoản ngân hàng
- Quản lý địa chỉ
- Xác thực eKYC với nhận diện khuôn mặt
- Giao diện Premium với animations và responsive design

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `portal`, `web`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Investor Profile Management" → Install
```

## Cấu hình

### Cấu hình eKYC API

1. Truy cập **Settings → eKYC API Config**
2. Điền thông tin API:
   - API Endpoint
   - API Key
   - Secret Key
3. Test kết nối
4. Save

## Hướng dẫn sử dụng

### 1. Thông tin cá nhân (Personal Profile)

**URL**: `/my/personal-profile`

| Thông tin     | Mô tả                 |
| ------------- | --------------------- |
| Họ tên        | Họ và tên đầy đủ      |
| CMND/CCCD     | Số giấy tờ tùy thân   |
| Ngày sinh     | Ngày tháng năm sinh   |
| Giới tính     | Nam/Nữ                |
| Quốc tịch     | Quốc gia              |
| Số điện thoại | Số điện thoại liên hệ |
| Email         | Email chính           |

**OCR Auto-fill**: Upload ảnh CMND/CCCD để tự động điền thông tin.

### 2. Thông tin ngân hàng (Bank Info)

**URL**: `/my/bank-info`

- Thêm/sửa/xóa tài khoản ngân hàng
- Chọn tài khoản mặc định
- Xác thực tài khoản

### 3. Thông tin địa chỉ (Address Info)

**URL**: `/my/address-info`

- Địa chỉ thường trú
- Địa chỉ tạm trú
- Địa chỉ liên hệ

### 4. Xác thực eKYC (Verification)

**URL**: `/my/verification`

**Quy trình**:

1. Upload ảnh CMND/CCCD mặt trước
2. Upload ảnh CMND/CCCD mặt sau
3. Chụp ảnh selfie (nhận diện khuôn mặt)
4. Hệ thống so sánh và xác thực
5. Kết quả: Đạt/Không đạt

## Cấu trúc Views

```
views/
├── personal_profile/
│   └── personal_profile_page.xml
├── bank_info/
│   └── bank_info_page.xml
├── address_info/
│   └── address_info_page.xml
├── verification/
│   ├── verification_page.xml
│   └── ekyc_verification_page.xml
└── [Backend views]
```

## Backend Management

- **eKYC Records**: Xem lịch sử xác thực eKYC
- **API Records**: Log các API calls
- **Partner Profiles**: Quản lý hồ sơ nhà đầu tư
- **Status Info**: Trạng thái xác thực

## Lưu ý

- eKYC có thể mất 1-2 phút để xử lý
- Ảnh CMND/CCCD phải rõ ràng, không bị mờ
- Selfie phải đủ ánh sáng và nhìn thẳng camera
- Module extends model `res.partner` của Odoo
