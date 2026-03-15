import json
import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────
# Regex patterns for offline intent classification
# ──────────────────────────────────────────────────────
# Vietnamese stock symbols: 3 uppercase letters (VNM, FPT, HPG, SSI, etc.)
_TICKER_RE = re.compile(r'\b([A-Z][A-Z0-9]{2,4})\b')

# Keywords indicating a MACRO question (market overview, VN-Index, etc.)
_MACRO_KEYWORDS = [
    'thị trường', 'thi truong', 'vn-index', 'vnindex', 'vn30', 'hnx-index',
    'toàn cảnh', 'toan canh', 'tổng quan', 'tong quan', 'vĩ mô', 'vi mo',
    'nhóm ngành', 'nhom nganh', 'dòng tiền', 'dong tien', 'blue chip', 'bluechip',
    'thị trường chung', 'hose', 'hnx', 'upcom', 'sàn chứng khoán', 'index',
    'chỉ số', 'chi so', 'ngành nào', 'nganh nao', 'cổ phiếu nào', 'co phieu nao',
    'xu hướng', 'xu huong', 'sập', 'crash', 'bull', 'bear', 'tăng hay giảm',
    'hôm nay', 'tuần này', 'tháng này', 'phiên sáng', 'phiên chiều',
    'fed', 'lạm phát', 'lam phat', 'lãi suất', 'lai suat', 'gdp',
]

# Known VN stock tickers — validated against DB at runtime via _is_valid_ticker()
# This static set is only used as a fast-path hint for common tickers
_KNOWN_PREFIXES = {
    'VNM', 'FPT', 'HPG', 'SSI', 'VCB', 'BID', 'CTG', 'MBB', 'TCB', 'VPB',
    'MSN', 'VIC', 'VHM', 'VRE', 'SAB', 'GAS', 'PLX', 'POW', 'PVD', 'PVS',
    'REE', 'DPM', 'DCM', 'HAG', 'HNG', 'MWG', 'PNJ', 'DGW', 'FRT', 'GMD',
    'VJC', 'HVN', 'ACB', 'SHB', 'STB', 'EIB', 'LPB', 'TPB', 'HDB', 'OCB',
    'KDH', 'DXG', 'NVL', 'PDR', 'DIG', 'CEO', 'KBC', 'IJC', 'NLG', 'VND',
    'HCM', 'BSI', 'AGR', 'CTS', 'SHS', 'VCI', 'ORS', 'TCI', 'VIX', 'DVN',
}

# Noise words that look like tickers but aren't
# NOTE: Do NOT add valid VN stock symbols here (CEO, VND, EVN are real tickers)
_TICKER_NOISE = {
    # Technical indicator names
    'RSI', 'SMA', 'MACD', 'EMA', 'ATR', 'OBV', 'ADX',
    # Finance/tech abbreviations (not VN stock symbols)
    'OTP', 'API', 'PDF', 'USD', 'EUR', 'JPY', 'ETF', 'IPO',
    'CFO', 'GDP', 'CPI', 'FDI', 'ODA', 'WTO', 'FTA', 'ADB', 'IMF', 'FED',
    'BOJ', 'ECB', 'PER', 'ROE', 'ROA', 'EPS', 'NAV', 'NPL', 'NIM', 'NPM',
    'BOT', 'BTC', 'ETH', 'NFT',
    # Common English 3-letter words
    'THE', 'FOR', 'AND', 'NOT', 'BUT', 'YOU', 'ALL', 'ANY', 'CAN', 'HER',
    'WAS', 'ONE', 'OUR', 'OUT', 'ARE', 'HAS', 'HIS', 'HOW', 'MAN', 'NEW',
    'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'DID', 'GET', 'HIM', 'LET', 'SAY',
    'SHE', 'TOO', 'USE',
    # Common Vietnamese 3-letter words (not stock tickers)
    'DAD', 'MOM', 'SON', 'GHI', 'CHO', 'HAY', 'NEN',
    'SAO', 'TEN', 'TAM', 'THU', 'RAT', 'CON', 'MOT', 'HAI',
    'TRE', 'HOI', 'VOI', 'DAT', 'XIN',
}

# Analysis-related keywords that require specific ticker
_ANALYSIS_KEYWORDS = [
    'phân tích', 'phan tich', 'đánh giá', 'danh gia', 'nhận định', 'nhan dinh',
    'nên mua', 'nen mua', 'nên bán', 'nen ban', 'có nên', 'co nen',
    'review', 'analyze', 'analysis', 'dự báo', 'du bao', 'triển vọng', 'trien vong',
    'mục tiêu', 'muc tieu', 'target', 'khuyến nghị', 'khuyen nghi',
    'so sánh', 'so sanh', 'compare', 'versus', 'hay', 'hoặc',
]


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

    # ──────────────────────────────────────────────
    # Intent Classification (Offline, regex-based)
    # ──────────────────────────────────────────────
    @api.model
    def _classify_intent(self, message):
        """
        Phân loại ý định bằng regex/keywords. Không gọi LLM.
        Returns: (intent: str, symbols: list[str])
          intent = 'TICKER' | 'MACRO' | 'CHAT'
        """
        msg_lower = message.lower().strip()
        msg_upper = message.upper().strip()

        # 1. Extract potential stock symbols
        raw_symbols = _TICKER_RE.findall(msg_upper)
        # Filter noise and validate
        symbols = []
        for s in raw_symbols:
            if s in _TICKER_NOISE:
                continue
            # Accept if in known list OR exists in database
            if s in _KNOWN_PREFIXES:
                symbols.append(s)
            elif len(s) == 3 and s.isalpha():
                # Could be a valid ticker — check DB
                exists = self.sudo().search_count([('name', '=', s)], limit=1)
                if exists:
                    symbols.append(s)
        symbols = list(dict.fromkeys(symbols))  # deduplicate, preserve order

        # 2. Check for TICKER intent
        if symbols:
            # User mentioned specific tickers — this is a TICKER query
            has_analysis_keyword = any(kw in msg_lower for kw in _ANALYSIS_KEYWORDS)
            # Even without analysis keywords, if they just say a ticker name, analyze it
            return 'TICKER', symbols

        # 3. Check for MACRO intent
        if any(kw in msg_lower for kw in _MACRO_KEYWORDS):
            return 'MACRO', []

        # 4. Default: CHAT (knowledge Q&A, greetings, explanations)
        return 'CHAT', []

    # ──────────────────────────────────────────────
    # Main Chat Entry Point
    # ──────────────────────────────────────────────
    @api.model
    def ai_chat(self, message):
        """
        Xử lý tin nhắn đa năng. Phân loại offline, chỉ gọi LLM 1 lần cho response.
        Luôn trả về dict có cấu trúc chuẩn — KHÔNG BAO GIỜ crash.
        """
        try:
            intent, symbols = self._classify_intent(message)

            if intent == 'TICKER' and symbols:
                return self._handle_ticker(message, symbols)
            elif intent == 'MACRO':
                return self._handle_macro(message)
            else:
                return self._handle_chat(message)

        except Exception as e:
            _logger.error("ai_chat unhandled error: %s", e, exc_info=True)
            return {
                'status': 'success',
                'type': 'general',
                'data': {
                    'text_content': (
                        "Xin lỗi, hệ thống gặp sự cố khi xử lý yêu cầu. "
                        "Vui lòng thử lại hoặc đặt câu hỏi khác."
                    )
                }
            }

    # ──────────────────────────────────────────────
    # CHAT Handler — Knowledge Q&A, greetings, explanations
    # ──────────────────────────────────────────────
    @api.model
    def _handle_chat(self, message):
        import pytz
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')

        system_prompt = f"""Bạn là ARC Intelligence - Cố vấn tài chính chuyên nghiệp am hiểu chứng khoán Việt Nam. Hôm nay là {current_date_str}.

NHIỆM VỤ:
- Trả lời câu hỏi giao tiếp, giải thích kiến thức, thuật ngữ tài chính một cách chuyên nghiệp, khách quan và dễ hiểu.
- Hỗ trợ giải thích: Chỉ báo kỹ thuật (RSI, MACD, Bollinger Bands...), Phân tích cơ bản (P/E, P/B, ROE...), Chiến lược đầu tư, Quy tắc giao dịch T+2.5, Thuế & phí giao dịch, Kiến thức phái sinh, Quản trị rủi ro.
- Nếu người dùng muốn phân tích mã cổ phiếu cụ thể, hướng dẫn họ nhập mã (VD: "FPT" hoặc "Phân tích HPG").
- Tuyệt đối KHÔNG BỊA ĐẶT SỐ LIỆU GIÁ CỔ PHIẾU (AI không có dữ liệu realtime).
- Nếu câu hỏi hoàn toàn không liên quan tài chính/kinh tế, từ chối lịch sự và hướng về chủ đề đầu tư.

PHONG CÁCH:
- Chuyên nghiệp nhưng thân thiện, dễ hiểu.
- Trả lời bằng tiếng Việt, sử dụng markdown (bold, italic, bullet points).
- Ngắn gọn, súc tích, tránh lan man."""

        result = self.env['ai.chatbot.service'].call_openrouter(message, system_prompt)

        if not result['success']:
            return self._llm_error_response(result['error'])

        return {
            'status': 'success',
            'type': 'general',
            'data': {
                'text_content': result['content'].replace('\n', '<br/>')
            }
        }

    # ──────────────────────────────────────────────
    # SSI Credentials Helper (try both config sources)
    # ──────────────────────────────────────────────
    @api.model
    def _get_ssi_credentials(self):
        """
        Lấy SSI credentials từ 2 nguồn theo thứ tự ưu tiên:
        1. ssi.api.config model (module stock_data) — nguồn chính
        2. ir.config_parameter (module ai_trading_assistant) — nguồn dự phòng
        Returns: (consumer_id, consumer_secret, api_url) or (None, None, None)
        """
        # 1. Try ssi.api.config (stock_data module)
        try:
            ssi_config = self.env['ssi.api.config'].sudo().search(
                [('is_active', '=', True)], limit=1
            )
            if ssi_config and ssi_config.consumer_id and ssi_config.consumer_secret:
                return (
                    ssi_config.consumer_id,
                    ssi_config.consumer_secret,
                    ssi_config.api_url or 'https://fc-data.ssi.com.vn/'
                )
        except Exception:
            pass  # Model may not exist if stock_data module not installed

        # 2. Fallback to ir.config_parameter
        icp = self.env['ir.config_parameter'].sudo()
        ssi_id = icp.get_param('ai_trading.ssi_consumer_id', '')
        ssi_secret = icp.get_param('ai_trading.ssi_consumer_secret', '')
        api_url = icp.get_param('ai_trading.ssi_api_url', 'https://fc-data.ssi.com.vn/')
        if ssi_id and ssi_secret:
            return ssi_id, ssi_secret, api_url

        return None, None, None

    # ──────────────────────────────────────────────
    # MACRO Handler — Market overview, VN-Index, sectors
    # ──────────────────────────────────────────────
    @api.model
    def _handle_macro(self, message):
        import pytz
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

        # Fetch VN-Index data from SSI
        market_context = "Hiện chưa lấy được dữ liệu thị trường mới nhất."
        latest_vni_price = None

        ssi_id, ssi_secret, api_url = self._get_ssi_credentials()

        if ssi_id and ssi_secret:
            try:
                from ssi_fc_data import fc_md_client, model as ssi_model

                class Config:
                    pass
                conf = Config()
                conf.consumerID, conf.consumerSecret, conf.url = ssi_id, ssi_secret, api_url
                client = fc_md_client.MarketDataClient(conf)

                end_d = datetime.now(vn_tz)
                start_d = end_d - timedelta(days=5)
                req = ssi_model.daily_ohlc(
                    'VNINDEX', start_d.strftime('%d/%m/%Y'), end_d.strftime('%d/%m/%Y'), 1, 10, True
                )
                res = client.daily_ohlc(conf, req)
                data = res if isinstance(res, dict) else json.loads(res)

                if str(data.get('status')) == '200' and data.get('data'):
                    candles = data.get('data', [])
                    if candles:
                        latest = candles[0]
                        latest_vni_price = float(latest.get('Close', 0))
                        if latest_vni_price > 0:
                            market_context = (
                                f"VN-Index phiên mới nhất ({latest.get('TradingDate')}): "
                                f"Đóng cửa tại {latest.get('Close')} điểm. "
                                f"Khối lượng: {latest.get('Volume', 0):,} cp."
                            )
            except Exception as e:
                _logger.warning("Error fetching VN-Index data: %s", e)
                market_context = "Không truy cập được dữ liệu VN-Index realtime."
        else:
            _logger.warning("No SSI credentials configured (checked ssi.api.config and ir.config_parameter)")

        current_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')

        vni_prompt_part = (
            f"Hãy cung cấp nhận định chuyên sâu dựa trên số điểm {latest_vni_price} này."
            if latest_vni_price
            else "Hãy cung cấp nhận định chuyên sâu dựa trên tình trạng hiện tại."
        )

        system_prompt = f"""Bạn là ARC Intelligence - Giám đốc Phân tích vĩ mô. Hôm nay là ngày thực tế: {current_date_str}.
Người dùng đang hỏi về vĩ mô/toàn cảnh thị trường chứng khoán Việt Nam.
[DỮ LIỆU VN-INDEX MỚI NHẤT]: {market_context}
{vni_prompt_part}

PHONG CÁCH:
- Đề xuất các nhóm ngành hot và 3 mã tiềm năng.
- Phong thái Giám đốc Chiến lược, am hiểu dòng tiền tổ chức.
- Trả lời bằng tiếng Việt, sử dụng markdown formatting.
- Ngắn gọn, có chiều sâu, không lan man."""

        result = self.env['ai.chatbot.service'].call_openrouter(message, system_prompt)

        if not result['success']:
            return self._llm_error_response(result['error'])

        return {
            'status': 'success',
            'type': 'general',
            'data': {
                'text_content': result['content']
            }
        }

    # ──────────────────────────────────────────────
    # TICKER Handler — Analyze specific stock symbols
    # ──────────────────────────────────────────────
    @api.model
    def _handle_ticker(self, message, symbols):
        multi_data = []
        for sym in symbols:
            try:
                result = self._analyze_ticker_data(sym)
                multi_data.append(result)
            except Exception as e:
                _logger.error("Error analyzing ticker %s: %s", sym, e, exc_info=True)
                multi_data.append({
                    'status': 'exception',
                    'symbol': sym,
                    'message': f"Lỗi khi phân tích {sym}. Vui lòng thử lại."
                })

        return {
            'status': 'success',
            'type': 'multi',
            'data': multi_data
        }

    # ──────────────────────────────────────────────
    # LLM Error Response (structured fallback)
    # ──────────────────────────────────────────────
    @api.model
    def _llm_error_response(self, error_code):
        error_messages = {
            'missing_api_key': (
                "⚙️ **Chưa cấu hình API Key**\n\n"
                "Vui lòng liên hệ Admin để cấu hình OpenRouter API Key "
                "trong phần **Cài đặt → AI Trading**."
            ),
            'timeout': (
                "⏱️ **Hệ thống AI đang bận**\n\n"
                "Máy chủ AI phản hồi chậm. Vui lòng thử lại sau giây lát.\n\n"
                "💡 *Mẹo*: Bạn vẫn có thể nhập mã cổ phiếu (VD: **FPT**) "
                "để xem phân tích kỹ thuật mà không cần AI."
            ),
            'connection_error': (
                "🔌 **Lỗi kết nối**\n\n"
                "Không thể kết nối tới máy chủ AI. Vui lòng kiểm tra kết nối mạng.\n\n"
                "💡 *Mẹo*: Bạn vẫn có thể nhập mã cổ phiếu (VD: **FPT**) "
                "để xem phân tích kỹ thuật mà không cần AI."
            ),
        }
        text = error_messages.get(error_code, (
            "⚠️ **Không thể kết nối AI**\n\n"
            "Hệ thống gặp sự cố tạm thời. Vui lòng thử lại.\n\n"
            "💡 *Mẹo*: Bạn vẫn có thể nhập mã cổ phiếu (VD: **FPT**) "
            "để xem phân tích kỹ thuật."
        ))
        return {
            'status': 'success',
            'type': 'general',
            'data': {
                'text_content': text.replace('\n', '<br/>')
            }
        }

    # ──────────────────────────────────────────────
    # Ticker Analysis Engine (unchanged core logic)
    # ──────────────────────────────────────────────
    def _analyze_ticker_data(self, symbol):
        """Hàm nội bộ thực hiện trọn vẹn quy trình: Fetch -> AI Inference -> Trả về dict data cho 1 mã."""
        ticker = self.sudo().search([('name', '=', symbol)], limit=1)
        if not ticker:
            # Detect market: check SSI securities table, fallback to HOSE
            market = 'HOSE'
            try:
                ssi_sec = self.env['ssi.securities'].sudo().search(
                    [('symbol', '=', symbol)], limit=1
                )
                if ssi_sec and ssi_sec.exchange:
                    market = ssi_sec.exchange
            except Exception:
                pass  # ssi.securities may not exist
            ticker = self.sudo().create({
                'name': symbol, 'company_name': f'Mã {symbol}',
                'market': market, 'is_active': True
            })

        # 1. Sync Data (Chuẩn hóa múi giờ VN)
        try:
            import pytz
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            to_date_str = datetime.now(vn_tz).strftime('%d/%m/%Y')
            latest_c = self.env['stock.candle'].sudo().search(
                [('ticker_id', '=', ticker.id)], order='date desc', limit=1
            )
            from_date_str = (
                (latest_c.date - timedelta(days=2)).strftime('%d/%m/%Y')
                if latest_c
                else (datetime.now(vn_tz) - timedelta(days=150)).strftime('%d/%m/%Y')
            )
            fetcher = self.env['ssi.data.fetcher'].sudo().create({})
            fetcher.fetch_daily_ohlcv(symbol, from_date_str, to_date_str)
        except Exception:
            pass

        # 2. Chuẩn bị DataFrame
        local_candles = self.env['stock.candle'].sudo().search(
            [('ticker_id', '=', ticker.id)], order='date desc', limit=150
        )
        if not local_candles:
            return {'status': 'error', 'symbol': symbol, 'message': f'Mã {symbol} thiếu dữ liệu.'}

        data_list = []
        for c in local_candles:
            data_list.append({
                'date': c.date.strftime('%Y-%m-%d'), 'tic': symbol,
                'open': float(c.open), 'high': float(c.high),
                'low': float(c.low), 'close': float(c.close), 'volume': float(c.volume)
            })
        df = pd.DataFrame(data_list).sort_values('date', ascending=True)
        df['Close'] = df['close']
        df['TradingDate'] = df['date']

        # 3. Lấy giá Real-time SSI
        real_latest_price = None
        real_latest_date = None
        ssi_id, ssi_secret, api_url = self._get_ssi_credentials()
        if ssi_id and ssi_secret:
            try:
                import pytz
                vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                from ssi_fc_data import fc_md_client, model as ssi_model

                class Conf:
                    pass
                conf = Conf()
                conf.consumerID = ssi_id
                conf.consumerSecret = ssi_secret
                conf.url = api_url
                client = fc_md_client.MarketDataClient(conf)
                res_t = client.daily_stock_price(
                    conf,
                    ssi_model.daily_stock_price(
                        symbol,
                        datetime.now(vn_tz).strftime('%d/%m/%Y'),
                        datetime.now(vn_tz).strftime('%d/%m/%Y'),
                        1, 1, ticker.market.lower()
                    )
                )
                d_t = res_t if isinstance(res_t, dict) else json.loads(res_t)
                if str(d_t.get('status')) == '200' and d_t.get('data'):
                    today = d_t['data'][0]
                    real_latest_price = float(today.get('MatchPrice') or today.get('ClosePrice'))
                    real_latest_date = str(today.get('TradingDate', datetime.now(vn_tz).strftime('%d/%m/%Y')))
                    t_date = datetime.strptime(real_latest_date, '%d/%m/%Y').date()
                    ex = self.env['stock.candle'].sudo().search(
                        [('ticker_id', '=', ticker.id), ('date', '=', t_date)], limit=1
                    )
                    vals = {
                        'ticker_id': ticker.id, 'date': t_date,
                        'close': real_latest_price,
                        'open': float(today.get('OpenPrice', real_latest_price)),
                        'high': float(today.get('HighestPrice', real_latest_price)),
                        'low': float(today.get('LowestPrice', real_latest_price)),
                        'volume': float(today.get('TotalVolumn', 0))
                    }
                    if ex:
                        ex.sudo().write(vals)
                    else:
                        self.env['stock.candle'].sudo().create(vals)
            except Exception:
                pass

        if not real_latest_price:
            real_latest_price = df.iloc[-1]['close']
            real_latest_date = df.iloc[-1]['date']

        if str(df.iloc[-1]['date']) == real_latest_date:
            df.loc[df.index[-1], 'close'] = real_latest_price
        else:
            df = pd.concat([df, pd.DataFrame([{
                'date': real_latest_date, 'tic': symbol,
                'close': real_latest_price, 'Close': real_latest_price
            }])], ignore_index=True)

        # 4. Technical Indicators (Expanded Suite)
        # ── Core Trend ──
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()

        # ── RSI (Wilder's smoothing) ──
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)

        # ── MACD (12, 26, 9) ──
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['signal_line']

        # ── Bollinger Bands (20, 2σ) ──
        bb_mid = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = bb_mid + (bb_std * 2)
        df['bb_lower'] = bb_mid - (bb_std * 2)
        df['bb_width'] = ((df['bb_upper'] - df['bb_lower']) / bb_mid * 100).fillna(0)
        df['bb_pct'] = ((df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])).fillna(0.5)

        # ── Stochastic %K(14) / %D(3) ──
        low14 = df['low'].rolling(window=14).min()
        high14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = ((df['close'] - low14) / (high14 - low14) * 100).fillna(50)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean().fillna(50)

        # ── ADX (14) — Trend Strength ──
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean()

        atr14 = df['tr'].rolling(window=14).mean().replace(0, np.nan)
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr14)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr14)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        df['adx'] = dx.rolling(window=14).mean().fillna(20)
        df['plus_di'] = plus_di.fillna(0)
        df['minus_di'] = minus_di.fillna(0)

        # ── OBV (On-Balance Volume) & OBV Trend ──
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['obv'] = obv
        df['obv_sma'] = df['obv'].rolling(window=20).mean()

        # ── Volume metrics ──
        df['vol_sma20'] = df['volume'].rolling(window=20).mean()

        # ── Extract latest values ──
        latest_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else latest_row
        l_price, l_date = float(latest_row['close']), str(latest_row['date'])
        rsi_v = float(latest_row['rsi'])
        sma_v = float(latest_row['sma20'])
        ema9_v = float(latest_row['ema9'])
        ema50_v = float(latest_row['ema50'])
        macd_v = float(latest_row['macd'])
        sig_v = float(latest_row['signal_line'])
        macd_hist_v = float(latest_row['macd_hist'])
        bb_pct_v = float(latest_row['bb_pct'])
        bb_width_v = float(latest_row['bb_width'])
        stoch_k_v = float(latest_row['stoch_k'])
        stoch_d_v = float(latest_row['stoch_d'])
        adx_v = float(latest_row['adx'])
        plus_di_v = float(latest_row['plus_di'])
        minus_di_v = float(latest_row['minus_di'])
        atr_v = float(latest_row['atr']) or (l_price * 0.02)
        obv_v = float(latest_row['obv'])
        obv_sma_v = float(latest_row['obv_sma'] or obv_v)
        vol_ratio = float(latest_row['volume']) / max(float(latest_row['vol_sma20'] or 1), 1)

        # 5. Inference
        active_strategy = self.env['ai.strategy'].sudo().search(
            [('status', '=', 'active'), '|', ('ticker_ids', '=', False), ('ticker_ids', 'in', ticker.id)],
            limit=1, order='id desc'
        )

        def fmt(v):
            return f"{v / 1000:,.2f}"

        if not active_strategy:
            return {
                'status': 'success', 'symbol': symbol, 'type': 'no_model',
                'data': {
                    'symbol': symbol,
                    'latest_price': fmt(l_price),
                    'sma_val': fmt(sma_v),
                    'rsi_val': f"{rsi_v:.1f}",
                    'latest_date': l_date
                }
            }

        pred_action, ai_error_msg = active_strategy.get_inference_action(ticker)

        # 6. Multi-Indicator Confluence Scoring System
        # Each signal returns a value in [-1, +1]: negative = bearish, positive = bullish

        def _rsi_signal(rsi):
            if rsi >= 80: return -1.0     # Extremely overbought
            if rsi >= 70: return -0.6     # Overbought
            if rsi <= 20: return 1.0      # Extremely oversold
            if rsi <= 30: return 0.6      # Oversold
            if rsi <= 45: return 0.2      # Slightly bullish
            if rsi >= 55: return -0.2     # Slightly bearish
            return 0.0                     # Neutral

        def _macd_signal(macd, signal, hist, prev_hist):
            s = 0.0
            if macd > signal: s += 0.4     # MACD above signal
            else: s -= 0.4
            if hist > 0 and prev_hist <= 0: s += 0.6  # Bullish crossover
            elif hist < 0 and prev_hist >= 0: s -= 0.6 # Bearish crossover
            elif hist > prev_hist: s += 0.2  # Momentum increasing
            else: s -= 0.2
            return max(min(s, 1.0), -1.0)

        def _bb_signal(bb_pct, bb_width):
            if bb_pct <= 0.0: return 0.8            # Below lower band (oversold)
            if bb_pct <= 0.2: return 0.4             # Near lower band
            if bb_pct >= 1.0: return -0.8            # Above upper band (overbought)
            if bb_pct >= 0.8: return -0.4            # Near upper band
            if bb_width < 3: return 0.3              # Squeeze (potential breakout)
            return 0.0

        def _ema_signal(price, ema9, ema50):
            s = 0.0
            if price > ema9: s += 0.3
            else: s -= 0.3
            if ema9 > ema50: s += 0.4   # Golden cross territory
            else: s -= 0.4               # Death cross territory
            if price > ema50: s += 0.3
            else: s -= 0.3
            return max(min(s, 1.0), -1.0)

        def _volume_signal(vol_ratio, obv, obv_sma):
            s = 0.0
            if vol_ratio > 2.0: s += 0.4      # High volume (confirming)
            elif vol_ratio > 1.2: s += 0.2
            elif vol_ratio < 0.5: s -= 0.2     # Low volume (weak move)
            if obv > obv_sma: s += 0.4         # OBV trending up
            else: s -= 0.3
            return max(min(s, 1.0), -1.0)

        def _adx_signal(adx, plus_di, minus_di):
            """ADX measures trend STRENGTH, DI± measures direction."""
            if adx < 20: return 0.0             # No trend
            direction = 0.5 if plus_di > minus_di else -0.5
            if adx >= 40: return direction * 2   # Strong trend
            if adx >= 25: return direction * 1.5
            return direction

        def _stoch_signal(k, d):
            if k <= 20 and d <= 20: return 0.7   # Oversold
            if k >= 80 and d >= 80: return -0.7   # Overbought
            if k > d and k < 50: return 0.3       # Bullish crossover in oversold
            if k < d and k > 50: return -0.3      # Bearish crossover in overbought
            return 0.0

        # Calculate individual signals
        prev_hist = float(prev_row.get('macd_hist', 0)) if hasattr(prev_row, 'get') else float(prev_row['macd'] - prev_row['signal_line']) if 'macd' in prev_row.index else 0

        sig_ai = float(pred_action) if pred_action != -999.0 else 0.0
        sig_rsi = _rsi_signal(rsi_v)
        sig_macd = _macd_signal(macd_v, sig_v, macd_hist_v, prev_hist)
        sig_bb = _bb_signal(bb_pct_v, bb_width_v)
        sig_ema = _ema_signal(l_price, ema9_v, ema50_v)
        sig_vol = _volume_signal(vol_ratio, obv_v, obv_sma_v)
        sig_adx = max(min(_adx_signal(adx_v, plus_di_v, minus_di_v), 1.0), -1.0)
        sig_stoch = _stoch_signal(stoch_k_v, stoch_d_v)

        # Weighted confluence score
        # When AI (finrl) is unavailable, redistribute weight to technical indicators
        if pred_action == -999.0:
            WEIGHTS = {
                'ai': 0.0, 'rsi': 0.16, 'macd': 0.17, 'bb': 0.14,
                'ema': 0.16, 'volume': 0.14, 'adx': 0.13, 'stoch': 0.10,
            }
        else:
            WEIGHTS = {
                'ai': 0.25, 'rsi': 0.12, 'macd': 0.13, 'bb': 0.10,
                'ema': 0.12, 'volume': 0.10, 'adx': 0.10, 'stoch': 0.08,
            }
        confluence = (
            sig_ai * WEIGHTS['ai']
            + sig_rsi * WEIGHTS['rsi']
            + sig_macd * WEIGHTS['macd']
            + sig_bb * WEIGHTS['bb']
            + sig_ema * WEIGHTS['ema']
            + sig_vol * WEIGHTS['volume']
            + sig_adx * WEIGHTS['adx']
            + sig_stoch * WEIGHTS['stoch']
        )

        # Determine signal from confluence
        ai_conf = min(abs(pred_action * 100), 100) if pred_action != -999.0 else 0.0

        if pred_action == -999.0:
            # AI unavailable — use pure technical analysis signal
            if confluence >= 0.30:
                tech_signal = "MUA"
            elif confluence <= -0.30:
                tech_signal = "BÁN"
            else:
                tech_signal = "TRUNG LẬP"
        elif confluence >= 0.30:
            tech_signal = "MUA"
        elif confluence <= -0.30:
            tech_signal = "BÁN"
        else:
            tech_signal = "TRUNG LẬP"

        # Star Metrics — Composite scoring from actual indicators
        # Price strength: RSI + Stochastic position
        price_s = min(max(round((rsi_v / 20) * 0.6 + (stoch_k_v / 25) * 0.4), 1), 5)
        # Trend strength: EMA cross + ADX
        ema_trend = 1.0 if ema9_v > ema50_v else -1.0
        trend_s = min(max(round((adx_v / 15) * (1 if ema_trend > 0 else 0.5) + (1 if l_price > sma_v else 0)), 1), 5)
        # Position: MACD + confluence direction
        pos_s = min(max(round(3 + confluence * 2.5), 1), 5)
        # Flow: Volume ratio + OBV confirmation
        obv_trend = 1.0 if obv_v > obv_sma_v else 0.5
        flow_s = min(max(round(vol_ratio * 1.5 * obv_trend + 0.5), 1), 5)
        # Volatility: BB width (narrower = higher score for potential breakout)
        volat_s = min(max(round(5 - bb_width_v / 3), 1), 5)
        # Base: Price position relative to recent range
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        price_range = recent_high - recent_low
        base_s = min(max(round((l_price - recent_low) / max(price_range * 0.2, 1) + 1), 1), 5)

        # Overall score: Normalized weighted formula
        # Map confluence [-1, +1] to [10, 95]
        score = min(max(int(52.5 + confluence * 42.5), 10), 95)
        khq_c = "#10b981" if score > 65 else ("#f59e0b" if score > 45 else "#ef4444")
        khq_l = "Khả quan" if score > 65 else ("Trung lập" if score > 45 else "Kém khả quan")

        is_neg = ("BÁN" in tech_signal)
        is_neutral = ("TRUNG LẬP" in tech_signal)

        # Position sizing & R:R (using ATR and support/resistance)
        support_v = max(recent_low, sma_v - (atr_v * 1.5))
        resist_v = min(recent_high, sma_v + (atr_v * 2.0))
        if resist_v <= l_price:
            resist_v = l_price + (atr_v * 2.0)

        is_bullish_trend = confluence > 0
        anchor_buy = l_price if is_bullish_trend else min(l_price, support_v)
        b_low, b_high = anchor_buy - (atr_v * 0.5), anchor_buy + (atr_v * 0.5)

        stop_loss = support_v - atr_v
        if stop_loss > l_price:
            stop_loss = l_price - (atr_v * 1.5)
        risk_buf_pct = ((l_price - stop_loss) / l_price) * 100

        t1 = max(resist_v, l_price + (l_price - stop_loss) * 1.5)
        t2 = t1 + (atr_v * 2)
        swing_ret_pct = ((t1 - l_price) / l_price) * 100
        swing_ret_pct = min(swing_ret_pct, 40.0)
        risk_buf_pct = min(risk_buf_pct, 15.0)

        # Expert analysis (with extended indicator context)
        expert_comment = self.env['ai.chatbot.service'].get_expert_analysis(
            symbol, l_price, l_date, tech_signal, b_low, b_high, t1, t2,
            rsi_v, sma_v, macd_v,
            active_strategy.algorithm or 'ppo',
            active_strategy.sharpe_ratio or 0.0,
            swing_ret_pct, risk_buf_pct, pred_action,
            # New indicator context
            ema9=ema9_v, ema50=ema50_v,
            bb_pct=bb_pct_v, bb_width=bb_width_v,
            stoch_k=stoch_k_v, stoch_d=stoch_d_v,
            adx=adx_v, confluence=confluence,
            vol_ratio=vol_ratio
        )

        action_c = "#00d084" if "MUA" in tech_signal else ("#e74c3c" if "BÁN" in tech_signal else "#f39c12")

        if is_neutral:
            z_label, z_val = "", ""
            t_label, t_val, t_color = "", "", ""
            p_label, p_val = "", ""
        elif is_neg:
            z_label, z_val = "Vùng canh bán", f"{fmt(l_price)} - {fmt(t1)}"
            t_label, t_val, t_color = "", "", ""
            p_label, p_val = "", ""
        else:
            z_label, z_val = "Vùng canh mua", f"{fmt(b_low)} - {fmt(b_high)}"
            t_label, t_val, t_color = "Mục tiêu chốt lời", f"{fmt(t1)} - {fmt(t2)}", "#10b981"
            p_label, p_val = "Lãi kỳ vọng", f"+{swing_ret_pct:.2f}%"

        # Stars label based on ADX trend strength
        stars_label = "MẠNH" if adx_v >= 25 else ("TRUNG BÌNH" if adx_v >= 15 else "YẾU")

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
            'stars_label': stars_label,
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
            'ai_confidence': f"{ai_conf:.1f}",
            # Extended indicators for display
            'ema9_val': fmt(ema9_v),
            'ema50_val': fmt(ema50_v),
            'bb_pct': f"{bb_pct_v:.2f}",
            'stoch_k': f"{stoch_k_v:.1f}",
            'stoch_d': f"{stoch_d_v:.1f}",
            'adx_val': f"{adx_v:.1f}",
            'macd_hist': f"{macd_hist_v:.2f}",
            'vol_ratio': f"{vol_ratio:.2f}",
            'confluence': f"{confluence:.3f}",
        }

        return {
            'status': 'success',
            'symbol': symbol,
            'type': 'analysis',
            'data': data_dict
        }
