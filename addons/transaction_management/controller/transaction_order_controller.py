from odoo import http
from odoo.http import request
import json
import base64
import os
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access
from ..utils.timezone_utils import format_datetime_user_tz, format_date_user_tz

class TransactionOrderController(http.Controller):

    @http.route('/transaction_management/order', type='http', auth='user', website=True)
    @require_module_access('transaction_management')
    def transaction_order_page(self, **kw):
        # Lấy dữ liệu thật từ model portfolio.transaction của user hiện tại
        # Logic: History bao gồm các lệnh đã hoàn thành HOẶC các lệnh pending nhưng đã qua ngày
        from odoo.fields import Date
        from datetime import datetime, time
        
        # Build domain: (status=completed) OR (status=pending AND create_date < today)
        # Note: XML-RPC doesn't support generic OR on search easily inside the domain list without prefix syntax
        # Using Odoo's normalized domain ['|', (A), (B)]
        
        today = Date.context_today(request.env.user)
        
        transactions = request.env['portfolio.transaction'].search([
            ('investment_type', '=', 'fund_certificate'),
            ('user_id', '=', request.env.user.id),
            '|',
            ('status', '=', 'completed'),
            '&', ('status', '=', 'pending'), ('create_date', '<', Date.today())
        ], order='create_date desc')

        # Hàm chuyển đổi loại giao dịch (đồng bộ với widget: buy/sell/exchange)
        def get_transaction_type_display(type):
            type_map = {
                'buy': 'buy',
                'sell': 'sell',
                'exchange': 'exchange'
            }
            return type_map.get(type, type)

        # Hàm chuyển đổi trạng thái
        def get_status_display(status):
            status_map = {
                'pending': 'Chờ khớp lệnh',
                'completed': 'Đã khớp lệnh',
                'cancelled': 'Đã hủy'
            }
            return status_map.get(status, status)

        # Không cần kiểm tra field cũ nữa vì đã chuyển sang fund.signed.contract

        # Helper: lấy NAV - ưu tiên price (giá đặt), sau đó current_nav, fund.current_nav
        def get_nav_value(tx):
            try:
                # Ưu tiên: price (giá khớp) > current_nav (NAV tại thời điểm giao dịch) > fund.current_nav
                if getattr(tx, 'price', None) and float(tx.price) > 0:
                    return float(tx.price)
                if getattr(tx, 'current_nav', None) and float(tx.current_nav) > 0:
                    return float(tx.current_nav)
                fund = tx.fund_id
                if fund and getattr(fund, 'current_nav', None) and float(fund.current_nav) > 0:
                    return float(fund.current_nav)
                cert = fund.certificate_id if fund else None
                if cert and getattr(cert, 'initial_certificate_price', None):
                    return float(cert.initial_certificate_price)
            except Exception:
                pass
            return 0.0

        # Helper: lấy contract từ fund.signed.contract
        SignedContract = request.env['fund.signed.contract'].sudo()

        orders = []
        for transaction in transactions:
            partner = request.env.user.partner_id
            account_number = ''
            if partner:
                status_info = request.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                account_number = status_info.account_number if status_info else ''

            # Contract logic: Ưu tiên transaction_id, sau đó investment_id
            contract = SignedContract.get_contract_by_transaction(transaction.id)
            
            # Nếu là lệnh bán, tìm hợp đồng từ lệnh mua liên quan
            if not contract and transaction.transaction_type == 'sell':
                buy_orders = request.env['portfolio.transaction'].sudo().search([
                    ('user_id', '=', transaction.user_id.id),
                    ('fund_id', '=', transaction.fund_id.id),
                    ('transaction_type', '=', 'buy'),
                    ('status', '=', 'completed'),
                ], order='create_date desc')
                for buy_order in buy_orders:
                    contract = SignedContract.get_contract_by_transaction(buy_order.id)
                    if contract:
                        break
            
            # Fallback: tìm theo investment
            if not contract:
                Investment = request.env['portfolio.investment'].sudo()
                candidate_inv = Investment.search([
                    ('user_id', '=', transaction.user_id.id if transaction.user_id else 0),
                    ('fund_id', '=', transaction.fund_id.id if transaction.fund_id else 0),
                ], limit=1, order='id desc')
                if candidate_inv:
                    contract = SignedContract.search([('investment_id', '=', candidate_inv.id)], limit=1, order='id desc')

            has_contract = bool(contract)
            contract_url = f"/transaction_management/contract/{transaction.id}" if has_contract else ''
            contract_download_url = f"/transaction_management/contract/{transaction.id}?download=1" if has_contract else ''
            contract_id = contract.id if contract else None
            contract_name = contract.name if contract else ''
            contract_filename = contract.filename if contract else ''

            nav_value = get_nav_value(transaction)
            
            # Xác định session_date
            session_date_obj = (transaction.date_end if hasattr(transaction, 'date_end') and transaction.date_end else None) or (transaction.created_at if hasattr(transaction, 'created_at') and transaction.created_at else None) or transaction.create_date
            session_date_str = format_date_user_tz(request.env, session_date_obj, '%d/%m/%Y') if session_date_obj else "N/A"
            
            # Lấy executions (matched orders) nếu có
            executions = []
            MatchedOrder = request.env['transaction.matched.orders'].sudo()
            if transaction.transaction_type == 'buy':
                matched_records = MatchedOrder.search([('buy_order_id', '=', transaction.id)])
            else:
                matched_records = MatchedOrder.search([('sell_order_id', '=', transaction.id)])
            
            for rec in matched_records:
                counter_tx = rec.sell_order_id if transaction.transaction_type == 'buy' else rec.buy_order_id
                executions.append({
                    'id': rec.id,
                    'matched_quantity': float(rec.matched_quantity or 0),
                    'matched_price': float(rec.matched_price or 0),
                    'total_value': float(rec.total_value or 0),
                    'match_date': format_datetime_user_tz(request.env, rec.match_date, '%d/%m/%Y, %H:%M') if rec.match_date else '',
                    'counter_investor': counter_tx.user_id.name if counter_tx and counter_tx.user_id else 'N/A',
                    'counter_type': counter_tx.transaction_type if counter_tx else '',
                })

            # Get actual values from transaction record
            raw_amount = float(transaction.amount or 0)
            raw_fee = float(getattr(transaction, 'fee', 0) or 0)
            
            # Calculate T+2 date (Time stock arrives)
            t2_date_str = ''
            if transaction.status == 'filled' or transaction.exchange_status == 'filled' or transaction.status == 'completed' or transaction.status == 'pending':
                try:
                    base_date = transaction.created_at if getattr(transaction, 'created_at', False) else transaction.create_date
                    if base_date:
                        d = base_date.date()
                        import datetime
                        # Add 2 days, naive logic
                        arrival_date = d + datetime.timedelta(days=2)
                        if arrival_date.weekday() >= 5: # Sat or Sun
                            arrival_date += datetime.timedelta(days=2)
                        
                        t2_date_str = format_date_user_tz(request.env, arrival_date, '%d/%m/%Y')
                except Exception:
                    pass

            orders.append({
                'id': transaction.id,
                'account_number': account_number,
                'fund_name': transaction.fund_id.name if transaction.fund_id else '',
                'order_date': format_datetime_user_tz(request.env, transaction.created_at if getattr(transaction, 'created_at', False) else (transaction.create_date if transaction.create_date else None), '%d/%m/%Y, %H:%M') or '',
                'order_code': transaction.name or f"TX{transaction.id:06d}",
                'nav': round(nav_value),  # Raw number for frontend formatting
                'amount': round(raw_amount),  # Original investment amount
                'fee': round(raw_fee),  # Actual fee from record
                'session_date': session_date_str,
                'status': get_status_display(transaction.status),
                'status_detail': transaction.description or 'Hoàn thành' if transaction.status == 'completed' else 'Chờ xử lý',
                'transaction_type': get_transaction_type_display(transaction.transaction_type),
                'units': round(float(transaction.units or 0)),
                'fund_ticker': transaction.fund_id.ticker if transaction.fund_id else '',
                'currency': transaction.currency_id.symbol if transaction.currency_id else 'đ',
                'has_contract': has_contract,
                'contract_id': contract_id,
                'contract_url': contract_url,
                'contract_download_url': contract_download_url,
                'contract_name': contract_name,
                'contract_filename': contract_filename,
                'executions': executions,
                't2_date': t2_date_str, # Time stock arrives (T+2)
                'order_mode': transaction.order_mode or '',
                'order_type_detail': transaction.order_type_detail or '',
                'market': transaction.market or '',
                'investment_type': transaction.investment_type or '',
            })

        orders_json = json.dumps(orders, ensure_ascii=False)
        return request.render('transaction_management.transaction_order_page', {
            'orders_json': orders_json,
        }) 

    @http.route('/transaction_management/contract/<int:tx_id>', type='http', auth='user')
    @require_module_access('transaction_management')
    def transaction_contract(self, tx_id, download=False, **kw):
        # Tìm transaction
        transaction = request.env['portfolio.transaction'].sudo().browse(tx_id)
        if not transaction or not transaction.exists():
            return request.not_found()

        SignedContract = request.env['fund.signed.contract'].sudo()
        
        # Priority 1: Get by transaction_id using same logic as has_contract
        signed_contract = SignedContract.get_contract_by_transaction(transaction.id)
        
        # Priority 2: For sell orders, get contract from related buy order
        if not signed_contract and transaction.transaction_type == 'sell':
            buy_orders = request.env['portfolio.transaction'].sudo().search([
                ('user_id', '=', transaction.user_id.id),
                ('fund_id', '=', transaction.fund_id.id),
                ('transaction_type', '=', 'buy'),
                ('status', '=', 'completed'),
            ], order='create_date desc')
            for buy_order in buy_orders:
                signed_contract = SignedContract.get_contract_by_transaction(buy_order.id)
                if signed_contract:
                    break
        
        # Priority 3: Fallback to investment
        if not signed_contract:
            Investment = request.env['portfolio.investment'].sudo()
            candidate_inv = Investment.search([
                ('user_id', '=', transaction.user_id.id if transaction.user_id else 0),
                ('fund_id', '=', transaction.fund_id.id if transaction.fund_id else 0),
            ], limit=1, order='id desc')
            if candidate_inv:
                signed_contract = SignedContract.search([('investment_id', '=', candidate_inv.id)], limit=1, order='id desc')

        if not signed_contract or not signed_contract.exists() or not signed_contract.file_data:
            return request.not_found()

        headers = [
            ('Content-Type', 'application/pdf'),
            ('X-Content-Type-Options', 'nosniff'),
        ]

        filename = signed_contract.filename or f"contract_{tx_id}.pdf"
        if str(download).lower() in ('1', 'true', 'yes'):
            headers.append(('Content-Disposition', f'attachment; filename="{filename}"'))
        else:
            headers.append(('Content-Disposition', f'inline; filename="{filename}"'))

        try:
            data = base64.b64decode(signed_contract.file_data)
            return request.make_response(data, headers=headers)
        except Exception:
            return request.not_found()