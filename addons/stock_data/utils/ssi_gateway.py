# -*- coding: utf-8 -*-
import logging
import time
from functools import wraps
from odoo.exceptions import UserError

try:
    from ssi_fc_data import fc_md_client, model
    SSI_SDK_AVAILABLE = True
except ImportError:
    SSI_SDK_AVAILABLE = False

_logger = logging.getLogger(__name__)


class SSIConnectionError(Exception):
    """Raised when connection to SSI fails"""
    pass


class SSIDataError(Exception):
    """Raised when data fetching fails"""
    pass


def with_retry(max_retries=3, delay=1):
    """
    Decorator to retry failed API calls with exponential backoff.
    Only retries on SSIDataError, not on SSIConnectionError.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except SSIDataError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)
                        _logger.warning("Retry %d/%d for %s (waiting %ds): %s", 
                                       attempt + 1, max_retries, func.__name__, sleep_time, e)
                        time.sleep(sleep_time)
            raise last_error
        return wrapper
    return decorator


class RateLimiter:
    """
    Simple rate limiter for API calls.
    Ensures minimum interval between calls to avoid overwhelming the API.
    """
    def __init__(self, calls_per_second=5):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    def wait(self):
        """Wait if needed to respect rate limit"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class SSIGateway:
    """
    Adapter pattern to wrap ssi-fc-data SDK.
    Provides a clean interface for Odoo models and handles low-level SDK details.
    """

    def __init__(self, consumer_id, consumer_secret, api_url=None):
        if not SSI_SDK_AVAILABLE:
            raise UserError("SSI FC Data SDK is not installed.")
            
        self.consumer_id = consumer_id
        self.consumer_secret = consumer_secret
        self.api_url = api_url or 'https://fc-data.ssi.com.vn/'
        
        # Configure SDK config object
        class Config:
            pass
        
        self.config = Config()
        self.config.consumerID = self.consumer_id
        self.config.consumerSecret = self.consumer_secret
        self.config.url = self.api_url
        
        try:
            self.client = fc_md_client.MarketDataClient(self.config)
        except Exception as e:
            _logger.error("Failed to initialize SSI Client: %s", e)
            raise SSIConnectionError(f"Failed to init client: {e}")

    def get_access_token(self):
        """Test connection and get access token"""
        try:
            req = model.accessToken(self.consumer_id, self.consumer_secret)
            res = self.client.access_token(req)
            if res.get('status') == 'Success':
                return res.get('data', {}).get('accessToken')
            raise SSIConnectionError(res.get('message', 'Unknown error'))
        except Exception as e:
            _logger.error("Get Access Token Failed: %s", e)
            raise SSIConnectionError(str(e))

    def get_securities(self, market, page_index=1, page_size=1000):
        """Fetch securities list"""
        try:
            req = model.securities(market, page_index, page_size)
            res = self.client.securities(self.config, req)
            if res.get('status') != 'Success':
                 raise SSIDataError(res.get('message'))
            return res.get('data', {})
        except Exception as e:
            _logger.error("Get Securities Failed: %s", e)
            raise SSIDataError(str(e))

    def get_securities_details(self, market, symbol, page_index=1, page_size=100):
        """Fetch securities details"""
        try:
            req = model.securities_details(market, symbol, page_index, page_size)
            res = self.client.securities_details(self.config, req)
            if res.get('status') != 'Success':
                 raise SSIDataError(res.get('message'))
            return res.get('data', {})
        except Exception as e:
            _logger.error("Get Securities Details Failed: %s", e)
            raise SSIDataError(str(e))

    def get_daily_stock_price(self, symbol, from_date, to_date, market, page_index=1, page_size=100):
        """Fetch daily stock price (snapshot/board info)"""
        try:
            # Dates provided as dd/mm/yyyy string or dates
            if hasattr(from_date, 'strftime'): from_date = from_date.strftime('%d/%m/%Y')
            if hasattr(to_date, 'strftime'): to_date = to_date.strftime('%d/%m/%Y')
            
            req = model.daily_stock_price(symbol, from_date, to_date, page_index, page_size, market)
            res = self.client.daily_stock_price(self.config, req)
            if res.get('status') != 'Success':
                 raise SSIDataError(res.get('message'))
            return res.get('data', [])
        except Exception as e:
             _logger.error("Get Daily Stock Price Failed: %s", e)
             raise SSIDataError(str(e))

    def get_daily_ohlc(self, symbol, from_date, to_date, page_index=1, page_size=100, ascending=True):
        """Fetch Daily OHLC"""
        try:
            if hasattr(from_date, 'strftime'): from_date = from_date.strftime('%d/%m/%Y')
            if hasattr(to_date, 'strftime'): to_date = to_date.strftime('%d/%m/%Y')
            
            req = model.daily_ohlc(symbol, from_date, to_date, page_index, page_size, ascending)
            res = self.client.daily_ohlc(self.config, req)
            if res.get('status') != 'Success':
                 raise SSIDataError(res.get('message'))
            return res.get('data', [])
        except Exception as e:
             _logger.error("Get Daily OHLC Failed: %s", e)
             raise SSIDataError(str(e))

    def get_intraday_ohlc(self, symbol, from_date, to_date, page_index=1, page_size=100, ascending=True, resolution=1):
        """Fetch Intraday OHLC"""
        try:
            if hasattr(from_date, 'strftime'): from_date = from_date.strftime('%d/%m/%Y')
            if hasattr(to_date, 'strftime'): to_date = to_date.strftime('%d/%m/%Y')
            
            req = model.intraday_ohlc(symbol, from_date, to_date, page_index, page_size, ascending, resolution)
            res = self.client.intraday_ohlc(self.config, req)
            if res.get('status') != 'Success':
                 raise SSIDataError(res.get('message'))
            return res.get('data', [])
        except Exception as e:
             _logger.error("Get Intraday OHLC Failed: %s", e)
             raise SSIDataError(str(e))

    def get_index_list(self, exchange, page_index=1, page_size=100):
        """Fetch index list for an exchange (HOSE, HNX, UPCOM)"""
        try:
            req = model.index_list(exchange, page_index, page_size)
            res = self.client.index_list(self.config, req)
            if res.get('status') != 'Success':
                raise SSIDataError(res.get('message'))
            return res.get('data', {})
        except Exception as e:
            _logger.error("Get Index List Failed: %s", e)
            raise SSIDataError(str(e))

    def get_index_components(self, index_code, page_index=1, page_size=100):
        """Fetch components of an index (e.g., VN30, HNX30)"""
        try:
            req = model.index_components(index_code, page_index, page_size)
            res = self.client.index_components(self.config, req)
            if res.get('status') != 'Success':
                raise SSIDataError(res.get('message'))
            return res.get('data', {})
        except Exception as e:
            _logger.error("Get Index Components Failed: %s", e)
            raise SSIDataError(str(e))

    def get_daily_index(self, request_id, index_id, from_date, to_date, page_index=1, page_size=100):
        """Fetch daily index data"""
        try:
            if hasattr(from_date, 'strftime'): from_date = from_date.strftime('%d/%m/%Y')
            if hasattr(to_date, 'strftime'): to_date = to_date.strftime('%d/%m/%Y')
            
            req = model.daily_index(request_id, index_id, from_date, to_date, page_index, page_size, '', '')
            res = self.client.daily_index(self.config, req)
            if res.get('status') != 'Success':
                raise SSIDataError(res.get('message'))
            return res.get('data', {})
        except Exception as e:
            _logger.error("Get Daily Index Failed: %s", e)
            raise SSIDataError(str(e))
