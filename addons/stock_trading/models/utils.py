# -*- coding: utf-8 -*-

"""
Utility functions cho stock_trading module
Chứa các helper functions được dùng chung
"""

import json
import base64
from datetime import datetime


# Constants
class TokenConstants:
    """Constants liên quan đến token"""
    # JWT token expiration buffer (1 giờ) - giống AccessTokenModel.is_expired()
    EXPIRATION_BUFFER_SECONDS = 3600
    
    # Write token lifetime (8 giờ) - thông tin cho user
    WRITE_TOKEN_LIFETIME_HOURS = 8
    
    # JWT payload field names
    JWT_EXP_FIELD = 'exp'
    
    # JWT token parts count
    JWT_MIN_PARTS = 2
    
    # Base64 padding
    BASE64_PADDING_BLOCK_SIZE = 4


class TimeFormatConstants:
    """Constants cho format thời gian"""
    # Time units in seconds
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_MINUTE = 60
    
    # Messages
    EXPIRED_MESSAGE = 'Đã hết hạn'
    HOURS_FORMAT = '{hours} giờ'
    HOURS_MINUTES_FORMAT = '{hours} giờ {minutes} phút'
    MINUTES_FORMAT = '{minutes} phút'
    MINUTES_SECONDS_FORMAT = '{minutes} phút {seconds} giây'
    SECONDS_FORMAT = '{seconds} giây'


def decode_jwt_token(token):
    """
    Decode JWT token và trả về payload dictionary
    
    Args:
        token: JWT token string (format: header.payload.signature)
        
    Returns:
        dict: Payload dictionary hoặc None nếu decode thất bại
    """
    if not token:
        return None
    
    try:
        # Decode JWT token (format: header.payload.signature)
        token_parts = token.split('.')
        if len(token_parts) < TokenConstants.JWT_MIN_PARTS:
            return None
        
        # Decode payload (base64)
        payload = token_parts[1]
        # Add padding nếu cần
        padding_needed = (TokenConstants.BASE64_PADDING_BLOCK_SIZE - len(payload) % TokenConstants.BASE64_PADDING_BLOCK_SIZE) % TokenConstants.BASE64_PADDING_BLOCK_SIZE
        payload += '=' * padding_needed
        
        decoded_payload = base64.b64decode(payload)
        payload_dict = json.loads(decoded_payload.decode('utf-8'))
        
        return payload_dict
    except Exception:
        return None


def get_token_expiration_timestamp(token):
    """
    Lấy expiration timestamp từ JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        int: Expiration timestamp hoặc 0 nếu không có
    """
    payload = decode_jwt_token(token)
    if not payload:
        return 0
    
    return payload.get(TokenConstants.JWT_EXP_FIELD, 0)


def is_token_expired(token, buffer_seconds=None):
    """
    Kiểm tra token có hết hạn không (có buffer)
    
    Args:
        token: JWT token string
        buffer_seconds: Buffer time trước khi hết hạn (default: TokenConstants.EXPIRATION_BUFFER_SECONDS)
        
    Returns:
        bool: True nếu token đã hết hạn hoặc sắp hết hạn (trong buffer), False nếu còn hiệu lực
    """
    if buffer_seconds is None:
        buffer_seconds = TokenConstants.EXPIRATION_BUFFER_SECONDS
    
    exp_timestamp = get_token_expiration_timestamp(token)
    if not exp_timestamp:
        return True
    
    exp_time = datetime.fromtimestamp(exp_timestamp)
    delta = exp_time - datetime.now()
    
    # Token hết hạn nếu còn < buffer_seconds
    return delta.total_seconds() < buffer_seconds


def format_time_remaining(total_seconds):
    """
    Format thời gian còn lại thành string dễ đọc
    
    Args:
        total_seconds: Tổng số giây còn lại
        
    Returns:
        str: Formatted time string (ví dụ: "7 giờ 30 phút", "5 phút 15 giây")
    """
    if total_seconds <= 0:
        return TimeFormatConstants.EXPIRED_MESSAGE
    
    hours = total_seconds // TimeFormatConstants.SECONDS_PER_HOUR
    minutes = (total_seconds % TimeFormatConstants.SECONDS_PER_HOUR) // TimeFormatConstants.SECONDS_PER_MINUTE
    seconds = total_seconds % TimeFormatConstants.SECONDS_PER_MINUTE
    
    if hours > 0:
        if minutes > 0:
            return TimeFormatConstants.HOURS_MINUTES_FORMAT.format(hours=hours, minutes=minutes)
        else:
            return TimeFormatConstants.HOURS_FORMAT.format(hours=hours)
    elif minutes > 0:
        if seconds > 0:
            return TimeFormatConstants.MINUTES_SECONDS_FORMAT.format(minutes=minutes, seconds=seconds)
        else:
            return TimeFormatConstants.MINUTES_FORMAT.format(minutes=minutes)
    else:
        return TimeFormatConstants.SECONDS_FORMAT.format(seconds=seconds)


def get_token_expires_in(token):
    """
    Tính thời gian còn lại của token và format thành string
    
    Args:
        token: JWT token string
        
    Returns:
        str: Formatted time remaining hoặc empty string nếu không có token
    """
    if not token:
        return ''
    
    exp_timestamp = get_token_expiration_timestamp(token)
    if not exp_timestamp:
        return ''
    
    exp_time = datetime.fromtimestamp(exp_timestamp)
    now = datetime.now()
    delta = exp_time - now
    total_seconds = int(delta.total_seconds())
    
    return format_time_remaining(total_seconds)

