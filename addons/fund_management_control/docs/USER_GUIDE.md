# Fund Management Control - Hướng Dẫn Sử Dụng

## Giới thiệu

**Fund Management Control** là module quản trị dành cho Admin, cung cấp các chức năng cấu hình và quản lý:

- Chứng chỉ quỹ (Fund Certificate)
- Loại chương trình (Scheme Type)
- Chương trình (Scheme)
- Biểu phí (Fee Schedule)
- SIP Settings
- Cài đặt thuế (Tax Settings)
- Dữ liệu tham chiếu: Ngày lễ, Ngân hàng, Chi nhánh, Địa chỉ...

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `bus`, `mail`, `web`, `fund_management_dashboard`, `investor_list`, `stock_data`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Fund Management Control" → Install
```

## Hướng dẫn sử dụng

### 1. Quản lý Chứng chỉ quỹ (Fund Certificate)

**Chức năng**:

- Thêm/Sửa/Xóa CCQ
- Đồng bộ dữ liệu từ nguồn ngoài
- Cấu hình thông tin quỹ

**Thông tin CCQ**:
| Trường | Mô tả |
|--------|-------|
| Mã CCQ | Mã định danh quỹ |
| Tên CCQ | Tên đầy đủ |
| NAV hiện tại | Giá trị tài sản ròng |
| Trạng thái | Active/Inactive |

### 2. Quản lý Loại chương trình (Scheme Type)

- Định nghĩa các loại chương trình đầu tư
- VD: Tích lũy, Tăng trưởng, Cân bằng...

### 3. Quản lý Chương trình (Scheme)

- Tạo chương trình đầu tư cụ thể
- Liên kết với CCQ và loại chương trình
- Cấu hình điều kiện tham gia

### 4. Biểu phí (Fee Schedule)

**Các loại phí**:
| Loại phí | Mô tả |
|----------|-------|
| Phí mua | Phí khi mua CCQ |
| Phí bán | Phí khi bán CCQ |
| Phí quản lý | Phí quản lý hàng năm |
| Phí lưu ký | Phí lưu ký CCQ |

### 5. SIP Settings (Systematic Investment Plan)

- Cấu hình đầu tư định kỳ
- Ngày trích, số tiền tối thiểu
- Quy tắc tự động

### 6. Cài đặt Thuế (Tax Settings)

- Thuế thu nhập từ đầu tư
- Thuế trước bạ
- Quy tắc tính thuế

### 7. Dữ liệu tham chiếu

#### Ngày lễ (Holiday)

- Danh sách ngày lễ/nghỉ
- Ảnh hưởng đến ngày giao dịch

#### Ngân hàng (Bank)

- Danh sách ngân hàng
- Mã SWIFT, tên viết tắt

#### Chi nhánh ngân hàng (Bank Branch)

- Chi nhánh của từng ngân hàng
- Địa chỉ, mã chi nhánh

#### Địa chỉ (Country/City/Ward)

- Quốc gia
- Tỉnh/Thành phố
- Phường/Xã

## Cấu trúc Views

```
views/
├── fund_certificate/     # CCQ management
├── scheme_type/          # Loại chương trình
├── scheme/               # Chương trình
├── fee_schedule/         # Biểu phí
├── sip_settings/         # SIP
├── tax_settings/         # Thuế
├── holiday/              # Ngày lễ
├── bank/                 # Ngân hàng
├── bank_branch/          # Chi nhánh
├── country/              # Quốc gia
├── city/                 # Thành phố
└── ward/                 # Phường/Xã
```

## Cron Jobs

- Tự động đồng bộ dữ liệu
- Cấu hình: `data/cron_data.xml`

## Lưu ý

- Module này chỉ dành cho Admin/Back-office
- Thay đổi cấu hình ảnh hưởng đến toàn hệ thống
- Nên backup trước khi thay đổi lớn
