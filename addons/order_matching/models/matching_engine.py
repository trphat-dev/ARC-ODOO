# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime, timedelta
from ..utils import const, validators
from typing import List, Dict, Tuple, Optional
from enum import Enum

_logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Loại lệnh giao dịch"""
    BUY = 'buy'
    SELL = 'sell'


class PartialMatchingEngine(models.Model):
    """
    Engine khớp lệnh một phần chính xác theo thuật toán Stock Exchange
    Dựa trên thuật toán từ StockExchangeApp với Priority Queue và FIFO
    """
    _name = 'transaction.partial.matching.engine'
    _description = 'Partial Matching Engine for Stock Exchange'
    _rec_name = 'name'

    name = fields.Char(string='Engine Name', required=True, default='Partial Matching Engine')
    fund_id = fields.Many2one('portfolio.fund', string='Fund', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    
    # Cấu hình engine
    use_time_priority = fields.Boolean(
        string='Use Time Priority (FIFO)', 
        default=True,
        help='Ưu tiên thời gian khi cùng giá'
    )
    min_match_quantity = fields.Float(
        string='Minimum Match Quantity', 
        default=50.0,
        help='Số lượng tối thiểu để khớp lệnh'
    )
    max_partial_matches = fields.Integer(
        string='Max Partial Matches per Order',
        default=10,
        help='Số lần khớp một phần tối đa cho mỗi lệnh'
    )
    
    # Thống kê (tính động dựa trên giao dịch đã khớp)
    total_matches = fields.Integer(
        string='Total Matches',
        compute='_compute_engine_match_stats',
        store=True,
        search='_search_total_matches'
    )
    total_partial_matches = fields.Integer(
        string='Total Partial Matches',
        compute='_compute_engine_match_stats',
        store=True,
        search='_search_total_partial_matches'
    )
    last_match_date = fields.Datetime(
        string='Last Match Date',
        compute='_compute_engine_match_stats',
        store=True,
        search='_search_last_match_date'
    )
    
    # Logs
    match_logs = fields.Text(string='Match Logs', readonly=True)

    def add_order(self, order_record):
        """
        Thêm lệnh vào engine và thực hiện khớp lệnh CHUẨN
        Dựa trên CompanyOrderBookModule.addOrder() từ StockExchangeApp-main
        
        Java workflow:
        public List<CompanyStockTransaction> addOrder(CompanyOrder order) {
            if (order.getOrderType() == CompanyOrderType.BUY) {
                buyOrders.add(order);
            } else if (order.getOrderType() == CompanyOrderType.SELL) {
                sellOrders.add(order);
            }
            return match();  // Match ngay sau khi thêm
        }
        
        Args:
            order_record: portfolio.transaction record
            
        Returns:
            List[Dict]: Danh sách các cặp lệnh đã khớp
        """
        try:
            # Validate order
            if not self._validate_order(order_record):
                return []
            
            # Thêm lệnh vào priority queue (tương tự buyOrders.add() hoặc sellOrders.add())
            self._add_to_queue(order_record)
            
            # Thực hiện khớp lệnh NGAY LẬP TỨC (tương tự return match() trong Java)
            matched_pairs = self._match_orders()
            
            # Cập nhật thống kê
            self._update_statistics(matched_pairs)
            
            return matched_pairs
            
        except Exception as e:
            _logger.error("Error in add_order: %s", str(e))
            import traceback
            _logger.error("Traceback: %s", traceback.format_exc())
            return []

    def _validate_order(self, order_record):
        """
        Validate lệnh trước khi thêm vào engine
        Tính toán remaining_units chính xác từ units - matched_units (theo chuẩn Stock Exchange)
        """
        if not order_record:
            return False
        
        if order_record.fund_id.id != self.fund_id.id:
            return False
            
        if order_record.status != 'pending':
            return False
        
        # Tính toán remaining_units chính xác từ units - matched_units
        units_total = float(order_record.units or 0)
        matched_total = float(order_record.matched_units or 0)
        remaining = max(0.0, units_total - matched_total)
            
        if remaining <= 0:
            return False
            
        # CHỈ khớp lệnh thỏa thuận (negotiated)
        # Lệnh thường (normal) gửi lên sàn hoặc xử lý riêng, không vào sổ lệnh khớp nội bộ
        if hasattr(order_record, 'order_mode') and order_record.order_mode == 'normal':
            return False
            
        return True

    def _add_to_queue(self, order_record):
        """
        Thêm lệnh vào priority queue tương ứng CHUẨN
        Dựa trên CompanyOrderBookModule.addOrder() từ StockExchangeApp-main
        
        Java: 
        if (order.getOrderType() == CompanyOrderType.BUY) {
            buyOrders.add(order);  // PriorityQueue tự động sắp xếp theo Comparator
        } else if (order.getOrderType() == CompanyOrderType.SELL) {
            sellOrders.add(order);
        }
        
        Odoo: Lưu vào database với priority_score để sắp xếp
        Tính toán quantity chính xác từ units - matched_units (theo chuẩn Stock Exchange)
        """
        # Tính toán remaining_units chính xác từ units - matched_units
        # Java sử dụng order.getQuantity() trực tiếp, nhưng trong Odoo cần tính từ units - matched_units
        units_total = float(order_record.units or 0)
        matched_total = float(order_record.matched_units or 0)
        remaining = max(0.0, units_total - matched_total)
        
        # Kiểm tra xem order đã có trong queue chưa (tránh duplicate)
        existing_queue = self.env['transaction.order.queue'].search([
            ('engine_id', '=', self.id),
            ('order_id', '=', order_record.id),
            ('status', '=', 'pending')
        ], limit=1)
        
        if existing_queue:
            # Cập nhật queue record hiện có
            # QUAN TRỌNG: Chỉ cập nhật quantity và price, KHÔNG cập nhật priority_score
            # priority_score chỉ phụ thuộc vào price và create_time (thời gian đặt lệnh ban đầu)
            # KHÔNG phụ thuộc vào quantity/remaining_units
            # Lệnh khớp một phần vẫn giữ nguyên vị trí FIFO (theo thời gian ban đầu)
            existing_queue.write({
                'quantity': remaining,
                'price': order_record.price or order_record.current_nav,
                # KHÔNG cập nhật priority_score - giữ nguyên để không đẩy xuống cuối
            })
            return existing_queue
        
        # Tạo queue record mới (tương tự add() vào PriorityQueue)
        queue_record = self.env['transaction.order.queue'].create({
            'engine_id': self.id,
            'order_id': order_record.id,
            'order_type': order_record.transaction_type,
            'price': order_record.price or order_record.current_nav,
            'quantity': remaining,  # Sử dụng remaining đã tính toán chính xác
            'priority_score': self._calculate_priority_score(order_record),
            'create_time': order_record.create_date,
            'status': 'pending'
        })
        
        return queue_record

    def _calculate_priority_score(self, order_record):
        """
        Tính điểm ưu tiên theo Price-Time Priority CHUẨN
        Dựa trên CompanyStockComparator từ StockExchangeApp-main
        
        Logic Java Comparator:
        - Buy: return -1 nếu order1 có priority cao hơn (giá cao hơn, hoặc cùng giá nhưng thời gian sớm hơn)
        - Sell: return -1 nếu order1 có priority cao hơn (giá thấp hơn, hoặc cùng giá nhưng thời gian sớm hơn)
        
        PriorityQueue sắp xếp theo: return -1 → priority cao hơn → ở đầu queue
        
        Công thức Odoo (score cao hơn = priority cao hơn):
        - Buy: (price * large_number) - time_int
          → Giá cao hơn → score cao hơn
          → Cùng giá, time_int nhỏ hơn (sớm hơn) → score cao hơn
        - Sell: (max_price - price) * large_number - time_int
          → Giá thấp hơn → (max_price - price) cao hơn → score cao hơn
          → Cùng giá, time_int nhỏ hơn (sớm hơn) → score cao hơn
        """
        price = float(order_record.price or order_record.current_nav or 0)
        create_time = order_record.create_date
        
        # Chuyển đổi thời gian thành số để so sánh (giống companyOrderIntegerTime trong Java)
        # Java: (h1*10+h2)*60+(m1*10+m2) = hour*60 + minute
        time_score = self._time_to_integer(create_time)
        
        # Sử dụng số lớn để đảm bảo giá có priority cao hơn thời gian
        # Giả sử giá tối đa là 999999, time_int tối đa là 1440 (24*60)
        LARGE_MULTIPLIER = 1000000
        
        if order_record.transaction_type == 'buy':
            # Buy: Giá cao nhất trước, cùng giá thì thời gian sớm nhất trước
            # Java: if (order1.getPrice() < order2.getPrice()) return 1; (order1 thấp hơn)
            #       else if (order1.getPrice() == order2.getPrice()) {
            #           if (order1TimeStamp > order2TimeStamp) return 1; (order1 muộn hơn)
            #       }
            #       return -1; (order1 cao hơn/ưu tiên hơn)
            # Công thức: (price * LARGE_MULTIPLIER) - time_score
            # → Giá cao hơn → score cao hơn
            # → Cùng giá, time_score nhỏ hơn (sớm hơn) → score cao hơn
            return (price * LARGE_MULTIPLIER) - time_score
        else:  # sell
            # Sell: Giá thấp nhất trước, cùng giá thì thời gian sớm nhất trước
            # Java: if (order1.getPrice() > order2.getPrice()) return 1; (order1 cao hơn)
            #       else if (order1.getPrice() == order2.getPrice()) {
            #           if (order1TimeStamp > order2TimeStamp) return 1; (order1 muộn hơn)
            #       }
            #       return -1; (order1 thấp hơn/ưu tiên hơn)
            # Công thức: (MAX_PRICE - price) * LARGE_MULTIPLIER - time_score
            # → Giá thấp hơn → (MAX_PRICE - price) cao hơn → score cao hơn
            # → Cùng giá, time_score nhỏ hơn (sớm hơn) → score cao hơn
            MAX_PRICE = 1000000  # Giả sử giá tối đa
            return (MAX_PRICE - price) * LARGE_MULTIPLIER - time_score

    def _time_to_integer(self, datetime_obj):
        """
        Chuyển đổi datetime thành integer để so sánh CHUẨN
        Tương tự companyOrderIntegerTime trong Java
        
        Java: 
        private int companyOrderIntegerTime(String timeStamp) {
            int h1 = timeStamp.charAt(0) - '0';
            int h2 = timeStamp.charAt(1) - '0';
            int m1 = timeStamp.charAt(3) - '0';
            int m2 = timeStamp.charAt(4) - '0';
            return (h1*10+h2)*60+(m1*10+m2);
        }
        
        Format input: "HH:MM" (ví dụ: "09:45")
        Output: Số phút từ 00:00 (ví dụ: 09:45 → 9*60+45 = 585)
        """
        if not datetime_obj:
            return 0
        
        try:
            # Lấy giờ và phút từ datetime
            hour = datetime_obj.hour
            minute = datetime_obj.minute
            # Chuyển thành phút từ 00:00 (giống Java: hour*60 + minute)
            # Ví dụ: 09:45 → 9*60+45 = 585
            return hour * 60 + minute
        except Exception:
            return 0

    def _match_orders(self):
        """
        Thực hiện khớp lệnh theo thuật toán Stock Exchange CHUẨN
        Dựa trên CompanyOrderBookModule.match() và checkTransactionExecutor()
        
        Thuật toán chuẩn từ StockExchangeApp-main:
        1. Khớp khi: buy_price >= sell_price (CHỈ kiểm tra giá, không kiểm tra fund/user)
        2. Giá khớp: Luôn lấy giá của sell order
        3. Số lượng khớp: min(buy_quantity, sell_quantity)
        4. Sau khi khớp:
           - Nếu buy_quantity > sell_quantity: Cập nhật buy với số lượng còn lại, remove sell
           - Nếu buy_quantity == sell_quantity: Remove cả 2
           - Nếu buy_quantity < sell_quantity: Cập nhật sell với số lượng còn lại, remove buy
        
        LƯU Ý: Trong StockExchangeApp gốc không có kiểm tra fund/user.
        Kiểm tra fund/user ở đây là business requirement của Odoo module.
        """
        matched_pairs = []
        
        try:
            # Lấy buy orders (sắp xếp theo priority score giảm dần - giá cao nhất trước)
            # Tương tự PriorityQueue với CompanyStockComparator(CompanyOrderType.BUY)
            buy_queues = self.env['transaction.order.queue'].search([
                ('engine_id', '=', self.id),
                ('order_type', '=', 'buy'),
                ('status', '=', 'pending'),
                ('quantity', '>', 0)
            ], order='priority_score desc')
            
            # Lấy sell orders (sắp xếp theo priority score giảm dần - giá thấp nhất trước)
            # Tương tự PriorityQueue với CompanyStockComparator(CompanyOrderType.SELL)
            sell_queues = self.env['transaction.order.queue'].search([
                ('engine_id', '=', self.id),
                ('order_type', '=', 'sell'),
                ('status', '=', 'pending'),
                ('quantity', '>', 0)
            ], order='priority_score desc')
            
            # Khớp lệnh theo thuật toán chuẩn Stock Exchange
            # QUAN TRỌNG: Chỉ khớp 1 cặp mỗi lần để đảm bảo:
            # 1. Thứ tự ưu tiên được giữ nguyên (khớp cặp đầu tiên trước)
            # 2. Dữ liệu được commit và refresh đúng
            # 3. Queue được reload từ database sau mỗi lần khớp
            max_iterations = 1  # CHỈ KHỚP 1 CẶP MỖI LẦN
            iteration_count = 0
            
            while buy_queues and sell_queues and iteration_count < max_iterations:
                iteration_count += 1
                
                # QUAN TRỌNG: Reload queue từ database trước mỗi lần khớp để đảm bảo thứ tự ưu tiên đúng
                # Sau khi khớp cặp trước, queue có thể đã thay đổi (orders đã hết hoặc remaining thay đổi)
                buy_queues = self.env['transaction.order.queue'].search([
                    ('engine_id', '=', self.id),
                    ('order_type', '=', 'buy'),
                    ('status', '=', 'pending'),
                    ('quantity', '>', 0)
                ], order='priority_score desc')
                
                sell_queues = self.env['transaction.order.queue'].search([
                    ('engine_id', '=', self.id),
                    ('order_type', '=', 'sell'),
                    ('status', '=', 'pending'),
                    ('quantity', '>', 0)
                ], order='priority_score desc')
                
                if not buy_queues or not sell_queues:
                    break
                
                # Lấy lệnh tốt nhất từ mỗi bên (tương tự peek() trong Java)
                best_buy_queue = buy_queues[0] if buy_queues else None
                best_sell_queue = sell_queues[0] if sell_queues else None
                
                if not best_buy_queue or not best_sell_queue:
                    break
                
                # QUAN TRỌNG: Lấy lệnh tốt nhất từ mỗi bên (index [0] = lệnh ưu tiên cao nhất)
                # Sau khi reload và sort, lệnh tốt nhất luôn ở đầu danh sách:
                # - Buy: queues[0] = giá cao nhất, thời gian sớm nhất (priority_score cao nhất)
                # - Sell: queues[0] = giá thấp nhất, thời gian sớm nhất (priority_score cao nhất)
                
                # ĐIỀU KIỆN KHỚP CHUẨN: buy_price >= sell_price (theo StockExchangeApp)
                # Java: buyOrders.peek().getPrice() >= sellOrders.peek().getPrice()
                if best_buy_queue.price < best_sell_queue.price:
                    # Giá không thỏa mãn, không thể khớp cặp đầu tiên
                    # QUAN TRỌNG: Break để reload và thử lại, không pop(0) vì có thể lần sau sẽ khớp được
                    break
                
                # Lấy order records
                buy_order = best_buy_queue.order_id
                sell_order = best_sell_queue.order_id
                
                # Validate điều kiện khớp lệnh theo chuẩn sàn chứng chỉ quỹ quốc tế
                can_match, match_reason = validators.OrderValidator.validate_matching_conditions(buy_order, sell_order)
                if not can_match:
                    # Không thể khớp cặp đầu tiên do điều kiện khác (cùng user, etc.)
                    # QUAN TRỌNG: Break để reload và thử lại, không pop(0) vì có thể lần sau sẽ khớp được
                    _logger.debug("[MATCH] Không thể khớp cặp đầu tiên: Buy %s x Sell %s - %s",
                                 buy_order.id, sell_order.id, match_reason)
                    break
                
                # Khớp lệnh - cả hai lệnh đều thỏa điều kiện
                # QUAN TRỌNG: Refresh lại remaining từ database để đảm bảo tính chính xác
                # Tránh khớp vượt số lượng khi lệnh đã khớp ở lần trước
                buy_order.invalidate_recordset(['matched_units', 'remaining_units', 'units'])
                sell_order.invalidate_recordset(['matched_units', 'remaining_units', 'units'])
                # Reload từ database để lấy giá trị mới nhất
                buy_order = self.env['portfolio.transaction'].browse(buy_order.id)
                sell_order = self.env['portfolio.transaction'].browse(sell_order.id)
                
                # Tính lại remaining chính xác từ database (theo chuẩn Stock Exchange)
                buy_units_total = float(buy_order.units or 0)
                buy_matched_total = float(buy_order.matched_units or 0)
                buy_quantity = max(0.0, buy_units_total - buy_matched_total)
                
                sell_units_total = float(sell_order.units or 0)
                sell_matched_total = float(sell_order.matched_units or 0)
                sell_quantity = max(0.0, sell_units_total - sell_matched_total)
                
                # Cập nhật queue.quantity từ remaining thực tế
                if best_buy_queue.quantity != buy_quantity:
                    best_buy_queue.write({'quantity': buy_quantity})
                if best_sell_queue.quantity != sell_quantity:
                    best_sell_queue.write({'quantity': sell_quantity})
                
                # Java: int quantitySold = Math.min(buyOrderQuantity, sellOrderQuantity);
                matched_quantity = min(buy_quantity, sell_quantity)
                
                if matched_quantity <= 0:
                    # Orders đã hết remaining, break để reload và thử lại
                    _logger.debug("[MATCH] Matched quantity <= 0: Buy %s (remaining=%s) x Sell %s (remaining=%s)",
                                 buy_order.id, buy_quantity, sell_order.id, sell_quantity)
                    break
                
                # Kiểm tra min_match_quantity (nếu có)
                if hasattr(self, 'min_match_quantity') and self.min_match_quantity and matched_quantity < self.min_match_quantity:
                    _logger.debug("[MATCH] Matched quantity (%s) < min_match_quantity (%s) - Không thể khớp",
                                 matched_quantity, self.min_match_quantity)
                    break
                
                # QUAN TRỌNG: Tạo execution record TRƯỚC (matched_units sẽ được tính lại tự động từ executions)
                # Tạo cặp khớp (giá khớp = sell_price theo chuẩn Stock Exchange)
                # Java: .price(sellOrder.getPrice()).build()
                pair = self._create_matched_pair(buy_order, sell_order, matched_quantity, best_sell_queue.price)
                if not pair:
                    _logger.error("[MATCH] Không thể tạo matched pair cho Buy %s x Sell %s", buy_order.id, sell_order.id)
                    break
                
                matched_pairs.append(pair)
                
                # QUAN TRỌNG: matched_units là computed field, sẽ được tính lại tự động từ executions
                # Không cần write trực tiếp vào matched_units
                # Chỉ cần invalidate và refresh để trigger recompute
                buy_order.invalidate_recordset(['matched_units', 'remaining_units'])
                sell_order.invalidate_recordset(['matched_units', 'remaining_units'])
                
                # Commit database để đảm bảo execution record được lưu
                self.env.cr.commit()
                
                # QUAN TRỌNG: Reload từ database để lấy matched_units mới nhất (từ executions)
                # Đảm bảo remaining_units được tính chính xác trước khi tiếp tục
                buy_order.invalidate_recordset(['matched_units', 'remaining_units'])
                sell_order.invalidate_recordset(['matched_units', 'remaining_units'])
                buy_order = self.env['portfolio.transaction'].browse(buy_order.id)
                sell_order = self.env['portfolio.transaction'].browse(sell_order.id)
                
                # Tính toán remaining từ database sau khi refresh
                buy_units = float(buy_order.units or 0)
                buy_matched_after = float(buy_order.matched_units or 0)  # Đã được tính từ executions
                buy_remaining_actual = max(0.0, buy_units - buy_matched_after)
                
                sell_units = float(sell_order.units or 0)
                sell_matched_after = float(sell_order.matched_units or 0)  # Đã được tính từ executions
                sell_remaining_actual = max(0.0, sell_units - sell_matched_after)
                
                # QUAN TRỌNG: Kiểm tra lại remaining sau khi commit và refresh
                # Nếu remaining <= 0, không thể khớp tiếp
                if buy_remaining_actual <= 0 or sell_remaining_actual <= 0:
                    _logger.debug("[MATCH] Remaining <= 0 sau khi khớp: Buy remaining=%s, Sell remaining=%s",
                                 buy_remaining_actual, sell_remaining_actual)
                    break
                
                # Xử lý theo thuật toán chuẩn Stock Exchange (checkTransactionExecutor)
                # Java: if (buyOrderQuantity > sellOrderQuantity) { ... }
                if buy_quantity > sell_quantity:
                    # Buy order còn lại, Sell order hết
                    # Java: newOrderAfterSellingStocks.setQuantity(Math.subtractExact(buyOrderQuantity, quantitySold));
                    #       buyOrders.poll(); sellOrders.poll();
                    #       buyOrders.add(newOrderAfterSellingStocks);
                    
                    # QUAN TRỌNG: matched_units là computed field, đã được tính từ executions
                    # Chỉ cần cập nhật status và ccq_remaining_to_match
                    buy_order.with_context(bypass_investment_update=True).sudo().write({
                        'ccq_remaining_to_match': buy_remaining_actual,
                        'status': 'pending' if buy_remaining_actual > 0 else 'completed',
                    })
                    
                    sell_order.sudo().write({
                        'ccq_remaining_to_match': 0,
                        'status': 'completed',
                    })
                    
                    # QUAN TRỌNG: Commit database để đảm bảo execution record được lưu
                    self.env.cr.commit()
                    
                    # Reload từ database để lấy matched_units mới nhất (từ executions)
                    buy_order.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order.invalidate_recordset(['matched_units', 'remaining_units'])
                    buy_order = self.env['portfolio.transaction'].browse(buy_order.id)
                    sell_order = self.env['portfolio.transaction'].browse(sell_order.id)
                    
                    # Tính lại remaining chính xác từ database sau khi commit
                    buy_units_after = float(buy_order.units or 0)
                    buy_matched_after = float(buy_order.matched_units or 0)  # Đã được tính từ executions
                    buy_remaining_actual = max(0.0, buy_units_after - buy_matched_after)
                    
                    # Cập nhật queue với remaining thực tế từ database
                    # QUAN TRỌNG: KHÔNG cập nhật priority_score để giữ nguyên thứ tự ưu tiên
                    # priority_score chỉ phụ thuộc vào price và create_time (thời gian đặt lệnh ban đầu)
                    # KHÔNG phụ thuộc vào quantity/remaining_units
                    # Lệnh khớp một phần vẫn giữ nguyên vị trí FIFO (theo thời gian ban đầu)
                    best_buy_queue.write({
                        'quantity': buy_remaining_actual,
                        'status': 'pending' if buy_remaining_actual > 0 else 'completed'
                        # KHÔNG cập nhật priority_score - giữ nguyên để không đẩy xuống cuối
                    })
                    best_sell_queue.write({
                        'quantity': 0,
                        'status': 'completed'
                    })
                    
                    # Remove sell order khỏi queue (poll())
                    sell_queues = sell_queues[1:]
                    # Nếu buy order hết, remove khỏi queue, nếu không thì giữ lại (add lại với quantity mới)
                    if buy_remaining_actual <= 0:
                        buy_queues = buy_queues[1:]
                    # Nếu còn remaining, queue đã được cập nhật, không cần remove
                    
                elif buy_quantity == sell_quantity:
                    # Cả hai orders đều khớp hết
                    # Java: buyOrders.poll(); sellOrders.poll();
                    
                    # QUAN TRỌNG: matched_units là computed field, đã được tính từ executions
                    # Chỉ cần cập nhật status và ccq_remaining_to_match
                    buy_order.sudo().write({
                        'ccq_remaining_to_match': 0,
                        'status': 'completed',
                    })
                    
                    sell_order.sudo().write({
                        'ccq_remaining_to_match': 0,
                        'status': 'completed',
                    })
                    
                    # QUAN TRỌNG: Commit database để đảm bảo execution record được lưu
                    self.env.cr.commit()
                    
                    # Reload từ database để lấy matched_units mới nhất (từ executions)
                    buy_order.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order.invalidate_recordset(['matched_units', 'remaining_units'])
                    buy_order = self.env['portfolio.transaction'].browse(buy_order.id)
                    sell_order = self.env['portfolio.transaction'].browse(sell_order.id)
                    
                    # Cập nhật queue
                    best_buy_queue.write({
                        'quantity': 0,
                        'status': 'completed'
                    })
                    best_sell_queue.write({
                        'quantity': 0,
                        'status': 'completed'
                    })
                    
                    # QUAN TRỌNG: Sau khi commit và cập nhật, break để reload queue từ database
                    # Đảm bảo chỉ khớp 1 cặp mỗi lần và thứ tự ưu tiên được giữ nguyên
                    break
                    
                else:  # buy_quantity < sell_quantity
                    # Sell order còn lại, Buy order hết
                    # Java: newOrderAfterSellingStocks.setQuantity(Math.subtractExact(sellOrderQuantity, quantitySold));
                    #       buyOrders.poll(); sellOrders.poll();
                    #       sellOrders.add(newOrderAfterSellingStocks);
                    
                    # QUAN TRỌNG: matched_units là computed field, đã được tính từ executions
                    # Chỉ cần cập nhật status và ccq_remaining_to_match
                    # sell_remaining_actual đã được tính ở trên (dòng 443)
                    sell_order.with_context(bypass_investment_update=True).sudo().write({
                        'ccq_remaining_to_match': sell_remaining_actual,
                        'status': 'pending' if sell_remaining_actual > 0 else 'completed',
                    })
                    
                    buy_order.sudo().write({
                        'ccq_remaining_to_match': 0,
                        'status': 'completed',
                    })
                    
                    # QUAN TRỌNG: Commit database để đảm bảo execution record được lưu
                    self.env.cr.commit()
                    
                    # Reload từ database để lấy matched_units mới nhất (từ executions)
                    buy_order.invalidate_recordset(['matched_units', 'remaining_units'])
                    sell_order.invalidate_recordset(['matched_units', 'remaining_units'])
                    buy_order = self.env['portfolio.transaction'].browse(buy_order.id)
                    sell_order = self.env['portfolio.transaction'].browse(sell_order.id)
                    
                    # Tính lại remaining chính xác từ database sau khi commit
                    sell_units_after = float(sell_order.units or 0)
                    sell_matched_after = float(sell_order.matched_units or 0)  # Đã được tính từ executions
                    sell_remaining_actual = max(0.0, sell_units_after - sell_matched_after)
                    
                    # Cập nhật queue với remaining thực tế từ database
                    # QUAN TRỌNG: KHÔNG cập nhật priority_score để giữ nguyên thứ tự ưu tiên
                    # priority_score chỉ phụ thuộc vào price và create_time (thời gian đặt lệnh ban đầu)
                    # KHÔNG phụ thuộc vào quantity/remaining_units
                    # Lệnh khớp một phần vẫn giữ nguyên vị trí FIFO (theo thời gian ban đầu)
                    best_sell_queue.write({
                        'quantity': sell_remaining_actual,
                        'status': 'pending' if sell_remaining_actual > 0 else 'completed'
                        # KHÔNG cập nhật priority_score - giữ nguyên để không đẩy xuống cuối
                    })
                    best_buy_queue.write({
                        'quantity': 0,
                        'status': 'completed'
                    })
                    
                    # QUAN TRỌNG: Sau khi commit và cập nhật, break để reload queue từ database
                    # Đảm bảo chỉ khớp 1 cặp mỗi lần và thứ tự ưu tiên được giữ nguyên
                    break
            
            
            return matched_pairs
            
        except Exception as e:
            _logger.error("Error in _match_orders: %s", str(e))
            import traceback
            _logger.error("Traceback: %s", traceback.format_exc())
            return []

    def _create_matched_pair(self, buy_order, sell_order, matched_quantity, matched_price=None):
        """
        Tạo cặp lệnh khớp theo chuẩn Stock Exchange CHUẨN
        Dựa trên CompanyStockTransaction từ StockExchangeApp-main
        
        Java:
        return CompanyStockTransaction.builder()
            .buyStockOrderId(buyOrder.getId())
            .sellStockOrderId(sellOrder.getId())
            .quantity(quantitySold)
            .price(sellOrder.getPrice()).build();
        
        Format output: "#{buy_id} {price} {quantity} #{sell_id}"
        Ví dụ: "#3 237.45 90 #2"
        
        Args:
            buy_order: Lệnh mua (portfolio.transaction)
            sell_order: Lệnh bán (portfolio.transaction)
            matched_quantity: Số lượng khớp (min(buy_quantity, sell_quantity))
            matched_price: Giá khớp (theo chuẩn Stock Exchange = sell_price)
        """
        try:
            # Giá khớp: Luôn lấy giá của sell order (theo chuẩn Stock Exchange)
            # Java: .price(sellOrder.getPrice())
            if matched_price is None:
                matched_price = sell_order.price or sell_order.current_nav or 0
            
            # QUAN TRỌNG: Không set name thủ công - để sequence tự động tạo format HDC-DDMMYY/STT
            # Sequence sẽ tự động tạo name theo format: HDC-DDMMYY/STT
            # Mỗi cặp lệnh sẽ có mã thỏa thuận riêng từ sequence
            
            # Tạo matched order record (name sẽ được tự động tạo bởi sequence trong create() method)
            matched_order = self.env['transaction.matched.orders'].create({
                # Không set name - để sequence tự động tạo format HDC-DDMMYY/STT
                'buy_order_id': buy_order.id,
                'sell_order_id': sell_order.id,
                'matched_quantity': matched_quantity,
                'matched_price': matched_price,  # Giá khớp = giá sell (theo chuẩn Stock Exchange)
                'fund_id': self.fund_id.id,
                # Execution luôn được coi là đã ghi nhận xong
                'status': 'done',
                'buy_user_type': self._get_user_type(buy_order),
                'sell_user_type': self._get_user_type(sell_order),
            })
            
            return {
                'id': matched_order.id,
                'buy_id': buy_order.id,
                'sell_id': sell_order.id,
                'matched_quantity': matched_quantity,
                'matched_price': matched_price,  # Giá khớp = giá sell
                'match_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'algorithm_used': 'Partial Matching Engine (Stock Exchange Standard)',
                'fund_name': self.fund_id.name,
            }
            
        except Exception as e:
            _logger.error("Error creating matched pair: %s", str(e))
            import traceback
            _logger.error("Traceback: %s", traceback.format_exc())
            return None

    def _get_user_type(self, transaction):
        """Xác định loại user"""
        if not transaction.user_id:
            return 'investor'
        
        if transaction.user_id.has_group('base.group_user'):
            return 'market_maker'
        
        if hasattr(transaction, 'source') and transaction.source == 'sale':
            return 'market_maker'
        
        return 'investor'
    
    @api.model
    def calculate_priority_score_for_order(self, order_record):
        """
        Helper method để tính priority score cho order
        Có thể được gọi từ controller/service layer
        
        Args:
            order_record: portfolio.transaction record
            
        Returns:
            float: Priority score
        """
        return self._calculate_priority_score(order_record)
    
    @api.model
    def time_to_integer_helper(self, datetime_obj):
        """
        Helper method để chuyển datetime thành integer
        Có thể được gọi từ controller/service layer
        
        Args:
            datetime_obj: datetime object
            
        Returns:
            int: Số phút từ 00:00
        """
        if not datetime_obj:
            return 0
        
        try:
            hour = datetime_obj.hour
            minute = datetime_obj.minute
            return hour * 60 + minute
        except Exception:
            return 0
    
    @api.model
    def get_order_price(self, order):
        """
        Helper method để lấy giá của order
        Có thể được gọi từ controller/service layer
        
        Args:
            order: portfolio.transaction record
            
        Returns:
            float: Giá của order
        """
        if hasattr(order, 'price') and order.price:
            return float(order.price)
        elif hasattr(order, 'current_nav') and order.current_nav:
            return float(order.current_nav)
        return 0.0
    
    @api.model
    def can_match_orders(self, buy_order, sell_order):
        """
        Helper method để kiểm tra có thể khớp 2 orders không
        Có thể được gọi từ controller/service layer
        
        Args:
            buy_order: portfolio.transaction record (buy)
            sell_order: portfolio.transaction record (sell)
            
        Returns:
            tuple: (can_match: bool, reason: str)
        """
        # Kiểm tra cùng fund
        buy_fund_id = buy_order.fund_id.id if buy_order.fund_id else None
        sell_fund_id = sell_order.fund_id.id if sell_order.fund_id else None
        
        if buy_fund_id and sell_fund_id and buy_fund_id != sell_fund_id:
            return False, _("Khác quỹ")
        
        # Kiểm tra không cùng user
        buy_user_id = buy_order.user_id.id if buy_order.user_id else None
        sell_user_id = sell_order.user_id.id if sell_order.user_id else None
        
        if buy_user_id and sell_user_id and buy_user_id == sell_user_id:
            buy_user_name = buy_order.user_id.name if buy_order.user_id else "N/A"
            return False, _("Cùng nhà đầu tư (%s)") % buy_user_name
        
        # Kiểm tra giá
        buy_price = self.get_order_price(buy_order)
        sell_price = self.get_order_price(sell_order)
        
        if buy_price < sell_price:
            return False, _("Giá không thỏa mãn (buy_price=%s < sell_price=%s)") % (buy_price, sell_price)
        
        # Kiểm tra remaining
        buy_units = float(buy_order.units or 0)
        buy_matched = float(buy_order.matched_units or 0)
        buy_remaining = max(0.0, buy_units - buy_matched)
        
        sell_units = float(sell_order.units or 0)
        sell_matched = float(sell_order.matched_units or 0)
        sell_remaining = max(0.0, sell_units - sell_matched)
        
        if buy_remaining <= 0:
            return False, _("Buy order không còn remaining")
        
        if sell_remaining <= 0:
            return False, _("Sell order không còn remaining")
        
        return True, _("Có thể khớp")

    def _update_transaction_status(self, buy_order, sell_order, matched_quantity):
        """
        Cập nhật trạng thái giao dịch sau khi khớp
        Dựa trên thuật toán từ CompanyOrderBookModule.checkTransactionExecutor
        
        NOTE: Method này đã được tích hợp vào _match_orders() để đảm bảo logic nhất quán.
        Giữ lại để tương thích với code cũ nếu có gọi riêng.
        """
        try:
            # Tính toán số lượng còn lại chính xác từ units - matched_units
            buy_units = float(buy_order.units or 0)
            buy_current_matched = float(buy_order.matched_units or 0)
            buy_new_matched = buy_current_matched + matched_quantity
            buy_new_remaining = max(0, buy_units - buy_new_matched)
            
            sell_units = float(sell_order.units or 0)
            sell_current_matched = float(sell_order.matched_units or 0)
            sell_new_matched = sell_current_matched + matched_quantity
            sell_new_remaining = max(0, sell_units - sell_new_matched)
            
            # Update buy order
            # NOTE: matched_units and remaining_units are computed fields from executions
            # Do NOT write to them directly — they will recompute automatically
            buy_vals = {
                'ccq_remaining_to_match': buy_new_remaining,
                'status': 'completed' if buy_new_remaining <= 0 else 'pending',
            }
            
            if buy_new_remaining <= 0:
                buy_order.sudo().write(buy_vals)
            else:
                buy_order.with_context(bypass_investment_update=True).sudo().write(buy_vals)
            
            # Update sell order
            sell_vals = {
                'ccq_remaining_to_match': sell_new_remaining,
                'status': 'completed' if sell_new_remaining <= 0 else 'pending',
            }
            
            if sell_new_remaining <= 0:
                sell_order.sudo().write(sell_vals)
            else:
                sell_order.with_context(bypass_investment_update=True).sudo().write(sell_vals)
                
        except Exception as e:
            _logger.error("Error updating transaction status: %s", str(e))
            import traceback
            _logger.error("Traceback: %s", traceback.format_exc())

    def _update_statistics(self, matched_pairs):
        """Cập nhật thống kê engine"""
        # Giữ lại để log nội bộ; thống kê hiển thị được tính động qua _compute_engine_match_stats
        if not matched_pairs:
            return
        # Ghi log để truy vết (không thay đổi trường thống kê hiển thị)
        try:
            new_logs = (self.match_logs or '') + "\nMatched %s pairs at %s" % (len(matched_pairs), fields.Datetime.now())
            self.match_logs = new_logs.strip()
        except Exception:
            pass

    @api.depends('fund_id')
    @api.depends_context('force_recompute')
    def _compute_engine_match_stats(self):
        """Tính thống kê từ bảng transaction.matched.orders (danh sách lệnh thỏa thuận)"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        Transaction = self.env['portfolio.transaction'].sudo()

        for engine in self:
            if not engine.fund_id:
                engine.total_matches = 0
                engine.total_partial_matches = 0
                engine.last_match_date = False
                continue

            # Lấy tất cả matched orders theo quỹ từ danh sách lệnh thỏa thuận
            matched_orders = MatchedOrder.search([
                ('fund_id', '=', engine.fund_id.id),
                ('status', 'in', ['partial', 'done'])  # Chỉ lấy các lệnh đã xác nhận hoặc hoàn thành
            ])
            
            # Tổng số lần khớp
            engine.total_matches = len(matched_orders)

            # Lần khớp cuối cùng
            if matched_orders:
                # Ưu tiên field match_date, fallback create_date
                dates = []
                for mo in matched_orders:
                    match_date = mo.match_date or mo.create_date
                    if match_date:
                        dates.append(match_date)
                engine.last_match_date = max(dates) if dates else False
            else:
                engine.last_match_date = False

            # Tính số lần khớp một phần
            # Một cặp được coi là khớp một phần nếu sau khi khớp, 
            # lệnh mua hoặc lệnh bán vẫn còn remaining_units > 0
            partial_count = 0
            for mo in matched_orders:
                try:
                    # Lấy thông tin lệnh mua và bán
                    buy_order = mo.buy_order_id
                    sell_order = mo.sell_order_id
                    
                    if buy_order and sell_order:
                        # Tính toán remaining_units chính xác từ units - matched_units (theo chuẩn Stock Exchange)
                        buy_units = float(buy_order.units or 0)
                        buy_matched = float(buy_order.matched_units or 0)
                        buy_remaining = max(0.0, buy_units - buy_matched)
                        
                        sell_units = float(sell_order.units or 0)
                        sell_matched = float(sell_order.matched_units or 0)
                        sell_remaining = max(0.0, sell_units - sell_matched)
                        
                        # Nếu một trong hai lệnh còn remaining > 0 thì là khớp một phần
                        if buy_remaining > 0 or sell_remaining > 0:
                            partial_count += 1
                            
                except Exception as e:
                    # Log lỗi nhưng không dừng quá trình
                    _logger.warning("Error checking partial match for %s: %s", mo.name, str(e))
                    continue
                    
            engine.total_partial_matches = partial_count

    @api.model
    def _trigger_recompute_stats(self):
        """Trigger recompute cho tất cả engines khi có thay đổi dữ liệu"""
        engines = self.search([])
        engines.with_context(force_recompute=True)._compute_engine_match_stats()

    def _search_total_matches(self, operator, value):
        """Search method cho total_matches"""
        if operator == '>':
            return [('fund_id', 'in', self._get_funds_with_matches_greater_than(value))]
        elif operator == '=':
            return [('fund_id', 'in', self._get_funds_with_matches_equal_to(value))]
        elif operator == '>=':
            return [('fund_id', 'in', self._get_funds_with_matches_greater_equal(value))]
        return []

    def _search_total_partial_matches(self, operator, value):
        """Search method cho total_partial_matches"""
        if operator == '>':
            return [('fund_id', 'in', self._get_funds_with_partial_matches_greater_than(value))]
        elif operator == '=':
            return [('fund_id', 'in', self._get_funds_with_partial_matches_equal_to(value))]
        elif operator == '>=':
            return [('fund_id', 'in', self._get_funds_with_partial_matches_greater_equal(value))]
        return []

    def _search_last_match_date(self, operator, value):
        """Search method cho last_match_date"""
        if operator == '>':
            return [('fund_id', 'in', self._get_funds_with_last_match_after(value))]
        elif operator == '=':
            return [('fund_id', 'in', self._get_funds_with_last_match_on(value))]
        elif operator == '>=':
            return [('fund_id', 'in', self._get_funds_with_last_match_after_equal(value))]
        return []

    def _get_funds_with_matches_greater_than(self, value):
        """Lấy danh sách fund_id có total_matches > value từ danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        matched_orders = MatchedOrder.read_group(
            [
                ('fund_id', '!=', False),
                ('status', 'in', ['partial', 'done'])
            ],
            ['fund_id'],
            ['fund_id']
        )
        fund_ids = []
        for group in matched_orders:
            if group['fund_id_count'] > value:
                fund_ids.append(group['fund_id'][0])
        return fund_ids

    def _get_funds_with_matches_equal_to(self, value):
        """Lấy danh sách fund_id có total_matches = value từ danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        matched_orders = MatchedOrder.read_group(
            [
                ('fund_id', '!=', False),
                ('status', 'in', ['partial', 'done'])
            ],
            ['fund_id'],
            ['fund_id']
        )
        fund_ids = []
        for group in matched_orders:
            if group['fund_id_count'] == value:
                fund_ids.append(group['fund_id'][0])
        return fund_ids

    def _get_funds_with_matches_greater_equal(self, value):
        """Lấy danh sách fund_id có total_matches >= value từ danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        matched_orders = MatchedOrder.read_group(
            [
                ('fund_id', '!=', False),
                ('status', 'in', ['partial', 'done'])
            ],
            ['fund_id'],
            ['fund_id']
        )
        fund_ids = []
        for group in matched_orders:
            if group['fund_id_count'] >= value:
                fund_ids.append(group['fund_id'][0])
        return fund_ids

    def _get_funds_with_partial_matches_greater_than(self, value):
        """Lấy danh sách fund_id có partial matches > value"""
        # Simplified implementation - có thể cải thiện sau
        return self._get_funds_with_matches_greater_than(value)

    def _get_funds_with_partial_matches_equal_to(self, value):
        """Lấy danh sách fund_id có partial matches = value"""
        # Simplified implementation - có thể cải thiện sau
        return self._get_funds_with_matches_equal_to(value)

    def _get_funds_with_partial_matches_greater_equal(self, value):
        """Lấy danh sách fund_id có partial matches >= value"""
        # Simplified implementation - có thể cải thiện sau
        return self._get_funds_with_matches_greater_equal(value)

    def _get_funds_with_last_match_after(self, value):
        """Lấy danh sách fund_id có last_match_date > value từ danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        matched_orders = MatchedOrder.search([
            ('fund_id', '!=', False),
            ('status', 'in', ['confirmed', 'done']),
            ('match_date', '>', value)
        ])
        return list(set(matched_orders.mapped('fund_id.id')))

    def _get_funds_with_last_match_on(self, value):
        """Lấy danh sách fund_id có last_match_date = value từ danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        matched_orders = MatchedOrder.search([
            ('fund_id', '!=', False),
            ('status', 'in', ['confirmed', 'done']),
            ('match_date', '=', value)
        ])
        return list(set(matched_orders.mapped('fund_id.id')))

    def _get_funds_with_last_match_after_equal(self, value):
        """Lấy danh sách fund_id có last_match_date >= value từ danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        matched_orders = MatchedOrder.search([
            ('fund_id', '!=', False),
            ('status', 'in', ['confirmed', 'done']),
            ('match_date', '>=', value)
        ])
        return list(set(matched_orders.mapped('fund_id.id')))

    def clear_queue(self):
        """Xóa tất cả lệnh trong queue"""
        self.env['transaction.order.queue'].search([
            ('engine_id', '=', self.id)
        ]).unlink()

    def get_queue_status(self):
        """Lấy trạng thái queue"""
        buy_count = self.env['transaction.order.queue'].search_count([
            ('engine_id', '=', self.id),
            ('order_type', '=', 'buy'),
            ('status', '=', 'pending')
        ])
        
        sell_count = self.env['transaction.order.queue'].search_count([
            ('engine_id', '=', self.id),
            ('order_type', '=', 'sell'),
            ('status', '=', 'pending')
        ])
        
        return {
            'buy_orders': buy_count,
            'sell_orders': sell_count,
            'total_orders': buy_count + sell_count
        }

    def process_all_pending_orders(self):
        """
        Xử lý tất cả lệnh pending trong queue
        Tính toán remaining_units chính xác từ units - matched_units (theo chuẩn Stock Exchange)
        """
        matched_pairs = []
        
        # Lấy tất cả lệnh pending
        pending_orders = self.env['portfolio.transaction'].search([
            ('fund_id', '=', self.fund_id.id),
            ('status', '=', 'pending')
        ])
        
        # Lọc các lệnh có remaining > 0 bằng cách tính toán chính xác
        valid_orders = []
        for order in pending_orders:
            units_total = float(order.units or 0)
            matched_total = float(order.matched_units or 0)
            remaining = max(0.0, units_total - matched_total)
            if remaining > 0:
                valid_orders.append(order)
        
        # Thêm từng lệnh vào engine
        for order in valid_orders:
            pairs = self.add_order(order)
            matched_pairs.extend(pairs)
        
        return matched_pairs

    @api.model
    def create_engine_for_fund(self, fund_id):
        """Tạo engine mới cho một quỹ"""
        existing = self.search([('fund_id', '=', fund_id), ('is_active', '=', True)])
        if existing:
            return existing[0]
        
        return self.create({
            'name': _('Partial Matching Engine - %s') % fund_id,
            'fund_id': fund_id,
            'is_active': True
        })

    @api.model
    def auto_create_engines_for_funds_with_matches(self, *args, **kwargs):
        """Tự động tạo engine cho các quỹ đã có matched orders trong danh sách lệnh thỏa thuận"""
        MatchedOrder = self.env['transaction.matched.orders'].sudo()
        
        # Lấy danh sách các quỹ đã có matched orders
        matched_orders = MatchedOrder.search([
            ('fund_id', '!=', False),
            ('status', 'in', ['confirmed', 'done'])
        ])
        
        fund_ids = list(set(matched_orders.mapped('fund_id.id')))
        
        created_engines = []
        for fund_id in fund_ids:
            # Kiểm tra xem đã có engine chưa
            existing = self.search([('fund_id', '=', fund_id), ('is_active', '=', True)])
            if not existing:
                # Tạo engine mới
                fund = self.env['portfolio.fund'].browse(fund_id)
                engine = self.create({
                    'name': _('Bộ Khớp Lệnh - %s') % fund.name,
                    'fund_id': fund_id,
                    'is_active': True
                })
                created_engines.append(engine)
        
        # Trả về thông báo ngắn gọn
        try:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Hoàn tất'),
                    'message': _('Đã tạo %(n)d engine (nếu thiếu).', n=len(created_engines)),
                    'sticky': False,
                }
            }
        except Exception:
            return True


class TransactionOrderQueue(models.Model):
    """
    Model lưu trữ lệnh trong queue của engine
    Thay thế cho PriorityQueue trong Java
    """
    _name = 'transaction.order.queue'
    _description = 'Transaction Order Queue'
    _order = 'priority_score desc'
    _rec_name = 'order_id'

    engine_id = fields.Many2one('transaction.partial.matching.engine', string='Engine', required=True)
    order_id = fields.Many2one('portfolio.transaction', string='Order', required=True)
    order_type = fields.Selection([
        ('buy', 'Buy'),
        ('sell', 'Sell')
    ], string='Order Type', required=True)
    
    price = fields.Float(string='Price', digits=(16, 2))
    quantity = fields.Float(string='Remaining Quantity', digits=(16, 2))
    priority_score = fields.Float(string='Priority Score', digits=(20, 6))
    create_time = fields.Datetime(string='Create Time')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')
    
    # Thông tin bổ sung
    user_id = fields.Many2one(related='order_id.user_id', string='User', store=True)
    fund_id = fields.Many2one(related='order_id.fund_id', string='Fund', store=True)
    
    # Các trường từ transaction để hiển thị chính xác số lượng khớp
    ccq_remaining_to_match = fields.Float(
        related='order_id.ccq_remaining_to_match', 
        string='CCQ Còn Lại Cần Khớp', 
        store=True,
        digits=(16, 2)
    )
    matched_units = fields.Float(
        related='order_id.matched_units', 
        string='CCQ Đã Khớp', 
        store=True,
        digits=(16, 2)
    )
    remaining_units = fields.Float(
        related='order_id.remaining_units', 
        string='CCQ Còn Lại', 
        store=True,
        digits=(16, 2)
    )
    
    @api.model
    def cleanup_old_queues(self, days=7):
        """Dọn dẹp queue cũ"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_queues = self.search([
            ('create_time', '<', cutoff_date),
            ('status', 'in', ['completed', 'cancelled'])
        ])
        old_queues.unlink()
        return len(old_queues)

    def update_queue_from_transaction(self, transaction_id):
        """
        Cập nhật queue khi transaction thay đổi
        Đồng bộ số lượng còn lại cần khớp từ transaction
        Tính toán remaining_units chính xác từ units - matched_units (theo chuẩn Stock Exchange)
        """
        try:
            transaction = self.env['portfolio.transaction'].browse(transaction_id)
            if not transaction.exists():
                return False
            
            # Tính toán remaining_units chính xác từ units - matched_units
            units_total = float(transaction.units or 0)
            matched_total = float(transaction.matched_units or 0)
            remaining = max(0.0, units_total - matched_total)
            
            # Tìm queue record tương ứng
            queue_record = self.search([
                ('order_id', '=', transaction_id),
                ('status', '=', 'pending')
            ], limit=1)
            
            if queue_record:
                # Cập nhật quantity từ transaction (sử dụng remaining đã tính toán chính xác)
                queue_record.write({
                    'quantity': remaining,
                    'ccq_remaining_to_match': remaining,  # Cập nhật chính xác
                    'matched_units': matched_total,
                    'remaining_units': remaining
                })
                
                # Nếu không còn quantity, đánh dấu completed
                if remaining <= 0:
                    queue_record.status = 'completed'
                
                return True
            
            return False
            
        except Exception as e:
            _logger.error("Error updating queue from transaction: %s", str(e))
            return False
    