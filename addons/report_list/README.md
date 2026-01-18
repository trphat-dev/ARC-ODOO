# Fund Management Control Module

## Tổng quan
Module này cung cấp chức năng báo cáo số dư và báo cáo giao dịch, kế thừa dữ liệu trực tiếp từ `transaction_management` module.

## Các thay đổi đã thực hiện

### 1. Cập nhật Dependencies
- Thêm dependency vào `transaction_management` và `overview_fund_management` trong `__manifest__.py`
- Đảm bảo module có thể truy cập các model `portfolio.transaction` và `portfolio.investment`

### 2. Cập nhật Models

#### Report Balance Model (`report_balance_model.py`)
- **Thay đổi**: Kế thừa từ `portfolio.investment` thay vì tạo model riêng
- **Lý do**: Sử dụng dữ liệu thật từ các khoản đầu tư thay vì dữ liệu giả
- **Fields computed**: Tất cả các field đều được compute từ dữ liệu thật:
  - `so_tai_khoan`: Từ `user_id.partner_id` và `status.info`
  - `nha_dau_tu`: Từ `user_id.name`
  - `dksh`: Từ `amount`
  - `quy`: Từ `fund_id.name`
  - `so_ccq`: Từ `units`

#### Report Transaction Model (`report_transaction_model.py`)
- **Thay đổi**: Kế thừa từ `portfolio.transaction` thay vì tạo model riêng
- **Lý do**: Sử dụng dữ liệu giao dịch thật từ `transaction_management`
- **Fields computed**: Map các field từ transaction thật:
  - `so_tai_khoan`: Từ `user_id.partner_id`
  - `nha_dau_tu`: Từ `user_id.name`
  - `ma_giao_dich`: Từ `name`
  - `loai_lenh`: Map từ `transaction_type` (buy/sell)

### 3. Cập nhật Controllers

#### Report Balance Controller (`report_balance.py`)
- **Thay đổi**: Sử dụng `portfolio.investment` thay vì `report.balance`
- **Search mapping**: Map các field search từ frontend sang model fields thật
- **Filter mapping**: Cập nhật domain filters để sử dụng field names đúng

#### Report Transaction Controller (`report_transaction.py`)
- **Thay đổi**: Sử dụng trực tiếp `portfolio.transaction`
- **Search mapping**: Map các field search từ frontend sang model fields thật
- **Order type mapping**: Cập nhật mapping từ `purchase/sell` thay vì `mua/ban`

### 4. Cập nhật Security
- Thêm quyền truy cập cho `portfolio.investment` model
- Đảm bảo user có thể đọc/ghi dữ liệu từ các model kế thừa

## Lợi ích của việc kế thừa

### 1. Dữ liệu thật
- Báo cáo số dư hiển thị dữ liệu thật từ `portfolio.investment`
- Báo cáo giao dịch hiển thị dữ liệu thật từ `portfolio.transaction`
- Không cần tạo dữ liệu giả hoặc duplicate

### 2. Tính nhất quán
- Dữ liệu luôn đồng bộ với module `transaction_management`
- Khi có giao dịch mới, báo cáo tự động cập nhật
- Không có risk data inconsistency

### 3. Bảo trì dễ dàng
- Chỉ cần maintain một nguồn dữ liệu
- Logic business tập trung ở `transaction_management`
- `fund_management_control` chỉ focus vào reporting

## Cách sử dụng

### 1. Báo cáo số dư (`/report-balance`)
- Hiển thị tất cả khoản đầu tư active của user
- Filter theo quỹ, ngày, loại nhà đầu tư
- Export PDF với dữ liệu thật

### 2. Báo cáo giao dịch (`/report-transaction`)
- Hiển thị tất cả giao dịch của user
- Filter theo quỹ, khoảng thời gian
- Export PDF với dữ liệu thật

## Dependencies
- `base`
- `crm`
- `web`
- `transaction_list`
- `transaction_management` (mới)
- `overview_fund_management` (mới)

## Lưu ý quan trọng
1. Module này phụ thuộc vào `transaction_management` và `overview_fund_management`
2. Đảm bảo các module dependency đã được cài đặt trước
3. Dữ liệu hiển thị phụ thuộc vào dữ liệu thật trong database
4. Các computed fields sẽ tự động cập nhật khi dữ liệu gốc thay đổi
