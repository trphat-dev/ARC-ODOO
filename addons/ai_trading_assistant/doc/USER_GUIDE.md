# Hướng dẫn sử dụng: AI Trading Assistant

**Phiên bản**: 2.0 (State of the Art with Generic FinRL)
**Module**: `ai_trading_assistant`

---

## 1. Giới thiệu tổng quan

**AI Trading Assistant** là trợ lý đầu tư thông minh tích hợp sâu trong hệ thống HDC-FMS. Module sử dụng công nghệ **Deep Reinforcement Learning (Học tăng cường sâu)** vối thư viện FinRL để tự động hóa quy trình đầu tư chứng khoán: từ phân tích dữ liệu, nhận định thị trường, đến ra quyết định mua/bán và quản trị rủi ro.

### Điểm nổi bật:

- **Trí tuệ nhân tạo (AI)**: Sử dụng các thuận toán tiên tiến nhất (PPO, A2C, DDPG, SAC, TD3).
- **Ensemble Strategy**: Cơ chế "Hội đồng quản trị", kết hợp quyết định từ nhiều model để tăng độ chính xác.
- **Quản trị rủi ro**: Tự động phát hiện thị trường sập (Market Crash) bằng chỉ số **Turbulence Index**.
- **Tương tác tự nhiên**: Chatbot tích hợp sẵn, hỗ trợ hỏi đáp và vẽ biểu đồ kỹ thuật ngay trong khung chat.

---

## 2. Thiết lập cấu hình (Configuration)

Trước khi sử dụng, cần thiết lập các thông số cơ bản.

1.  Truy cập **AI Trading** > **Configuration** > **Settings**.
2.  **Thông số cơ bản**:
    - **SSI FastConnect**: Đảm bảo đã kết nối API SSI thành công.
    - **Data Source**: Chọn nguồn dữ liệu (mặc định: SSI API).
3.  **Cấu hình FinRL (FinRL Settings)**:
    - **DRL Algorithm**: Chọn thuật toán training.
      - _Khuyên dùng_: **`Ensemble - Voting Strategy`** (Kết hợp sức mạnh số đông).
      - _Các lựa chọn khác_: PPO (Ổn định), A2C (Nhanh), DDPG/SAC (Cho chiến lược Continuous).
    - **Training Timesteps**: Số bước huấn luyện (Mặc định: 50,000 - 100,000).
    - **Action Space**:
      - **Discrete**: Mua / Giữ / Bán (Đơn giản, dễ quản lý).
      - **Continuous**: Tỷ trọng % vốn (Linh hoạt, nâng cao).
    - **Risk Management**:
      - Bật **Turbulence Index**: Để AI tự động phòng thủ khi thị trường biến động mạnh.

---

## 3. Các tính năng chính (Core Features)

### 3.1. AI Chatbot (Tư vấn viên ảo)

Chatbot đóng vai trò là chuyên viên tư vấn 24/7.

- **Truy cập**: Biểu tượng Chat góc dưới màn hình hoặc menu **AI Chatbot**.
- **Chức năng**:
  - Hỏi giá cổ phiếu: "Giá FPT hôm nay thế nào?"
  - Xin lời khuyên: "Có nên mua HPG lúc này không?"
  - Vẽ biểu đồ: "Vẽ chart VNM với chỉ báo MACD".
  - _Lưu ý_: Chatbot sẽ kiểm tra sức mua thực tế của tài khoản trước khi tư vấn khối lượng mua.

### 3.2. Quản lý Chiến lược (AI Strategies)

Nơi định nghĩa các "Robot" đầu tư khác nhau.

- **Tạo mới**: Vào **Strategies** > **New**.
- Điền tên chiến lược (VD: "Bluechip Tăng trưởng").
- Danh sách theo dõi (Watchlist): Thêm các mã cổ phiếu muốn AI theo dõi (VD: FPT, MWG, VCB).

### 3.3. Huấn luyện Mô hình (Training)

Đây là bước dạy AI học cách giao dịch ("Luyện công").

1.  Vào một **Strategy** cụ thể.
2.  Nhấn nút **Start Training**.
3.  Hệ thống sẽ:
    - Tải dữ liệu lịch sử từ SSI.
    - Tính toán chỉ báo kỹ thuật (RSI, MACD, Volume...).
    - Chạy thuật toán FinRL để tìm ra quy luật tối ưu.
    - Hiển thị tiến độ và kết quả (Sharpe Ratio, Lợi nhuận) trực quan.

### 3.4. Dự báo & Khuyến nghị (Predictions)

Sau khi train xong, AI sẽ sinh ra các dự báo hàng ngày.

- Truy cập **Permissions** (Dự báo).
- Xem danh sách các tín hiệu: **BUY** (Xanh), **SELL** (Đỏ), **HOLD** (Xám).
- **Độ tin cậy (Confidence)**: Thể hiện mức độ chắc chắn của AI (0% - 100%).
- **Thao tác**:
  - Nhấn **View Chart** để xem lại biểu đồ kỹ thuật.
  - Nhấn **Place Order** để chuyển lệnh sang module Giao dịch (Stock Trading).

---

## 4. Tính năng nâng cao (Advanced Features)

Dành cho nhà đầu tư chuyên nghiệp muốn tối ưu hiệu suất.

### 4.1. Ensemble Learning (Cơ chế Bỏ phiếu)

Thay vì tin vào 1 Robot, hệ thống sẽ train đồng thời 3-5 Robot khác nhau (PPO, A2C, DDPG...).

- **Khi dự báo**: Các Robot sẽ bỏ phiếu.
- **Kết quả**: Tín hiệu cuối cùng được đưa ra dựa trên đa số (Majority Vote) hoặc trung bình cộng.
- **Lợi ích**: Giảm thiểu tín hiệu giả, tránh "bắt dao rơi".

### 4.2. Chỉ số Bất ổn (Turbulence Index)

Hệ thống tự động đo lường độ "rung lắc" của thị trường.

- Nếu **Turbulence > Threshold** (Ngưỡng an toàn): AI sẽ chuyển sang chế độ "Panic Mode" -> Ưu tiên Bán hoặc Giữ tiền mặt, hạn chế Mua mới.
- Đây là lớp bảo vệ tài khoản quan trọng khi thị trường sập (Crash).

### 4.3. Tối ưu tham số (Hyperparameter Tuning) (BETA)

Sử dụng thư viện **Optuna** để tự động tìm bộ tham số tốt nhất ("Learning Rate" nào tốt nhất cho mã VNM? "Batch Size" nào tốt cho HPG?).

- Sử dụng hàm `tune()` trong code hoặc nút **Auto-Tune** (sắp ra mắt trên GD).

---

## 5. Quy trình sử dụng mẫu (Use Case Scenarios)

### Kịch bản 1: Nhận định thị trường hàng ngày (Daily Routine)

1.  **7:00 PM**: Hệ thống tự động cập nhật dữ liệu ngày hôm nay.
2.  **7:30 PM**: AI chạy dự báo (Prediction) cho danh mục theo dõi.
3.  **8:00 PM**: Nhà đầu tư vào check mục **Permissions**.
    - Lọc các mã có tín hiệu **BUY** và Confidence > 80%.
    - Xem chart xác nhận.
4.  **Sáng hôm sau**: Đặt lệnh chờ sẵn hoặc dùng Chatbot để đặt lệnh nhanh.

### Kịch bản 2: Xây dựng chiến lược mới cho dòng Bank

1.  Tạo Strategy mới: "Vietnam Banks".
2.  Add symbols: STB, MBB, CTG, VCB, ACB.
3.  Cấu hình: Chọn **Ensemble Strategy** để có độ ổn định cao nhất.
4.  Nhấn **Train Model** (nếu dữ liệu nhiều, có thể train qua đêm).
5.  Sáng hôm sau kiểm tra **Backtest Metrics**: Nếu Sharpe Ratio > 1.5 và Return > 20%/năm -> Kích hoạt sử dụng thực tế.

---

---

## 6. Phân biệt Dry Run và Live Trading

Hệ thống hỗ trợ 2 chế độ vận hành chính. Hiểu rõ sự khác biệt giúp bạn tránh rủi ro mất tiền thật khi chưa sẵn sàng.

| Đặc điểm          | Dry Run (Chạy thử/Giả lập)                                          | Live Trading (Giao dịch Thực)                                                |
| :---------------- | :------------------------------------------------------------------ | :--------------------------------------------------------------------------- |
| **Mục đích**      | Kiểm tra chiến lược, theo dõi hiệu quả AI mà không rủi ro.          | Kiếm lợi nhuận thực tế từ thị trường.                                        |
| **Tiền tệ**       | Tiền ảo (Virtual Balance).                                          | Tiền thật trong tài khoản SSI.                                               |
| **Lệnh (Order)**  | Chỉ sinh ra bản ghi **Prediction** trên phần mềm. Không gửi đi đâu. | Chuyển Prediction thành **Stock Order** và gửi lên Sở Giao dịch qua SSI API. |
| **Rủi ro**        | = 0. Nếu lỗ, chỉ là con số trên báo cáo.                            | Có thể mất vốn nếu thị trường đi ngược dự đoán.                              |
| **Cảm xúc**       | Thoải mái, khách quan.                                              | Áp lực tâm lý thật.                                                          |
| **Khi nào dùng?** | Khi mới train xong model mới, cần kiểm chứng 1-2 tuần.              | Khi model đã chứng minh hiệu quả (Sharpe > 1.5) qua giai đoạn Dry Run.       |

> **Khuyến nghị**: Luôn luôn chạy **Dry Run** ít nhất 7 ngày với bất kỳ chiến lược mới nào trước khi cấp vốn thật (Live Trading).
