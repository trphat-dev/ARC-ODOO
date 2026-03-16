from odoo import fields, _
import logging
from datetime import datetime
from ssi_fc_data import model


_logger = logging.getLogger(__name__)

# Config keys & defaults
_TARGET_SYMBOLS_KEY = 'ssi.realtime.target_symbols'
_MAX_OHLC_SYMBOLS_KEY = 'ssi.ohlc.max_symbols'
_DEFAULT_MAX_OHLC_SYMBOLS = 5


def fetch_all_ohlc(wizard, client, sdk_config):
    securities_model = wizard.env['ssi.securities']
    daily_ohlc_model = wizard.env['ssi.daily.ohlc']
    intraday_ohlc_model = wizard.env['ssi.intraday.ohlc']

    domain = [('is_active', '=', True)]
    max_symbols = _DEFAULT_MAX_OHLC_SYMBOLS

    try:
        if getattr(wizard, 'symbol', False):
            # Prioritize symbols entered in wizard
            manual_symbols = [s.strip().upper() for s in wizard.symbol.split(',') if s.strip()]
            if manual_symbols:
                domain.append(('symbol', 'in', manual_symbols))
                max_symbols = None  # Bypass limit when symbols are explicitly requested
                _logger.debug("Fetch OHLC: Using manual target symbols: %s", ', '.join(manual_symbols))
        else:
            # Fallback to system config
            icp = wizard.env['ir.config_parameter'].sudo()
            symbols_str = icp.get_param(_TARGET_SYMBOLS_KEY, default='')
            if symbols_str and symbols_str.strip():
                target_symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
                if target_symbols:
                    domain.append(('symbol', 'in', target_symbols))
                    _logger.debug("Using configured target symbols: %s", ', '.join(target_symbols))

            max_symbols_raw = icp.get_param(_MAX_OHLC_SYMBOLS_KEY, default=str(_DEFAULT_MAX_OHLC_SYMBOLS))
            try:
                max_symbols_val = int(max_symbols_raw or _DEFAULT_MAX_OHLC_SYMBOLS)
                if max_symbols_val >= 1:
                    max_symbols = max_symbols_val
            except Exception:
                _logger.debug("Invalid max OHLC symbols config '%s', using default %s", max_symbols_raw, _DEFAULT_MAX_OHLC_SYMBOLS)
    except Exception:
        _logger.debug("Error reading target symbols / max symbols config, using defaults")

    securities = securities_model.search(domain, order='symbol asc', limit=max_symbols)
    if not securities:
        _logger.warning("Không tìm thấy chứng khoán nào để fetch OHLC")
        return
    
    _logger.debug("Bắt đầu fetch OHLC cho %d mã chứng khoán", len(securities))

    daily_success = 0
    intraday_success = 0
    error_count = 0

    to_date = getattr(wizard, 'to_date', None) or fields.Date.today()
    from_date = getattr(wizard, 'from_date', None) or to_date
    _today = fields.Date.today()

    from datetime import timedelta
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days) + 1):
            yield start_date + timedelta(n)

    for security in securities:
        try:
            _logger.debug("Fetching OHLC for symbol: %s (ID: %s)", security.symbol, security.id)

            # 1. Fetch Daily OHLC for the range
            daily_req = model.daily_ohlc(
                symbol=security.symbol,
                fromDate=from_date.strftime('%d/%m/%Y'),
                toDate=to_date.strftime('%d/%m/%Y'),
                pageIndex=1,
                pageSize=100,
                ascending=True
            )
            daily_response = client.daily_ohlc(sdk_config, daily_req)
            if daily_response.get('status') == 'Success' and daily_response.get('data'):
                daily_items = daily_response['data'] if isinstance(daily_response['data'], list) else []
                for item in daily_items:
                    date_str = item.get('Date', '')
                    if date_str:
                        try:
                            try: date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except ValueError: date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                        except Exception: date_obj = from_date
                    else: date_obj = from_date

                    existing = daily_ohlc_model.search([('security_id', '=', security.id), ('date', '=', date_obj)], limit=1)
                    
                    def _get_value(payload, *keys, default=0.0):
                        for k in keys:
                            val = payload.get(k)
                            if val is not None and val != '':
                                try: return float(val)
                                except (ValueError, TypeError): continue
                        return default
                    
                    values = {
                        'security_id': security.id,
                        'date': date_obj,
                        'open_price': _get_value(item, 'Open', 'open', default=0.0),
                        'high_price': _get_value(item, 'High', 'high', default=0.0),
                        'low_price': _get_value(item, 'Low', 'low', default=0.0),
                        'close_price': _get_value(item, 'Close', 'close', default=0.0),
                        'volume': _get_value(item, 'Volume', 'volume', 'TotalVolume', default=0.0),
                        'value': _get_value(item, 'TotalValue', 'totalValue', default=0.0),
                        'change': _get_value(item, 'Change', 'change', default=0.0),
                        'change_percent': _get_value(item, 'ChangePercent', 'changePercent', default=0.0),
                        'previous_close': _get_value(item, 'PreviousClose', 'previousClose', default=0.0),
                        'last_update': fields.Datetime.now(),
                    }

                    if existing: existing.write(values)
                    else: daily_ohlc_model.create(values)
                    daily_success += 1

            # 2. Fetch Intraday OHLC for each day in range
            for single_date in daterange(from_date, to_date):
                _logger.debug("Fetching Intraday OHLC for %s on %s", security.symbol, single_date)
                current_page = 1
                page_size = getattr(wizard, 'page_size', None) or 500
                total_day_saved = 0
                while True:
                    intraday_req = model.intraday_ohlc(
                        symbol=security.symbol,
                        fromDate=single_date.strftime('%d/%m/%Y'),
                        toDate=single_date.strftime('%d/%m/%Y'),
                        pageIndex=current_page,
                        pageSize=page_size,
                        ascending=True,
                        resolution=1
                    )
                    intraday_response = client.intraday_ohlc(sdk_config, intraday_req)
                    if intraday_response.get('status') != 'Success' or not intraday_response.get('data'):
                        break
                    intraday_items = intraday_response['data'] if isinstance(intraday_response['data'], list) else []
                    if not intraday_items:
                        break
                    for item in intraday_items:
                        time_str = item.get('Time', '') or item.get('time', '') or '00:00'
                        existing_intra = intraday_ohlc_model.search([
                            ('security_id', '=', security.id),
                            ('date', '=', single_date),
                            ('time', '=', time_str)
                        ], limit=1)

                        def _get_val(payload, *keys, default=0.0):
                            for k in keys:
                                val = payload.get(k)
                                if val is not None and val != '':
                                    try: return float(val)
                                    except: continue
                            return default
                        
                        intra_values = {
                            'security_id': security.id,
                            'date': single_date,
                            'time': time_str,
                            'open_price': _get_val(item, 'Open', 'open'),
                            'high_price': _get_val(item, 'High', 'high'),
                            'low_price': _get_val(item, 'Low', 'low'),
                            'close_price': _get_val(item, 'Close', 'close'),
                            'volume': _get_val(item, 'Volume', 'volume', 'MatchVolume'),
                            'total_value': _get_val(item, 'TotalValue', 'totalValue'),
                            'resolution': int(item.get('Resolution', 1)),
                        }

                        if existing_intra: existing_intra.write(intra_values)
                        else: intraday_ohlc_model.create(intra_values)
                        total_day_saved += 1
                    current_page += 1
                    if current_page > 10: break # Safety break
                if total_day_saved:
                    intraday_success += 1
                try: wizard.env.cr.commit()
                except Exception: pass

            # 3. Stock Price Enrichment
            try:
                price_req = model.daily_stock_price(
                    symbol=security.symbol,
                    fromDate=from_date.strftime('%d/%m/%Y'),
                    toDate=to_date.strftime('%d/%m/%Y'),
                    pageIndex=1, market=security.market
                )
                price_resp = client.daily_stock_price(sdk_config, price_req)
                if price_resp.get('status') == 'Success' and price_resp.get('data'):
                    price_items = price_resp['data'] if isinstance(price_resp['data'], list) else []
                    if price_items:
                        p = price_items[0]
                        security.write({
                            'reference_price': p.get('ReferencePrice', security.reference_price),
                            'ceiling_price': p.get('CeilingPrice', security.ceiling_price),
                            'floor_price': p.get('FloorPrice', security.floor_price),
                        })
            except Exception: pass
        except Exception as e:
            _logger.error("Error fetching OHLC for %s: %s", security.symbol, str(e))
            error_count += 1
            continue

    # Update wizard result
    try:
        wizard.sudo().write({'last_count': total_count})
    except Exception:
        _logger.debug("Skip writing last_count due to transaction state", exc_info=True)

    try:
        wizard._push_notice('Auto Fetch', _('OHLC fetched for %s symbols (daily: %s, intraday: %s, errors: %s)') % (
            total_count, daily_success, intraday_success, error_count
        ), 'success')
    except Exception:
        pass


