from odoo import models, fields, api
import requests

class AIChatbotService(models.AbstractModel):
    _name = 'ai.chatbot.service'
    _description = 'AI Chatbot LLM Integration Service'

    @api.model
    def call_openrouter(self, prompt, system_content=""):
        api_key = self.env['ir.config_parameter'].sudo().get_param('ai_trading.llm_api_key')
        if not api_key:
            return "Vui lòng cấu hình OpenRouter API Key để sử dụng tính năng này."
        
        model_name = self.env['ir.config_parameter'].sudo().get_param('ai_trading.llm_model_name', 'arcee-ai/trinity-large-preview:free')
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            messages = []
            if system_content:
                messages.append({"role": "system", "content": system_content})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": model_name,
                "messages": messages,
                "extra_body": {"reasoning": {"enabled": True}}
            }
            response = requests.post(url, headers=headers, json=data, timeout=20)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f">>>>> OPENROUTER API ERROR: {str(e)}")
        return "Kết nối AI đang bận, vui lòng thử lại sau."

    @api.model
    def get_expert_analysis(self, symbol, price, date, signal, buy_low, buy_high, t1, t2, rsi, sma, macd, algo, sharpe, return_pct, drawdown, pred_action):
        def f(v): return f"{v/1000:,.2f}"
        fallback = f"Mã {symbol} đang giao dịch tại mức {f(price)}. Dữ liệu kỹ thuật cho thấy tín hiệu {signal} với vùng hỗ trợ quanh {f(buy_low)}."
        
        # Luôn lấy ngày và năm hiển tại để làm context chuẩn nhất cho nhận định
        from datetime import datetime
        import pytz
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')
        current_year = datetime.now(vn_tz).year
        
        prompt = f"""
NGỮ CẢNH THỊ TRƯỜNG & KẾT QUẢ AI DỰ ĐOÁN:
- Hôm nay là ngày hiện tại thực tế: {current_date_str} (Năm {current_year})
- Mã cổ phiếu: {symbol} (Dữ liệu kỹ thuật ứng với ngày làm việc gần nhất: {date})
- Giá: {f(price)} | SMA20: {f(sma)} | RSI: {rsi:.1f} | MACD: {macd:.2f}
- Thuật toán AI FinRL: {algo.upper()} | Sharpe Ratio (Test Set): {sharpe:.2f}
- Tín hiệu Mạng Nơ-ron (Agent Action): {pred_action:.3f} (Khoảng từ -1.0 BÁN MẠNH đến +1.0 MUA MẠNH) -> KL: {signal}
- Vùng giá Khuyến nghị: Mua {f(buy_low)}-{f(buy_high)} | Chốt lời T+: {f(t1)}-{f(t2)}

YÊU CẦU ĐẶC THÙ THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM (TẠI THỜI ĐIỂM HIỆN TẠI {current_year}):
1. Tổng hợp dữ liệu kỹ thuật và kết quả Backtest AI ở trên để đưa ra CHIẾN LƯỢC ĐẦU TƯ CHUẨN QUỐC TẾ nhưng phù hợp Việt Nam. Nhìn nhận thị trường theo bối cảnh thực tế năm {current_year}.
2. Tuyệt đối KHÔNG nhắc lại các con số cụ thể về giá, RSI, SMA hay MACD trong nội dung nhận xét (vì người dùng đã nhìn thấy trên biểu đồ).
3. Đưa ra chiến lược hành động cụ thể. ĐẶC BIỆT LƯU Ý: Thị trường Việt Nam áp dụng cơ chế thanh toán T+2.5 (Mua xong 2.5 ngày sau hàng mới về để bán) và Biên độ dao động (HOSE/VN30: 7%, HNX: 10%, UPCOM: 15%). Nếu lãi kỳ vọng quá lớn, bạn phải nhắc nhở nỗ lực chốt lời theo từng phần để tránh trượt giá.
4. Trình bày súc tích (3-4 câu), phong thái Giám đốc Chiến lược tại các ngân hàng đầu tư lớn, am hiểu dòng tiền tạo lập (Shark/Whale).
"""
        system_content = f"Bạn là ARC Intelligence - Chuyên gia Chiến lược Đầu tư am hiểu sâu sắc thị trường chứng khoán Việt Nam (HOSE, HNX, UPCOM) với đặc thù T+2.5. Hiện tại là thời điểm kinh tế năm {current_year}. Nhiệm vụ của bạn là biến những con số kỹ thuật khô khan thành các nhận định có chiều sâu. Giải thích phải có tính thời sự, am hiểu đặc tính của từng mã cổ phiếu (Bluechip, Midcap, đầu cơ) và rủi ro thanh khoản T+2.5."
        
        analysis = self.call_openrouter(prompt, system_content)
        if "Kết nối AI" in analysis:
            return fallback
        return analysis.replace('\n', '<br/>')
