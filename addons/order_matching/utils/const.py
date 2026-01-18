# -*- coding: utf-8 -*-
"""
Constants for Order Matching Module - Chuẩn Sàn Chứng Chỉ Quỹ Quốc Tế
"""

# Order Status
ORDER_STATUS_PENDING = 'pending'
ORDER_STATUS_COMPLETED = 'completed'
ORDER_STATUS_CANCELLED = 'cancelled'

ORDER_STATUSES = [
    (ORDER_STATUS_PENDING, 'Chờ khớp'),
    (ORDER_STATUS_COMPLETED, 'Đã hoàn thành'),
    (ORDER_STATUS_CANCELLED, 'Đã hủy'),
]

# Transaction Types
TRANSACTION_TYPE_BUY = 'buy'
TRANSACTION_TYPE_SELL = 'sell'

TRANSACTION_TYPES = [
    (TRANSACTION_TYPE_BUY, 'Mua'),
    (TRANSACTION_TYPE_SELL, 'Bán'),
]

# Order Types for Matching
ORDER_TYPE_BUY = 'buy'
ORDER_TYPE_SELL = 'sell'

ORDER_TYPES = [
    (ORDER_TYPE_BUY, 'Mua'),
    (ORDER_TYPE_SELL, 'Bán'),
]

# User Types
USER_TYPE_INVESTOR = 'investor'
USER_TYPE_MARKET_MAKER = 'market_maker'

USER_TYPES = [
    (USER_TYPE_INVESTOR, 'Nhà đầu tư'),
    (USER_TYPE_MARKET_MAKER, 'Nhà tạo lập'),
]

# Matching Algorithm
MATCHING_ALGORITHM_PRICE_TIME_PRIORITY = 'price_time_priority'
MATCHING_ALGORITHM_MARKET_MAKER = 'market_maker'

MATCHING_ALGORITHMS = [
    (MATCHING_ALGORITHM_PRICE_TIME_PRIORITY, 'Price-Time Priority (FIFO)'),
    (MATCHING_ALGORITHM_MARKET_MAKER, 'Market Maker'),
]

# Matching Limits
MIN_MATCH_QUANTITY = 0.01  # Số lượng khớp tối thiểu: 0.01 CCQ
MAX_MATCH_QUANTITY = 999999999.99  # Số lượng khớp tối đa: 999,999,999.99 CCQ

# Price-Time Priority Rules
PRIORITY_RULE_BUY_HIGHEST_PRICE_FIRST = True  # Buy: Giá cao nhất trước
PRIORITY_RULE_SELL_LOWEST_PRICE_FIRST = True  # Sell: Giá thấp nhất trước
PRIORITY_RULE_EARLIEST_TIME_FIRST = True  # Cùng giá: Thời gian sớm nhất trước

# Matching Conditions
MATCH_CONDITION_PRICE = 'buy_price >= sell_price'  # Điều kiện giá: buy_price >= sell_price
MATCH_CONDITION_DIFFERENT_USER = True  # Phải khác user
MATCH_CONDITION_PENDING_STATUS = True  # Phải ở trạng thái pending

# Match Price Rule (Chuẩn Stock Exchange)
MATCH_PRICE_RULE_SELL_PRICE = True  # Giá khớp = giá sell order (theo chuẩn Stock Exchange)

# Status Transitions
VALID_STATUS_TRANSITIONS = {
    ORDER_STATUS_PENDING: [ORDER_STATUS_COMPLETED, ORDER_STATUS_CANCELLED],
    ORDER_STATUS_COMPLETED: [],  # Không thể chuyển từ completed
    ORDER_STATUS_CANCELLED: [],  # Không thể chuyển từ cancelled
}

# Settlement Periods (Days)
SETTLEMENT_PERIOD_T_PLUS_0 = 0  # T+0: Khớp ngay
SETTLEMENT_PERIOD_T_PLUS_1 = 1  # T+1: Khớp sau 1 ngày
SETTLEMENT_PERIOD_T_PLUS_2 = 2  # T+2: Khớp sau 2 ngày
DEFAULT_SETTLEMENT_PERIOD = SETTLEMENT_PERIOD_T_PLUS_0

# Decimal Precision
PRICE_DECIMAL_PLACES = 2  # 2 chữ số thập phân cho giá
QUANTITY_DECIMAL_PLACES = 2  # 2 chữ số thập phân cho số lượng
AMOUNT_DECIMAL_PLACES = 2  # 2 chữ số thập phân cho số tiền

# Priority Score Calculation
PRIORITY_SCORE_PRICE_WEIGHT = 1000000  # Trọng số cho giá (để đảm bảo giá quan trọng hơn thời gian)
PRIORITY_SCORE_TIME_WEIGHT = 1  # Trọng số cho thời gian

# Queue Management
QUEUE_MAX_ITERATIONS = 10000  # Số lần lặp tối đa trong matching loop
QUEUE_BATCH_SIZE = 100  # Số lượng orders xử lý mỗi batch

# Error Messages
ERROR_INVALID_STATUS_TRANSITION = "Không thể chuyển từ trạng thái '%s' sang '%s'"
ERROR_SAME_USER_MATCH = "Không thể khớp lệnh của cùng một user"
ERROR_INVALID_MATCHING_CONDITION = "Điều kiện khớp không thỏa mãn: %s"
ERROR_INVALID_ORDER_STATUS = "Trạng thái lệnh không hợp lệ: Phải là 'pending'"
ERROR_INSUFFICIENT_REMAINING = "Số lượng còn lại không đủ: %s < %s"

# Success Messages
SUCCESS_ORDER_CREATED = "Tạo lệnh thành công"
SUCCESS_ORDER_MATCHED = "Khớp lệnh thành công"
SUCCESS_ORDER_CANCELLED = "Hủy lệnh thành công"
SUCCESS_ORDER_UPDATED = "Cập nhật lệnh thành công"

# Log Messages
LOG_ORDER_CREATED = "[ORDER] Tạo lệnh: ID=%s, Type=%s, Units=%s, Price=%s"
LOG_ORDER_MATCHED = "[MATCH] Khớp lệnh: Buy=%s x Sell=%s, Qty=%s, Price=%s"
LOG_ORDER_CANCELLED = "[ORDER] Hủy lệnh: ID=%s"
LOG_ORDER_UPDATED = "[ORDER] Cập nhật lệnh: ID=%s, Status=%s"

