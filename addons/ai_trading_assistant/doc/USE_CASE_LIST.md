# DANH SÁCH CHI TIẾT TOÀN BỘ USE CASES

Tài liệu này liệt kê đầy đủ các trường hợp sử dụng (Use Cases) của hệ thống AI Trading Assistant, bao gồm cả các tác vụ quản trị và vận hành chi tiết.

## Phân nhóm 1: Cấu hình & Thiết lập (Configuration)

| ID       | Tên Use Case                 | Mô tả                                                                              |
| :------- | :--------------------------- | :--------------------------------------------------------------------------------- |
| **UC01** | **Cấu hình Kết nối SSI API** | Nhập Client ID, Secret Key để kết nối với SSI FastConnect.                         |
| **UC02** | **Cấu hình FinRL Global**    | Thiết lập thuật toán mặc định (PPO/Ensemble), số bước training (timesteps).        |
| **UC03** | **Cấu hình Quản trị Rủi ro** | Bật/tắt Turbulence Index, thiết lập Stop Loss mặc định cho Chatbot.                |
| **UC04** | **Cấu hình Chatbot**         | Thiết lập System Prompt, chọn Model LLM (GPT-4/Claude), API Key.                   |
| **UC05** | **Phân quyền Người dùng**    | Cấp quyền User (chỉ xem) hoặc Manager (được train/chỉnh sửa config) cho nhân viên. |

## Phân nhóm 2: Quản lý Dữ liệu (Data Management)

| ID       | Tên Use Case                       | Mô tả                                                                       |
| :------- | :--------------------------------- | :-------------------------------------------------------------------------- |
| **UC06** | **Đồng bộ Dữ liệu EOD Thủ công**   | Kích hoạt nút "Fetch Data" để tải dữ liệu cuối ngày ngay lập tức.           |
| **UC07** | **Đồng bộ Dữ liệu Tự động (Cron)** | Hệ thống tự động chạy job tải dữ liệu vào 18:00 hàng ngày.                  |
| **UC08** | **Kiểm tra Chất lượng Dữ liệu**    | Hệ thống tự động scan và báo lỗi các mã thiếu dữ liệu hoặc mất thanh khoản. |
| **UC09** | **Xóa Cache Dữ liệu**              | Xóa dữ liệu tạm để giải phóng bộ nhớ hoặc tải lại từ đầu khi có lỗi.        |

## Phân nhóm 3: Quản lý Chiến lược (Strategy Management)

| ID       | Tên Use Case                         | Mô tả                                                      |
| :------- | :----------------------------------- | :--------------------------------------------------------- |
| **UC10** | **Tạo Chiến lược Mới**               | Định nghĩa một strategy mới (VD: "Bluechips", "Penny").    |
| **UC11** | **Quản lý Watchlist**                | Thêm/Xóa các mã cổ phiếu trong một chiến lược.             |
| **UC12** | **Sao chép Chiến lược**              | Duplicate một chiến lược có sẵn để thử nghiệm tham số mới. |
| **UC13** | **Kích hoạt/Vô hiệu hóa Chiến lược** | Tạm dừng một chiến lược không hiệu quả mà không cần xóa.   |

## Phân nhóm 4: Huấn luyện & Tối ưu AI (Training & Optimization)

| ID       | Tên Use Case                           | Mô tả                                                                          |
| :------- | :------------------------------------- | :----------------------------------------------------------------------------- |
| **UC14** | **Huấn luyện Đơn lẻ (Single Agent)**   | Train một model cụ thể (VD: chỉ dùng PPO) cho chiến lược.                      |
| **UC15** | **Huấn luyện Hợp nhất (Ensemble)**     | Train tổ hợp nhiều model (PPO, A2C, DDPG...) cùng lúc để lấy ý kiến số đông.   |
| **UC16** | **Tự động Tối ưu Tham số (Auto-Tune)** | Chạy Optuna để tìm Learning Rate/Batch Size tối ưu cho mã cổ phiếu "khó tính". |
| **UC17** | **Huấn luyện lại (Retrain)**           | Cập nhật model cũ với dữ liệu mới nhất (Incremental Learning).                 |
| **UC18** | **Xem Log Huấn luyện**                 | Theo dõi quá trình training (Loss, Reward) qua Tensorboard hoặc Log text.      |

## Phân nhóm 5: Vận hành & Giao dịch (Operations & Trading)

| ID       | Tên Use Case                              | Mô tả                                                                             |
| :------- | :---------------------------------------- | :-------------------------------------------------------------------------------- |
| **UC19** | **Sinh Tín hiệu Dự báo (Prediction)**     | Hệ thống tạo tín hiệu Mua/Bán hàng ngày dựa trên model đã train.                  |
| **UC20** | **Xem Chi tiết Dự báo**                   | Xem lý do AI khuyến nghị (Confidence, Indicator status) và Chart kỹ thuật.        |
| **UC21** | **Đặt Lệnh (Place Order)**                | Chuyển tín hiệu AI thành lệnh chờ trên hệ thống giao dịch (Stock Trading module). |
| **UC22** | **Giám sát Turbulence (Crash Detection)** | Hệ thống tự động kích hoạt "Panic Mode" khi chỉ số Market Turbulence tăng vọt.    |
| **UC23** | **Kiểm tra Sức mua (Buying Power Check)** | Hệ thống check tiền mặt khả dụng trước khi Chatbot/AI khuyến nghị mua.            |

## Phân nhóm 6: Phân tích & Báo cáo (Analysis & Reporting)

| ID       | Tên Use Case                      | Mô tả                                                                       |
| :------- | :-------------------------------- | :-------------------------------------------------------------------------- |
| **UC24** | **Xem Báo cáo Backtest**          | Xem hiệu quả quá khứ (Sharpe Ratio, Max Drawdown, Win Rate) của chiến lược. |
| **UC25** | **So sánh Hiệu quả**              | So sánh lợi nhuận giữa "Buy & Hold" vs "AI Trading".                        |
| **UC26** | **Xem Lịch sử Giao dịch Giả lập** | Xem lại các lệnh mua bán mà AI đã thực hiện trong quá trình Backtest.       |
| **UC27** | **Dashboard Monitor**             | Màn hình tổng quan trạng thái các Model (Đang chạy, Lỗi, Hiệu quả tốt/xấu). |

## Phân nhóm 7: Tương tác Chatbot (Assistant Interaction)

| ID       | Tên Use Case                   | Mô tả                                            |
| :------- | :----------------------------- | :----------------------------------------------- |
| **UC28** | **Hỏi Giá & Thông tin Cơ bản** | "Giá FPT bao nhiêu?", "PE của VCB là mấy?".      |
| **UC29** | **Yêu cầu Phân tích Kỹ thuật** | "Vẽ chart HPG và nhận định xu hướng".            |
| **UC30** | **Xin Lời khuyên Đầu tư**      | "Có nên mua MWG lúc này không?".                 |
| **UC31** | **Giải thích Thuật ngữ**       | "Chỉ số RSI là gì?", "Ensemble Learning là gì?". |
| **UC32** | **Báo cáo Tài sản**            | "Tổng tài sản của tôi hiện tại là bao nhiêu?".   |

## Phân nhóm 8: Bảo trì & Xử lý Lỗi (Maintenance)

| ID       | Tên Use Case                  | Mô tả                                                   |
| :------- | :---------------------------- | :------------------------------------------------------ |
| **UC33** | **Xem Error Logs**            | Xem chi tiết lỗi khi Training hoặc Prediction thất bại. |
| **UC34** | **Khởi động lại Service**     | Restart các background service nếu bị treo.             |
| **UC35** | **Sao lưu Model (Backup)**    | Export file model (.zip) ra ngoài để lưu trữ.           |
| **UC36** | **Khôi phục Model (Restore)** | Import file model đã lưu để sử dụng lại.                |
