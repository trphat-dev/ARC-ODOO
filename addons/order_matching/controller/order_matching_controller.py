# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import json
import logging
from datetime import datetime
from ..services.order_service import OrderService
from ..services.order_execution_service import OrderExecutionService
from ..services.position_service import PositionService
from ..utils import const, validators
from ..utils.timezone_utils import format_datetime_user_tz

_logger = logging.getLogger(__name__)


class OrderMatchingEngine:
    """Engine khớp lệnh theo chuẩn Stock Exchange - Price-Time Priority (FIFO)
    
    Sử dụng PartialMatchingEngine model để tránh duplicate code.
    Thuật toán chuẩn dựa trên StockExchangeApp-main:
    1. Buy orders: Giá cao nhất trước, cùng giá thì thời gian sớm nhất trước
    2. Sell orders: Giá thấp nhất trước, cùng giá thì thời gian sớm nhất trước
    3. Khớp khi: buy_price >= sell_price
    4. Giá khớp: Luôn lấy giá của sell order
    5. Số lượng khớp: min(buy_quantity, sell_quantity)
    6. Sau khi khớp:
       - Nếu buy_quantity > sell_quantity: Cập nhật buy order với số lượng còn lại, remove sell order
       - Nếu buy_quantity == sell_quantity: Remove cả 2 orders
       - Nếu buy_quantity < sell_quantity: Cập nhật sell order với số lượng còn lại, remove buy order
    """
    
    def __init__(self, env):
        self.env = env
        # Initialize services
        self.order_service = OrderService(env)
        self.execution_service = OrderExecutionService(env)
        self.position_service = PositionService(env)
        # Sử dụng PartialMatchingEngine để tránh duplicate code
        self.matching_engine_model = env['transaction.partial.matching.engine']
    
    def match_orders(self, buy_orders, sell_orders, use_time_priority=True):
        """
        Khớp lệnh theo thuật toán Price-Time Priority (FIFO) - CHUẨN STOCK EXCHANGE
        
        Args:
            buy_orders: List các lệnh mua (portfolio.transaction records)
            sell_orders: List các lệnh bán (portfolio.transaction records)
            use_time_priority: True = Price-Time Priority (FIFO), False = Best Price Only
        
        Returns:
            dict: {
                'matched_pairs': list,
                'remaining_buys': list,
                'remaining_sells': list,
                'algorithm_used': str
            }
        """
        try:
            # Sắp xếp orders theo Price-Time Priority
            buy_book = self._build_priority_queue(buy_orders, 'buy')
            sell_book = self._build_priority_queue(sell_orders, 'sell')
            
            matched_pairs = []
            max_iterations = 1  # QUAN TRỌNG: Chỉ khớp 1 cặp mỗi lần để đảm bảo dữ liệu được commit và refresh đúng
            iteration_count = 0
            
            # Khớp lệnh theo thuật toán chuẩn Stock Exchange
            # CHỈ KHỚP 1 CẶP MỖI LẦN để đảm bảo:
            # 1. Thứ tự ưu tiên được giữ nguyên (khớp cặp đầu tiên trước)
            # 2. Execution được commit vào database
            # 3. matched_units được tính lại chính xác từ executions
            # 4. remaining_units được cập nhật đúng
            # 5. Queue được rebuild từ database sau mỗi lần khớp
            while buy_book and sell_book and iteration_count < max_iterations:
                iteration_count += 1
                
                # QUAN TRỌNG: Reload orders từ database trước mỗi lần khớp
                # Sau khi khớp cặp trước, orders có thể đã thay đổi (remaining_units, status)
                # Cần reload để đảm bảo thứ tự ưu tiên đúng và không khớp lung tung
                fund_id = buy_orders[0].fund_id.id if buy_orders else (sell_orders[0].fund_id.id if sell_orders else None)
                
                # Reload orders từ database với remaining_units mới nhất
                buy_orders_updated = self.env['portfolio.transaction'].search([
                    ('transaction_type', '=', 'buy'),
                    ('status', '=', 'pending'),
                    ('remaining_units', '>', 0),
                ] + ([('fund_id', '=', fund_id)] if fund_id else []))
                
                sell_orders_updated = self.env['portfolio.transaction'].search([
                    ('transaction_type', '=', 'sell'),
                    ('status', '=', 'pending'),
                    ('remaining_units', '>', 0),
                ] + ([('fund_id', '=', fund_id)] if fund_id else []))
                
                # Rebuild priority queue với dữ liệu mới nhất từ database
                buy_book = self._build_priority_queue(buy_orders_updated, 'buy')
                sell_book = self._build_priority_queue(sell_orders_updated, 'sell')
                
                if not buy_book or not sell_book:
                    break
                
                # QUAN TRỌNG: Lấy lệnh tốt nhất từ mỗi bên (index [0] = lệnh ưu tiên cao nhất)
                # Sau khi sort, lệnh tốt nhất luôn ở đầu danh sách:
                # - Buy: book[0] = giá cao nhất, thời gian sớm nhất
                # - Sell: book[0] = giá thấp nhất, thời gian sớm nhất
                best_buy = buy_book[0] if buy_book else None
                best_sell = sell_book[0] if sell_book else None
                
                if not best_buy or not best_sell:
                    break
                
                # Kiểm tra điều kiện giá: buy_price >= sell_price (điều kiện khớp cơ bản)
                buy_price = best_buy['price'] or 0
                sell_price = best_sell['price'] or 0
                
                if buy_price < sell_price:
                    # Giá không thỏa mãn, không thể khớp cặp này
                    # QUAN TRỌNG: Không thể khớp cặp đầu tiên, break để reload và thử lại
                    # Không pop(0) vì có thể lần sau sẽ khớp được khi có lệnh mới
                    _logger.debug("[MATCH] Giá không thỏa mãn: Buy %s (giá %s) < Sell %s (giá %s) - Không thể khớp",
                                  best_buy['rec'].id, buy_price, best_sell['rec'].id, sell_price)
                    break
                
                # Kiểm tra điều kiện khớp: cùng quỹ, khác user
                can_match_result, match_reason = self._can_match(best_buy, best_sell)
                if not can_match_result:
                    # Không khớp được do điều kiện khác (cùng user, etc.)
                    # QUAN TRỌNG: Break để reload và thử lại, không pop(0) vì có thể lần sau sẽ khớp được
                    _logger.info("[MATCH] Không thể khớp cặp đầu tiên: Buy %s (giá %s, user %s) vs Sell %s (giá %s, user %s) - Lý do: %s",
                                 best_buy['rec'].id, best_buy['price'],
                                 best_buy['rec'].user_id.id if best_buy['rec'].user_id else None,
                                 best_sell['rec'].id, best_sell['price'],
                                 best_sell['rec'].user_id.id if best_sell['rec'].user_id else None,
                                 match_reason)
                    break
                
                # Khớp lệnh - cả hai lệnh đều thỏa điều kiện
                # QUAN TRỌNG: Đây là cặp ưu tiên cao nhất (index [0] trong danh sách đã sort)
                # Refresh lại remaining từ database để đảm bảo tính chính xác
                # Tránh khớp vượt số lượng khi lệnh đã khớp ở lần trước
                
                # Lấy order records từ best_buy và best_sell
                buy_order_rec = self.env['portfolio.transaction'].browse(best_buy['rec'].id)
                sell_order_rec = self.env['portfolio.transaction'].browse(best_sell['rec'].id)
                
                # Refresh lại remaining từ database
                buy_order_rec.invalidate_recordset(['matched_units', 'remaining_units', 'units'])
                sell_order_rec.invalidate_recordset(['matched_units', 'remaining_units', 'units'])
                
                # Reload từ database để lấy giá trị mới nhất
                buy_order_rec = self.env['portfolio.transaction'].browse(buy_order_rec.id)
                sell_order_rec = self.env['portfolio.transaction'].browse(sell_order_rec.id)
                
                # Tính lại remaining chính xác từ database (theo chuẩn Stock Exchange)
                buy_units_total = float(buy_order_rec.units or 0)
                buy_matched_total = float(buy_order_rec.matched_units or 0)
                buy_quantity = max(0.0, buy_units_total - buy_matched_total)
                
                sell_units_total = float(sell_order_rec.units or 0)
                sell_matched_total = float(sell_order_rec.matched_units or 0)
                sell_quantity = max(0.0, sell_units_total - sell_matched_total)
                
                # Cập nhật remaining trong queue từ database thực tế
                best_buy['remaining'] = buy_quantity
                best_sell['remaining'] = sell_quantity
                
                matched_quantity = min(buy_quantity, sell_quantity)
                
                if matched_quantity <= 0:
                    # Loại bỏ orders đã hết
                    if buy_quantity <= 0:
                        buy_book.pop(0)
                    if sell_quantity <= 0:
                        sell_book.pop(0)
                    continue
                
                # Tạo execution record qua OrderExecutionService
                # Sử dụng helper method từ PartialMatchingEngine
                matched_price = self.matching_engine_model.get_order_price(sell_order_rec)  # Giá khớp = giá sell order
                _logger.info("[MATCH] Đang tạo execution: Buy %s (giá %s, remaining %s) x Sell %s (giá %s, remaining %s), Qty=%s, Price=%s",
                             buy_order_rec.id, buy_price, buy_quantity,
                             sell_order_rec.id, sell_price, sell_quantity,
                             matched_quantity, matched_price)
                try:
                    execution = self.execution_service.add_execution(
                        buy_order_rec,
                        sell_order_rec,
                        matched_quantity,
                        matched_price,
                        context={'source': 'order_matching_engine'}
                    )
                    _logger.info("[MATCH] ✓ Đã tạo execution %s (%s) cho cặp Buy %s x Sell %s, Qty=%s, Price=%s",
                                 execution.id, execution.name, buy_order_rec.id, sell_order_rec.id,
                                 matched_quantity, matched_price)
                except Exception as e:
                    import traceback
                    _logger.error("[MATCH] ✗ LỖI khi tạo execution cho cặp Buy %s x Sell %s: %s",
                                  buy_order_rec.id, sell_order_rec.id, str(e))
                    _logger.error("[MATCH] Traceback: %s", traceback.format_exc())
                    # KHÔNG continue - phải raise exception để dừng matching nếu không tạo được execution
                    raise
                
                # Tạo cặp khớp cho response (luôn tạo để trả về frontend)
                pair = self._create_matched_pair(best_buy, best_sell, matched_quantity)
                matched_pairs.append(pair)
                
                # QUAN TRỌNG: Commit database để đảm bảo execution record được lưu
                self.env.cr.commit()
                
                # QUAN TRỌNG: Reload từ database để lấy matched_units mới nhất (từ executions)
                # Đảm bảo remaining_units được tính chính xác trước khi tiếp tục
                buy_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                sell_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                buy_order_rec = self.env['portfolio.transaction'].browse(buy_order_rec.id)
                sell_order_rec = self.env['portfolio.transaction'].browse(sell_order_rec.id)
                
                # Tính toán remaining từ database sau khi refresh
                buy_units = float(buy_order_rec.units or 0)
                buy_matched_after = float(buy_order_rec.matched_units or 0)  # Đã được tính từ executions
                buy_new_remaining = max(0.0, buy_units - buy_matched_after)
                
                sell_units = float(sell_order_rec.units or 0)
                sell_matched_after = float(sell_order_rec.matched_units or 0)  # Đã được tính từ executions
                sell_new_remaining = max(0.0, sell_units - sell_matched_after)
                
                # QUAN TRỌNG: Kiểm tra lại remaining sau khi commit và refresh
                # Nếu remaining <= 0, không thể khớp tiếp
                if buy_new_remaining <= 0 or sell_new_remaining <= 0:
                    _logger.debug("[MATCH] Remaining <= 0 sau khi khớp: Buy remaining=%s, Sell remaining=%s",
                                 buy_new_remaining, sell_new_remaining)
                    break
                
                if buy_quantity > sell_quantity:
                    # Buy order còn lại, Sell order hết
                    # QUAN TRỌNG: Buy order đang ở đầu queue (best_buy = buy_book[0])
                    # Cần cập nhật remaining ngay tại vị trí đầu tiên, KHÔNG remove
                    
                    # Cập nhật buy order status
                    # matched_units sẽ được tính tự động từ executions (computed field)
                    # remaining_units sẽ được tính tự động từ units - matched_units (computed field)
                    buy_new_status = 'pending' if buy_new_remaining > 0 else 'completed'
                    self.order_service.update_status(
                        buy_order_rec,
                        buy_new_status,
                        matched_units=None,  # Không truyền - sẽ tính từ executions
                        remaining_units=buy_new_remaining,  # Chỉ để tính is_matched
                        context={'bypass_investment_update': True}
                    )
                    
                    # Cập nhật sell order: đã khớp hết
                    self.order_service.update_status(
                        sell_order_rec,
                        'completed',
                        matched_units=None,  # Không truyền - sẽ tính từ executions
                        remaining_units=0,  # Chỉ để tính is_matched
                        context={'bypass_investment_update': True}
                    )
                    
                    # Cập nhật positions qua PositionService
                    matched_price = self.matching_engine_model.get_order_price(sell_order_rec)
                    self.position_service.update_positions(
                        buy_order_rec,
                        sell_order_rec,
                        matched_quantity,
                        matched_price
                    )
                    
                    # QUAN TRỌNG: Commit database sau mỗi lần khớp để đảm bảo execution được lưu
                    self.env.cr.commit()
                    
                    # Refresh lại orders từ database để lấy matched_units mới nhất
                    buy_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    # Reload từ database để lấy giá trị mới nhất
                    buy_order_rec = self.env['portfolio.transaction'].browse(buy_order_rec.id)
                    sell_order_rec = self.env['portfolio.transaction'].browse(sell_order_rec.id)
                    
                    # Tính lại remaining chính xác từ database sau khi commit
                    buy_units_after = float(buy_order_rec.units or 0)
                    buy_matched_after = float(buy_order_rec.matched_units or 0)
                    buy_remaining_actual = max(0.0, buy_units_after - buy_matched_after)
                    
                    # QUAN TRỌNG: Kiểm tra remaining sau khi commit và refresh
                    # Nếu remaining <= 0, không thể khớp tiếp
                    if buy_remaining_actual <= 0:
                        _logger.info("[MATCH] Buy order %s đã hết remaining sau khi khớp, break để reload",
                                     buy_order_rec.id)
                        break
                    
                    # QUAN TRỌNG: Buy order đang ở đầu queue (index 0), cập nhật remaining ngay tại đó
                    # Remove sell order khỏi queue (đã khớp hết)
                    sell_book.pop(0)
                    
                    # Cập nhật buy order trong queue tại vị trí đầu tiên với remaining thực tế từ database
                    buy_book[0]['remaining'] = buy_remaining_actual
                    _logger.info("[MATCH] ✓ Buy order %s còn lại %s units (từ DB), cập nhật tại đầu queue",
                                 buy_order_rec.id, buy_remaining_actual)
                    
                    # QUAN TRỌNG: Break ngay sau khi khớp 1 cặp để đảm bảo chỉ khớp từ từ
                    # Frontend sẽ gọi lại API để khớp tiếp cặp tiếp theo
                    _logger.info("[MATCH] ✓ Đã khớp 1 cặp: Buy %s x Sell %s, Qty=%s, Buy remaining=%s",
                                 buy_order_rec.id, sell_order_rec.id, matched_quantity, buy_remaining_actual)
                    break
                    
                elif buy_quantity == sell_quantity:
                    # Cả hai orders đều khớp hết
                    # Invalidate để trigger recompute matched_units từ executions
                    buy_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    
                    # Cập nhật status qua OrderService
                    # matched_units sẽ được tính tự động từ executions (computed field)
                    self.order_service.update_status(
                        buy_order_rec,
                        'completed',
                        matched_units=None,  # Không truyền - sẽ tính từ executions
                        remaining_units=0,  # Chỉ để tính is_matched
                        context={'bypass_investment_update': True}
                    )
                    
                    self.order_service.update_status(
                        sell_order_rec,
                        'completed',
                        matched_units=None,  # Không truyền - sẽ tính từ executions
                        remaining_units=0,  # Chỉ để tính is_matched
                        context={'bypass_investment_update': True}
                    )
                    
                    # Cập nhật positions qua PositionService
                    matched_price = self.matching_engine_model.get_order_price(sell_order_rec)
                    self.position_service.update_positions(
                        buy_order_rec,
                        sell_order_rec,
                        matched_quantity,
                        matched_price
                    )
                    
                    # QUAN TRỌNG: Commit database sau mỗi lần khớp để đảm bảo execution được lưu
                    self.env.cr.commit()
                    
                    # Refresh lại orders từ database để lấy matched_units mới nhất
                    buy_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    # Reload từ database để lấy giá trị mới nhất
                    buy_order_rec = self.env['portfolio.transaction'].browse(buy_order_rec.id)
                    sell_order_rec = self.env['portfolio.transaction'].browse(sell_order_rec.id)
                    
                    # QUAN TRỌNG: Sau khi commit, break để reload orders từ database
                    # Đảm bảo chỉ khớp 1 cặp mỗi lần và thứ tự ưu tiên được giữ nguyên
                    _logger.info("[MATCH] ✓ Đã khớp hoàn toàn cặp: Buy %s x Sell %s, Qty=%s",
                                 buy_order_rec.id, sell_order_rec.id, matched_quantity)
                    break
                    
                else:  # buy_quantity < sell_quantity
                    # Sell order còn lại, Buy order hết
                    # QUAN TRỌNG: Sell order đang ở đầu queue (best_sell = sell_book[0])
                    # Cần cập nhật remaining ngay tại vị trí đầu tiên, KHÔNG remove
                    
                    # Cập nhật sell order status
                    # matched_units sẽ được tính tự động từ executions (computed field)
                    sell_new_status = 'pending' if sell_new_remaining > 0 else 'completed'
                    self.order_service.update_status(
                        sell_order_rec,
                        sell_new_status,
                        matched_units=None,  # Không truyền - sẽ tính từ executions
                        remaining_units=sell_new_remaining,  # Chỉ để tính is_matched
                        context={'bypass_investment_update': True}
                    )
                    
                    # Cập nhật buy order: đã khớp hết
                    self.order_service.update_status(
                        buy_order_rec,
                        'completed',
                        matched_units=None,  # Không truyền - sẽ tính từ executions
                        remaining_units=0,  # Chỉ để tính is_matched
                        context={'bypass_investment_update': True}
                    )
                    
                    # Cập nhật positions qua PositionService
                    matched_price = self.matching_engine_model.get_order_price(sell_order_rec)
                    self.position_service.update_positions(
                        buy_order_rec,
                        sell_order_rec,
                        matched_quantity,
                        matched_price
                    )
                    
                    # QUAN TRỌNG: Commit database sau mỗi lần khớp để đảm bảo execution được lưu
                    self.env.cr.commit()
                    
                    # Refresh lại orders từ database để lấy matched_units mới nhất
                    buy_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order_rec.invalidate_recordset(['matched_units', 'remaining_units'])
                    # Reload từ database để lấy giá trị mới nhất
                    buy_order_rec = self.env['portfolio.transaction'].browse(buy_order_rec.id)
                    sell_order_rec = self.env['portfolio.transaction'].browse(sell_order_rec.id)
                    
                    # Tính lại remaining chính xác từ database sau khi commit
                    sell_units_after = float(sell_order_rec.units or 0)
                    sell_matched_after = float(sell_order_rec.matched_units or 0)
                    sell_remaining_actual = max(0.0, sell_units_after - sell_matched_after)
                    
                    # QUAN TRỌNG: Kiểm tra remaining sau khi commit và refresh
                    # Nếu remaining <= 0, không thể khớp tiếp
                    if sell_remaining_actual <= 0:
                        _logger.info("[MATCH] Sell order %s đã hết remaining sau khi khớp, break để reload",
                                     sell_order_rec.id)
                        break
                    
                    # QUAN TRỌNG: Sell order đang ở đầu queue (index 0), cập nhật remaining ngay tại đó
                    # Remove buy order khỏi queue (đã khớp hết)
                    buy_book.pop(0)
                    
                    # Cập nhật sell order trong queue tại vị trí đầu tiên với remaining thực tế từ database
                    sell_book[0]['remaining'] = sell_remaining_actual
                    _logger.info("[MATCH] ✓ Sell order %s còn lại %s units (từ DB), cập nhật tại đầu queue",
                                 sell_order_rec.id, sell_remaining_actual)
                    
                    # QUAN TRỌNG: Break ngay sau khi khớp 1 cặp để đảm bảo chỉ khớp từ từ
                    # Frontend sẽ gọi lại API để khớp tiếp cặp tiếp theo
                    _logger.info("[MATCH] ✓ Đã khớp 1 cặp: Buy %s x Sell %s, Qty=%s, Sell remaining=%s",
                                 buy_order_rec.id, sell_order_rec.id, matched_quantity, sell_remaining_actual)
                    break
                
                
            
            return {
                "matched_pairs": matched_pairs,
                "remaining_buys": [item['rec'] for item in buy_book],
                "remaining_sells": [item['rec'] for item in sell_book],
                "algorithm_used": "Price-Time Priority (FIFO)"
            }
            
        except Exception as e:
            import traceback
            _logger.error("[MATCH ERROR] Lỗi khi khớp lệnh: %s", str(e))
            _logger.error("[MATCH ERROR] Traceback: %s", traceback.format_exc())
            return {
                "matched_pairs": [],
                "remaining_buys": buy_orders,
                "remaining_sells": sell_orders,
                "algorithm_used": "Price-Time Priority (FIFO)",
                "error": str(e)
            }
    
    def _build_priority_queue(self, orders, order_type):
        """
        Xây dựng priority queue theo Price-Time Priority
        Sử dụng helper methods từ PartialMatchingEngine để tránh duplicate code
        
        Args:
            orders: List các orders
            order_type: 'buy' hoặc 'sell'
        
        Returns:
            List đã sắp xếp theo priority
        """
        book = []
        
        for order in orders:
            # Tính toán remaining_units chính xác
            units_total = float(order.units or 0)
            matched_total = float(order.matched_units or 0)
            remaining = max(0.0, units_total - matched_total)
            
            # Chỉ thêm vào queue nếu còn remaining > 0
            if remaining > 0:
                # Sử dụng helper method từ PartialMatchingEngine
                order_price = self.matching_engine_model.get_order_price(order)
                order_time = self._get_order_time(order)
                # QUAN TRỌNG: Ưu tiên created_at (thời gian đặt lệnh ban đầu), sau đó create_date
                time_for_int = (order.created_at if hasattr(order, 'created_at') and order.created_at else None) or (order.create_date if hasattr(order, 'create_date') else None)
                time_int = self.matching_engine_model.time_to_integer_helper(time_for_int)
                
                book.append({
                    'rec': order,
                    'remaining': remaining,
                    'price': order_price,
                    'time': order_time,
                    'time_int': time_int
                })
        
        # Sắp xếp theo Price-Time Priority CHUẨN FIFO
        # QUAN TRỌNG: Lệnh tốt nhất (ưu tiên cao nhất) phải ở index [0]
        if order_type == 'buy':
            # Buy: Giá cao nhất trước, cùng giá thì thời gian sớm nhất trước
            # Sắp xếp giảm dần theo giá (-price), tăng dần theo thời gian (time_int)
            # → Lệnh giá cao nhất, thời gian sớm nhất sẽ ở đầu danh sách
            book.sort(key=lambda x: (-x['price'], x['time_int']))
        else:  # sell
            # Sell: Giá thấp nhất trước, cùng giá thì thời gian sớm nhất trước
            # Sắp xếp tăng dần theo giá (price), tăng dần theo thời gian (time_int)
            # → Lệnh giá thấp nhất, thời gian sớm nhất sẽ ở đầu danh sách
            book.sort(key=lambda x: (x['price'], x['time_int']))
        
        # Đảm bảo: Sau khi sort, lệnh tốt nhất (ưu tiên cao nhất) luôn ở index [0]
        # - Buy: book[0] = lệnh giá cao nhất, thời gian sớm nhất
        # - Sell: book[0] = lệnh giá thấp nhất, thời gian sớm nhất
        return book
    
    def _get_order_time(self, order):
        """Lấy thời gian đặt lệnh - Ưu tiên created_at, fallback create_date
        
        Chuyển đổi từ UTC sang timezone của user trước khi format.
        """
        # QUAN TRỌNG: Ưu tiên created_at (thời gian đặt lệnh ban đầu), sau đó create_date
        dt = None
        if hasattr(order, 'created_at') and order.created_at:
            dt = order.created_at
        elif hasattr(order, 'create_date') and order.create_date:
            dt = order.create_date
        
        if dt:
            # Sử dụng helper function để chuyển đổi timezone
            result = format_datetime_user_tz(self.env, dt)
            if result:
                return result
        
        # Fallback cuối cùng - trả về thời gian hiện tại theo user timezone
        return format_datetime_user_tz(self.env, datetime.now())
    
    def _can_match(self, buy_item, sell_item):
        """
        Kiểm tra có thể khớp lệnh không
        Sử dụng helper method từ PartialMatchingEngine để tránh duplicate code
        
        Returns:
            tuple: (can_match: bool, reason: str)
        """
        buy = buy_item['rec']
        sell = sell_item['rec']
        
        # Sử dụng helper method từ PartialMatchingEngine
        return self.matching_engine_model.can_match_orders(buy, sell)
    
    def _create_matched_pair(self, buy_item, sell_item, matched_quantity):
        """
        Tạo cặp lệnh khớp theo chuẩn Stock Exchange
        Sử dụng helper methods từ PartialMatchingEngine để tránh duplicate code
        """
        buy = buy_item['rec']
        sell = sell_item['rec']
        
        # Giá khớp: Luôn lấy giá của sell order (theo chuẩn Stock Exchange)
        matched_price = sell_item['price']
        
        # QUAN TRỌNG: Không tạo mã thủ công - để sequence tự động tạo format HDC-DDMMYY/STT
        # Mỗi cặp lệnh sẽ có mã thỏa thuận riêng từ sequence
        # Name sẽ được tự động tạo trong create() method của transaction.matched.orders
        
        return {
            "buy_id": buy.id,
            "sell_id": sell.id,
            "buy_order_id": buy.id,
            "sell_order_id": sell.id,
            "matched_quantity": matched_quantity,
            "matched_price": matched_price,
            "matched_ccq": matched_quantity,
            "buy_price": buy_item['price'],
            "sell_price": sell_item['price'],
            "buy_units": getattr(buy, 'units', 0) or 0,
            "sell_units": getattr(sell, 'units', 0) or 0,
            "buy_remaining": buy_item['remaining'],
            "sell_remaining": sell_item['remaining'],
            # Times: Ưu tiên created_at (thời gian đặt lệnh), fallback create_date
            "buy_in_time": format_datetime_user_tz(self.env, buy.created_at if hasattr(buy, 'created_at') and buy.created_at else buy.create_date) or buy_item.get('time', ''),
            "sell_in_time": format_datetime_user_tz(self.env, sell.created_at if hasattr(sell, 'created_at') and sell.created_at else sell.create_date) or sell_item.get('time', ''),
            # Out times: date_end (thời gian khớp)
            "buy_out_time": format_datetime_user_tz(self.env, buy.date_end if hasattr(buy, 'date_end') and buy.date_end else None) or '',
            "sell_out_time": format_datetime_user_tz(self.env, sell.date_end if hasattr(sell, 'date_end') and sell.date_end else None) or '',
            # Thêm các field gốc để frontend có thể sử dụng
            "buy_created_at": format_datetime_user_tz(self.env, buy.created_at if hasattr(buy, 'created_at') and buy.created_at else buy.create_date) or '',
            "sell_created_at": format_datetime_user_tz(self.env, sell.created_at if hasattr(sell, 'created_at') and sell.created_at else sell.create_date) or '',
            "buy_date_end": format_datetime_user_tz(self.env, buy.date_end if hasattr(buy, 'date_end') and buy.date_end else None) or '',
            "sell_date_end": format_datetime_user_tz(self.env, sell.date_end if hasattr(sell, 'date_end') and sell.date_end else None) or '',
            "buy_source": getattr(buy, 'source', 'portal'),
            "sell_source": getattr(sell, 'source', 'portal'),
            "match_time": format_datetime_user_tz(self.env, datetime.now()),
            "algorithm_used": "Price-Time Priority (FIFO)",
            "fund_name": buy.fund_id.name if buy.fund_id else 'N/A',
            "fund_id": buy.fund_id.id if buy.fund_id else None,
            # Name sẽ được tự động tạo bởi sequence với format HDC-DDMMYY/STT
        }


class OrderMatchingController(http.Controller):
    """Controller khớp lệnh giao dịch - API chính cho order matching"""
    
    def _is_market_maker(self, transaction):
        """Kiểm tra xem transaction có phải là market maker không"""
        try:
            if not transaction.user_id:
                return False
            
            if transaction.user_id.has_group('base.group_user'):
                return True
            
            if hasattr(transaction, 'source') and transaction.source == 'sale':
                return True
            
            return False
        except Exception:
            return False
    
    @http.route('/api/transaction-list/match-orders', type='http', auth='user', methods=['POST'], csrf=False)
    def match_transactions(self, **kwargs):
        """Khớp lệnh giao dịch sử dụng engine riêng"""
        try:
            Transaction = request.env['portfolio.transaction'].sudo()
            
            # Đọc tham số từ JSON body
            try:
                raw = (request.httprequest.data or b'').decode('utf-8')
                data = json.loads(raw) if raw else {}
            except Exception:
                try:
                    data = request.jsonrequest or {}
                except Exception:
                    data = {}
            
            status_mode = (data.get('status_mode') or 'pending').strip().lower()
            use_time_priority = data.get('use_time_priority', False)
            fund_id = data.get('fund_id')
            match_type = data.get('match_type', 'all')
            
            # Advisory lock để tránh chạy song song
            locked = False
            try:
                request.env.cr.execute("SELECT pg_try_advisory_lock(hashtext(%s))", ('transaction_matching_lock',))
                res = request.env.cr.fetchone()
                locked = bool(res and res[0])
            except Exception:
                locked = True
            if not locked:
                return request.make_response(
                    json.dumps({
                        "success": True,
                        "message": "Matching đang chạy ở tiến trình khác",
                        "summary": {"total_matched": 0}
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            # CHUẨN QUỐC TẾ: Xây dựng domain theo chế độ trạng thái
            # KHÔNG BAO GIỜ split/clone order - chỉ tạo execution records
            # remaining_units được tính từ executions: remaining = units - sum(executions.matched_quantity)
            def _build_domains(mode):
                if (mode or 'pending') == 'completed':
                    buy_domain = [('transaction_type', '=', 'buy'), ('status', '=', 'completed'), ('ccq_remaining_to_match', '>', 0)]
                    sell_domain = [('transaction_type', '=', 'sell'), ('status', '=', 'completed'), ('ccq_remaining_to_match', '>', 0)]
                else:  # pending
                    # CHUẨN QUỐC TẾ: Lấy TẤT CẢ lệnh pending có remaining_units > 0
                    # remaining_units = units - matched_units (computed từ executions)
                    buy_domain = [
                        ('transaction_type', '=', 'buy'), 
                        ('status', '=', 'pending'),
                        ('remaining_units', '>', 0)
                    ]
                    sell_domain = [
                        ('transaction_type', '=', 'sell'), 
                        ('status', '=', 'pending'),
                        ('remaining_units', '>', 0)
                    ]
                
                try:
                    if fund_id:
                        fid = int(fund_id)
                        buy_domain.append(('fund_id', '=', fid))
                        sell_domain.append(('fund_id', '=', fid))
                except Exception:
                    pass
                return buy_domain, sell_domain
            
            buy_domain, sell_domain = _build_domains(status_mode)
            pending_buys = Transaction.search(buy_domain)
            pending_sells = Transaction.search(sell_domain)
            
            # Lọc theo loại khớp lệnh
            if match_type == 'investor_investor':
                pending_buys = pending_buys.filtered(lambda t: not self._is_market_maker(t))
                pending_sells = pending_sells.filtered(lambda t: not self._is_market_maker(t))
            elif match_type == 'market_maker_investor':
                pending_buys = pending_buys.filtered(lambda t: self._is_market_maker(t))
                pending_sells = pending_sells.filtered(lambda t: not self._is_market_maker(t))
            
            if not pending_buys or not pending_sells:
                return request.make_response(
                    json.dumps({
                        "success": True,
                        "message": _("Không có lệnh mua/bán phù hợp để khớp (loại: %s)") % match_type,
                        "matched_pairs": [],
                        "remaining": {"buys": [b.id for b in (pending_buys or [])], "sells": [s.id for s in (pending_sells or [])]},
                        "summary": {"total_matched": 0, "total_buy_orders": len(pending_buys), "total_sell_orders": len(pending_sells)}
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            matching_engine = OrderMatchingEngine(request.env)
            
            # Nhóm theo fund để tăng tỷ lệ khớp
            def _group_by_fund(recs):
                groups = {}
                for r in recs:
                    fid = r.fund_id.id if r.fund_id else 0
                    groups.setdefault(fid, []).append(r)
                return groups
            
            buy_groups = _group_by_fund(pending_buys)
            sell_groups = _group_by_fund(pending_sells)
            
            matched_pairs = []
            remaining_buys = []
            remaining_sells = []
            algorithm_used = 'Price-Time Priority (FIFO)'
            
            for fid, buys in buy_groups.items():
                sells = sell_groups.get(fid, [])
                if not buys or not sells:
                    remaining_buys.extend(buys or [])
                    remaining_sells.extend(sells or [])
                    continue
                
                result = matching_engine.match_orders(buys, sells, use_time_priority)
                matched_pairs.extend(result.get('matched_pairs', []))
                remaining_buys.extend(result.get('remaining_buys', []))
                remaining_sells.extend(result.get('remaining_sells', []))
                algorithm_used = result.get('algorithm_used', algorithm_used)
            
            # NOTE: Execution records đã được tạo trong OrderMatchingEngine.match_orders()
            # qua OrderExecutionService.addExecution() - không cần tạo lại ở đây
            # Chỉ đếm số lượng execution đã được tạo
            created_count = len(matched_pairs)
            
            # Log summary
            _logger.info("[MATCH] Created %s execution records via OrderExecutionService", created_count)
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "matched_pairs": matched_pairs,
                    "remaining": {"buys": [b.id for b in remaining_buys], "sells": [s.id for s in remaining_sells]},
                    "summary": {
                        "total_matched": len(matched_pairs),
                        "total_buy_orders": len(pending_buys),
                        "total_sell_orders": len(pending_sells)
                    },
                    "algorithm_used": algorithm_used
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            import traceback
            _logger.error("Lỗi khi khớp lệnh: %s", str(e))
            _logger.error("Traceback: %s", traceback.format_exc())
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e),
                    "matched_pairs": [],
                    "summary": {"total_matched": 0}
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )
        finally:
            try:
                request.env.cr.execute("SELECT pg_advisory_unlock(hashtext(%s))", ('transaction_matching_lock',))
            except Exception:
                pass
