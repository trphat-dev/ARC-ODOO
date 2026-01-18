# Copyright 2024
# License AGPL-3.0 or later

"""
Constants for Fund Management module
"""

# Transaction types
TRANSACTION_TYPE_BUY = 'buy'
TRANSACTION_TYPE_SELL = 'sell'
TRANSACTION_TYPES = [
    (TRANSACTION_TYPE_BUY, 'Buy'),
    (TRANSACTION_TYPE_SELL, 'Sell'),
]

# Transaction status
STATUS_PENDING = 'pending'
STATUS_COMPLETED = 'completed'
STATUS_CANCELLED = 'cancelled'
TRANSACTION_STATUSES = [
    (STATUS_PENDING, 'Pending'),
    (STATUS_COMPLETED, 'Completed'),
    (STATUS_CANCELLED, 'Cancelled'),
]

# Investment status
INVESTMENT_STATUS_ACTIVE = 'active'
INVESTMENT_STATUS_INACTIVE = 'inactive'
INVESTMENT_STATUS_CLOSED = 'closed'
INVESTMENT_STATUSES = [
    (INVESTMENT_STATUS_ACTIVE, 'Active'),
    (INVESTMENT_STATUS_INACTIVE, 'Inactive'),
    (INVESTMENT_STATUS_CLOSED, 'Closed'),
]

# Fund status
FUND_STATUS_ACTIVE = 'active'
FUND_STATUS_INACTIVE = 'inactive'
FUND_STATUS_CLOSED = 'closed'
FUND_STATUSES = [
    (FUND_STATUS_ACTIVE, 'Active'),
    (FUND_STATUS_INACTIVE, 'Inactive'),
    (FUND_STATUS_CLOSED, 'Closed'),
]

# Investment types
INVESTMENT_TYPE_STOCK = 'stock'
INVESTMENT_TYPE_BOND = 'bond'
INVESTMENT_TYPE_REAL_ESTATE = 'real_estate'
INVESTMENT_TYPE_CRYPTO = 'crypto'
INVESTMENT_TYPE_FUND_CERTIFICATE = 'fund_certificate'
INVESTMENT_TYPE_DEPOSIT = 'deposit'
INVESTMENT_TYPE_ETF = 'etf'
INVESTMENT_TYPE_OTHER = 'other'
INVESTMENT_TYPES = [
    (INVESTMENT_TYPE_STOCK, 'Stock'),
    (INVESTMENT_TYPE_BOND, 'Bond'),
    (INVESTMENT_TYPE_REAL_ESTATE, 'Real Estate'),
    (INVESTMENT_TYPE_CRYPTO, 'Cryptocurrency'),
    (INVESTMENT_TYPE_FUND_CERTIFICATE, 'Fund Certificate'),
    (INVESTMENT_TYPE_DEPOSIT, 'Deposit'),
    (INVESTMENT_TYPE_ETF, 'ETF'),
    (INVESTMENT_TYPE_OTHER, 'Other'),
]

# Fund investment types
FUND_INVESTMENT_TYPE_INCOME = 'Income'
FUND_INVESTMENT_TYPE_GROWTH = 'Growth'
FUND_INVESTMENT_TYPE_INCOME_GROWTH = 'Income & Growth'
FUND_INVESTMENT_TYPE_CAPITAL_GROWTH = 'Capital Growth'
FUND_INVESTMENT_TYPES = [
    (FUND_INVESTMENT_TYPE_INCOME, 'Income'),
    (FUND_INVESTMENT_TYPE_GROWTH, 'Growth'),
    (FUND_INVESTMENT_TYPE_INCOME_GROWTH, 'Income & Growth'),
    (FUND_INVESTMENT_TYPE_CAPITAL_GROWTH, 'Capital Growth'),
]

# Transaction sources
SOURCE_PORTAL = 'portal'
SOURCE_SALE = 'sale'
SOURCE_PORTFOLIO = 'portfolio'
TRANSACTION_SOURCES = [
    (SOURCE_PORTAL, 'Portal'),
    (SOURCE_SALE, 'Sale Portal'),
    (SOURCE_PORTFOLIO, 'Portfolio'),
]

# Fee calculation constants
FEE_THRESHOLD_1 = 10000000  # 10M
FEE_THRESHOLD_2 = 20000000  # 20M
FEE_RATE_1 = 0.003  # 0.3%
FEE_RATE_2 = 0.002  # 0.2%
FEE_RATE_3 = 0.001  # 0.1%

# MROUND step
MROUND_STEP = 50

# Default values
DEFAULT_FUND_STATUS = FUND_STATUS_ACTIVE
DEFAULT_INVESTMENT_STATUS = INVESTMENT_STATUS_ACTIVE
DEFAULT_TRANSACTION_STATUS = STATUS_PENDING
DEFAULT_TRANSACTION_SOURCE = SOURCE_PORTFOLIO
DEFAULT_INVESTMENT_TYPE = INVESTMENT_TYPE_FUND_CERTIFICATE
DEFAULT_TERM_MONTHS = 12
DEFAULT_DAYS_PER_MONTH = 30

# Fund type mapping
FUND_TYPE_MAPPING = {
    'equity': FUND_INVESTMENT_TYPE_GROWTH,
    'bond': FUND_INVESTMENT_TYPE_INCOME,
    'mixed': FUND_INVESTMENT_TYPE_INCOME_GROWTH,
}

# Contract signed types
CONTRACT_SIGNED_TYPE_HAND = 'hand'
CONTRACT_SIGNED_TYPE_DIGITAL = 'digital'
CONTRACT_SIGNED_TYPES = [
    (CONTRACT_SIGNED_TYPE_HAND, 'Handwritten'),
    (CONTRACT_SIGNED_TYPE_DIGITAL, 'Digital'),
]

# =============================================================================
# ORDER MODE - Phân biệt lệnh thường vs lệnh thỏa thuận
# =============================================================================
ORDER_MODE_NORMAL = 'normal'          # Lệnh thường - gửi trực tiếp lên sàn
ORDER_MODE_NEGOTIATED = 'negotiated'  # Lệnh thỏa thuận - khớp nội bộ trước
ORDER_MODES = [
    (ORDER_MODE_NORMAL, 'Đặt lệnh thường'),
    (ORDER_MODE_NEGOTIATED, 'Đặt lệnh thỏa thuận'),
]
DEFAULT_ORDER_MODE = ORDER_MODE_NEGOTIATED

# =============================================================================
# ORDER TYPE DETAIL - Loại lệnh chi tiết (cho lệnh thường)
# =============================================================================
ORDER_TYPE_LO = 'LO'    # Limit Order - Lệnh giới hạn
ORDER_TYPE_MP = 'MP'    # Market Price - Lệnh thị trường (HOSE/HNX)
ORDER_TYPE_MTL = 'MTL'  # Market To Limit - Lệnh giới hạn thị trường
ORDER_TYPE_ATO = 'ATO'  # At The Opening - Lệnh mở cửa (chỉ HOSE, 9h00-9h15)
ORDER_TYPE_ATC = 'ATC'  # At The Close - Lệnh đóng cửa (14h30-14h45)
ORDER_TYPE_PLO = 'PLO'  # Post Limit Order - Lệnh khớp sau giờ (UPCOM)

ORDER_TYPE_DETAILS = [
    (ORDER_TYPE_LO, 'LO - Lệnh giới hạn'),
    (ORDER_TYPE_MP, 'MP - Lệnh thị trường'),
    (ORDER_TYPE_MTL, 'MTL - Lệnh giới hạn thị trường'),
    (ORDER_TYPE_ATO, 'ATO - Lệnh mở cửa'),
    (ORDER_TYPE_ATC, 'ATC - Lệnh đóng cửa'),
    (ORDER_TYPE_PLO, 'PLO - Lệnh khớp sau giờ (UPCOM)'),
]
DEFAULT_ORDER_TYPE_DETAIL = ORDER_TYPE_LO  # Default to LO

# Order type constraints by market
# HOSE: LO, MP, ATO, ATC, MTL
# HNX: LO, MP, ATC, MTL
# UPCOM: LO, PLO, ATC
ORDER_TYPES_BY_MARKET = {
    'HOSE': [ORDER_TYPE_LO, ORDER_TYPE_MP, ORDER_TYPE_MTL, ORDER_TYPE_ATO, ORDER_TYPE_ATC],
    'HNX': [ORDER_TYPE_LO, ORDER_TYPE_MP, ORDER_TYPE_MTL, ORDER_TYPE_ATC],
    'UPCOM': [ORDER_TYPE_LO, ORDER_TYPE_PLO, ORDER_TYPE_ATC],
}

# Market order types (price = 0)
MARKET_ORDER_TYPES = [ORDER_TYPE_MP, ORDER_TYPE_MTL, ORDER_TYPE_ATO, ORDER_TYPE_ATC, ORDER_TYPE_PLO]

# Limit order types (requires price > 0)
LIMIT_ORDER_TYPES = [ORDER_TYPE_LO]

# =============================================================================
# MARKET - Sàn niêm yết
# =============================================================================
MARKET_HOSE = 'HOSE'
MARKET_HNX = 'HNX'
MARKET_UPCOM = 'UPCOM'
MARKETS = [
    (MARKET_HOSE, 'HOSE'),
    (MARKET_HNX, 'HNX'),
    (MARKET_UPCOM, 'UPCOM'),
]

# =============================================================================
# EXCHANGE STATUS - Trạng thái lệnh trên sàn (cho lệnh thường)
# =============================================================================
EXCHANGE_STATUS_PENDING = 'pending'      # Chờ gửi lên sàn
EXCHANGE_STATUS_SENT = 'sent'            # Đã gửi lên sàn
EXCHANGE_STATUS_FILLED = 'filled'        # Đã khớp hoàn toàn
EXCHANGE_STATUS_PARTIAL = 'partial'      # Khớp một phần
EXCHANGE_STATUS_REJECTED = 'rejected'    # Bị từ chối
EXCHANGE_STATUS_CANCELLED = 'cancelled'  # Đã hủy
EXCHANGE_STATUSES = [
    (EXCHANGE_STATUS_PENDING, 'Chờ gửi'),
    (EXCHANGE_STATUS_SENT, 'Đã gửi'),
    (EXCHANGE_STATUS_FILLED, 'Đã khớp'),
    (EXCHANGE_STATUS_PARTIAL, 'Khớp một phần'),
    (EXCHANGE_STATUS_REJECTED, 'Bị từ chối'),
    (EXCHANGE_STATUS_CANCELLED, 'Đã hủy'),
]
DEFAULT_EXCHANGE_STATUS = EXCHANGE_STATUS_PENDING

# =============================================================================
# LOT SIZE - Quy định lô giao dịch
# =============================================================================
LOT_SIZE = 100  # CCQ giao dịch theo lô 100

