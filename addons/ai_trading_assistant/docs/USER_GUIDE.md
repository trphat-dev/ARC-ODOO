# AI Trading Assistant - Hướng Dẫn Sử Dụng

## Giới thiệu

**AI Trading Assistant** (AI Consultant) là module tích hợp AI cho giao dịch chứng khoán, sử dụng FinRL Deep Reinforcement Learning và tích hợp SSI FastConnect API.

## Tính năng chính

- **SSI FastConnect Integration**: Dữ liệu thị trường VN (HOSE, HNX, UPCOM)
- **FinRL DRL**: Các thuật toán PPO, A2C, SAC, TD3, DDPG
- **Technical Indicators**: RSI, MACD, Bollinger Bands, SMA
- **Backtesting**: Test chiến lược với dữ liệu lịch sử
- **AI Chatbot**: Tư vấn đầu tư real-time

## Yêu cầu

- **Odoo version**: 18.0
- **Dependencies**: `base`, `web`, `mail`, `bus`, `stock_data`, `stock_trading`
- **Python packages**:
  - `stable_baselines3`
  - `gymnasium`
  - `torch`
  - `pandas`, `pandas_ta`
  - `numpy`, `plotly`, `matplotlib`
  - `openai` (for OpenRouter)
- **License**: LGPL-3

## Cài đặt

```bash
# Cài đặt packages
pip install stable-baselines3 gymnasium torch pandas pandas_ta plotly matplotlib openai

# Cài đặt module
Odoo Settings → Apps → Search "AI Consultant" → Install
```

## Cấu hình

### Cấu hình AI Trading

1. Truy cập **AI Trading → Configuration**
2. Cấu hình các parameters:
   - Training timesteps
   - Algorithm (PPO/A2C/SAC...)
   - Technical indicators
3. Save

### Cấu hình Chatbot

1. Truy cập **AI Chatbot → Global Config**
2. Nhập OpenRouter API Key
3. Chọn model (GPT-4, Claude...)
4. Save

## Hướng dẫn sử dụng

### 1. Training Model

1. Chọn Strategy
2. Chọn mã CK để train
3. Chọn khoảng thời gian dữ liệu
4. Chọn algorithm và parameters
5. Start Training
6. Theo dõi qua TensorBoard

### 2. Backtesting

1. Chọn model đã train
2. Chọn khoảng thời gian test
3. Run Backtest
4. Xem kết quả:
   - Total Return
   - Sharpe Ratio
   - Max Drawdown
   - Trade Analysis

### 3. AI Predictions

- Xem dự đoán từ model
- Signal: Buy/Sell/Hold
- Confidence score

### 4. AI Chatbot

- Hỏi đáp về thị trường
- Phân tích kỹ thuật
- Tư vấn chiến lược
- Tạo biểu đồ

## Cấu trúc Backend

```
views/
├── ai_trading_config_views.xml      # Cấu hình
├── ai_strategy_views.xml            # Chiến lược
├── ai_model_training_views.xml      # Training
├── ai_prediction_views.xml          # Dự đoán
├── backtest_wizard_views.xml        # Backtest
├── ai_chatbot_views.xml             # Chatbot
├── ai_chatbot_global_config_views.xml
└── ai_trading_menus.xml
```

## Technical Indicators

| Indicator | Mô tả                                 |
| --------- | ------------------------------------- |
| RSI       | Relative Strength Index               |
| MACD      | Moving Average Convergence Divergence |
| BB        | Bollinger Bands                       |
| ATR       | Average True Range                    |
| SMA50/200 | Simple Moving Average                 |

## Lưu ý

- Training cần GPU để tăng tốc
- Backtest không đảm bảo lợi nhuận tương lai
- AI Chatbot chỉ mang tính tham khảo
- Không phải lời khuyên đầu tư chính thức
