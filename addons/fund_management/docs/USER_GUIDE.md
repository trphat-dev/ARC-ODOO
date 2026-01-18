# Fund Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**Fund Management** là module chính quản lý các nghiệp vụ liên quan đến quỹ đầu tư, bao gồm:

- Mua/Bán chứng chỉ quỹ (CCQ)
- Smart OTP xác thực giao dịch
- Chữ ký số hợp đồng
- Quản lý danh mục đầu tư

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `bus`, `mail`, `portal`, `web`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Fund Management" → Install
```

## Hướng dẫn sử dụng

### 1. Xem danh sách quỹ

**URL**: `/fund`

- Hiển thị danh sách các quỹ đang hoạt động
- Thông tin: NAV, Lợi nhuận, Phí...

### 2. So sánh quỹ

**URL**: `/fund/compare`

- So sánh hiệu suất các quỹ
- Biểu đồ trực quan

### 3. Mua CCQ (Fund Buy)

**URL**: `/fund/buy/{fund_id}`

**Quy trình**:

1. Chọn quỹ muốn mua
2. Nhập số tiền đầu tư
3. Xem phí và tổng tiền
4. Xác nhận điều khoản
5. Ký hợp đồng số
6. Xác thực Smart OTP
7. Hoàn tất

### 4. Bán CCQ (Fund Sell)

**URL**: `/fund/sell/{fund_id}`

**Quy trình**:

1. Chọn quỹ muốn bán
2. Nhập số unit cần bán
3. Xem giá trị ước tính
4. Xác nhận
5. Xác thực Smart OTP
6. Hoàn tất

### 5. Số dư tài khoản

**URL**: `/my/account-balance`

- Xem số dư khả dụng
- Lịch sử thay đổi số dư

## Cấu trúc Views

```
views/
├── fund/
│   ├── fund.xml              # Fund list view
│   ├── fund_action.xml       # Actions
│   ├── fund_menu.xml         # Menu
│   ├── fund_page.xml         # Frontend page
│   ├── fund_compare.xml      # Compare page
│   ├── fund_buy/
│   │   ├── fund_buy.xml      # Buy form
│   │   ├── fund_confirm.xml  # Confirmation
│   │   ├── fund_result.xml   # Result page
│   │   ├── fee_template.xml  # Fee display
│   │   ├── terms_modal_template.xml     # Terms modal
│   │   └── signature_modal_template.xml # Signature modal
│   └── fund_sell/
│       ├── fund_sell.xml         # Sell form
│       └── fund_sell_confirm.xml # Confirmation
├── investment/
│   └── investment_views.xml  # Investment management
├── transaction/
│   └── transaction_views.xml # Transaction views
├── account_balance/
│   ├── account_balance_views.xml
│   └── account_balance_page.xml
├── balance_history/
│   └── balance_history_views.xml
├── comparison/
│   └── comparison_views.xml
└── signed_contract/
    └── signed_contract_views.xml
```

## Smart OTP

- Xác thực 2 yếu tố cho giao dịch
- Mã OTP gửi qua SMS/Email
- Thời hạn: 5 phút

## Chữ ký số

- Ký hợp đồng trực tiếp trên giao diện
- Lưu trữ chữ ký dạng ảnh
- Có giá trị pháp lý

## Cron Jobs

- **Fund Sync**: Tự động đồng bộ dữ liệu quỹ
- Cấu hình: `data/fund_sync_cron.xml`

## Lưu ý

- Giao dịch chỉ được thực hiện trong giờ làm việc
- Lệnh mua sẽ được khớp vào phiên tiếp theo
- Số tiền tối thiểu tùy thuộc vào từng quỹ
