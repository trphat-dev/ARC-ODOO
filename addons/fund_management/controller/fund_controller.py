from odoo import http
from odoo.http import request, Response
import json
from datetime import datetime, timedelta, timezone
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access


class FundController(http.Controller):

    @http.route('/data_fund', type='http', auth='public', cors='*')
    def get_funds(self):
        """Get all funds data"""
        funds = request.env['portfolio.fund'].sudo().search([])
        
        result = [
            {
                "id": fund.id,
                "ticker": fund.ticker,
                'name': fund.name,
                'description': fund.description,
                'current_nav': fund.current_nav,
                'low_price': fund.low_price,
                'high_price': fund.high_price,
                'open_price': fund.open_price,
                'reference_price': fund.reference_price,
                'ceiling_price': fund.ceiling_price,
                'floor_price': fund.floor_price,
                'investment_type': fund.investment_type,
                'nav_history_json': fund.nav_history_json,
                # expose color so frontend can use the actual fund color
                'color': getattr(fund, 'color', None) or getattr(fund, 'fund_color', None),
                # market dynamics
                'change': getattr(fund, 'change', 0.0) or 0.0,
                'change_percent': getattr(fund, 'change_percent', 0.0) or 0.0,
                'volume': getattr(fund, 'volume', 0.0) or 0.0,
            }
            for fund in funds
        ]

        return Response(
            json.dumps(result),
            content_type='application/json'
        )

    @http.route('/fund_widget', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_widget_page(self, **kwargs):
        """Fund widget page"""
        return request.render('fund_management.assets_fund_widget_page')

    @http.route('/fund_compare', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_compare_page(self, **kwargs):
        """Fund comparison page"""
        return request.render('fund_management.assets_fund_compare')

    @http.route('/fund_buy', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_buy_page(self, **kwargs):
        """Fund buying page"""
        return request.render('fund_management.fund_buy')

    @http.route('/fund_confirm', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_confirm_page(self, **kwargs):
        """Fund confirmation page"""
        return request.render('fund_management.fund_confirm')

    @http.route('/fund_result', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_result_page(self, **kwargs):
        """Fund result page"""
        return request.render('fund_management.fund_result')

    @http.route('/fund_sell', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_sell_page(self, **kwargs):
        """Fund selling page"""
        return request.render('fund_management.fund_sell')

    @http.route('/fund_sell_confirm', type='http', auth='user', website=True)
    @require_module_access('fund_management')
    def fund_sell_confirm(self, **kwargs):
        """Fund sell confirmation page"""
        return request.render('fund_management.fund_sell_confirm')

    @http.route('/api/fund/calc', type='http', auth='user', methods=['GET'], csrf=False)
    @require_module_access('fund_management')
    def fund_calc(self):
        """Get fund calculation data"""
        try:
            term_rates = request.env['nav.term.rate'].sudo().search([
                ('active', '=', True)
            ], order='term_months asc')
            
            result = [
                {
                    'month': rate.term_months,
                    'interest_rate': rate.interest_rate,
                }
                for rate in term_rates
            ]
            
            return Response(
                json.dumps(result),
                content_type='application/json'
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in fund_calc: {e}", exc_info=True)
            return Response(
                json.dumps({'error': 'Internal server error'}),
                content_type='application/json',
                status=500
            )

    @http.route('/fund_ohlc', type='http', auth='user', methods=['GET'], csrf=False)
    @require_module_access('fund_management')
    def fund_ohlc(self, **kwargs):
        """Return OHLC data for a given ticker and range.
        Query params:
          - ticker: symbol/ticker to fetch
          - range: one of 1D,5D,1M,3M,6M,1Y (defaults to 1M)
          - fromDate, toDate: optional (YYYY-MM-DD). If provided, override range window
        """
        try:
            ticker = (kwargs.get('ticker') or '').strip().upper()
            range_key = (kwargs.get('range') or '1M').upper()
            from_date_str = (kwargs.get('fromDate') or '').strip()
            to_date_str = (kwargs.get('toDate') or '').strip()
            if not ticker:
                return Response(json.dumps({'error': 'Missing ticker'}), content_type='application/json', status=400)

            # Determine date range
            today = datetime.utcnow().date()
            if from_date_str and to_date_str:
                try:
                    from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                    to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                except Exception:
                    return Response(json.dumps({'error': 'Invalid fromDate/toDate'}), content_type='application/json', status=400)
            elif range_key == '1Y':
                from_date = today - timedelta(days=365)
            elif range_key == '6M':
                from_date = today - timedelta(days=182)
            elif range_key == '3M':
                from_date = today - timedelta(days=91)
            elif range_key == '5D':
                from_date = today - timedelta(days=5)
            elif range_key == '1D':
                from_date = today - timedelta(days=1)
            else:
                from_date = today - timedelta(days=31)
            to_date = locals().get('to_date', today)

            data = []
            if range_key == '1D':
                # Prefer intraday OHLC for 1D if available
                try:
                    intraday_model = request.env['ssi.intraday.ohlc'].sudo()
                    # Search by symbol (related field) and date
                    intraday_records = intraday_model.search([
                        ('symbol', '=', ticker),
                        ('date', '>=', from_date),
                        ('date', '<=', to_date),
                    ], order='date asc, time asc')
                    
                    for r in intraday_records:
                        # Parse time string to datetime
                        time_str = getattr(r, 'time', '') or ''
                        date_obj = getattr(r, 'date', None)
                        
                        if not date_obj:
                            continue
                        
                        # Parse time string (format: HH:MM:SS or HH:MM)
                        dt = None
                        if time_str:
                            try:
                                # Try parsing HH:MM:SS or HH:MM format
                                time_parts = time_str.split(':')
                                if len(time_parts) >= 2:
                                    hour = int(time_parts[0])
                                    minute = int(time_parts[1])
                                    second = int(time_parts[2]) if len(time_parts) > 2 else 0
                                    dt = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute, second=second))
                            except (ValueError, IndexError):
                                # Fallback to start of day
                                dt = datetime.combine(date_obj, datetime.min.time())
                        else:
                            # Fallback to start of day if no time
                            dt = datetime.combine(date_obj, datetime.min.time())
                        
                        if not dt:
                            continue
                        
                        # Convert to Unix timestamp (seconds) using explicit VN timezone (UTC+7)
                        vn_tz = timezone(timedelta(hours=7))
                        dt_vn = dt.replace(tzinfo=vn_tz)
                        ts = int(dt_vn.timestamp())
                        
                        data.append({
                            't': ts,
                            'o': float(getattr(r, 'open_price', 0.0) or 0.0),
                            'h': float(getattr(r, 'high_price', 0.0) or 0.0),
                            'l': float(getattr(r, 'low_price', 0.0) or 0.0),
                            'c': float(getattr(r, 'close_price', 0.0) or 0.0),
                            'v': float(getattr(r, 'volume', 0.0) or 0.0),
                        })
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    data = []

            # Fallback or for other ranges: use daily OHLC
            if not data:
                ohlc_model = request.env['ssi.daily.ohlc'].sudo()
                records = ohlc_model.search([
                    ('symbol', '=', ticker),
                    ('date', '>=', from_date),
                    ('date', '<=', to_date),
                ], order='date asc')
                data = [
                    {
                        't': r.date.strftime('%Y-%m-%d'),
                        'o': r.open_price or 0.0,
                        'h': r.high_price or 0.0,
                        'l': r.low_price or 0.0,
                        'c': r.close_price or 0.0,
                        'v': r.volume or 0.0,
                    }
                    for r in records
                ]

            return Response(json.dumps({'status': 'Success', 'data': data}), content_type='application/json')
        except Exception as e:
            return Response(
                json.dumps({'status': 'Error', 'message': 'Internal server error'}),
                content_type='application/json',
                status=500
            )

