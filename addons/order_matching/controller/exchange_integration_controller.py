from odoo import http, fields, _
from odoo.http import request
import json


class ExchangeIntegrationController(http.Controller):
    """Controller gửi cặp lệnh đã khớp (transaction.matched.orders) lên sàn thông qua stock_trading.trading.order.

    Quy ước hiện tại:
    - Tạo cả lệnh MUA (buy order) và lệnh BÁN (sell order) cho cặp lệnh đã khớp.
    - Map fund.ticker -> ssi.securities.symbol để tìm instrument.
    - order_type = 'stock', order_type_detail = 'MTL', market='VN', price=0 (theo API yêu cầu).
    - quantity = matched_quantity (làm tròn xuống số nguyên an toàn).
    - account sẽ lấy tự động từ trading.config của user (onchange trong trading.order), nếu có.
    """

    def _find_instrument_by_fund(self, fund):
        """Tìm instrument (ssi.securities) theo ticker của quỹ nếu có.
        Trả về record hoặc None.
        """
        try:
            if not fund:
                return None
            ticker = getattr(fund, 'ticker', None)
            if not ticker:
                return None
            Sec = request.env['ssi.securities'].sudo()
            return Sec.search([('symbol', '=', str(ticker).strip().upper())], limit=1)
        except Exception:
            return None

    def _get_user_account(self, user_id):
        """Lấy account từ trading.config của user"""
        try:
            Config = request.env['trading.config'].sudo()
            cfg = Config.search([('user_id', '=', user_id), ('active', '=', True)], limit=1)
            if cfg and cfg.account:
                return str(cfg.account).strip().upper()
        except Exception:
            pass
        return None

    def _create_trading_order_from_matched_pair(self, matched):
        """Tạo trading.order từ một bản ghi transaction.matched.orders.
        Tạo cả lệnh MUA và lệnh BÁN cho cặp lệnh đã khớp.

        Args:
            matched: record của transaction.matched.orders
        Returns:
            dict: {
                'buy_order': trading.order record (lệnh mua),
                'sell_order': trading.order record (lệnh bán)
            }
        """
        Tx = request.env['portfolio.transaction'].sudo()
        TradingOrder = request.env['trading.order'].sudo()

        # Lấy buy và sell orders
        buy_tx = matched.buy_order_id
        sell_tx = matched.sell_order_id
        
        if not buy_tx or not buy_tx.exists():
            raise http.JsonRPCException(message=_('Không tìm thấy lệnh mua trong cặp đã khớp'))
        
        if not sell_tx or not sell_tx.exists():
            raise http.JsonRPCException(message=_('Không tìm thấy lệnh bán trong cặp đã khớp'))

        # Xác định instrument theo fund (cả 2 lệnh phải cùng fund)
        fund = buy_tx.fund_id
        if not fund:
            fund = sell_tx.fund_id
        
        instrument = self._find_instrument_by_fund(fund)
        if not instrument:
            raise http.JsonRPCException(message=_('Không tìm thấy mã chứng khoán tương ứng với quỹ: %s') % (fund.name if fund else 'N/A'))

        # Số lượng
        try:
            qty = int(float(matched.matched_quantity or 0))
        except Exception:
            qty = 0
        if qty <= 0:
            raise http.JsonRPCException(message=_('Số lượng khớp không hợp lệ'))

        # Lấy user và account cho buy order
        buy_user = buy_tx.user_id
        if not buy_user:
            raise http.JsonRPCException(message=_('Lệnh mua không có thông tin người dùng'))
        
        buy_account = self._get_user_account(buy_user.id)
        if not buy_account:
            raise http.JsonRPCException(message=_('Không tìm thấy tài khoản giao dịch trong API Configuration của người dùng mua (user_id: %s). Vui lòng cấu hình `trading.config` (account) cho user này.') % buy_user.id)

        # Lấy user và account cho sell order
        sell_user = sell_tx.user_id
        if not sell_user:
            raise http.JsonRPCException(message=_('Lệnh bán không có thông tin người dùng'))
        
        sell_account = self._get_user_account(sell_user.id)
        if not sell_account:
            raise http.JsonRPCException(message=_('Không tìm thấy tài khoản giao dịch trong API Configuration của người dùng bán (user_id: %s). Vui lòng cấu hình `trading.config` (account) cho user này.') % sell_user.id)

        # Tạo request_id cho từng lệnh
        # Lưu ý: RequestID chỉ được chứa [0-9][a-z][A-Z] và chỉ có 8 ký tự
        # Vì giới hạn 8 ký tự, không thể dùng pattern chung để link
        # Việc link sẽ dựa vào matched_order_id và related_order_id
        import random
        import string
        
        def generate_request_id():
            """Tạo request_id ngẫu nhiên 8 ký tự [0-9][a-z][A-Z]"""
            chars = string.digits + string.ascii_letters
            return ''.join(random.choice(chars) for _ in range(8))
        
        buy_request_id = generate_request_id()
        sell_request_id = generate_request_id()
        
        # Đảm bảo 2 request_id khác nhau
        while buy_request_id == sell_request_id:
            sell_request_id = generate_request_id()
        
        # Lấy giá khớp (matched_price) - theo chuẩn Stock Exchange = giá sell order
        matched_price = float(matched.matched_price or 0)
        if matched_price <= 0:
            # Fallback: lấy giá từ sell order (theo chuẩn Stock Exchange)
            matched_price = float(sell_tx.price or sell_tx.current_nav or (fund.current_nav if fund else 0))

        # Tạo deviceId và userAgent chung cho cả 2 lệnh để sàn có thể nhận biết chúng đến từ cùng nguồn
        # Điều này giúp sàn hiểu đây là cặp lệnh cần khớp với nhau
        import time
        common_device_id = f"MATCHED{matched.id}{int(time.time())}"
        common_user_agent = f"MatchedPair/{matched.id}"
        
        # Lấy order_type_detail và price từ giao dịch gốc (theo loại lệnh nhà đầu tư đặt)
        buy_order_type_detail = getattr(buy_tx, 'order_type_detail', None) or 'LO'
        buy_price = float(buy_tx.price or matched_price or 0)
        
        # Tạo BUY trading order với order_type và price từ giao dịch gốc
        buy_order_vals = {
            'user_id': buy_user.id,
            'account': buy_account,
            'order_type': 'stock',
            'market': 'VN',
            'buy_sell': 'B',
            'order_type_detail': buy_order_type_detail,  # Lấy từ giao dịch gốc
            'instrument_id': instrument.id,
            'quantity': qty,
            'price': buy_price,  # Lấy từ giao dịch gốc hoặc giá khớp
            'request_id': buy_request_id,  # Request ID để link với sell order
            'matched_order_id': matched.id,  # Link đến matched pair
            'is_matched_pair': True,  # Đánh dấu đây là lệnh trong cặp khớp
            'device_id': common_device_id,  # Cùng deviceId để sàn nhận biết
            'user_agent': common_user_agent,  # Cùng userAgent để sàn nhận biết
        }
        
        # Add matching fields if they exist
        if 'matched_order_id' in TradingOrder._fields:
             buy_order_vals['matched_order_id'] = matched.id
             buy_order_vals['is_matched_pair'] = True
             
        buy_order = TradingOrder.create(buy_order_vals)

        # Lấy order_type_detail và price từ giao dịch gốc (theo loại lệnh nhà đầu tư đặt)
        sell_order_type_detail = getattr(sell_tx, 'order_type_detail', None) or 'LO'
        sell_price = float(sell_tx.price or matched_price or 0)
        
        # Tạo SELL trading order với order_type và price từ giao dịch gốc
        sell_order_vals = {
            'user_id': sell_user.id,
            'account': sell_account,
            'order_type': 'stock',
            'market': 'VN',
            'buy_sell': 'S',
            'order_type_detail': sell_order_type_detail,  # Lấy từ giao dịch gốc
            'instrument_id': instrument.id,
            'quantity': qty,
            'price': sell_price,  # Lấy từ giao dịch gốc hoặc giá khớp
            'request_id': sell_request_id,  # Request ID để link với buy order
            'matched_order_id': matched.id,  # Link đến matched pair
            'is_matched_pair': True,  # Đánh dấu đây là lệnh trong cặp khớp
            'related_order_id': buy_order.id,  # Link đến buy order
            'device_id': common_device_id,  # Cùng deviceId để sàn nhận biết
            'user_agent': common_user_agent,  # Cùng userAgent để sàn nhận biết
        }
        
        # Add matching fields if they exist
        if 'matched_order_id' in TradingOrder._fields:
             sell_order_vals['matched_order_id'] = matched.id
             sell_order_vals['is_matched_pair'] = True
             
        sell_order = TradingOrder.create(sell_order_vals)
        
        # Link buy order to sell order
        if 'related_order_id' in TradingOrder._fields:
            if 'related_order_id' not in buy_order: # Double check if write is needed
                 try:
                    buy_order.write({'related_order_id': sell_order.id})
                 except Exception:
                    pass
            if 'related_order_id' in sell_order_vals: # If we didn't add it to create vals
                 pass
            else:
                 try:
                    sell_order.write({'related_order_id': buy_order.id}) # Wait, logic was buy->sell
                 except Exception:
                     pass
        
        # Ghi thông tin vào notes để tracking
        pair_reference = f"MATCHED-PAIR-{matched.id}"
        pair_info = f"Cặp khớp #{matched.id} - Giá: {matched_price:,.0f} - SL: {qty}"
        
        if 'notes' in TradingOrder._fields:
            buy_order.write({'notes': f'{pair_info} | Sell Order: {sell_order.name or sell_order.id}'})
            sell_order.write({'notes': f'{pair_info} | Buy Order: {buy_order.name or buy_order.id}'})
        elif 'description' in TradingOrder._fields:
            buy_order.write({'description': f'Lệnh mua trong cặp khớp: {pair_reference}'})
            sell_order.write({'description': f'Lệnh bán trong cặp khớp: {pair_reference}'})

        return {
            'buy_order': buy_order,
            'sell_order': sell_order
        }

    def _coerce_id_list(self, raw):
        """Chuyển đổi nhiều kiểu input thành list[int].
        Hỗ trợ: list, tuple, set, số đơn, chuỗi CSV, hoặc dict có keys ids/matched_order_ids.
        """
        try:
            if raw is None:
                return []
            # Trường hợp dict bọc
            if isinstance(raw, dict):
                inner = raw.get('matched_order_ids') or raw.get('ids') or raw.get('data') or raw
                return self._coerce_id_list(inner)
            # Trường hợp đã là list-like
            if isinstance(raw, (list, tuple, set)):
                out = []
                for v in raw:
                    try:
                        out.append(int(v))
                    except Exception:
                        continue
                return out
            # Trường hợp số đơn
            if isinstance(raw, (int,)):
                return [int(raw)]
            # Trường hợp chuỗi: thử JSON trước, sau đó CSV
            if isinstance(raw, str):
                s = raw.strip()
                if not s:
                    return []
                # Thử parse JSON list
                try:
                    data = json.loads(s)
                    return self._coerce_id_list(data)
                except Exception:
                    pass
                # CSV: "1,2,3"
                parts = [p.strip() for p in s.split(',') if p.strip()]
                out = []
                for p in parts:
                    try:
                        out.append(int(p))
                    except Exception:
                        continue
                return out
        except Exception:
            return []
        return []

    @http.route('/api/transaction-list/send-to-exchange', type='json', auth='user')
    def send_pair_to_exchange(self, matched_order_id=None, auto_submit=True, **kwargs):
        """Gửi một cặp lệnh đã khớp lên sàn dưới dạng trading.order (cả lệnh MUA và lệnh BÁN).

        Params:
            matched_order_id: ID của transaction.matched.orders
            auto_submit: bool, mặc định True sẽ gọi action_submit_order ngay
        """
        try:
            if not matched_order_id:
                return {'success': False, 'message': _('Thiếu matched_order_id')}

            Matched = request.env['transaction.matched.orders'].sudo()
            matched = Matched.browse(int(matched_order_id))
            if not matched or not matched.exists():
                return {'success': False, 'message': _('Không tìm thấy cặp lệnh đã khớp')}

            orders = self._create_trading_order_from_matched_pair(matched)
            buy_order = orders['buy_order']
            sell_order = orders['sell_order']

            # Tự động submit nếu yêu cầu
            # Gửi đồng thời cả 2 lệnh để sàn có thể khớp chúng với nhau
            buy_submit_success = False
            sell_submit_success = False
            submit_errors = []

            if auto_submit:
                # Submit cả 2 lệnh đồng thời (song song) để sàn có thể khớp chúng với nhau
                # Vì API không có tham số để chỉ định matched pair, cách duy nhất là gửi đồng thời
                # để cả 2 lệnh vào order book cùng lúc và sàn sẽ tự động khớp chúng
                import threading
                import queue
                
                buy_result = queue.Queue()
                sell_result = queue.Queue()
                
                def submit_buy():
                    """Submit buy order trong thread riêng"""
                    try:
                        buy_order.action_submit_order()
                        buy_result.put(('success', None))
                    except Exception as err:
                        buy_result.put(('error', str(err)))
                
                def submit_sell():
                    """Submit sell order trong thread riêng"""
                    try:
                        sell_order.action_submit_order()
                        sell_result.put(('success', None))
                    except Exception as err:
                        sell_result.put(('error', str(err)))
                
                # Tạo và start cả 2 threads đồng thời
                buy_thread = threading.Thread(target=submit_buy)
                sell_thread = threading.Thread(target=submit_sell)
                
                buy_thread.start()
                sell_thread.start()
                
                # Đợi cả 2 threads hoàn thành
                buy_thread.join()
                sell_thread.join()
                
                # Lấy kết quả
                buy_status, buy_err = buy_result.get()
                sell_status, sell_err = sell_result.get()
                
                if buy_status == 'success':
                    buy_submit_success = True
                else:
                    submit_errors.append(_('Lệnh mua: %s') % buy_err)
                
                if sell_status == 'success':
                    sell_submit_success = True
                else:
                    submit_errors.append(_('Lệnh bán: %s') % sell_err)
                    
                # Lưu ý: Vì gửi song song, sàn sẽ tự động khớp 2 lệnh này với nhau
                # nếu chúng có cùng instrument, quantity và được gửi gần như cùng lúc

            # Cập nhật trạng thái đã gửi lên sàn vào matched order nếu cả 2 đều thành công
            if (buy_submit_success and sell_submit_success) or not auto_submit:
                matched.write({
                    'sent_to_exchange': True,
                    'sent_to_exchange_at': fields.Datetime.now()
                })

            # Trả về kết quả
            if auto_submit and submit_errors:
                return {
                    'success': False,
                    'buy_order_id': buy_order.id,
                    'sell_order_id': sell_order.id,
                    'buy_submit_success': buy_submit_success,
                    'sell_submit_success': sell_submit_success,
                    'message': _('Đã tạo trading orders nhưng submit thất bại: %s') % '; '.join(submit_errors)
                }

            return {
                'success': True,
                'buy_order_id': buy_order.id,
                'sell_order_id': sell_order.id,
                'buy_submit_success': buy_submit_success if auto_submit else None,
                'sell_submit_success': sell_submit_success if auto_submit else None,
                'message': _('Đã tạo%s cả lệnh mua và lệnh bán thành công') % (' và submit' if auto_submit else ''),
            }
        except http.JsonRPCException as je:
            return {'success': False, 'message': str(je)}
        except Exception as e:
            return {'success': False, 'message': _('Lỗi: %s') % str(e)}

    @http.route('/api/transaction-list/send-many-to-exchange', type='json', auth='user')
    def send_many_pairs_to_exchange(self, matched_order_ids=None, auto_submit=True, **kwargs):
        """Gửi nhiều cặp lệnh đã khớp lên sàn (cả lệnh MUA và lệnh BÁN).

        Params:
            matched_order_ids: list[int] các ID của transaction.matched.orders
            auto_submit: bool
        """
        try:
            # Chuẩn hóa danh sách IDs
            ids = self._coerce_id_list(matched_order_ids)
            if not ids:
                return {'success': False, 'message': _('Danh sách matched_order_ids không hợp lệ hoặc rỗng')}

            Matched = request.env['transaction.matched.orders'].sudo()
            recs = Matched.browse(ids).exists()
            results = []
            created_pairs = 0
            submitted_pairs = 0

            for rec in recs:
                try:
                    orders = self._create_trading_order_from_matched_pair(rec)
                    buy_order = orders['buy_order']
                    sell_order = orders['sell_order']
                    created_pairs += 1
                    
                    buy_submit_ok = False
                    sell_submit_ok = False
                    submit_errors = []
                    
                    if auto_submit:
                        # Submit buy order
                        try:
                            buy_order.action_submit_order()
                            buy_submit_ok = True
                        except Exception as submit_err:
                            submit_errors.append(_('Lệnh mua: %s') % str(submit_err))
                        
                        # Submit sell order
                        try:
                            sell_order.action_submit_order()
                            sell_submit_ok = True
                        except Exception as submit_err:
                            submit_errors.append(_('Lệnh bán: %s') % str(submit_err))
                        
                        if buy_submit_ok and sell_submit_ok:
                            submitted_pairs += 1
                    
                    # Cập nhật trạng thái đã gửi lên sàn nếu cả 2 đều thành công
                    if (buy_submit_ok and sell_submit_ok) or not auto_submit:
                        rec.write({
                            'sent_to_exchange': True,
                            'sent_to_exchange_at': fields.Datetime.now()
                        })
                    
                    results.append({
                        'matched_id': rec.id,
                        'buy_order_id': buy_order.id,
                        'sell_order_id': sell_order.id,
                        'success': True if (not auto_submit or (buy_submit_ok and sell_submit_ok)) else False,
                        'buy_submit_success': buy_submit_ok if auto_submit else None,
                        'sell_submit_success': sell_submit_ok if auto_submit else None,
                        'errors': submit_errors if submit_errors else None
                    })
                except Exception as per_err:
                    results.append({'matched_id': rec.id, 'success': False, 'message': str(per_err)})

            return {
                'success': True,
                'created_pairs': created_pairs,
                'submitted_pairs': submitted_pairs if auto_submit else 0,
                'total_orders_created': created_pairs * 2,  # Mỗi cặp tạo 2 orders
                'results': results,
                'message': _('Đã xử lý %s cặp, tạo %s orders (mua+bán), submit %s cặp') % (len(ids), created_pairs * 2, submitted_pairs if auto_submit else 0)
            }
        except Exception as e:
            return {'success': False, 'message': _('Lỗi: %s') % str(e)}

    # Alias để tương thích frontend: bulk-send-to-exchange
    @http.route('/api/transaction-list/bulk-send-to-exchange', type='json', auth='user')
    def bulk_send_pairs_alias(self, **kwargs):
        """Alias cho send_many_pairs_to_exchange để tương thích URL frontend hiện tại."""
        try:
            # Ưu tiên kwargs (JSON-RPC params)
            raw_ids = (
                kwargs.get('matched_order_ids') or
                kwargs.get('matchedOrderIds') or
                kwargs.get('ids') or
                kwargs.get('selected_ids')
            )
            auto_submit = kwargs.get('auto_submit', kwargs.get('autoSubmit', True))

            # Nếu không có trong kwargs, thử lấy từ request.jsonrequest (plain JSON)
            if not raw_ids:
                try:
                    payload = request.jsonrequest or {}
                    raw_ids = (
                        payload.get('matched_order_ids') or
                        payload.get('matchedOrderIds') or
                        payload.get('ids') or
                        payload.get('selected_ids') or
                        None
                    )
                    if 'auto_submit' in payload or 'autoSubmit' in payload:
                        auto_submit = payload.get('auto_submit', payload.get('autoSubmit', auto_submit))
                except Exception:
                    raw_ids = None

            # Nếu vẫn không có, thử đọc raw body
            if not raw_ids:
                try:
                    body = (request.httprequest.data or b'').decode('utf-8')
                    raw = json.loads(body) if body else {}
                    raw_ids = (
                        (raw.get('matched_order_ids') if isinstance(raw, dict) else None) or
                        (raw.get('matchedOrderIds') if isinstance(raw, dict) else None) or
                        (raw.get('ids') if isinstance(raw, dict) else None) or
                        (raw.get('selected_ids') if isinstance(raw, dict) else None) or
                        raw
                    )
                    if isinstance(raw, dict) and ('auto_submit' in raw or 'autoSubmit' in raw):
                        auto_submit = raw.get('auto_submit', raw.get('autoSubmit', auto_submit))
                except Exception:
                    raw_ids = None

            # Cuối cùng: nếu vẫn rỗng, thử coerce cả kwargs làm list ids
            ids = self._coerce_id_list(raw_ids if raw_ids is not None else kwargs)
            return self.send_many_pairs_to_exchange(matched_order_ids=ids, auto_submit=auto_submit)
        except Exception as e:
            return {'success': False, 'message': _('Lỗi: %s') % str(e)}


