# Asset Management - Hướng Dẫn Sử Dụng

## Giới thiệu

**Asset Management** là module quản lý tài sản đầu tư của nhà đầu tư, hiển thị danh mục đầu tư chi tiết và hiệu suất từng khoản đầu tư.

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `mail`, `portal`, `web`, `fund_management`
- **License**: LGPL-3

## Cài đặt

```
Odoo Settings → Apps → Search "Asset Management" → Install
```

## Hướng dẫn sử dụng

### 1. Xem danh mục tài sản

**Đường dẫn Backend**: Asset Management menu

**Thông tin hiển thị cho mỗi khoản đầu tư**:
| Thông tin | Mô tả |
|-----------|-------|
| CCQ | Tên chứng chỉ quỹ |
| Số unit | Số lượng CCQ nắm giữ |
| Giá mua TB | Giá mua trung bình |
| NAV hiện tại | Giá trị NAV mới nhất |
| Giá trị hiện tại | NAV × Số unit |
| Lãi/Lỗ | Chênh lệch giá trị |
| % Thay đổi | Phần trăm lãi/lỗ |

### 2. Phân loại tài sản

- **Theo CCQ**: Nhóm theo từng loại quỹ
- **Theo kỳ hạn**: Ngắn hạn / Dài hạn
- **Theo trạng thái**: Đang hoạt động / Đáo hạn / Đã bán

### 3. Biểu đồ phân bổ

- Pie chart hiển thị % từng CCQ
- Có thể click để xem chi tiết

## Cấu trúc Views

```
views/
└── asset_management/
    └── asset_management_page.xml
```

## Assets

```
static/src/
├── scss/
│   └── asset_management.scss
└── js/asset_management/
    ├── asset_management_widget.js
    └── entrypoint.js
```

## Lưu ý

- Dữ liệu được lấy từ model `portfolio.investment`
- Giá trị được cập nhật khi NAV thay đổi
- Module này chỉ hiển thị, không có chức năng giao dịch
