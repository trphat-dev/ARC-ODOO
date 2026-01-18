# Report List - Hướng Dẫn Sử Dụng

## Giới thiệu

**Report List** là module quản lý báo cáo toàn diện, cung cấp 12 loại báo cáo khác nhau với khả năng xuất PDF.

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `web`, `fund_management`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Report List" → Install
```

## Danh sách báo cáo

### 1. Báo cáo số dư (Balance Report)

**Đường dẫn Backend**: Report List → Balance Report

- Số dư tiền mặt
- Số dư CCQ
- Tổng giá trị

### 2. Báo cáo giao dịch (Transaction Report)

**Đường dẫn Backend**: Report List → Transaction Report

- Lịch sử giao dịch
- Filter theo thời gian, loại

### 3. Báo cáo lịch sử lệnh (Order History Report)

**Đường dẫn Backend**: Report List → Order History Report

- Tất cả lệnh đã đặt
- Trạng thái từng lệnh

### 4. Báo cáo thống kê hợp đồng (Contract Statistics)

**Đường dẫn Backend**: Report List → Contract Statistics

- Số lượng hợp đồng theo loại
- Giá trị theo thời gian

### 5. Báo cáo bán sớm (Early Sale Report)

**Đường dẫn Backend**: Report List → Early Sale Report

- Các khoản bán trước đáo hạn
- Phí phạt (nếu có)

### 6. Báo cáo tổng hợp hợp đồng (Contract Summary)

**Đường dẫn Backend**: Report List → Contract Summary

- Tổng hợp theo CCQ
- Tổng giá trị theo kỳ hạn

### 7. Báo cáo hợp đồng mua (Purchase Contract)

**Đường dẫn Backend**: Report List → Purchase Contract

- Chi tiết hợp đồng mua
- Thông tin thanh toán

### 8. Báo cáo hợp đồng bán (Sell Contract)

**Đường dẫn Backend**: Report List → Sell Contract

- Chi tiết hợp đồng bán
- Tiền nhận được

### 9. Báo cáo AOC (Account Opening Confirmation)

**Đường dẫn Backend**: Report List → AOC Report

- Xác nhận mở tài khoản
- Thông tin nhà đầu tư

### 10. Báo cáo nhà đầu tư (Investor Report)

**Đường dẫn Backend**: Report List → Investor Report

- Danh sách nhà đầu tư
- Thông tin tổng hợp

### 11. Báo cáo danh sách người dùng (User List Report)

**Đường dẫn Backend**: Report List → User List Report

- Danh sách users hệ thống
- Vai trò và quyền

### 12. Báo cáo kỳ hạn lãi suất (Tenors Interest Rates)

**Đường dẫn Backend**: Report List → Tenors Interest Rates

- Bảng lãi suất theo kỳ hạn
- Lịch sử thay đổi

## Tính năng chung

- **Filter**: Lọc theo nhiều tiêu chí
- **Search**: Tìm kiếm nhanh
- **Export PDF**: Xuất báo cáo PDF
- **Print**: In trực tiếp

## Cấu trúc Views

```
views/
├── report_balance/
│   ├── report_balance_page.xml
│   └── report_balance_pdf_template.xml
├── report_transaction/
│   ├── report_transaction_page.xml
│   └── report_transaction_pdf_template.xml
└── [... similar for other reports]
```

## Lưu ý

- Báo cáo PDF sử dụng template riêng
- Một số báo cáo cần quyền đặc biệt
- Dữ liệu real-time từ database
