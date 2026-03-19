import time
import logging
import requests
from odoo import models, api

_logger = logging.getLogger(__name__)

# Unified default — must match ssi_config.py field default
DEFAULT_LLM_MODEL = 'google/gemma-3-27b-it:free'


class AIChatbotService(models.AbstractModel):
    _name = 'ai.chatbot.service'
    _description = 'AI Chatbot LLM Integration Service'

    # ──────────────────────────────────────────────
    # Core LLM Call (with retry & structured response)
    # ──────────────────────────────────────────────
    @api.model
    def call_openrouter(self, prompt, system_content="", max_retries=2, timeout=60):
        """
        Gọi OpenRouter LLM API với retry logic.
        Returns: dict {'success': bool, 'content': str, 'error': str|None}
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('ai_trading.llm_api_key')
        if not api_key:
            return {
                'success': False,
                'content': '',
                'error': 'missing_api_key',
            }

        model_name = self.env['ir.config_parameter'].sudo().get_param(
            'ai_trading.llm_model_name', DEFAULT_LLM_MODEL
        )

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": prompt})

        data = {"model": model_name, "messages": messages}

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                if response.status_code == 200:
                    body = response.json()
                    content = body.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if content:
                        return {'success': True, 'content': content, 'error': None}
                    last_error = 'empty_response'
                else:
                    last_error = f"http_{response.status_code}"
                    _logger.warning("OpenRouter API HTTP %s (attempt %d): %s",
                                    response.status_code, attempt + 1, response.text[:300])
            except requests.exceptions.Timeout:
                last_error = 'timeout'
                _logger.warning("OpenRouter API timeout (attempt %d/%d)", attempt + 1, max_retries + 1)
            except requests.exceptions.ConnectionError:
                last_error = 'connection_error'
                _logger.warning("OpenRouter API connection error (attempt %d/%d)", attempt + 1, max_retries + 1)
            except Exception as e:
                last_error = str(e)
                _logger.error("OpenRouter API unexpected error: %s", e)

            # Exponential backoff before retry
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 4))

        return {'success': False, 'content': '', 'error': last_error}

    # ──────────────────────────────────────────────
    # Expert Analysis (for TICKER cards)
    # ──────────────────────────────────────────────
    @api.model
    def get_expert_analysis(self, symbol, price, date, signal, buy_low, buy_high, t1, t2,
                            rsi, sma, macd, algo, sharpe, return_pct, drawdown, pred_action,
                            **kwargs):
        """Extended expert analysis with multi-indicator context."""
        def f(v):
            return f"{v / 1000:,.2f}"

        fallback = (
            f"Mã {symbol} đang giao dịch tại mức {f(price)}. "
            f"Dữ liệu kỹ thuật cho thấy tín hiệu {signal} với vùng hỗ trợ quanh {f(buy_low)}."
        )

        from datetime import datetime
        import pytz
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')
        current_year = datetime.now(vn_tz).year

        # Build extended indicator context
        ema9 = kwargs.get('ema9', 0)
        ema50 = kwargs.get('ema50', 0)
        bb_pct = kwargs.get('bb_pct', 0.5)
        bb_width = kwargs.get('bb_width', 0)
        stoch_k = kwargs.get('stoch_k', 50)
        stoch_d = kwargs.get('stoch_d', 50)
        adx = kwargs.get('adx', 20)
        confluence = kwargs.get('confluence', 0)
        vol_ratio = kwargs.get('vol_ratio', 1.0)

        # Descriptive context for AI
        bb_pos = "giữa band" if 0.2 < bb_pct < 0.8 else ("gần đáy Bollinger" if bb_pct <= 0.2 else "gần đỉnh Bollinger")
        ema_status = "EMA9 > EMA50 (xu hướng tăng)" if ema9 > ema50 else "EMA9 < EMA50 (xu hướng giảm)"
        adx_desc = "Không có xu hướng rõ" if adx < 20 else ("Xu hướng trung bình" if adx < 25 else ("Xu hướng mạnh" if adx < 40 else "Xu hướng rất mạnh"))
        stoch_zone = "quá bán" if stoch_k < 20 else ("quá mua" if stoch_k > 80 else "trung tính")
        vol_desc = "thấp" if vol_ratio < 0.7 else ("trung bình" if vol_ratio < 1.3 else ("cao" if vol_ratio < 2.0 else "đột biến"))

        prompt = f"""
NGỮ CẢNH THỊ TRƯỜNG & KẾT QUẢ AI DỰ ĐOÁN:
- Hôm nay là ngày hiện tại thực tế: {current_date_str} (Năm {current_year})
- Mã cổ phiếu: {symbol} (Dữ liệu kỹ thuật ứng với ngày làm việc gần nhất: {date})
- Thuật toán AI FinRL: {algo.upper()} | Sharpe Ratio (Test Set): {sharpe:.2f}
- Tín hiệu Mạng Nơ-ron (Agent Action): {pred_action:.3f} -> KL: {signal}
- Vùng giá Khuyến nghị: Mua {f(buy_low)}-{f(buy_high)} | Chốt lời T+: {f(t1)}-{f(t2)}

BỐI CẢNH CHỈ BÁO KỸ THUẬT (8 chỉ báo):
1. RSI(14) = {rsi:.1f} | Stochastic({stoch_k:.0f}/{stoch_d:.0f}) = vùng {stoch_zone}
2. MACD = {macd:.2f} | {ema_status}
3. Bollinger Band: giá ở vị trí {bb_pos} (BB%={bb_pct:.2f}, BW={bb_width:.1f}%)
4. ADX(14) = {adx:.1f}: {adx_desc}
5. Khối lượng: {vol_desc} (ratio = {vol_ratio:.1f}x trung bình 20 phiên)
6. Confluence Score (tổng hợp 8 tín hiệu x trọng số): {confluence:.3f} (-1.0 Bearish → +1.0 Bullish)

YÊU CẦU ĐẶC THÙ THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM (TẠI THỜI ĐIỂM HIỆN TẠI {current_year}):
1. Phân tích TỔNG HỢP tất cả 8 chỉ báo trên kết hợp kết quả AI FinRL để đưa ra CHIẾN LƯỢC ĐẦU TƯ rõ ràng, cụ thể. Quan tâm đặc biệt đến:
   - Sự đồng thuận/phân kỳ giữa các chỉ báo (VD: RSI quá bán NHƯNG ADX yếu = không đáng tin)
   - Bollinger Band Squeeze (nếu BB width thấp) = tiềm năng bùng nổ
   - Dòng tiền (volume ratio) có xác nhận xu hướng không
2. Tuyệt đối KHÔNG nhắc lại các con số cụ thể (vì người dùng đã nhìn thấy trên biểu đồ).
3. Chiến lược hành động: ĐẶC BIỆT LƯU Ý T+2.5 và Biên độ dao động (HOSE/VN30: 7%, HNX: 10%, UPCOM: 15%). Nếu lãi kỳ vọng quá lớn, nhắc nhở chốt lời theo từng phần.
4. Trình bày súc tích (4-5 câu), phong thái Giám đốc Chiến lược tại các ngân hàng đầu tư lớn.
"""
        system_content = (
            f"Bạn là ARC Intelligence - Chuyên gia Chiến lược Đầu tư am hiểu sâu sắc thị trường "
            f"chứng khoán Việt Nam (HOSE, HNX, UPCOM) với đặc thù T+2.5. Hiện tại là năm {current_year}. "
            f"Bạn kết hợp phân tích kỹ thuật đa chỉ báo (RSI, MACD, Bollinger Bands, Stochastic, ADX, OBV) "
            f"với tín hiệu AI FinRL để đưa ra nhận định có chiều sâu. "
            f"Chú trọng phân tích sự đồng thuận giữa các chỉ báo, không chỉ dựa vào một indicator đơn lẻ."
        )

        result = self.call_openrouter(prompt, system_content)
        if not result['success']:
            return fallback
        return result['content'].replace('\n', '<br/>')

