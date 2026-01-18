# Transaction List - Hướng Dẫn Sử Dụng

## Giới thiệu

**Transaction List** là module quản lý danh sách lệnh giao dịch của nhà đầu tư với 2 tab chính:

- **Pending**: Lệnh chờ duyệt/chờ khớp
- **Approved**: Lệnh đã được duyệt/đã khớp

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `bus`, `mail`, `portal`, `web`, `order_matching`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Transaction List" → Install
```

## Hướng dẫn sử dụng

### 1. Xem danh sách giao dịch

**Đường dẫn Backend**: Transaction List menu

### 2. Tab Pending (Chờ xử lý)

Hiển thị các lệnh:

- Chờ duyệt
- Đang xử lý
- Chờ khớp

**Thông tin hiển thị**:
| Trường | Mô tả |
|--------|-------|
| Mã lệnh | ID giao dịch |
| Loại | Mua/Bán |
| CCQ | Chứng chỉ quỹ |
| Số tiền/Unit | Giá trị giao dịch |
| Trạng thái | Pending/Processing |
| Ngày đặt | Thời gian đặt lệnh |

### 3. Tab Approved (Đã xử lý)

Hiển thị các lệnh:

- Đã khớp hoàn toàn
- Đã khớp một phần
- Đã hủy

**Thông tin thêm**:

- Matched Units (số unit đã khớp)
- Remaining Units (số unit còn lại)
- Ngày khớp

### 4. Tính năng

- **Filter**: Lọc theo CCQ, loại lệnh, trạng thái
- **Search**: Tìm theo mã lệnh, tên CCQ
- **Export**: Xuất danh sách Excel/CSV

## Cấu trúc Views

```
views/
├── transaction_list_views.xml    # Backend views
├── menu_views.xml                # Menu
└── transaction_list/
    └── transaction_list_page.xml # Frontend page
```

## Assets

```
static/src/
├── scss/
│   └── transaction_list.scss
└── js/transaction_list/
    ├── transaction_list_tab.js
    └── entrypoint.js
```

## Lưu ý

- Lệnh pending có thể bị hủy trước khi khớp
- Lệnh đã khớp không thể hủy
- Dữ liệu được lấy từ `order_matching` module
