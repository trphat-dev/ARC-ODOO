# Stock Data Module

Module tích hợp dữ liệu chứng khoán từ SSI FastConnect Data API vào Odoo 18.

## Tính năng

- ✅ Lấy danh sách chứng khoán (Securities)
- ✅ Chi tiết chứng khoán
- ✅ Dữ liệu OHLC hàng ngày (Daily OHLC)
- ✅ Dữ liệu OHLC trong ngày (Intraday OHLC)
- ✅ Danh sách chỉ số (Index List)
- ✅ Thành phần chỉ số (Index Components)
- ✅ Tự động cập nhật dữ liệu

## Yêu cầu

### Cài đặt Python Package

Module yêu cầu SDK `ssi-fc-data`. Cài đặt bằng cách:

```bash
cd fc-data/dist/ssi_fc_data-2.2.2
pip install .
```

Hoặc cài đặt từ thư mục addons:

```bash
cd addons/fc-data/dist/ssi_fc_data-2.2.2
pip install .
```

### Thông tin API

Consumer ID: `YOUR_CONSUMER_ID`
Consumer Secret: `YOUR_CONSUMER_SECRET`

> **⚠️ Lưu ý:** Cấu hình Consumer ID/Secret trong Odoo tại **Stock Data > Configuration**.

## Cài đặt

1. Module đã có sẵn trong thư mục addons

2. Cài đặt dependencies:

   ```bash
   pip install ssi-fc-data requests websocket-client
   ```

3. Khởi động lại Odoo server

4. Vào Odoo, Apps > tìm "Stock Data" > Install

## Cấu hình

1. Vào **Stock Data > Configuration**
2. Kiểm tra thông tin API đã được điền sẵn:
   - Consumer ID
   - Consumer Secret
   - API URL
   - Stream URL
3. Click Save

## Sử dụng

### Lấy danh sách chứng khoán

1. Vào **Stock Data > Fetch Market Data**
2. Chọn Action: "Fetch Securities List"
3. Chọn Market (HOSE/HNX/UPCOM)
4. Click "Fetch Data"

### Xem danh sách chứng khoán

1. Vào **Stock Data > Securities**
2. Xem danh sách chứng khoán đã lấy về
3. Click vào security để xem chi tiết

### Lấy dữ liệu OHLC

1. Vào **Stock Data > Fetch Market Data**
2. Chọn Action: "Fetch Daily OHLC"
3. Nhập Symbol (ví dụ: FPT)
4. Chọn From Date và To Date
5. Click "Fetch Data"

## Model Structure

- **ssi.api.config**: API Configuration
- **ssi.securities**: Securities list
- **ssi.daily.ohlc**: Daily OHLC data
- **ssi.intraday.ohlc**: Intraday OHLC data
- **ssi.index.list**: Index list
- **ssi.index.components**: Index components
- **wizard.fetch.market.data**: Fetch wizard

## Author

HDC
