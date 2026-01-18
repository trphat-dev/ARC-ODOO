# -*- coding: utf-8 -*-

import logging
import json
import base64
from io import BytesIO
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    import pandas_ta as ta
    CHARTS_AVAILABLE = True
except ImportError:
    ta = None
    _logger.warning('pandas_ta is not available. Indicators cannot be calculated.')
    CHARTS_AVAILABLE = False





class AIChartController(http.Controller):
    """Controller for generating charts"""

    @http.route('/ai_chart/technical_chart_data_json', type='json', auth='user', methods=['POST'])
    def technical_chart_data_json(self, prediction_id=None, symbol=None, market=None, days=30, resolution='1D', **kwargs):
        """Return chart data as JSON for OWL component"""
        try:
            # Get params from function arguments first (Odoo JSON RPC standard)
            if not prediction_id and not symbol:
                jsonrequest = getattr(request, 'jsonrequest', {})
                params = jsonrequest.get('params', {})
                if params:
                    prediction_id = params.get('prediction_id') or prediction_id
                    symbol = params.get('symbol') or symbol
                    market = params.get('market') or market
                    days = params.get('days', days)
                    resolution = params.get('resolution', resolution)
            
            # Convert prediction_id to int if provided
            if prediction_id:
                try:
                    prediction_id = int(prediction_id)
                except (ValueError, TypeError):
                    prediction_id = None
            
            _logger.info(f'Technical chart data request: prediction_id={prediction_id}, symbol={symbol}, market={market}, days={days}, resolution={resolution}')
            
            chart_result = self._prepare_lightweight_charts_data(
                prediction_id=prediction_id,
                symbol=symbol,
                market=market,
                days=int(days) if days else 365,
                resolution=resolution
            )
            return chart_result
        except Exception as e:
            _logger.error(f'Technical chart data JSON error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}

    def _prepare_lightweight_charts_data(self, prediction_id=None, symbol=None, market=None, days=365, resolution='1D'):
        """
        Prepare data for Lightweight Charts (TradingView).
        
        Args:
            prediction_id: ai.prediction ID
            symbol: Stock symbol
            market: HOSE, HNX, UPCOM
            days: Number of days to fetch
            resolution: '1D', '1', '5', '15', '30', '60'
            
        Returns:
            dict: Chart data and configuration
        """
        try:
            from datetime import datetime, timedelta
            from odoo import fields as odoo_fields
            
            # Get prediction or use symbol
            if prediction_id:
                prediction = request.env['ai.prediction'].browse(int(prediction_id))
                if not prediction.exists() or prediction.strategy_id.user_id != request.env.user:
                    return {'success': False, 'error': 'Prediction not found'}
                symbol = prediction.symbol
                market = prediction.market
                strategy = prediction.strategy_id
            elif symbol and market:
                strategy = request.env['ai.strategy'].search([
                    ('user_id', '=', request.env.user.id),
                    ('market', '=', market),
                ], limit=1)
                if not strategy:
                    return {'success': False, 'error': 'Strategy not found'}
            else:
                return {'success': False, 'error': 'Prediction ID or Symbol required'}

            # Get historical OHLC data
            config = strategy.config_id
            if not config or not config.ssi_config_id:
                return {'success': False, 'error': 'SSI configuration not found'}

            # Use env to get SSI Client if possible, or fallback relative import
            # Better to rely on what works in other methods, but ideally should be Env based service
            ssi_client = None
            try:
                # Try getting from env if module structure supports it (e.g. abstract model)
                # But here we instantiate the class directly as per original code
                from ..models.ssi_client import SSIClient
                ssi_client = SSIClient(config=config.ssi_config_id, env=request.env)
            except ImportError:
                 try:
                    from odoo.addons.ai_trading_assistant.models.ssi_client import SSIClient
                    ssi_client = SSIClient(config=config.ssi_config_id, env=request.env)
                 except Exception as e:
                    return {'success': False, 'error': f'Failed to load SSI Client: {e}'}

            
            # Calculate date range
            today = odoo_fields.Date.today()
            from_date = today - timedelta(days=days)
            
            import pandas as pd
            
            is_intraday_resolution = str(resolution) in ['1', '5', '15', '30', '60']
            df = pd.DataFrame()

            if is_intraday_resolution:
                # Fetch Intraday Range
                _logger.info(f'Fetching intraday data for {symbol} ({resolution}m) from {from_date} to {today}')
                intraday_temp_data = ssi_client.get_intraday_ohlc_range(symbol, from_date, today, market, resolution=str(resolution))
                
                if not intraday_temp_data:
                    return {'success': False, 'error': 'No intraday data found'}
                
                df = pd.DataFrame(intraday_temp_data)
                
                # Ensure datetime column for sorting
                if 'time' in df.columns:
                     df['datetime'] = pd.to_datetime(
                         df['date'].astype(str) + ' ' + df['time'].astype(str),
                         format='%Y-%m-%d %H:%M:%S',
                         errors='coerce'
                     )
            
            else:
                # Daily Data (History + Today Intraday)
                daily_data = []
                intraday_data = []
                
                if from_date < today:
                    historical_data = ssi_client.get_daily_ohlc(symbol, from_date, today - timedelta(days=1), market)
                    if historical_data:
                        daily_data = historical_data
                
                # Fetch today's intraday to construct current bar
                intraday_resolution = getattr(strategy, 'intraday_resolution', '1') or '1'
                today_intraday = ssi_client.get_intraday_ohlc(symbol, today, market, resolution=intraday_resolution)
                
                if today_intraday and len(today_intraday) > 0:
                    today_str = today.strftime('%Y-%m-%d')
                    for item in today_intraday:
                        time_str = item.get('time', '') or item.get('Time', '')
                        if not time_str:
                            continue
                        if len(time_str.split(':')) == 2:
                            time_str = f"{time_str}:00"
                        intraday_data.append({
                            'date': today_str,
                            'time': time_str,
                            'datetime': f"{today_str} {time_str}",
                            'open': float(item.get('open', 0) or item.get('Open', 0) or 0.0),
                            'high': float(item.get('high', 0) or item.get('High', 0) or 0.0),
                            'low': float(item.get('low', 0) or item.get('Low', 0) or 0.0),
                            'close': float(item.get('close', 0) or item.get('Close', 0) or 0.0),
                            'volume': float(item.get('volume', 0) or item.get('Volume', 0) or 0.0),
                        })
                else:
                    # Fallback to database
                    if request.env:
                        security = request.env['ssi.securities'].search([
                            ('symbol', '=', symbol),
                            ('market', '=', market or 'HOSE')
                        ], limit=1)
                        if security:
                            intraday_records = request.env['ssi.intraday.ohlc'].search([
                                ('security_id', '=', security.id),
                                ('date', '=', today),
                            ], order='time asc', limit=500)
                            if intraday_records:
                                today_str = today.strftime('%Y-%m-%d')
                                for rec in intraday_records:
                                    time_str = str(rec.time) if rec.time else '00:00:00'
                                    if len(time_str.split(':')) == 2:
                                        time_str = f"{time_str}:00"
                                    intraday_data.append({
                                        'date': today_str,
                                        'time': time_str,
                                        'datetime': f"{today_str} {time_str}",
                                        'open': float(rec.open_price or 0.0),
                                        'high': float(rec.high_price or 0.0),
                                        'low': float(rec.low_price or 0.0),
                                        'close': float(rec.close_price or 0.0),
                                        'volume': float(rec.volume or 0.0),
                                    })
                
                # Format daily data
                formatted_daily_data = []
                for item in daily_data:
                    date_str = item.get('date', '')
                    if not date_str:
                        continue
                    formatted_daily_data.append({
                        'date': date_str,
                        'time': '00:00:00',
                        'datetime': f"{date_str} 00:00:00",
                        'open': float(item.get('open', 0.0)),
                        'high': float(item.get('high', 0.0)),
                        'low': float(item.get('low', 0.0)),
                        'close': float(item.get('close', 0.0)),
                        'volume': float(item.get('volume', 0.0)),
                    })
                
                all_data = formatted_daily_data + intraday_data
                
                if not all_data or len(all_data) < 2:
                    return {'success': False, 'error': 'Insufficient data for chart'}
                
                # Convert to DataFrame
                df = pd.DataFrame(all_data)
            
            # Parse datetime
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                mask = df['datetime'].isna()
                if mask.any():
                    df.loc[mask, 'datetime'] = pd.to_datetime(
                        df.loc[mask, 'date'].astype(str) + ' ' + df.loc[mask, 'time'].astype(str),
                        errors='coerce'
                    )
                df = df.sort_values('datetime')
            else:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                if 'time' in df.columns:
                    df['datetime'] = pd.to_datetime(
                        df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['time'].astype(str),
                        format='%Y-%m-%d %H:%M:%S',
                        errors='coerce'
                    )
                    df['datetime'] = df['datetime'].fillna(df['date'])
                df = df.sort_values('datetime' if 'datetime' in df.columns else 'date')
            
            df = df[df['datetime'].notna() if 'datetime' in df.columns else df['date'].notna()]
            
            if len(df) == 0:
                return {'success': False, 'error': 'No valid data after date parsing'}
            
            # Determine if we have intraday data
            has_intraday = 'time' in df.columns and df['time'].notna().any() and (df['time'] != '00:00:00').any()

            # REFACTORED: Use centralized indicator calculation
            if hasattr(strategy, 'calculate_indicators'):
                df_with_indicators = strategy.calculate_indicators(df)
            else:
                _logger.warning("Strategy model missing calculate_indicators method. Falling back to simple DF.")
                df_with_indicators = df.copy()

            if df_with_indicators is None or len(df_with_indicators) == 0:
                return {'success': False, 'error': 'Failed to calculate indicators'}
            
            # Log data availability
            total_rows = len(df_with_indicators)
            _logger.info(f'Data for chart: {total_rows} rows')
            
            # Convert to Lightweight Charts format
            datetime_col = df_with_indicators['datetime'] if 'datetime' in df_with_indicators.columns else df_with_indicators['date']
            
            candlestick_data = []
            ma_short_data = []
            ma_long_data = []
            rsi_data = []
            volume_data = []
            markers = []

            def _format_chart_time(value):
                """Return Lightweight Charts time value (timestamp for intraday)."""
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return None
                try:
                    ts = value if isinstance(value, pd.Timestamp) else pd.to_datetime(value, errors='coerce')
                except Exception:
                    return None
                if ts is None or pd.isna(ts):
                    return None
                if has_intraday:
                    # Lightweight Charts expects UNIX timestamp for intraday precision
                    try:
                        return int(ts.to_pydatetime().timestamp())
                    except Exception:
                        # Fallback using nanoseconds value
                        return int(ts.value // 10**9)
                return {
                    'year': ts.year,
                    'month': ts.month,
                    'day': ts.day,
                }

            prev_ma_short = None
            prev_ma_long = None
            golden_cross_count = 0
            death_cross_count = 0

            for idx, row in df_with_indicators.iterrows():
                dt = datetime_col.iloc[df_with_indicators.index.get_loc(idx)]
                time_obj = _format_chart_time(dt)
                if time_obj is None:
                    continue

                # Candlestick data
                candlestick_data.append({
                    'time': time_obj,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                })
                
                # MA data - Get SMA from centralized calculation
                # Use generic names 'sma_short' and 'sma_long'
                ma_short_val = row.get('sma_short')
                ma_long_val = row.get('sma_long')
                
                # Convert to float and handle NaN
                try:
                    ma_short_val = float(ma_short_val) if not pd.isna(ma_short_val) else None
                except (ValueError, TypeError):
                    ma_short_val = None
                
                try:
                    ma_long_val = float(ma_long_val) if not pd.isna(ma_long_val) else None
                except (ValueError, TypeError):
                    ma_long_val = None
                
                if ma_short_val is not None:
                    ma_short_data.append({
                        'time': time_obj,
                        'value': ma_short_val,
                    })
                
                if ma_long_val is not None:
                    ma_long_data.append({
                        'time': time_obj,
                        'value': ma_long_val,
                    })
                
                # RSI data
                rsi_val = row.get('rsi', 50.0)
                if pd.isna(rsi_val):
                    rsi_val = 50.0
                rsi_data.append({
                    'time': time_obj,
                    'value': float(rsi_val),
                })
                
                # Volume data
                volume_data.append({
                    'time': time_obj,
                    'value': float(row['volume']),
                })
                
                # Detect Golden Cross / Death Cross for markers
                # Need both previous and current values to detect cross
                if prev_ma_short is not None and prev_ma_long is not None:
                    if ma_short_val is not None and ma_long_val is not None:
                        # Golden Cross: MA short crosses above MA long
                        if prev_ma_short <= prev_ma_long and ma_short_val > ma_long_val:
                            markers.append({
                                'time': time_obj,
                                'position': 'belowBar',
                                'color': '#2196F3',
                                'shape': 'arrowUp',
                                'text': 'Golden Cross (Buy)',
                            })
                            golden_cross_count += 1
                        # Death Cross: MA short crosses below MA long
                        elif prev_ma_short >= prev_ma_long and ma_short_val < ma_long_val:
                            markers.append({
                                'time': time_obj,
                                'position': 'aboveBar',
                                'color': '#e91e63',
                                'shape': 'arrowDown',
                                'text': 'Death Cross (Sell)',
                            })
                            death_cross_count += 1
                
                # Update previous values for next iteration
                if ma_short_val is not None:
                    prev_ma_short = ma_short_val
                if ma_long_val is not None:
                    prev_ma_long = ma_long_val
            
            _logger.info(f'Chart data prepared: {len(candlestick_data)} candles, {len(ma_short_data)} SMA short, {len(ma_long_data)} SMA long')
            
            return {
                'success': True,
                'candlestick_data': candlestick_data,
                'ma_short_data': ma_short_data,
                'ma_long_data': ma_long_data,
                'rsi_data': rsi_data,
                'volume_data': volume_data,
                'markers': markers,
                'symbol': symbol,
                'market': market,
                # Dynamic values from strategy
                'ma_short_period': strategy.ma_short_period or 50,
                'ma_long_period': strategy.ma_long_period or 200,
            }
            
        except Exception as e:
            _logger.error(f'Lightweight charts data preparation error: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}





