# CHUẨN TÁCH LỆNH TRONG KHỚP LỆNH SÀN CHỨNG CHỈ QUỸ ĐÓNG

## TỔNG QUAN

Tài liệu này mô tả chi tiết về chuẩn tách lệnh (Order Splitting) trong hệ thống khớp lệnh sàn chứng chỉ quỹ đóng, dựa trên phân tích code hiện tại và các chuẩn thực tế của sàn chứng khoán.

---

## 1. MỤC ĐÍCH TÁCH LỆNH

### 1.1. Lý do tách lệnh
- **Khớp một phần**: Khi lệnh gốc chỉ khớp được một phần, phần còn lại cần được tách thành lệnh mới để tiếp tục khớp
- **Tối ưu hóa khớp lệnh**: Tách lệnh giúp tăng khả năng khớp bằng cách tạo ra các lệnh nhỏ hơn, dễ khớp hơn
- **Theo dõi chính xác**: Mỗi lệnh con đại diện cho một phần cụ thể của lệnh gốc, giúp theo dõi và quản lý chính xác

### 1.2. Khi nào tách lệnh
- **Sau khi khớp một phần**: Khi lệnh gốc đã khớp một phần nhưng vẫn còn số lượng chưa khớp
- **Chỉ lệnh gốc**: CHỈ lệnh gốc (không có `parent_order_id`) mới được tách
- **Lệnh con không được tách tiếp**: Lệnh đã được tách (có `parent_order_id`) không được tách tiếp để tránh tạo cây phân cấp phức tạp

---

## 2. CHUẨN SỐ LƯỢNG

### 2.1. Bội số làm tròn: 50 CCQ
- **Tất cả số lượng phải là bội số của 50**: Đây là chuẩn của sàn chứng chỉ quỹ đóng
- **Sử dụng hàm `mround(value, 50)`**: Làm tròn về bội số gần nhất của 50
- **Ví dụ**:
  - 123 CCQ → 100 CCQ (làm tròn xuống)
  - 175 CCQ → 200 CCQ (làm tròn lên)
  - 150 CCQ → 150 CCQ (giữ nguyên)

### 2.2. Số lượng tối thiểu: 50 CCQ
- **Mỗi lệnh con phải ≥ 50 CCQ**: Không được tạo lệnh nhỏ hơn 50 CCQ
- **Nếu không đủ 50 CCQ**: Không tách, giữ nguyên lệnh gốc
- **Logic trong code**:
  ```python
  min_quantity = 50.0
  if quantity_per_order < min_quantity:
      split_count = 1
      quantity_per_order = remaining_quantity
  ```

### 2.3. Số lượng tối đa
- **Không có giới hạn tối đa**: Lệnh có thể có số lượng bất kỳ (miễn là bội số của 50)
- **Tuy nhiên**: Trong thực tế, lệnh lớn thường được tách thành nhiều lệnh nhỏ để tăng khả năng khớp

---

## 3. QUY TRÌNH TÁCH LỆNH

### 3.1. Điều kiện tiên quyết
1. **Lệnh phải là lệnh gốc**: `parent_order_id = False`
2. **Lệnh đã khớp một phần**: `matched_units > 0` và `remaining_units > 0`
3. **Lệnh chưa được tách**: `split_order_ids` rỗng hoặc không tồn tại
4. **Số lượng còn lại ≥ 50 CCQ**: `remaining_quantity >= 50`

### 3.2. Các bước tách lệnh

#### Bước 1: Refresh dữ liệu
```python
# Đọc trực tiếp từ database để đảm bảo tính chính xác
self.env.cr.execute("SELECT units, matched_units FROM portfolio_transaction WHERE id = %s", (self.id,))
units_total = float(row[0] or 0)
matched_total = float(row[1] or 0)
current_remaining = max(0.0, units_total - matched_total)
```

#### Bước 2: Xác định số lượng tách
```python
# Đảm bảo remaining_quantity không vượt quá current_remaining
if remaining_quantity > current_remaining:
    remaining_quantity = current_remaining
```

#### Bước 3: Tính số lượng mỗi lệnh con
```python
# Mặc định tách thành 1 lệnh
split_count = 1
quantity_per_order = remaining_quantity

# Làm tròn về bội số của 50
quantity_per_order = mround(quantity_per_order, 50)
```

#### Bước 4: Tạo lệnh con
```python
new_order_vals = {
    'user_id': self.user_id.id,
    'fund_id': self.fund_id.id,
    'transaction_type': self.transaction_type,
    'status': 'pending',
    'units': order_quantity,  # Đã làm tròn về bội số 50
    'remaining_units': order_quantity,
    'matched_units': 0,
    'parent_order_id': self.id,  # QUAN TRỌNG: Liên kết với lệnh gốc
    'price': unit_price,
    'amount': mround(order_quantity * unit_price, 50),  # Amount cũng làm tròn
    # ... các trường khác
}
```

#### Bước 5: Cập nhật lệnh gốc
```python
# Lệnh gốc: remaining_units = 0 (vì đã chuyển sang lệnh con)
# matched_units giữ nguyên (phần đã khớp trước khi tách)
self.write({
    'remaining_units': 0,
    'ccq_remaining_to_match': 0,
    # matched_units giữ nguyên
    # status vẫn là 'pending' vì có lệnh con chưa khớp
})
```

---

## 4. QUAN HỆ LỆNH GỐC - LỆNH CON

### 4.1. Cấu trúc dữ liệu
- **Lệnh gốc**: `parent_order_id = False`
- **Lệnh con**: `parent_order_id = <id_lệnh_gốc>`
- **One2many**: `split_order_ids` trên lệnh gốc → danh sách lệnh con

### 4.2. Tính toán số lượng

#### Lệnh gốc:
- **units**: Tổng số lượng ban đầu (không đổi)
- **matched_units**: Phần khớp trực tiếp + tổng matched từ lệnh con
- **remaining_units**: Tổng remaining từ các lệnh con chưa khớp đủ

#### Công thức:
```python
# Phần khớp trực tiếp (trước khi tách)
direct_matched = units_gốc - tổng_units_lệnh_con

# Tổng matched
total_matched = direct_matched + tổng_matched_từ_lệnh_con

# Remaining
remaining = tổng_remaining_từ_lệnh_con_pending
```

### 4.3. Cập nhật lệnh gốc khi lệnh con khớp
- **Tự động cập nhật**: Khi lệnh con khớp (matched_units thay đổi hoặc status = completed)
- **Method**: `_update_parent_order_when_split_completed()`
- **Logic**:
  1. Tính tổng matched từ TẤT CẢ lệnh con
  2. Tính tổng remaining từ lệnh con pending
  3. Cập nhật lệnh gốc
  4. Nếu tất cả lệnh con completed → lệnh gốc completed

---

## 5. VÍ DỤ THỰC TẾ

### Ví dụ 1: Tách lệnh đơn giản
**Lệnh gốc**: 450 CCQ, giá 10,000 VNĐ
**Khớp**: 200 CCQ
**Còn lại**: 250 CCQ

**Kết quả**:
- Lệnh gốc: `matched_units = 200`, `remaining_units = 0`
- Lệnh con: `units = 250`, `remaining_units = 250`, `status = pending`

### Ví dụ 2: Tách lệnh với làm tròn
**Lệnh gốc**: 475 CCQ, giá 10,000 VNĐ
**Khớp**: 200 CCQ
**Còn lại**: 275 CCQ

**Kết quả**:
- Lệnh con: `units = 250` (275 → làm tròn xuống 250)
- Lệnh gốc: `matched_units = 200`, `remaining_units = 0`
- **Lưu ý**: 25 CCQ bị mất do làm tròn (cần xử lý trong business logic)

### Ví dụ 3: Lệnh con khớp tiếp
**Lệnh gốc**: 450 CCQ
**Lệnh con 1**: 250 CCQ
- Khớp: 100 CCQ
- Còn lại: 150 CCQ

**Cập nhật lệnh gốc**:
- `matched_units = 200 (trực tiếp) + 100 (từ con) = 300`
- `remaining_units = 150 (từ con)`

---

## 6. CÁC VẤN ĐỀ VÀ GIẢI PHÁP

### 6.1. Vấn đề: Làm tròn mất số lượng
**Vấn đề**: Khi làm tròn về bội số 50, có thể mất số lượng (ví dụ: 275 → 250, mất 25)

**Giải pháp hiện tại**:
- Lệnh cuối cùng nhận phần còn lại để đảm bảo tổng đúng
- Code:
  ```python
  if i == split_count - 1:
      order_quantity = available_quantity  # Nhận phần còn lại
  ```

**Đề xuất cải thiện**:
- Lưu phần dư vào lệnh gốc hoặc tạo lệnh đặc biệt
- Hoặc làm tròn lên thay vì xuống để đảm bảo không thiếu

### 6.2. Vấn đề: Đồng bộ dữ liệu
**Vấn đề**: Khi tách lệnh, cần đảm bảo dữ liệu được refresh từ database

**Giải pháp hiện tại**:
- Sử dụng `invalidate_recordset()` và đọc trực tiếp từ DB bằng SQL
- Code:
  ```python
  self.invalidate_recordset(['units', 'matched_units', 'remaining_units'])
  self.env.cr.execute("SELECT units, matched_units FROM ...")
  ```

### 6.3. Vấn đề: Lệnh con không được tách tiếp
**Vấn đề**: Lệnh con không được tách tiếp để tránh cây phân cấp phức tạp

**Giải pháp hiện tại**:
- Check `is_split_order` hoặc `parent_order_id` trước khi tách
- Code:
  ```python
  if self.is_split_order or self.parent_order_id:
      return self.env['portfolio.transaction']  # Không tách
  ```

---

## 7. CHUẨN THỰC TẾ SÀN CHỨNG KHOÁN

### 7.1. Chuẩn Việt Nam
- **Bội số**: 10 hoặc 100 (tùy loại chứng khoán)
- **Số lượng tối thiểu**: 10 hoặc 100 (lot size)
- **Chứng chỉ quỹ đóng**: Thường là 50 hoặc 100 CCQ

### 7.2. So sánh với hệ thống hiện tại
| Tiêu chí | Hệ thống hiện tại | Chuẩn thực tế |
|----------|-------------------|---------------|
| Bội số | 50 CCQ | 50 CCQ ✓ |
| Số lượng tối thiểu | 50 CCQ | 50 CCQ ✓ |
| Làm tròn | MROUND (gần nhất) | MROUND ✓ |
| Tách lệnh | Sau khớp một phần | Sau khớp một phần ✓ |
| Lệnh con tách tiếp | Không cho phép | Không cho phép ✓ |

---

## 8. KHUYẾN NGHỊ

### 8.1. Cải thiện hiện tại
1. **Xử lý phần dư khi làm tròn**: Lưu phần dư vào lệnh gốc hoặc tạo lệnh đặc biệt
2. **Validation chặt chẽ hơn**: Kiểm tra tổng số lượng trước và sau tách
3. **Logging chi tiết**: Ghi log đầy đủ để debug và audit

### 8.2. Tính năng mới
1. **Tách lệnh thủ công**: Cho phép admin tách lệnh thủ công nếu cần
2. **Hợp nhất lệnh con**: Cho phép hợp nhất các lệnh con về lệnh gốc (nếu chưa khớp)
3. **Báo cáo tách lệnh**: Thống kê số lần tách, số lượng tách, v.v.

---

## 9. KẾT LUẬN

Hệ thống tách lệnh hiện tại đã tuân thủ các chuẩn cơ bản của sàn chứng chỉ quỹ đóng:
- ✅ Bội số 50 CCQ
- ✅ Số lượng tối thiểu 50 CCQ
- ✅ Làm tròn bằng MROUND
- ✅ Chỉ lệnh gốc được tách
- ✅ Lệnh con không được tách tiếp
- ✅ Tự động cập nhật lệnh gốc khi lệnh con khớp

**Cần cải thiện**:
- ⚠️ Xử lý phần dư khi làm tròn
- ⚠️ Validation chặt chẽ hơn
- ⚠️ Logging chi tiết hơn

---

**Tài liệu được tạo bởi**: AI Assistant  
**Ngày**: 2024  
**Phiên bản**: 1.0

