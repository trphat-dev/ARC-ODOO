from odoo import http
from odoo.http import request
import json
from datetime import datetime
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access
from ..utils.timezone_utils import format_datetime_user_tz, format_date_user_tz

class TransactionsPendingController(http.Controller):

    @http.route('/transaction_management/pending', type='http', auth='user', website=True)
    @require_module_access('transaction_management')
    def transaction_management_page(self, **kw):
        # Lấy dữ liệu thật từ model portfolio.transaction của user hiện tại - chỉ lấy các giao dịch pending TRONG NGÀY
        # Logic: Qua ngày mới, lệnh pending cũ sẽ ẩn khỏi list pending (coi như hết hạn hoặc chuyển lịch sử log)
        # Sử dụng create_date hoặc created_at >= đầu ngày hiện tại (theo giờ server/UTC cho đơn giản, hoặc user TZ)
        from odoo.fields import Date, Datetime
        today = Date.context_today(request.env.user)
        # Convert date to datetime at min time (users timezone aware usually handled by context_today)
        # However for search, we need generic comparison.
        # Simple approach: Search based on date string comparison if possible, or datetime
        
        # Determine start of day in UTC roughly or just check current day
        # Since stock market sessions are defined, usually "New Day" implies created >= today 00:00
        
        # We will filter by created_at >= today 00:00 (user time)
        # For simplicity in controller, we can use create_date >= today
        
        transactions = request.env['portfolio.transaction'].search([
            ('investment_type', '=', 'fund_certificate'),
            ('status', '=', 'pending'),
            ('user_id', '=', request.env.user.id),
            ('create_date', '>=', Date.today()) # Show only orders created today
        ], order='create_date desc')

        # Hàm chuyển đổi loại giao dịch đồng bộ với widget
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

        orders = []
        for transaction in transactions:

            buy_date = ''
            holding_days = ''
            sell_fee = ''
            buy_order = None # Reset for each iteration

            # Chỉ tính cho lệnh bán
            if transaction.transaction_type == 'sell':
                # Lấy ngày giao dịch từ created_at hoặc create_date
                tx_date = transaction.created_at if getattr(transaction, 'created_at', False) else transaction.create_date
                if tx_date:
                    # Tìm lệnh mua gần nhất trước ngày bán
                    domain = [
                        ('user_id', '=', request.env.user.id),
                        ('fund_id', '=', transaction.fund_id.id),
                        ('transaction_type', '=', 'buy'),
                    ]
                    # Thêm điều kiện ngày: ưu tiên created_at, nếu không có thì dùng create_date
                    if getattr(transaction, 'created_at', False):
                        domain.append(('created_at', '<=', tx_date))
                    else:
                        domain.append(('create_date', '<=', tx_date))
                    
                    buy_order = request.env['portfolio.transaction'].search(
                        domain,
                        order='created_at desc, create_date desc',
                        limit=1
                    )
                    if buy_order:
                        buy_order_date = buy_order.created_at if getattr(buy_order, 'created_at', False) else buy_order.create_date
                        if buy_order_date:
                            buy_date = format_date_user_tz(request.env, buy_order_date, '%d/%m/%Y')
                            # Tính số ngày giữa hai ngày
                            tx_date_only = tx_date.date() if hasattr(tx_date, 'date') else tx_date
                            buy_date_only = buy_order_date.date() if hasattr(buy_order_date, 'date') else buy_order_date
                            holding_days = (tx_date_only - buy_date_only).days
                amount = transaction.amount
                if amount < 10000000:
                    sell_fee = int(amount * 0.003)
                elif amount < 20000000:
                    sell_fee = int(amount * 0.002)
                else:
                    sell_fee = int(amount * 0.001)

            partner = request.env.user.partner_id
            account_number = ''
            if partner:
                status_info = request.env['status.info'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                account_number = status_info.account_number if status_info else ''
            
            # Logic Hợp đồng:
            # - Với lệnh bán: Dùng hợp đồng của lệnh mua tương ứng (nếu có)
            # - Với các lệnh khác: Dùng chính nó
            target_tx = transaction
            if transaction.transaction_type == 'sell' and buy_order:
                target_tx = buy_order

            contract_name = ''
            contract_filename = ''
            
            # Kiểm tra xem có hợp đồng không (file trực tiếp hoặc signed contract)
            has_contract = bool(getattr(target_tx, 'contract_file', False))
            
            # Nếu chưa có file trực tiếp, kiểm tra trong fund.signed.contract
            if not has_contract:
                try:
                    Investment = request.env['portfolio.investment'].sudo()
                    candidate_inv = Investment.search([
                        ('user_id', '=', target_tx.user_id.id if target_tx.user_id else 0),
                        ('fund_id', '=', target_tx.fund_id.id if target_tx.fund_id else 0),
                    ], limit=1, order='id desc')
                    
                    domain_contract = []
                    if candidate_inv:
                        domain_contract = [('investment_id', '=', candidate_inv.id)]
                    else:
                        partner_id = target_tx.user_id.partner_id.id if target_tx.user_id and target_tx.user_id.partner_id else None
                        if partner_id:
                            domain_contract = [('partner_id', '=', partner_id)]
                    
                    if domain_contract:
                        signed_contract = request.env['fund.signed.contract'].sudo().search(domain_contract, limit=1, order='id desc')
                        if signed_contract:
                            has_contract = True
                            contract_name = signed_contract.name or ''
                            contract_filename = signed_contract.filename or (target_tx.name and f"{target_tx.name}.pdf") or ''
                except Exception:
                    pass
            else:
                contract_filename = (target_tx.name and f"{target_tx.name}.pdf") or ''

            # Setup URLs dùng target_tx
            contract_url = f"/transaction_management/contract/{target_tx.id}" if has_contract else ''
            contract_download_url = f"/transaction_management/contract/{target_tx.id}?download=1" if has_contract else ''

            nav_value = get_nav_value(transaction)
            # Lấy executions (matched orders) nếu có
            executions = []
            try:
                MatchedOrder = request.env['transaction.matched.orders'].sudo()
                if transaction.transaction_type == 'buy':
                    matched_records = MatchedOrder.search([('buy_order_id', '=', transaction.id)])
                else:
                    matched_records = MatchedOrder.search([('sell_order_id', '=', transaction.id)])
                
                for rec in matched_records:
                    executions.append({
                        'id': rec.id,
                        'matched_quantity': float(rec.matched_quantity or 0),
                        'matched_price': float(rec.matched_price or 0),
                        'total_value': float(rec.total_value or 0),
                        'match_date': format_datetime_user_tz(request.env, rec.match_date, '%d/%m/%Y, %H:%M') if rec.match_date else '',
                    })
            except Exception:
                pass

            # Calculate T+2 date (Time stock arrives)
            t2_date_str = ''
            if transaction.status == 'filled' or transaction.exchange_status == 'filled' or transaction.status == 'pending':
                # Simplified T+2 business day logic
                # For more accuracy, should use a calendar module or T+2 API
                try:
                    base_date = transaction.created_at if getattr(transaction, 'created_at', False) else transaction.create_date
                    if base_date:
                        # Convert to date
                        d = base_date.date()
                        # Simple logic: +2 days, handle weekends vaguely (just for display)
                        # Better: checking user timezone
                        import datetime
                        # Add 2 days
                        arrival_date = d + datetime.timedelta(days=2)
                        # If weekend, push further (naive)
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
                'price': round(float(getattr(transaction, 'price', 0) or 0)),  # Giá đơn vị
                'amount': round(max(float(transaction.amount or 0) - float(getattr(transaction, 'fee', 0) or 0), 0)),  # Raw number
                'session_date': format_date_user_tz(request.env, transaction.created_at if getattr(transaction, 'created_at', False) else (transaction.create_date if transaction.create_date else None), '%d/%m/%Y') or "N/A",
                'status': get_status_display(transaction.status),
                'status_detail': transaction.description or 'Chờ xác nhận tiền',
                'transaction_type': get_transaction_type_display(transaction.transaction_type),
                'units': round(float(transaction.units or 0)),  # Raw number for frontend formatting
                'fund_ticker': transaction.fund_id.ticker if transaction.fund_id else '',
                'currency': transaction.currency_id.symbol if transaction.currency_id else 'đ',
                'buy_date': buy_date,
                'holding_days': holding_days,
                'sell_fee': sell_fee,
                'has_contract': has_contract,
                'contract_url': contract_url,
                'contract_download_url': contract_download_url,
                'contract_name': contract_name,
                'contract_filename': contract_filename,
                'executions': executions,
                't2_date': t2_date_str, # Time stock arrives (T+2)
                'order_mode': transaction.order_mode or '', # Normal / Negotiated
                'order_type_detail': transaction.order_type_detail or '', # LO, ATC...
                'market': transaction.market or '',
                'investment_type': transaction.investment_type or '',
            })

        orders_json = json.dumps(orders, ensure_ascii=False)
        return request.render('transaction_management.transaction_management_page', {
            'orders_json': orders_json,
        })

    @http.route('/transaction_management/cancel_order', type='json', auth='user', methods=['POST'])
    @require_module_access('transaction_management')
    def cancel_order(self, order_id=None, **kw):
        """Cancel a pending order"""
        try:
            if not order_id:
                return {'success': False, 'message': 'Thiếu mã lệnh'}
            
            # Find and validate the order
            order = request.env['portfolio.transaction'].sudo().browse(int(order_id))
            
            if not order or not order.exists():
                return {'success': False, 'message': 'Không tìm thấy lệnh'}
            
            # Check if order belongs to current user
            if order.user_id.id != request.env.user.id:
                return {'success': False, 'message': 'Không có quyền huỷ lệnh này'}
            
            # Check if order is pending
            if order.status != 'pending':
                return {'success': False, 'message': 'Chỉ có thể huỷ lệnh đang chờ xử lý'}
            
            # Cancel the order
            order.write({'status': 'cancelled'})
            
            return {'success': True, 'message': 'Huỷ lệnh thành công'}
            
        except Exception as e:
            return {'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}
