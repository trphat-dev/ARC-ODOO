# -*- coding: utf-8 -*-

"""
SSI FastConnect API Client Integration
Wrapper for SSI Data API to fetch Vietnamese stock market data
"""

import logging
import json
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from ssi_fc_data import model, fc_md_client
    SSI_AVAILABLE = True
except ImportError:
    SSI_AVAILABLE = False
    _logger.warning('SSI FastConnect Data SDK not available. SSI integration will be disabled.')


class SSIClient:
    """Client for interacting with SSI FastConnect Data API"""

    def __init__(self, config=None, env=None):
        """
        Initialize SSI client
        
        Args:
            config: ssi.api.config record (optional, will fetch if not provided)
            env: Odoo environment
        """
        self.env = env
        if not SSI_AVAILABLE:
            raise UserError(_('SSI FastConnect Data SDK is not installed. Please install: pip install ssi-fc-data'))
        
        # Get SSI config
        if config:
            self.config = config
        elif env:
            self.config = env['ssi.api.config'].get_config()
            if not self.config:
                raise UserError(_('SSI API Configuration not found. Please configure it in Stock Data module.'))
        else:
            raise UserError(_('Odoo environment or config is required'))

        # Build SDK config
        try:
            # Build SDK config directly (avoid import issues)
            # Note: self.config is already validated above
            
            consumer_id = getattr(self.config, 'consumer_id', None) or ''
            consumer_secret = getattr(self.config, 'consumer_secret', None) or ''
            api_url = getattr(self.config, 'api_url', None) or ''
            
            if not consumer_id.strip():
                raise UserError(_('Consumer ID is required. Please check SSI API configuration.'))
            if not consumer_secret.strip():
                raise UserError(_('Consumer Secret is required. Please check SSI API configuration.'))
            if not api_url.strip():
                raise UserError(_('API URL is required. Please check SSI API configuration.'))
            
            # Validate API URL format
            api_url_clean = api_url.strip()
            if not (api_url_clean.startswith('http://') or api_url_clean.startswith('https://')):
                raise UserError(_('API URL must start with http:// or https://. Current value: %s') % api_url_clean)
            
            # Create SDK config object
            class Config:
                pass
            sdk_config = Config()
            sdk_config.consumerID = consumer_id.strip()
            sdk_config.consumerSecret = consumer_secret.strip()
            sdk_config.url = api_url_clean
            sdk_config.auth_type = 'Bearer'
            
            self.sdk_config = sdk_config
            
            # Try to initialize client with better error handling
            _logger.info(f'Initializing SSI client with URL: {api_url_clean}, Consumer ID: {consumer_id[:10]}...')
            try:
                self.client = fc_md_client.MarketDataClient(self.sdk_config)
                _logger.info('SSI client initialized successfully')
            except NameError as e:
                # "This connection is invalid" error from SSI SDK
                error_msg = str(e)
                if 'connection is invalid' in error_msg.lower() or 'invalid' in error_msg.lower():
                    _logger.error(f'SSI API connection failed. Error: {error_msg}')
                    raise UserError(_(
                        'SSI API connection failed: Invalid credentials or connection.\n\n'
                        'Please check:\n'
                        '1. Consumer ID and Consumer Secret are correct\n'
                        '2. API URL is correct and accessible\n'
                        '3. Your SSI API account is active\n'
                        '4. Network connection to SSI servers is working\n\n'
                        'Error details: %s'
                    ) % error_msg)
                else:
                    raise
            except Exception as sdk_error:
                # Other SDK errors
                _logger.error(f'SSI SDK initialization error: {sdk_error}', exc_info=True)
                raise UserError(_(
                    'Failed to initialize SSI SDK client.\n\n'
                    'Error: %s\n\n'
                    'Please verify your SSI API configuration in Stock Data module.'
                ) % str(sdk_error))
            
        except UserError:
            raise
        except Exception as e:
            _logger.error(f'Failed to initialize SSI client: {e}', exc_info=True)
            raise UserError(_('Failed to initialize SSI client: %s') % str(e))

    def get_securities_list(self, market=None, page_index=1, page_size=200):
        """
        Get securities list from SSI API or Odoo database
        
        Args:
            market: Market filter (HOSE, HNX, UPCOM)
            page_index: Page index
            page_size: Page size
            
        Returns:
            list: List of securities
        """
        try:
            # Try to get from Odoo database first
            if self.env:
                domain = []
                if market:
                    domain.append(('market', '=', market))
                
                securities = self.env['ssi.securities'].search(domain, limit=page_size)
                if securities:
                    return [{
                        'symbol': s.symbol,
                        'market': s.market,
                        'stock_name_vn': s.stock_name_vn,
                        'stock_name_en': s.stock_name_en,
                        'current_price': s.current_price,
                        'reference_price': s.reference_price,
                    } for s in securities]

            # If not in database, fetch from API
            req = model.securities_list(
                market=market or '',
                pageIndex=str(page_index),
                pageSize=str(page_size)
            )
            
            response = self.client.securities_list(self.sdk_config, req)
            
            if response.get('status') == 'Success' and response.get('data'):
                return response['data']
            else:
                _logger.warning(f'SSI API returned error: {response.get("message", "Unknown error")}')
                return []

        except Exception as e:
            _logger.error(f'Failed to get securities list: {e}', exc_info=True)
            raise UserError(_('Failed to get securities list: %s') % str(e))

    def get_daily_ohlc(self, symbol, from_date, to_date, market=None):
        """
        Get daily OHLC data from SSI API
        
        Args:
            symbol: Stock symbol (e.g., 'FPT', 'VCB')
            from_date: Start date (string 'YYYY-MM-DD' or date object)
            to_date: End date (string 'YYYY-MM-DD' or date object)
            market: Market (HOSE, HNX, UPCOM)
            
        Returns:
            list: List of OHLC records
        """
        try:
            from datetime import datetime, date
            
            # Normalize date format
            if isinstance(from_date, str):
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        from_date_obj = datetime.strptime(from_date, '%d/%m/%Y').date()
                    except ValueError:
                        _logger.error(f'Invalid from_date format: {from_date}')
                        from_date_obj = None
            elif hasattr(from_date, 'date'):
                from_date_obj = from_date.date() if hasattr(from_date, 'date') else from_date
            else:
                from_date_obj = from_date
            
            if isinstance(to_date, str):
                try:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        to_date_obj = datetime.strptime(to_date, '%d/%m/%Y').date()
                    except ValueError:
                        _logger.error(f'Invalid to_date format: {to_date}')
                        to_date_obj = None
            elif hasattr(to_date, 'date'):
                to_date_obj = to_date.date() if hasattr(to_date, 'date') else to_date
            else:
                to_date_obj = to_date
            
            _logger.info(f'Fetching OHLC for {symbol} ({market}) from {from_date_obj} to {to_date_obj}')
            
            # Try to get from Odoo database first, but only if we have sufficient data
            if self.env and from_date_obj and to_date_obj:
                security = self.env['ssi.securities'].search([
                    ('symbol', '=', symbol),
                    ('market', '=', market or 'HOSE')
                ], limit=1)
                
                if security:
                    ohlc_records = self.env['ssi.daily.ohlc'].search([
                        ('security_id', '=', security.id),
                        ('date', '>=', from_date_obj),
                        ('date', '<=', to_date_obj),
                    ], order='date asc')
                    
                    # Calculate expected number of trading days (approximately)
                    # Vietnamese stock market: ~5 trading days per week, ~20-22 per month
                    days_diff = (to_date_obj - from_date_obj).days
                    expected_min_records = max(1, int(days_diff * 0.7))  # ~70% of days are trading days
                    
                    if ohlc_records and len(ohlc_records) >= expected_min_records:
                        # Database has sufficient data
                        result = [{
                            'date': o.date.strftime('%Y-%m-%d'),
                            'open': o.open_price,
                            'high': o.high_price,
                            'low': o.low_price,
                            'close': o.close_price,
                            'volume': o.volume,
                            'value': o.value,
                        } for o in ohlc_records]
                        _logger.info(f'Found {len(result)} records in database for {symbol} (expected at least {expected_min_records})')
                        return result
                    elif ohlc_records:
                        # Database has some data but not enough, fetch from API to supplement
                        _logger.warning(f'Database has only {len(ohlc_records)} records for {symbol}, expected at least {expected_min_records}. Fetching from API to get complete data.')
                        # Continue to API fetch below
                    else:
                        _logger.info(f'No records in database for {symbol}, fetching from API')

            # Fetch from API in chunks (to avoid API limits)
            if not from_date_obj or not to_date_obj:
                raise UserError(_('Invalid date range provided for fetching OHLC data.'))

            from datetime import timedelta
            chunk_size_days = 90
            current_start = from_date_obj
            combined_results = []

            _logger.info(f'Fetching daily OHLC from API in chunks for {symbol} ({market})')

            while current_start <= to_date_obj:
                current_end = min(current_start + timedelta(days=chunk_size_days - 1), to_date_obj)
                chunk_results = self._fetch_daily_ohlc_chunk(symbol, current_start, current_end)

                if chunk_results:
                    combined_results.extend(chunk_results)
                    # Save to database for future use
                    if self.env and security:
                        self._store_daily_ohlc_records(security, chunk_results)
                else:
                    _logger.warning(f'No OHLC data returned from API for {symbol} between {current_start} and {current_end}')

                current_start = current_end + timedelta(days=1)

            if combined_results:
                # Remove duplicates and sort by date
                unique = {}
                for rec in combined_results:
                    unique[rec['date']] = rec
                sorted_result = [unique[date] for date in sorted(unique.keys())]
                _logger.info(f'Fetched total {len(sorted_result)} records from SSI API for {symbol}')
                return sorted_result

            _logger.warning(f'No OHLC data available from SSI API for {symbol} between {from_date_obj} and {to_date_obj}')
            return []

        except Exception as e:
            _logger.error(f'Failed to get daily OHLC for {symbol}: {e}', exc_info=True)
            raise UserError(_('Failed to get daily OHLC for %s: %s') % (symbol, str(e)))

    def _fetch_daily_ohlc_chunk(self, symbol, start_date, end_date):
        """Fetch daily OHLC data for a smaller date range directly from API"""
        from datetime import datetime

        start_str = start_date.strftime('%d/%m/%Y')
        end_str = end_date.strftime('%d/%m/%Y')

        _logger.debug(f'Calling SSI API chunk for {symbol} from {start_str} to {end_str}')
        req = model.daily_ohlc(
            symbol=symbol,
            fromDate=start_str,
            toDate=end_str,
            pageIndex='1',
            pageSize='1000',
            ascending=True
        )

        response = self.client.daily_ohlc(self.sdk_config, req)
        if response.get('status') != 'Success' or not response.get('data'):
            _logger.warning(f'SSI API chunk returned error for {symbol}: {response.get("message", "Unknown error")}')
            return []

        data = response['data']
        if not isinstance(data, list):
            _logger.warning(f'SSI API chunk returned non-list data: {type(data)}')
            return []

        result = []
        for item in data:
            trading_date = (
                item.get('tradingDate')
                or item.get('TradingDate')
                or item.get('date')
                or item.get('Date')
                or ''
            )
            if not trading_date:
                continue
            try:
                if isinstance(trading_date, str):
                    if '/' in trading_date:
                        if len(trading_date.split('/')[0]) == 4:
                            parsed_date = datetime.strptime(trading_date, '%Y/%m/%d')
                        else:
                            parsed_date = datetime.strptime(trading_date, '%d/%m/%Y')
                    elif '-' in trading_date:
                        parsed_date = datetime.strptime(trading_date, '%Y-%m-%d')
                    else:
                        parsed_date = datetime.strptime(trading_date, '%Y%m%d')
                else:
                    parsed_date = trading_date

                result.append({
                    'date': parsed_date.strftime('%Y-%m-%d'),
                    'open': float(item.get('open') or item.get('Open') or item.get('OpenPrice') or item.get('openPrice') or 0),
                    'high': float(item.get('high') or item.get('High') or item.get('HighPrice') or item.get('highPrice') or 0),
                    'low': float(item.get('low') or item.get('Low') or item.get('LowPrice') or item.get('lowPrice') or 0),
                    'close': float(item.get('close') or item.get('Close') or item.get('ClosePrice') or item.get('closePrice') or 0),
                    'volume': float(item.get('volume') or item.get('Volume') or item.get('TotalVolume') or item.get('totalVolume') or item.get('MatchVolume') or item.get('matchVolume') or 0),
                    'value': float(item.get('value') or item.get('Value') or item.get('TotalValue') or item.get('totalValue') or 0),
                })
            except (ValueError, TypeError) as e:
                _logger.warning(f'Failed to parse date {trading_date} for {symbol}: {e}')
                continue

        return result

    def _store_daily_ohlc_records(self, security, data):
        """Persist fetched daily OHLC data into Odoo database for caching"""
        if not security or not self.env:
            return

        DailyOHLC = self.env['ssi.daily.ohlc']
        for item in data:
            date_str = item.get('date')
            if not date_str:
                continue
            try:
                date_obj = fields.Date.from_string(date_str)
            except Exception:
                continue

            existing = DailyOHLC.search([
                ('security_id', '=', security.id),
                ('date', '=', date_obj),
            ], limit=1)

            values = {
                'security_id': security.id,
                'date': date_obj,
                'open_price': item.get('open', 0.0),
                'high_price': item.get('high', 0.0),
                'low_price': item.get('low', 0.0),
                'close_price': item.get('close', 0.0),
                'volume': item.get('volume', 0.0),
                'value': item.get('value', 0.0),
            }

            if existing:
                existing.write(values)
            else:
                DailyOHLC.create(values)

    def get_intraday_ohlc(self, symbol, date, market=None, resolution='1'):
        """
        Get intraday OHLC data from SSI API for a single date
        
        Args:
            symbol: Stock symbol
            date: Trading date
            market: Market (HOSE, HNX, UPCOM)
            resolution: Resolution in minutes ('1', '5', '15', '30', '60')
            
        Returns:
            list: List of intraday OHLC records
        """
        try:
            from datetime import datetime, date as date_type
            
            # Normalize date format
            if isinstance(date, str):
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date, '%d/%m/%Y').date()
                    except ValueError:
                        _logger.error(f'Invalid date format: {date}')
                        date_obj = None
            elif hasattr(date, 'date'):
                date_obj = date.date() if hasattr(date, 'date') else date
            else:
                date_obj = date
            
            if not date_obj:
                return []
            
            # Try to get from Odoo database first
            if self.env:
                security = self.env['ssi.securities'].search([
                    ('symbol', '=', symbol),
                    ('market', '=', market or 'HOSE')
                ], limit=1)
                
                if security:
                    intraday_records = self.env['ssi.intraday.ohlc'].search([
                        ('security_id', '=', security.id),
                        ('date', '=', date_obj),
                    ], order='time asc')
                    
                    if intraday_records:
                        result = []
                        for i in intraday_records:
                            # Filter by resolution if available
                            if hasattr(i, 'resolution') and i.resolution:
                                if str(i.resolution) != str(resolution):
                                    continue
                            result.append({
                                'date': date_obj.strftime('%Y-%m-%d'),
                                'time': i.time,
                                'open': i.open_price,
                                'high': i.high_price,
                                'low': i.low_price,
                                'close': i.close_price,
                                'volume': i.volume,
                            })
                        if result:
                            _logger.info(f'Found {len(result)} intraday records in database for {symbol} on {date_obj}')
                            return result

            # If not in database, fetch from API
            date_str = date_obj.strftime('%d/%m/%Y')
            _logger.info(f'Calling SSI API for intraday data: {symbol} on {date_str} (resolution: {resolution}min)')
            
            # Note: SSI API intraday_ohlc may not accept 'market' parameter
            # Check API documentation for correct parameters
            try:
                req = model.intraday_ohlc(
                    symbol=symbol,
                    fromDate=date_str,
                    toDate=date_str,
                    pageIndex='1',
                    pageSize='1000',
                    resolution=resolution,  # Resolution in minutes
                )
            except TypeError:
                # If resolution parameter not supported, try without it
                _logger.warning(f'Resolution parameter not supported, trying without it')
                req = model.intraday_ohlc(
                    symbol=symbol,
                    fromDate=date_str,
                    toDate=date_str,
                    pageIndex='1',
                    pageSize='1000',
                )
            
            response = self.client.intraday_ohlc(self.sdk_config, req)
            
            if response.get('status') == 'Success' and response.get('data'):
                data = response['data']
                if isinstance(data, list):
                    result = []
                    for item in data:
                        # Parse time - could be in different formats
                        time_str = item.get('time', '') or item.get('Time', '')
                        if not time_str:
                            continue
                        
                        result.append({
                            'date': date_obj.strftime('%Y-%m-%d'),
                            'time': time_str,
                            'open': float(item.get('open') or item.get('Open') or item.get('OpenPrice') or item.get('openPrice') or 0),
                            'high': float(item.get('high') or item.get('High') or item.get('HighPrice') or item.get('highPrice') or 0),
                            'low': float(item.get('low') or item.get('Low') or item.get('LowPrice') or item.get('lowPrice') or 0),
                            'close': float(item.get('close') or item.get('Close') or item.get('ClosePrice') or item.get('closePrice') or 0),
                            'volume': float(item.get('volume') or item.get('Volume') or item.get('TotalVolume') or item.get('totalVolume') or item.get('MatchVolume') or item.get('matchVolume') or 0),
                        })
                    _logger.info(f'Fetched {len(result)} intraday records from SSI API for {symbol}')
                    return result
                return []
            else:
                error_msg = response.get('message', 'Unknown error')
                _logger.warning(f'SSI API returned error for intraday {symbol}: {error_msg}')
                return []

        except Exception as e:
            _logger.error(f'Failed to get intraday OHLC for {symbol}: {e}', exc_info=True)
            raise UserError(_('Failed to get intraday OHLC for %s: %s') % (symbol, str(e)))
    
    def get_intraday_ohlc_range(self, symbol, from_date, to_date, market=None, resolution='1'):
        """
        Get intraday OHLC data from SSI API for a date range
        
        Args:
            symbol: Stock symbol
            from_date: Start date
            to_date: End date
            market: Market (HOSE, HNX, UPCOM)
            resolution: Resolution in minutes ('1', '5', '15', '30', '60')
            
        Returns:
            list: List of intraday OHLC records for the date range
        """
        try:
            from datetime import datetime, timedelta, date as date_type
            
            # Normalize dates
            if isinstance(from_date, str):
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            elif hasattr(from_date, 'date'):
                from_date_obj = from_date.date() if hasattr(from_date, 'date') else from_date
            else:
                from_date_obj = from_date
                
            if isinstance(to_date, str):
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            elif hasattr(to_date, 'date'):
                to_date_obj = to_date.date() if hasattr(to_date, 'date') else to_date
            else:
                to_date_obj = to_date
            
            all_records = []
            current_date = from_date_obj
            
            _logger.info(f'Fetching intraday data for {symbol} from {from_date_obj} to {to_date_obj}')
            
            # Fetch data day by day
            while current_date <= to_date_obj:
                day_records = self.get_intraday_ohlc(symbol, current_date, market, resolution)
                if day_records:
                    all_records.extend(day_records)
                current_date += timedelta(days=1)
            
            _logger.info(f'Fetched {len(all_records)} total intraday records for {symbol} from {from_date_obj} to {to_date_obj}')
            return all_records
            
        except Exception as e:
            _logger.error(f'Failed to get intraday OHLC range for {symbol}: {e}', exc_info=True)
            raise UserError(_('Failed to get intraday OHLC range for %s: %s') % (symbol, str(e)))

    def get_current_price(self, symbol, market=None):
        """
        Get current price for symbol
        
        Args:
            symbol: Stock symbol
            market: Market (HOSE, HNX, UPCOM)
            
        Returns:
            float: Current price
        """
        try:
            if self.env:
                security = self.env['ssi.securities'].search([
                    ('symbol', '=', symbol),
                    ('market', '=', market or 'HOSE')
                ], limit=1)
                
                if security and security.current_price:
                    return security.current_price

            # Fetch latest price from API
            from odoo import fields as odoo_fields
            req = model.daily_stock_price(
                symbol=symbol,
                fromDate=odoo_fields.Date.today().strftime('%d/%m/%Y'),
                toDate=odoo_fields.Date.today().strftime('%d/%m/%Y'),
                pageIndex='1',
                pageSize='1',
                market=market or 'HOSE'
            )
            
            response = self.client.daily_stock_price(self.sdk_config, req)
            
            if response.get('status') == 'Success' and response.get('data'):
                data = response['data']
                if isinstance(data, list) and len(data) > 0:
                    return float(data[0].get('close', 0))
            
            return 0.0

        except Exception as e:
            _logger.error(f'Failed to get current price: {e}', exc_info=True)
            return 0.0

