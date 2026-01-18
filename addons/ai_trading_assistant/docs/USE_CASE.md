# AI Trading Assistant - Use Cases

## Tổng quan

Module AI Trading Assistant sử dụng Deep Reinforcement Learning để phân tích và đưa ra tín hiệu giao dịch chứng khoán.

## Actors

| Actor          | Mô tả                   |
| -------------- | ----------------------- |
| Data Scientist | Train và quản lý models |
| Trader         | Sử dụng tín hiệu AI     |
| Investor       | Sử dụng chatbot tư vấn  |

## Use Cases

### UC-01: Train AI Model

**Actor**: Data Scientist  
**Precondition**: Có dữ liệu lịch sử

**Flow**:

1. Tạo Strategy mới
2. Chọn mã CK để train (có thể multi-stock)
3. Chọn khoảng thời gian:
   - Training period
   - Validation period
4. Cấu hình:
   - Algorithm: PPO/A2C/SAC/TD3/DDPG
   - Timesteps: 100K-1M
   - Technical indicators
5. Start Training
6. Monitor qua TensorBoard
7. Save model khi hoàn thành

**Postcondition**:

- Model được train và lưu
- Có thể sử dụng cho prediction

---

### UC-02: Backtest Strategy

**Actor**: Data Scientist  
**Precondition**: Có model đã train

**Flow**:

1. Chọn model
2. Chọn period backtest (out-of-sample)
3. Cấu hình:
   - Initial capital
   - Transaction cost
   - Slippage
4. Run Backtest
5. Xem kết quả:
   - Equity curve
   - Daily returns
   - Performance metrics

**Postcondition**:

- Biết được hiệu suất model

---

### UC-03: Xem AI Predictions

**Actor**: Trader  
**Precondition**: Model đang active

**Flow**:

1. Truy cập Predictions
2. Xem dự đoán cho ngày mai:
   - Symbol
   - Signal: BUY/SELL/HOLD
   - Confidence: %
   - Position size gợi ý
3. Có thể filter theo signal

**Postcondition**:

- Có tín hiệu tham khảo

---

### UC-04: Chat với AI Consultant

**Actor**: Investor  
**Precondition**: Chatbot đã cấu hình

**Flow**:

1. Mở chatbot (bottom-right corner)
2. Hỏi về thị trường:
   - "Phân tích VNM hôm nay"
   - "Nên mua hay bán HPG?"
   - "Vẽ biểu đồ RSI của FPT"
3. AI trả lời với:
   - Phân tích text
   - Biểu đồ (nếu có)
   - Khuyến nghị

**Postcondition**:

- Nhận được tư vấn từ AI

---

### UC-05: Automated Trading

**Actor**: System  
**Precondition**: Model và Auto-trade enabled

**Flow**:

1. Mỗi ngày giao dịch:
   - Model chạy prediction
   - Nếu signal = BUY và confidence > threshold
   - Tạo lệnh mua qua stock_trading
2. Modes:
   - Dry-run: Chỉ log, không đặt lệnh
   - Live: Đặt lệnh thật

**Postcondition**:

- Lệnh được đặt tự động
- Có log để review

## DRL Training Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   DRL TRAINING PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │  Stock  │──▶│ Feature │──▶│   Gym   │──▶│  Train  │     │
│  │  Data   │   │Engineer │   │  Env    │   │  Agent  │     │
│  └─────────┘   └─────────┘   └─────────┘   └────┬────┘     │
│                                                  │          │
│                     ┌────────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│               ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│               │ Trained │──▶│Backtest │──▶│ Deploy  │      │
│               │  Model  │   │         │   │         │      │
│               └─────────┘   └─────────┘   └─────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Algorithms Comparison

```
┌────────────────────────────────────────────────────────────┐
│                 DRL ALGORITHMS                              │
├──────────┬──────────────────────────────────────────────────┤
│   PPO    │ Stable, good for beginners, policy gradient     │
├──────────┼──────────────────────────────────────────────────┤
│   A2C    │ Fast training, synchronous, actor-critic        │
├──────────┼──────────────────────────────────────────────────┤
│   SAC    │ Sample efficient, continuous action, off-policy │
├──────────┼──────────────────────────────────────────────────┤
│   TD3    │ Addresses overestimation, twin Q-networks       │
├──────────┼──────────────────────────────────────────────────┤
│   DDPG   │ Continuous control, deterministic policy        │
└──────────┴──────────────────────────────────────────────────┘
```
