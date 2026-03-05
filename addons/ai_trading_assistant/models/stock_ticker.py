from odoo import models, fields, api
import json
import requests
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StockTicker(models.Model):
    _name = 'stock.ticker'
    _description = 'Stock Ticker (Mã chứng khoán)'
    
    name = fields.Char(string='Mã CK (Symbol)', required=True, index=True)
    market = fields.Selection([
        ('HOSE', 'HOSE'),
        ('HNX', 'HNX'),
        ('UPCOM', 'UPCOM'),
    ], string='Sàn Giao Dịch', required=True, default='HOSE')
    company_name = fields.Char(string='Tên Công Ty')
    sector = fields.Char(string='Ngành nghề')
    is_active = fields.Boolean(string='Đang giao dịch', default=True)
    
    candle_ids = fields.One2many('stock.candle', 'ticker_id', string='Dữ liệu Nến')
    
    ai_strategy_ids = fields.Many2many(
        'ai.strategy',
        compute='_compute_ai_strategies',
        string='Chiến lược AI Áp dụng'
    )

    def _compute_ai_strategies(self):
        for rec in self:
            strategies = self.env['ai.strategy'].search([
                '|', ('ticker_ids', '=', False), ('ticker_ids', 'in', rec.id)
            ])
            rec.ai_strategy_ids = strategies

    _sql_constraints = [
        ('unique_ticker', 'unique(name)', 'Ma chung khoan nay da ton tai!')
    ]



    @api.model
    def ai_chat(self, message):
        """
        Logic xử lý tin nhắn ĐA NĂNG: Phân loại ý định, tư vấn cổ phiếu, vĩ mô, và trò chuyện chung.
        """
        # 1. Phân loại ý định (Intent Classification) & Trích xuất mã bằng LLM
        system_prompt_extract = """Bạn là trợ lý ảo phân loại câu hỏi chứng khoán. Đọc câu hỏi và trả về ĐÚNG 2 dòng như sau (Tuyệt đối không giải thích thêm):
INTENT: [TICKER hoặc MACRO hoặc CHAT]
SYMBOLS: [Danh sách mã cách nhau bởi dấu phẩy, hoặc NONE]

Quy tắc phân loại:
- TICKER: Khi người dùng hỏi cần phân tích, đánh giá, mua bán các mã cụ thể (VD: "Phân tích SSI", "Nên mua HPG không?").
- MACRO: Khi người dùng hỏi tổng quan thị trường, điểm số VN-Index, xu hướng chung (VD: "Thị trường nay sao", "VN-Index có sập không?").
- CHAT: Khi người dùng chào hỏi, hỏi kiến thức, giải thích thuật ngữ, công thức biểu đồ, hoặc trò chuyện chung (VD: "RSI là gì?", "Chào bạn").
- SYMBOLS: Điền các mã (VD: SSI, HPG) nếu nhắc tới. Ghi NONE nếu không.
"""
        extract_response = self.env['ai.chatbot.service'].call_openrouter(message, system_prompt_extract).strip().upper()
        
        intent = "CHAT"
        if "INTENT: TICKER" in extract_response: intent = "TICKER"
        elif "INTENT: MACRO" in extract_response: intent = "MACRO"
        
        symbols = []
        if intent == "TICKER" or "SYMBOLS:" in extract_response:
            lines = extract_response.split('\n')
            for line in lines:
                if line.startswith("SYMBOLS:"):
                    ticker_part = line.split("SYMBOLS:")[-1]
                    if "NONE" not in ticker_part:
                        symbols = re.findall(r'\b[A-Z0-9]{3,}\b', ticker_part)
                        symbols = list(set(symbols))
                        break

        if not symbols and intent == "TICKER":
            intent = "MACRO" # Fallback nếu hỏi chung chung mà AI lỡ xếp vào TICKER

        if intent == "CHAT":
            import pytz
            from datetime import datetime
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            current_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')
            
            system_prompt = f"""Bạn là ARC Intelligence - Cố vấn tài chính am hiểu chứng khoán Việt Nam. Hôm nay là {current_date_str}.
Nhiệm vụ của bạn: Trả lời câu hỏi giao tiếp, giải thích kiến thức, thuật ngữ, chia sẻ kinh nghiệm đầu tư một cách chuyên nghiệp, khách quan và dễ hiểu. 
Tuyệt đối KHÔNG ĐƯỢC BỊA ĐẶT SỐ LIỆU GIÁ CỔ PHIẾU DO AI KHÔNG CÓ DỮ LIỆU SÁNG NAY. 
Nếu người dùng hỏi các chủ đề không liên quan đến tài chính, chứng khoán hoặc kinh tế, hãy từ chối lịch sự và hướng họ trở lại chủ đề đầu tư."""
            
            response = self.env['ai.chatbot.service'].call_openrouter(message, system_prompt)
            return {
                'status': 'success', 
                'type': 'general',
                'data': {
                    'text_content': response.replace('\n', '<br/>')
                }
            }

        if intent == "MACRO":
            # --- XỬ LÝ NHẬN ĐỊNH VĨ MÔ TOÀN CẢNH ---
            market_context = "Hiện chưa lấy được dữ liệu thị trường mới nhất."
            latest_vni_price = None
            
            ssi_id = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_consumer_id', '')
            ssi_secret = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_consumer_secret', '')
            api_url = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_api_url', 'https://fc-data.ssi.com.vn/')
            
            if ssi_id and ssi_secret:
                try:
                    import pytz
                    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                    from ssi_fc_data import fc_md_client, model as ssi_model
                    class Config: pass
                    conf = Config()
                    conf.consumerID, conf.consumerSecret, conf.url = ssi_id, ssi_secret, api_url
                    client = fc_md_client.MarketDataClient(conf)
                    
                    # Lấy data VNINDEX rất gần (3 ngày đổ lại) để đảm bảo tươi mới
                    end_d = datetime.now(vn_tz)
                    start_d = end_d - timedelta(days=5)
                    req = ssi_model.daily_ohlc('VNINDEX', start_d.strftime('%d/%m/%Y'), end_d.strftime('%d/%m/%Y'), 1, 10, True)
                    res = client.daily_ohlc(conf, req)
                    
                    import json
                    data = res if isinstance(res, dict) else json.loads(res)
                    if str(data.get('status')) == '200' and data.get('data'):
                        candles = data.get('data', [])
                        if candles:
                            latest = candles[0]
                            latest_vni_price = float(latest.get('Close', 0))
                            if latest_vni_price > 0:
                                market_context = f"VN-Index phiên mới nhất ({latest.get('TradingDate')}): Đóng cửa tại {latest.get('Close')} điểm. Khối lượng: {latest.get('Volume', 0):,} cp."
                except Exception as e:
                    market_context = f"Lỗi dữ liệu vĩ mô: {e}"

            vni_prompt_part = f"Hãy cung cấp nhận định chuyên sâu dựa trên số điểm {latest_vni_price} này." if latest_vni_price else "Hãy cung cấp nhận định chuyên sâu dựa trên tình trạng hiện tại."
            
            import pytz
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            current_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')
            
            system_prompt = f"""Bạn là ARC Intelligence - Giám đốc Phân tích vĩ mô. Hôm nay là ngày thực tế: {current_date_str}.
Người dùng đang hỏi về vĩ mô/toàn cảnh thị trường chứng khoán Việt Nam.
[DỮ LIỆU VN-INDEX MỚI NHẤT]: {market_context}
{vni_prompt_part} Đề xuất các nhóm ngành hot và 3 mã tiềm năng."""
            
            response = self.env['ai.chatbot.service'].call_openrouter(message, system_prompt)
            return {
                'status': 'success', 
                'type': 'general',
                'data': {
                    'text_content': response
                }
            }
            
        # --- XỬ LÝ PHÂN TÍCH NHIỀU MÃ CHỨNG KHOÁN ---
        multi_data = []
        for sym in symbols:
            try:
                result = self._analyze_ticker_data(sym)
                multi_data.append(result)
            except Exception as e:
                multi_data.append({
                    'status': 'exception',
                    'symbol': sym,
                    'message': str(e)
                })

        return {
            'status': 'success', 
            'type': 'multi',
            'data': multi_data
        }

    def _analyze_ticker_data(self, symbol):
        """Hàm nội bộ thực hiện trọn vẹn quy trình: Fetch -> AI Inference -> Trả về dict data cho 1 mã."""
        ticker = self.sudo().search([('name', '=', symbol)], limit=1)
        if not ticker:
            ticker = self.sudo().create({'name': symbol, 'company_name': f'Mã {symbol}', 'market': 'HOSE', 'is_active': True})
            
        # 1. Sync Data (Chuẩn hóa múi giờ VN)
        try:
            import pytz
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            to_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')
            latest_c = self.env['stock.candle'].sudo().search([('ticker_id', '=', ticker.id)], order='date desc', limit=1)
            from_date_str = (latest_c.date - timedelta(days=2)).strftime('%d/%m/%Y') if latest_c else (datetime.now(vn_tz) - timedelta(days=150)).strftime('%d/%m/%Y')
            fetcher = self.env['ssi.data.fetcher'].sudo().create({})
            fetcher.fetch_daily_ohlcv(symbol, from_date_str, to_date_str)
        except Exception: pass
            
        # 2. Chuẩn bị DataFrame
        local_candles = self.env['stock.candle'].sudo().search([('ticker_id', '=', ticker.id)], order='date desc', limit=150)
        if not local_candles:
            return {'status': 'error', 'symbol': symbol, 'message': f'Mã {symbol} thiếu dữ liệu.'}
            
        data_list = []
        for c in local_candles:
            data_list.append({
                'date': c.date.strftime('%Y-%m-%d'), 'tic': symbol,
                'open': float(c.open), 'high': float(c.high), 'low': float(c.low), 'close': float(c.close), 'volume': float(c.volume)
            })
        df = pd.DataFrame(data_list).sort_values('date', ascending=True)
        df['Close'] = df['close']
        df['TradingDate'] = df['date']
        
        # 3. Lấy giá Real-time SSI (để card luôn tươi mới nhất ngay giây phút này)
        real_latest_price = None
        real_latest_date = None
        ssi_id = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_consumer_id', '')
        ssi_secret = self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_consumer_secret', '')
        if ssi_id and ssi_secret:
            try:
                import pytz
                vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                from ssi_fc_data import fc_md_client, model as ssi_model
                class Conf: pass
                conf = Conf(); conf.consumerID, conf.consumerSecret, conf.url = ssi_id, ssi_secret, self.env['ir.config_parameter'].sudo().get_param('ai_trading.ssi_api_url', 'https://fc-data.ssi.com.vn/')
                client = fc_md_client.MarketDataClient(conf)
                res_t = client.daily_stock_price(conf, ssi_model.daily_stock_price(symbol, datetime.now(vn_tz).strftime('%d/%m/%Y'), datetime.now(vn_tz).strftime('%d/%m/%Y'), 1, 1, ticker.market.lower()))
                d_t = res_t if isinstance(res_t, dict) else json.loads(res_t)
                if str(d_t.get('status')) == '200' and d_t.get('data'):
                    today = d_t['data'][0]
                    real_latest_price = float(today.get('MatchPrice') or today.get('ClosePrice'))
                    real_latest_date = str(today.get('TradingDate', datetime.now(vn_tz).strftime('%d/%m/%Y')))
                    # Cập nhật DB
                    t_date = datetime.strptime(real_latest_date, '%d/%m/%Y').date()
                    ex = self.env['stock.candle'].sudo().search([('ticker_id', '=', ticker.id), ('date', '=', t_date)], limit=1)
                    vals = {'ticker_id': ticker.id, 'date': t_date, 'close': real_latest_price, 'open': float(today.get('OpenPrice', real_latest_price)), 'high': float(today.get('HighestPrice', real_latest_price)), 'low': float(today.get('LowestPrice', real_latest_price)), 'volume': float(today.get('TotalVolumn', 0))}
                    if ex: ex.sudo().write(vals)
                    else: self.env['stock.candle'].sudo().create(vals)
            except Exception: pass

        if not real_latest_price:
            real_latest_price = df.iloc[-1]['close']
            real_latest_date = df.iloc[-1]['date']

        # Update DF with latest price
        if str(df.iloc[-1]['date']) == real_latest_date: df.loc[df.index[-1], 'close'] = real_latest_price
        else: df = pd.concat([df, pd.DataFrame([{'date': real_latest_date, 'tic': symbol, 'close': real_latest_price, 'Close': real_latest_price}])], ignore_index=True)
        
        # 4. Tech Indicators
        df['sma20'] = df['close'].rolling(window=20).mean()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['rsi'] = 100 - (100 / (1 + (gain / loss)))
        exp1, exp2 = df['close'].ewm(span=12).mean(), df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['signal_line'] = df['macd'].ewm(span=9).mean()
        
        latest_row = df.iloc[-1]
        l_price, l_date = float(latest_row['close']), str(latest_row['date'])
        rsi_v, sma_v = float(latest_row['rsi']), float(latest_row['sma20'])
        macd_v, sig_v = float(latest_row['macd']), float(latest_row['signal_line'])
        
        # 5. Inference
        active_strategy = self.env['ai.strategy'].sudo().search([('status', '=', 'active'), '|', ('ticker_ids', '=', False), ('ticker_ids', 'in', ticker.id)], limit=1, order='id desc')
        
        def fmt(v): return f"{v/1000:,.2f}"
        
        if not active_strategy:
            return {
                'status': 'success',
                'symbol': symbol,
                'type': 'no_model',
                'data': {
                    'symbol': symbol,
                    'latest_price': fmt(l_price),
                    'sma_val': fmt(sma_v),
                    'rsi_val': f"{rsi_v:.1f}",
                    'latest_date': l_date
                }
            }
            
        pred_action, ai_error_msg = active_strategy.get_inference_action(ticker)
        
        # 6. Cải tiến Logic Signals & Dynamic Metrics (Dựa trên ATR, MACD, RSI, Hỗ trợ/Kháng cự)
        # Tính Average True Range (ATR) 14 ngày làm thước đo biến động động
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        atr_v = float(df.iloc[-1]['atr']) or (l_price * 0.02) # Dự phòng 2% nếu ATR null
        
        # Xác định Kháng cự (Resistance) và Hỗ trợ (Support) gần nhất bằng Window 20 ngày
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        
        support_v = max(recent_low, sma_v - (atr_v * 1.5))
        resist_v = min(recent_high, sma_v + (atr_v * 2.0))
        if resist_v <= l_price: resist_v = l_price + (atr_v * 2.0)
        
        # Tổng hợp tín hiệu AI + Technicals
        ai_conf = 0.0
        tech_signal = "TRUNG LẬP / ĐỨNG NGOÀI"
        
        is_bullish_trend = (macd_v > sig_v) and (l_price > sma_v)
        is_bearish_trend = (macd_v < sig_v) and (l_price < sma_v)
        
        if pred_action == -999.0: 
            tech_signal = ai_error_msg or "LỖI CHƯA CÀI ĐẶT THƯ VIỆN AI"
        else:
            ai_conf = min(abs(pred_action * 100), 100)
            
            # Nới lỏng Threshold của AI xuống 0.05, hoặc nếu AI gần 0 nhưng Chart quá rõ rệt 
            # thì Fallback 100% sang phân tích kỹ thuật.
            if pred_action >= 0.05 or (abs(pred_action) < 0.05 and is_bullish_trend):
                # AI báo xu hướng Lên -> Hỗ trợ Mua
                if is_bullish_trend and rsi_v < 70:
                    tech_signal = "MUA"
                elif rsi_v >= 70:
                    tech_signal = "TRUNG LẬP / ĐỨNG NGOÀI" # Đang vùng rủi ro RSI Căng
                else:
                    tech_signal = "MUA" # Thăm dò
            elif pred_action <= -0.05 or (abs(pred_action) < 0.05 and is_bearish_trend):
                # AI báo xu hướng Xuống -> Hỗ trợ Bán
                if is_bearish_trend and rsi_v > 30:
                    tech_signal = "BÁN"
                elif rsi_v <= 30:
                    tech_signal = "TRUNG LẬP / ĐỨNG NGOÀI" # Quá bán, rủi ro mất hàng nếu rũ
                else:
                    tech_signal = "BÁN"
            else:
                # Trạng thái Sideway rập rình / Xu hướng hẹp
                if rsi_v < 40:
                    tech_signal = "MUA"
                elif rsi_v > 60:
                    tech_signal = "BÁN"
                else:
                    tech_signal = "TRUNG LẬP / ĐỨNG NGOÀI"

        # Tính toán các star metrics (1-5)
        price_s = min(max(int(rsi_v / 20) + 1, 1), 5)
        diff_sma = (l_price - sma_v) / sma_v * 100
        trend_s = 5 if diff_sma > 5 else (4 if diff_sma > 2 else (3 if diff_sma > -2 else (2 if diff_sma > -5 else 1)))
        pos_s = 5 if macd_v > sig_v and macd_v > 0 else (4 if macd_v > sig_v else (3 if macd_v > 0 else 2))
        vol_avg = df['volume'].tail(20).mean() or 1.0
        vol_ratio = latest_row['volume'] / vol_avg
        flow_s = min(max(int(vol_ratio * 2) + 1, 1), 5)
        volat_s = min(max(5 - int(abs(diff_sma) / 3), 1), 5)
        base_s = min(max(int((l_price - recent_low) / (recent_low * 0.02 or 1)) + 1, 1), 5)

        # Định cỡ Vị thế & Rủi ro/Lợi nhuận KỲ VỌNG theo ATR động (Không dùng hardcode 15% hay 5% nữa)
        # Điểm Mua = Gần hỗ trợ hoặc quanh giá hiện tại nếu đang up trend
        anchor_buy = l_price if is_bullish_trend else min(l_price, support_v)
        b_low, b_high = anchor_buy - (atr_v * 0.5), anchor_buy + (atr_v * 0.5)
        
        # Điểm cắt lỗ: Dưới vùng hỗ trợ 1 khoảng ATR
        stop_loss = support_v - atr_v
        if stop_loss > l_price: stop_loss = l_price - (atr_v * 1.5) # Fail-safe
        risk_buf_pct = ((l_price - stop_loss) / l_price) * 100
        
        # Điểm chốt lời: Kháng cự gần nhất hoặc nảy theo tỷ lệ R:R = 1:2
        t1 = max(resist_v, l_price + (l_price - stop_loss) * 1.5)
        t2 = t1 + (atr_v * 2)
        swing_ret_pct = ((t1 - l_price) / l_price) * 100
        
        # Không hardcode 1% hay 2%, chỉ giới hạn trên để không hoang tưởng
        swing_ret_pct = min(swing_ret_pct, 40.0) 
        risk_buf_pct = min(risk_buf_pct, 15.0)

        expert_comment = self.env['ai.chatbot.service'].get_expert_analysis(
            symbol, l_price, l_date, tech_signal, b_low, b_high, t1, t2, rsi_v, sma_v, macd_v,
            active_strategy.algorithm or 'ppo', active_strategy.sharpe_ratio or 0.0, swing_ret_pct, risk_buf_pct, pred_action
        )
        
        action_c = "#00d084" if "MUA" in tech_signal else ("#e74c3c" if "BÁN" in tech_signal else "#f39c12")
        score = min(max(int(rsi_v * 0.6 + (15 if macd_v > sig_v else 0) + (15 if l_price > sma_v else 0) + (10 if pred_action > 0 else 0)), 10), 95)
        khq_c = "#10b981" if score > 65 else ("#f59e0b" if score > 45 else "#ef4444")
        khq_l = "Khả quan" if score > 65 else ("Trung lập" if score > 45 else "Kém khả quan")

        is_neg = ("BÁN" in tech_signal)
        is_neutral = ("TRUNG LẬP" in tech_signal)
        
        if is_neutral:
            z_label, z_val = "", ""
            t_label, t_val, t_color = "", "", ""
            p_label, p_val = "", ""
        elif is_neg:
            z_label, z_val = "Vùng canh bán", f"{fmt(l_price)} - {fmt(t1)}"
            t_label, t_val, t_color = "", "", "" # Bỏ cắt lỗ/ngưỡng giá
            p_label, p_val = "", "" # Bỏ rủi ro sụt giảm
        else:
            z_label, z_val = "Vùng canh mua", f"{fmt(b_low)} - {fmt(b_high)}"
            t_label, t_val, t_color = "Mục tiêu chốt lời", f"{fmt(t1)} - {fmt(t2)}", "#10b981"
            p_label, p_val = "Lãi kỳ vọng", f"+{swing_ret_pct:.2f}%"

        data_dict = {
            'symbol': symbol,
            'latest_price': fmt(l_price),
            'sma_val': fmt(sma_v),
            'rsi_val': f"{rsi_v:.2f}",
            'latest_date': l_date,
            'action_color': action_c,
            'tech_signal': tech_signal,
            'display_profit': p_val,
            'profit_label': p_label,
            'zone_label': z_label,
            'zone_value': z_val,
            'target_label': t_label,
            'target_color': t_color,
            'target_value': t_val,
            'stars_label': "MẠNH",
            'overall_score': score,
            'khq_color': khq_c,
            'khq_label': khq_l,
            'price_stars': price_s,
            'trend_stars': trend_s,
            'pos_stars': pos_s,
            'flow_stars': flow_s,
            'volat_stars': volat_s,
            'base_stars': base_s,
            'expert_comment': expert_comment,
            'ai_confidence': f"{ai_conf:.1f}"
        }
        
        return {
            'status': 'success',
            'symbol': symbol,
            'type': 'analysis',
            'data': data_dict
        }
