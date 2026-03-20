from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class StockDataApiController(http.Controller):
    @http.route('/stock_data/api/securities', type='json', auth='public', methods=['POST'], csrf=False)
    def list_securities(self, **kwargs):
        """
        API endpoint to list securities with authentication via X-Api-Key header.
        For internal use, configure 'stock_data.api.secret' in System Parameters.
        """
        try:
            # Authentication check
            icp = request.env['ir.config_parameter'].sudo()
            api_secret = icp.get_param('stock_data.api.secret', default='')
            provided = request.httprequest.headers.get('X-Api-Key', '')
            
            if not api_secret:
                _logger.warning("API secret not configured")
                return {'status': 'Error', 'message': 'API not configured'}
            
            if provided != api_secret:
                _logger.warning("Unauthorized API access attempt")
                return {'status': 'Error', 'message': 'Unauthorized'}

            # Validate and parse parameters
            try:
                market = (kwargs.get('market') or '').strip().upper()
                page_index = max(int(kwargs.get('pageIndex') or 1), 1)
                page_size = min(max(int(kwargs.get('pageSize') or 200), 1), 1000)  # Limit max 1000
            except (ValueError, TypeError) as e:
                _logger.error("Invalid parameters: %s", e)
                return {'status': 'Error', 'message': 'Invalid parameters'}

            # Build domain
            domain = []
            if market and market in ['HOSE', 'HNX', 'UPCOM']:
                domain.append(('market', '=', market))

            # Query securities
            offset = (page_index - 1) * page_size
            recs = request.env['ssi.securities'].sudo().search(
                domain, 
                offset=offset, 
                limit=page_size, 
                order='symbol asc'
            )

            def _vals(rec):
                return {
                    'symbol': rec.symbol,
                    'market': rec.market,
                    'StockName': getattr(rec, 'stock_name_vn', '') or '',
                    'StockEnName': getattr(rec, 'stock_name_en', '') or '',
                    'floorCode': rec.floor_code or '',
                    'securityType': rec.security_type or '',
                    'ReferencePrice': rec.reference_price or 0.0,
                    'CeilingPrice': rec.ceiling_price or 0.0,
                    'FloorPrice': rec.floor_price or 0.0,
                    'Price': rec.current_price or 0.0,
                    'HighPrice': rec.high_price or 0.0,
                    'LowPrice': rec.low_price or 0.0,
                    'Volume': rec.volume or 0.0,
                    'TotalValue': rec.total_value or 0.0,
                    'Change': rec.change or 0.0,
                    'ChangePercent': rec.change_percent or 0.0,
                    'LastPrice': rec.last_price or 0.0,
                    'last_update': rec.last_update.isoformat() if rec.last_update else None,
                }

            return {
                'status': 'Success',
                'data': {
                    'items': [_vals(r) for r in recs],
                    'pageIndex': page_index,
                    'pageSize': page_size,
                    'count': len(recs),
                }
            }
        except Exception as e:
            _logger.exception("Error in list_securities API: %s", e)
            return {'status': 'Error', 'message': 'Internal server error'}

    @http.route('/stock_data/api/intraday_ohlc', type='http', auth='user', methods=['GET'], csrf=False)
    def get_intraday_ohlc(self, **kwargs):
        """
        API endpoint to get intraday OHLC data for candlestick chart.
        Parameters:
            - symbol: Security symbol (e.g., 'AAM', 'VNM')
            - resolution: Resolution in minutes (1, 15, 30, 45, 60)
            - date: Trading date (YYYY-MM-DD format, optional)
            - fromDate: Start date (YYYY-MM-DD, optional)
            - toDate: End date (YYYY-MM-DD, optional)
        """
        import json
        from datetime import datetime, date, timedelta
        
        try:
            symbol = (kwargs.get('symbol') or '').strip().upper()
            resolution = int(kwargs.get('resolution') or 60)
            date_str = kwargs.get('date', '')
            from_date_str = kwargs.get('fromDate', '')
            to_date_str = kwargs.get('toDate', '')
            
            if not symbol:
                return request.make_response(
                    json.dumps({'status': 'Error', 'message': 'Missing symbol parameter'}),
                    headers=[('Content-Type', 'application/json')]
                )

            security = request.env['ssi.securities'].sudo().search([('symbol', '=', symbol)], limit=1)
            if not security:
                return request.make_response(
                    json.dumps({'status': 'Error', 'message': f'Symbol {symbol} not found'}),
                    headers=[('Content-Type', 'application/json')]
                )

            IntradayOHLC = request.env['ssi.intraday.ohlc'].sudo()
            
            # Determine date range
            domain = [('security_id', '=', security.id)]
            
            if date_str:
                try:
                    trading_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    domain.append(('date', '=', trading_date))
                except ValueError:
                    pass
            elif from_date_str or to_date_str:
                if from_date_str:
                    try:
                        f_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                        domain.append(('date', '>=', f_date))
                    except ValueError: pass
                if to_date_str:
                    try:
                        t_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                        domain.append(('date', '<=', t_date))
                    except ValueError: pass
            else:
                # Find the last available date if no date is provided
                last_record = IntradayOHLC.search([('security_id', '=', security.id)], order='date desc', limit=1)
                trading_date = last_record.date if last_record else date.today()
                domain.append(('date', '=', trading_date))
            
            _logger.info(f"Intraday OHLC fetch range: symbol={symbol}, domain={domain}, resolution={resolution}")
            
            # Search for intraday data
            # 1. Try to find records with exact resolution
            exact_records = IntradayOHLC.search(domain + [('resolution', '=', resolution)], order='date asc, time asc')
            
            # --- AUTO-FETCH LOGIC ---
            # If records are empty or too few (e.g. just started streaming), try to fetch from SSI API
            if len(exact_records) < 5 and security:
                _logger.info(f"Intraday OHLC sparse ({len(exact_records)}), attempting fetch from SSI for {symbol} on {trading_date}")
                try:
                    fetched = security.action_fetch_single_intraday(from_date=trading_date, to_date=trading_date)
                    if fetched:
                        # Re-search after fetch
                        exact_records = IntradayOHLC.search(domain + [('resolution', '=', resolution)], order='date asc, time asc')
                except Exception as e:
                    _logger.error(f"Auto-fetch in API failed: {e}")
            
            records = exact_records
            data = []
            
            if not records and resolution > 1:
                # 2. Fallback: Get 1M records and aggregate manually
                _logger.info(f"Intraday OHLC: No {resolution}M data, fallback to 1M aggregation for {symbol}")
                base_records = IntradayOHLC.search(domain + [('resolution', '=', 1)], order='date asc, time asc')
                
                if base_records:
                    buckets = {} # (date, bucket_key) -> candle_data
                    
                    for br in base_records:
                        if not br.time or not br.date: continue
                        try:
                            # Parse time (HH:MM or HH:MM:SS)
                            h, m = map(int, br.time.split(':')[:2])
                            # Find the start of the resolution bucket
                            bucket_m = (m // resolution) * resolution
                            bucket_key = f"{h:02d}:{bucket_m:02d}"
                            
                            key = (br.date, bucket_key)
                            
                            if key not in buckets:
                                buckets[key] = {
                                    'date': br.date,
                                    'time': bucket_key,
                                    'open': br.open_price or 0,
                                    'high': br.high_price or 0,
                                    'low': br.low_price or 0,
                                    'close': br.close_price or 0,
                                    'volume': br.volume or 0,
                                }
                            else:
                                b = buckets[key]
                                b['high'] = max(b['high'], br.high_price or 0)
                                b['low'] = min(b['low'], br.low_price or 0)
                                b['close'] = br.close_price or 0 # Last one in bucket
                                b['volume'] += (br.volume or 0)
                        except Exception:
                            continue
                    
                    # Sort by date and bucket_key
                    sorted_keys = sorted(buckets.keys())
                    for k in sorted_keys:
                        data_item = buckets[k]
                        item = {
                            'date': data_item['date'].strftime('%Y-%m-%d'),
                            'time': data_item['time'],
                            'open': data_item['open'],
                            'high': data_item['high'],
                            'low': data_item['low'],
                            'close': data_item['close'],
                            'volume': data_item['volume'],
                        }
                        # Add timestamp
                        try:
                            h, m = map(int, data_item['time'].split(':'))
                            # Combine date and time
                            dt = datetime.combine(data_item['date'], datetime.min.time().replace(hour=h, minute=m))
                            item['timestamp'] = int(dt.timestamp())
                        except Exception:
                            pass
                        data.append(item)
                    
                    if data:
                        return request.make_response(
                            json.dumps({
                                'status': 'Success',
                                'data': data,
                                'symbol': symbol,
                                'resolution': resolution,
                                'is_aggregated': True,
                                'count': len(data)
                            }),
                            headers=[('Content-Type', 'application/json')]
                        )
            
            # 3. Standard processing for exact or default records
            if not records:
                # If still no data at all, try to get anything (very broad fallback)
                records = IntradayOHLC.search(domain, order='date asc, time asc', limit=2000)
            
            for rec in records:
                time_str = rec.time or ''
                item = {
                    'date': rec.date.strftime('%Y-%m-%d') if rec.date else '',
                    'time': time_str,
                    'open': rec.open_price or 0,
                    'high': rec.high_price or 0,
                    'low': rec.low_price or 0,
                    'close': rec.close_price or 0,
                    'volume': rec.volume or 0,
                }
                if time_str and rec.date:
                    try:
                        parts = time_str.split(':')
                        h = int(parts[0]) if len(parts) > 0 else 0
                        m = int(parts[1]) if len(parts) > 1 else 0
                        s = int(parts[2]) if len(parts) > 2 else 0
                        dt = datetime.combine(rec.date, datetime.min.time().replace(hour=h, minute=m, second=s))
                        item['timestamp'] = int(dt.timestamp())
                    except Exception:
                        pass
                data.append(item)
            
            return request.make_response(
                json.dumps({
                    'status': 'Success',
                    'data': data,
                    'symbol': symbol,
                    'resolution': resolution,
                    'count': len(data)
                }),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.exception("Error in get_intraday_ohlc API: %s", e)
            return request.make_response(
                json.dumps({'status': 'Error', 'message': 'Internal server error'}),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/stock_data/api/realtime_price', type='json', auth='public', methods=['POST'], csrf=False)
    def get_realtime_price(self, **kwargs):
        """
        Fetch realtime stock price directly from SSI API on-demand.
        No cronjob or streaming required.
        
        Parameters:
            - symbol: Stock symbol (required, e.g., 'FPT')
            - market: Market (optional, e.g., 'HOSE', 'HNX', 'UPCOM')
            - update_db: Whether to update database (optional, default=True)
        
        Returns:
            - Realtime price data from SSI API
        """
        from datetime import datetime
        
        try:
            # Optional authentication check - only validate if api_secret is configured
            icp = request.env['ir.config_parameter'].sudo()
            api_secret = icp.get_param('stock_data.api.secret', default='')
            provided = request.httprequest.headers.get('X-Api-Key', '')
            
            # If api_secret is configured, require valid key
            if api_secret and provided != api_secret:
                _logger.warning("Unauthorized API access attempt")
                return {'status': 'Error', 'message': 'Unauthorized'}
            
            # Parse parameters
            symbol = (kwargs.get('symbol') or '').strip().upper()
            market = (kwargs.get('market') or '').strip().upper()
            update_db = kwargs.get('update_db', True)
            
            if not symbol:
                return {'status': 'Error', 'message': 'Missing required parameter: symbol'}
            
            # Build SDK config and client
            try:
                from ssi_fc_data import model, fc_md_client
                sdk_config = request.env['ssi.sdk.config.builder'].sudo().build()
                client = fc_md_client.MarketDataClient(sdk_config)
            except ImportError:
                return {'status': 'Error', 'message': 'SSI SDK (ssi_fc_data) not installed'}
            except Exception as e:
                _logger.error("Failed to initialize SSI client: %s", e)
                return {'status': 'Error', 'message': 'Failed to initialize SSI client'}
            
            # Fetch realtime price from SSI API
            today = datetime.now().strftime('%d/%m/%Y')
            
            req = model.daily_stock_price(
                symbol=symbol,
                fromDate=today,
                toDate=today,
                pageIndex=1,
                pageSize=1,
                market=market or ''
            )
            
            response = client.daily_stock_price(sdk_config, req)
            
            if response.get('status') != 'Success':
                return {
                    'status': 'Error', 
                    'message': response.get('message', 'Failed to fetch data from SSI API')
                }
            
            # Extract data
            data = response.get('data', [])
            if isinstance(data, dict):
                data = data.get('data', []) or data.get('items', []) or [data]
            
            if not data:
                return {'status': 'Error', 'message': f'No realtime data found for symbol: {symbol}'}
            
            price_data = data[0] if isinstance(data, list) else data
            
            # Helper function to safely get float values
            def _to_float(value, default=0.0):
                if value in (None, '', False):
                    return default
                try:
                    return float(str(value).replace(',', ''))
                except (TypeError, ValueError):
                    return default
            
            def _get_value(payload, *keys, default=0.0):
                for key in keys:
                    for candidate in [key, key.lower(), key.upper()]:
                        if candidate in payload and payload[candidate] not in (None, ''):
                            return _to_float(payload[candidate], default)
                return default
            
            # Build response
            result = {
                'symbol': symbol,
                'market': market or price_data.get('Market', price_data.get('market', '')),
                'trading_date': price_data.get('TradingDate', price_data.get('tradingDate', today)),
                'reference_price': _get_value(price_data, 'ReferencePrice', 'RefPrice', 'TC'),
                'ceiling_price': _get_value(price_data, 'CeilingPrice', 'Ceiling', 'Tran'),
                'floor_price': _get_value(price_data, 'FloorPrice', 'Floor', 'San'),
                'open_price': _get_value(price_data, 'OpenPrice', 'Open'),
                'high_price': _get_value(price_data, 'HighestPrice', 'High'),
                'low_price': _get_value(price_data, 'LowestPrice', 'Low'),
                'close_price': _get_value(price_data, 'ClosePrice', 'Close'),
                'last_price': _get_value(price_data, 'LastPrice', 'Last'),
                'last_volume': _get_value(price_data, 'LastVol', 'LastVolume'),
                'price_change': _get_value(price_data, 'PriceChange', 'Change'),
                'price_change_percent': _get_value(price_data, 'PerPriceChange', 'RatioChange'),
                'total_match_volume': _get_value(price_data, 'TotalMatchVol', 'MatchVol'),
                'total_match_value': _get_value(price_data, 'TotalMatchVal', 'MatchVal'),
                'total_traded_volume': _get_value(price_data, 'TotalTradedVol', 'TotalVol'),
                'total_traded_value': _get_value(price_data, 'TotalTradedValue', 'TotalVal'),
                'foreign_buy_volume': _get_value(price_data, 'ForeignBuyVolTotal'),
                'foreign_sell_volume': _get_value(price_data, 'ForeignSellVolTotal'),
                'net_foreign_volume': _get_value(price_data, 'NetForeiVol', 'NetForeivol'),
                'timestamp': datetime.now().isoformat(),
            }
            
            # Update database if requested
            if update_db:
                try:
                    security = request.env['ssi.securities'].sudo().search([
                        ('symbol', '=', symbol)
                    ], limit=1)
                    
                    if security:
                        from odoo import fields as odoo_fields
                        security.write({
                            'reference_price': result['reference_price'] or security.reference_price,
                            'ceiling_price': result['ceiling_price'] or security.ceiling_price,
                            'floor_price': result['floor_price'] or security.floor_price,
                            'current_price': result['close_price'] or result['last_price'] or security.current_price,
                            'high_price': result['high_price'] or security.high_price,
                            'low_price': result['low_price'] or security.low_price,
                            'last_price': result['last_price'] or security.last_price,
                            'volume': result['total_traded_volume'] or result['total_match_volume'] or security.volume,
                            'last_update': odoo_fields.Datetime.now(),
                        })
                        result['db_updated'] = True
                        _logger.info("Updated security %s with realtime price", symbol)
                except Exception as e:
                    _logger.warning("Failed to update database for %s: %s", symbol, e)
                    result['db_updated'] = False
                    result['db_error'] = str(e)
            
            return {'status': 'Success', 'data': result}
            
        except Exception as e:
            _logger.exception("Error in get_realtime_price API: %s", e)
            return {'status': 'Error', 'message': 'Internal server error'}

    # =========================================================================
    # STREAMING API ENDPOINTS
    # =========================================================================
    
    @http.route('/stock_data/api/streaming/health', type='json', auth='user', methods=['POST'], csrf=False)
    def streaming_health(self, **kwargs):
        """
        Get streaming connection health status.
        
        Returns:
            - state: Connection state (connected, disconnected, etc.)
            - is_healthy: Boolean health indicator
            - health_score: 0-100 score
            - queue_size: Current message queue size
            - statistics: Message counts, errors, etc.
        """
        try:
            from ..services.streaming_manager import StreamingManager
            
            manager = StreamingManager.get_instance()
            health = manager.get_health()
            
            return {
                'status': 'Success',
                'data': health
            }
        except Exception as e:
            _logger.exception("Error in streaming_health API: %s", e)
            return {'status': 'Error', 'message': 'Internal server error'}

    @http.route('/stock_data/api/streaming/status', type='json', auth='user', methods=['POST'], csrf=False)
    def streaming_status(self, **kwargs):
        """
        Get detailed streaming status.
        
        Returns:
            - Full status dict from StreamingManager
        """
        try:
            from ..services.streaming_manager import StreamingManager
            
            manager = StreamingManager.get_instance()
            status = manager.get_status()
            
            return {
                'status': 'Success',
                'data': status
            }
        except Exception as e:
            _logger.exception("Error in streaming_status API: %s", e)
            return {'status': 'Error', 'message': 'Internal server error'}

    @http.route('/stock_data/api/streaming/start', type='json', auth='user', methods=['POST'], csrf=False)
    def streaming_start(self, **kwargs):
        """
        Start streaming via API.
        
        Parameters:
            - channel: Streaming channel (X, B, MI, F) - optional
            - symbols: Comma-separated symbols - optional
        
        Returns:
            - Success/Error status
        """
        try:
            config = request.env['ssi.api.config'].sudo().get_config()
            if not config:
                return {'status': 'Error', 'message': 'No active SSI API configuration found'}
            
            # Override channel/symbols if provided
            channel = kwargs.get('channel')
            symbols = kwargs.get('symbols')
            
            if channel:
                config.streaming_channel = channel
            if symbols:
                config.streaming_symbols = symbols
            
            # Use the config action which handles everything
            result = config.action_start_streaming()
            
            return {
                'status': 'Success',
                'message': 'Streaming started successfully',
                'channel': config.streaming_channel,
            }
        except Exception as e:
            _logger.exception("Error in streaming_start API: %s", e)
            return {'status': 'Error', 'message': 'Internal server error'}

    @http.route('/stock_data/api/streaming/stop', type='json', auth='user', methods=['POST'], csrf=False)
    def streaming_stop(self, **kwargs):
        """
        Stop streaming via API.
        
        Returns:
            - Success/Error status
        """
        try:
            config = request.env['ssi.api.config'].sudo().get_config()
            if not config:
                return {'status': 'Error', 'message': 'No active SSI API configuration found'}
            
            config.action_stop_streaming()
            
            return {
                'status': 'Success',
                'message': 'Streaming stopped successfully',
            }
        except Exception as e:
            _logger.exception("Error in streaming_stop API: %s", e)
            return {'status': 'Error', 'message': 'Internal server error'}

    @http.route('/stock_data/api/streaming/stats', type='http', auth='user', methods=['GET'], csrf=False)
    def streaming_stats(self, **kwargs):
        """
        Get streaming statistics as JSON (HTTP GET for easy browser access).
        """
        import json
        
        try:
            from ..services.streaming_manager import StreamingManager
            
            manager = StreamingManager.get_instance()
            status = manager.get_status()
            health = manager.get_health()
            
            # Combine status and health
            result = {
                'status': 'Success',
                'data': {
                    'connection': {
                        'state': status.get('state'),
                        'streaming': status.get('streaming'),
                        'connected_at': status.get('connected_at'),
                        'last_message_at': status.get('last_message_at'),
                    },
                    'health': {
                        'is_healthy': health.get('is_healthy'),
                        'score': health.get('health_score'),
                        'issues': health.get('issues', []),
                    },
                    'queue': {
                        'size': status.get('queue_size'),
                        'capacity': status.get('queue_capacity'),
                    },
                    'statistics': status.get('statistics', {}),
                    'channels': status.get('active_channels', {}),
                }
            }
            
            return request.make_response(
                json.dumps(result, indent=2, default=str),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.exception("Error in streaming_stats API: %s", e)
            return request.make_response(
                json.dumps({'status': 'Error', 'message': 'Internal server error'}),
                headers=[('Content-Type', 'application/json')]
            )
