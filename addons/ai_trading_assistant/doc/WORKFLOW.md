# QUY TRÌNH HOẠT ĐỘNG CHI TIẾT (SYSTEM WORKFLOW)

Tài liệu này mô tả chi tiết luồng dữ liệu và quy trình xử lý của hệ thống **AI Trading Assistant**, từ lúc tiếp nhận dữ liệu thị trường đến khi sinh ra lệnh giao dịch.

```mermaid
graph TD
    subgraph Data Ingestion [1. Thu thập Dữ liệu]
        SSI_API[SSI FastConnect API] --> |OHLCV + Intraday| DataProcessor[AI Data Processor]
        DataProcessor --> |Calculate Indicators| DB[(Database: Stock Data)]
        DB --> |Feature Engineering| FeatureStore[Normalized Features]
    end

    subgraph Training [2. Huấn luyện Mô hình]
        Strategy[AI Strategy] --> |Config| Trainer[Model Trainer]
        Trainer --> |Load Data| FeatureStore
        Trainer --> |Init| Env[SSI Trading Env]

        subgraph FinRL Core
            Env --> |State| Agent[DRL Agent]
            Agent --> |Action| Env
            Env --> |Reward| Agent

            subgraph Advanced Features
                Env --> |Detected| Turbulence[Turbulence Check]
                Agent --> |Voting| Ensemble[Ensemble Mechanism]
            end
        end

        Agent --> |Save| ModelFile[Trained Model (.zip)]
    end

    subgraph Operation [3. Vận hành & Dự báo]
        Cron[Daily Cron Job] --> |Trigger| Predictor[AI Predictor]
        Predictor --> |Load| ModelFile
        Predictor --> |Fetch Recent Data| FeatureStore
        Predictor --> |Predict Signal| Result{AI Signal}

        Result --> |BUY| Filter1[Check Confidence > 80%]
        Result --> |SELL| Filter2[Check Portfolio Has Stock]

        Filter1 --> |Pass| Output[AI Prediction Record]
        Filter2 --> |Pass| Output
    end

    subgraph Execution [4. Thực thi Lệnh]
        User[Nhà đầu tư] --> |Review| Output
        User --> |Approve| TradingOrder[Pending Order]
        TradingOrder --> |Send| StockTradingModule[Stock Trading]
        StockTradingModule --> |Place Order| SSI_Core[SSI Core System]
    end
```

## Giải thích Chi tiết Từng Bước

### Bước 1: Thu thập & Xử lý Dữ liệu (Data Ingestion)

1.  **Trigger**: Hệ thống chạy Cronjob định kỳ (18:00 hàng ngày) hoặc User kích hoạt thủ công.
2.  **Fetching**: Module gọi `ssi_client` kết nối tới SSI FastConnect API để lấy dữ liệu giá (Open, High, Low, Close, Volume).
3.  **Processing** (`SSIDataProcessor`):
    - Làm sạch dữ liệu, xử lý giá trị thiếu (FillNA).
    - Tính toán chỉ báo kỹ thuật: RSI, MACD, Bollinger Bands, SMA 50/200.
    - **New**: Tính chỉ số **Turbulence** (Độ nhiễu động) và các chỉ số cơ bản (PE, PB).
4.  **Storage**: Dữ liệu sạch được lưu vào database Odoo để tái sử dụng.

### Bước 2: Huấn luyện AI (Training Process)

1.  **Khởi tạo**: User chọn Strategy và nhấn "Start Training".
2.  **Environment Setup** (`SSIStockTradingEnv`):
    - Hệ thống dựng lại môi trường giả lập thị trường từ quá khứ.
    - Thiết lập vốn ảo, phí giao dịch, lô giao dịch (100 cp).
3.  **Core Learning**:
    - Agent (Robot) bắt đầu thử giao dịch ngẫu nhiên.
    - Nếu lãi -> Nhận thưởng dương (+Reward). Nếu lỗ hoặc chịu rủi ro cao -> Bị phạt (-Reward).
    - **Ensemble**: Hệ thống train lần lượt PPO, A2C, DDPG và lưu lại tất cả.
    - **Auto-Tune**: Nếu bật, Optuna sẽ chạy hàng chục lần thử để tìm tham số tốt nhất trước khi train chính thức.
4.  **Output**: File model (`.zip`) được lưu vào thư mục hệ thống.

### Bước 3: Dự báo & Ra quyết định (Prediction)

1.  **Input**: Lấy dữ liệu 200 ngày gần nhất của các mã trong Watchlist.
2.  **Inference**:
    - Load model đã train.
    - Đưa dữ liệu thị trường hiện tại vào model.
3.  **Voting (Ensemble)**:
    - Robot PPO hô: Mua.
    - Robot A2C hô: Mua.
    - Robot DDPG hô: Giữ.
    - => Kết quả: **MUA** (Đa số thắng).
4.  **Safety Check**:
    - Kiểm tra **Turbulence**: Nếu thị trường đang bão -> Hủy lệnh Mua, chuyển thành Giữ.
    - Kiểm tra sức mua tiền mặt (Buying Power).
5.  **Result**: Tạo bản ghi `ai.prediction` hiển thị trên giao diện người dùng.

### Bước 4: Thực thi Giao dịch (Execution)

1.  **Review**: User xem chart, giá khuyến nghị, độ tin cậy.
2.  **Action**: User nhấn nút **"Place Order"**.
3.  **Trading**: Hệ thống tạo lệnh chờ trong module `stock_trading`. Khi đến phiên, lệnh được đẩy thẳng lên sở giao dịch thông qua SSI Gateway.

---

## Các Cơ chế Đặc biệt

### 1. Cơ chế Chống "Say sóng" (Turbulence Shield)

- **Hoạt động**: Trước mỗi quyết định, AI nhìn vào chỉ số Turbulence.
- **Logic**:
  - Turbulence < Threshold: Giao dịch bình thường.
  - Turbulence > Threshold: Kích hoạt Panic Mode (Bán tháo hoặc Đứng ngoài).

### 2. Cơ chế "Học lại" (Incremental Learning)

- Mỗi tháng, User có thể nhấn nút "Retrain". Hệ thống sẽ lấy model cũ và train tiếp với dữ liệu 1 tháng vừa qua, giúp AI không bị "lạc hậu" với diễn biến mới của thị trường.
