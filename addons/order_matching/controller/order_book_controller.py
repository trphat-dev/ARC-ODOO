# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
from odoo.addons.user_permission_management.utils.permission_checker import require_module_access
from ..utils.timezone_utils import format_datetime_user_tz


class OrderBookController(http.Controller):
    """Controller cho trang sổ lệnh giao dịch"""

    @http.route('/order-book', type='http', auth='user', website=True)
    @require_module_access('order_matching')
    def order_book_page(self, **kwargs):
        """Trang sổ lệnh giao dịch"""
        return request.render('order_matching.order_book_page', {
            'title': 'Sổ lệnh giao dịch',
            'page_name': 'order_book'
        })

    @http.route('/completed-orders', type='http', auth='user', website=True)
    @require_module_access('order_matching')
    def completed_orders_page(self, **kwargs):
        return request.render('order_matching.completed_orders_page', {
            'title': 'Khoản đầu tư đã khớp',
            'page_name': 'completed_orders'
        })

    @http.route('/negotiated-orders', type='http', auth='user', website=True)
    @require_module_access('order_matching')
    def negotiated_orders_page(self, **kwargs):
        return request.render('order_matching.negotiated_orders_page', {
            'title': 'Khoản đầu tư khớp theo thỏa thuận',
            'page_name': 'negotiated_orders'
        })

    @http.route('/normal-orders', type='http', auth='user', website=True)
    @require_module_access('order_matching')
    def normal_orders_page(self, **kwargs):
        """Trang quản lý lệnh đặt thường"""
        return request.render('order_matching.normal_orders_page', {
            'title': 'Lệnh đặt thường',
            'page_name': 'normal_orders'
        })

    # ==== API SỔ LỆNH GIAO DỊCH ====
    @http.route('/api/transaction-list/order-book', type='http', auth='public', methods=['POST'], csrf=False)
    def get_order_book(self, **kwargs):
        """Lấy dữ liệu sổ lệnh giao dịch"""
        
        try:
            # Lấy fund_id từ request body
            import json
            request_data = json.loads(request.httprequest.data.decode('utf-8'))
            fund_id = request_data.get('fund_id')
            
            if not fund_id:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Thiếu fund_id"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            Transaction = request.env['portfolio.transaction'].sudo()
            Fund = request.env['portfolio.fund'].sudo()
            
            # Lấy thông tin fund
            fund = Fund.browse(int(fund_id))
            if not fund.exists():
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không tìm thấy fund"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            # Lấy lệnh mua (buy) chỉ trạng thái pending
            # Sắp xếp theo Price-Time Priority CHUẨN Stock Exchange (FIFO):
            # - Buy orders: Giá cao nhất trước, cùng giá thì thời gian sớm nhất trước
            # - Lệnh tốt nhất (ưu tiên cao nhất) sẽ ở đầu danh sách
            # CHUẨN QUỐC TẾ: Lấy TẤT CẢ lệnh pending có remaining_units > 0
            # KHÔNG BAO GIỜ split/clone order - chỉ tạo execution records
            # remaining_units được tính từ executions: remaining = units - sum(executions.matched_quantity)
            buy_orders = Transaction.search([
                ('fund_id', '=', int(fund_id)),
                ('transaction_type', '=', 'buy'),
                ('status', '=', 'pending'),
                ('remaining_units', '>', 0),
                ('order_mode', '=', 'negotiated'),
            ])
            
            # Sắp xếp theo Price-Time Priority để đảm bảo lệnh tốt nhất ở đầu danh sách
            # Sử dụng helper method từ PartialMatchingEngine để tính priority_score
            matching_engine = request.env['transaction.partial.matching.engine']
            buy_orders = sorted(buy_orders, key=lambda o: matching_engine.calculate_priority_score_for_order(o), reverse=True)
            
            # CHUẨN QUỐC TẾ: Lấy TẤT CẢ lệnh pending có remaining_units > 0
            # KHÔNG BAO GIỜ split/clone order - chỉ tạo execution records
            # remaining_units được tính từ executions: remaining = units - sum(executions.matched_quantity)
            sell_orders = Transaction.search([
                ('fund_id', '=', int(fund_id)),
                ('transaction_type', '=', 'sell'),
                ('status', '=', 'pending'),
                ('remaining_units', '>', 0),
                ('order_mode', '=', 'negotiated'),
            ])
            
            # Sắp xếp theo Price-Time Priority để đảm bảo lệnh tốt nhất ở đầu danh sách
            # Sử dụng helper method từ PartialMatchingEngine để tính priority_score
            sell_orders = sorted(sell_orders, key=lambda o: matching_engine.calculate_priority_score_for_order(o), reverse=True)
            
            # Tính thống kê
            total_buy_value = sum(order.price * order.units for order in buy_orders)
            total_sell_value = sum(order.price * order.units for order in sell_orders)
            total_ccq = sum(order.units for order in buy_orders) - sum(order.units for order in sell_orders)
            
            # Tính biến động giá (so với giá trước đó)
            price_change = 0
            price_change_percent = 0
            try:
                # Lấy giá trước đó từ NAV history hoặc fund config
                prev_price = fund.current_nav or 10000
                current_price = fund.current_nav or 10000
                price_change = current_price - prev_price
                if prev_price > 0:
                    price_change_percent = (price_change / prev_price) * 100
            except Exception:
                pass
            
            # CHUẨN QUỐC TẾ: Lấy các lệnh đã khớp một phần từ transaction.matched.orders
            # KHÔNG BAO GIỜ split/clone order - chỉ tạo execution records
            # partial_orders = orders có matched_units > 0 và remaining_units > 0
            # matched_units và remaining_units được tính từ executions (computed fields)
            partial_orders = []
            try:
                # Lấy lệnh mua đã khớp một phần (matched_units > 0 và remaining_units > 0)
                # matched_units = sum(matched_order_ids.matched_quantity) - computed từ executions
                # remaining_units = units - matched_units - computed từ executions
                partial_buy_orders = Transaction.search([
                    ('fund_id', '=', int(fund_id)),
                    ('transaction_type', '=', 'buy'),
                    ('status', '=', 'pending'),
                    ('matched_units', '>', 0),  # Đã khớp một phần
                    ('remaining_units', '>', 0),  # Còn lại chưa khớp
                    ('order_mode', '=', 'negotiated'),
                ], order='created_at asc')
                
                # Lấy lệnh bán đã khớp một phần (matched_units > 0 và remaining_units > 0)
                # matched_units = sum(matched_sell_order_ids.matched_quantity) - computed từ executions
                # remaining_units = units - matched_units - computed từ executions
                partial_sell_orders = Transaction.search([
                    ('fund_id', '=', int(fund_id)),
                    ('transaction_type', '=', 'sell'),
                    ('status', '=', 'pending'),
                    ('matched_units', '>', 0),  # Đã khớp một phần
                    ('remaining_units', '>', 0),  # Còn lại chưa khớp
                    ('order_mode', '=', 'negotiated'),
                ], order='created_at asc')
                
                # Format dữ liệu lệnh mua chưa khớp đủ
                for order in partial_buy_orders:
                    units_total = float(order.units or 0)
                    matched_total = float(order.matched_units or 0)  # Computed từ executions
                    remaining_calculated = float(order.remaining_units or 0)  # Computed từ executions
                    
                    # CHUẨN QUỐC TẾ: Tính toán từ executions, không từ split orders
                    # remaining_units đã được tính chính xác từ units - matched_units (computed field)
                    
                    # Chỉ thêm vào partial_orders nếu còn remaining > 0 (có phần chưa khớp)
                    if remaining_calculated > 0:
                        partial_orders.append({
                            "id": order.id,
                            "user_name": order.user_id.name if order.user_id else "N/A",
                            "transaction_type": order.transaction_type,
                            "price": float(getattr(order, 'price', 0) or 0),
                            "units": units_total,
                            "matched_units": matched_total,  # Từ executions
                            "remaining_units": remaining_calculated,  # Từ executions
                            "amount": float(getattr(order, 'amount', 0) or 0),
                            "status": getattr(order, 'status', 'pending'),
                            "created_at": format_datetime_user_tz(request.env, order.created_at if hasattr(order, 'created_at') and order.created_at else order.create_date) or None,
                            "date_end": format_datetime_user_tz(request.env, order.date_end if hasattr(order, 'date_end') and order.date_end else None) or None,
                            "ccq_remaining": remaining_calculated,
                        })
                
                # Format dữ liệu lệnh bán chưa khớp đủ
                for order in partial_sell_orders:
                    units_total = float(order.units or 0)
                    matched_total = float(order.matched_units or 0)  # Computed từ executions
                    remaining_calculated = float(order.remaining_units or 0)  # Computed từ executions
                    
                    # CHUẨN QUỐC TẾ: Tính toán từ executions, không từ split orders
                    # remaining_units đã được tính chính xác từ units - matched_units (computed field)
                    
                    # Chỉ thêm vào partial_orders nếu còn remaining > 0 (có phần chưa khớp)
                    if remaining_calculated > 0:
                        partial_orders.append({
                            "id": order.id,
                            "user_name": order.user_id.name if order.user_id else "N/A",
                            "transaction_type": order.transaction_type,
                            "price": float(getattr(order, 'price', 0) or 0),
                            "units": units_total,
                            "matched_units": matched_total,  # Từ executions
                            "remaining_units": remaining_calculated,  # Từ executions
                            "amount": float(getattr(order, 'amount', 0) or 0),
                            "status": getattr(order, 'status', 'pending'),
                            "created_at": format_datetime_user_tz(request.env, order.created_at if hasattr(order, 'created_at') and order.created_at else order.create_date) or None,
                            "date_end": format_datetime_user_tz(request.env, order.date_end if hasattr(order, 'date_end') and order.date_end else None) or None,
                            "ccq_remaining": remaining_calculated,
                        })
            except Exception as e:
                # Log lỗi nhưng không dừng quy trình
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning("Error loading partial orders: %s", str(e))

            # CHUẨN QUỐC TẾ: Format dữ liệu theo Price-Time Priority
            # KHÔNG BAO GIỜ split/clone order - chỉ tạo execution records
            # remaining_units được tính từ executions: remaining = units - sum(executions.matched_quantity)
            buy_orders_data = []
            for order in buy_orders:
                # CHUẨN QUỐC TẾ: Tính toán từ executions, không từ split orders
                units_total = float(order.units or 0)
                matched_total = float(order.matched_units or 0)  # Computed từ executions
                remaining_calculated = float(order.remaining_units or 0)  # Computed từ executions
                
                # CHUẨN QUỐC TẾ: KHÔNG BAO GIỜ split/clone order
                # Chỉ tạo execution records, không tạo order mới
                buy_orders_data.append({
                    "id": order.id,
                    "user_name": order.user_id.name if order.user_id else "N/A",
                    "price": float(order.price or 0),
                    "units": units_total,
                    "amount": float(order.amount or 0),
                    "status": order.status,
                    "created_at": format_datetime_user_tz(request.env, order.created_at if hasattr(order, 'created_at') and order.created_at else order.create_date) or None,
                    "date_end": format_datetime_user_tz(request.env, order.date_end if hasattr(order, 'date_end') and order.date_end else None) or None,
                    "ccq_remaining": remaining_calculated,
                    "matched_units": matched_total,  # Từ executions
                    "remaining_units": remaining_calculated,  # Từ executions
                    "priority_score": self._calculate_priority_score(order, 'buy'),
                })
            
            # KHÔNG sắp xếp lại ở đây để giữ nguyên thứ tự đã được tính toán
            # bởi Priority Engine (matching_engine.calculate_priority_score_for_order)
            # Buy orders đã được sort đúng theo Price-Time Priority từ bên trên.
            
            sell_orders_data = []
            for order in sell_orders:
                # CHUẨN QUỐC TẾ: Tính toán từ executions, không từ split orders
                units_total = float(order.units or 0)
                matched_total = float(order.matched_units or 0)  # Computed từ executions
                remaining_calculated = float(order.remaining_units or 0)  # Computed từ executions
                
                # CHUẨN QUỐC TẾ: KHÔNG BAO GIỜ split/clone order
                # Chỉ tạo execution records, không tạo order mới
                sell_orders_data.append({
                    "id": order.id,
                    "user_name": order.user_id.name if order.user_id else "N/A",
                    "price": float(order.price or 0),
                    "units": units_total,
                    "amount": float(order.amount or 0),
                    "status": order.status,
                    "created_at": format_datetime_user_tz(request.env, order.created_at if hasattr(order, 'created_at') and order.created_at else order.create_date) or None,
                    "date_end": format_datetime_user_tz(request.env, order.date_end if hasattr(order, 'date_end') and order.date_end else None) or None,
                    "ccq_remaining": remaining_calculated,
                    "matched_units": matched_total,  # Từ executions
                    "remaining_units": remaining_calculated,  # Từ executions
                    "priority_score": self._calculate_priority_score(order, 'sell'),
                })
            
            # KHÔNG sắp xếp lại ở đây để giữ nguyên thứ tự đã được tính toán
            # bởi Priority Engine (matching_engine.calculate_priority_score_for_order)
            # Sell orders đã được sort đúng theo Price-Time Priority từ bên trên.
            
            fund_info = {
                "id": fund.id,
                "name": fund.name,
                "ticker": fund.ticker,
                "current_nav": fund.current_nav,
                "total_buy_value": total_buy_value,
                "total_sell_value": total_sell_value,
                "total_ccq": total_ccq
            }
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "fund_info": fund_info,
                    "buy_orders": buy_orders_data,
                    "sell_orders": sell_orders_data,
                    "partial_orders": partial_orders,
                    "price_change": price_change,
                    "price_change_percent": price_change_percent,
                    "total_buy_orders": len(buy_orders_data),
                    "total_sell_orders": len(sell_orders_data),
                    "total_partial_orders": len(partial_orders)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            pass
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/funds', type='http', auth='public', methods=['POST'], csrf=False)
    def get_funds(self, **kwargs):
        """Lấy danh sách funds cho dropdown"""
        
        try:
            Fund = request.env['portfolio.fund'].sudo()
            # Tìm tất cả funds, không filter theo status
            funds = Fund.search([])
            
            funds_data = []
            for fund in funds:
                funds_data.append({
                    "id": fund.id,
                    "name": fund.name,
                    "ticker": fund.ticker,
                    "current_nav": fund.current_nav
                })
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "funds": funds_data
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            pass
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    # ==== API COMPLETED TRANSACTIONS ====
    @http.route('/api/transaction-list/completed', type='http', auth='user', methods=['POST'], csrf=False)
    def get_completed_transactions(self, **kwargs):
        """Trả về danh sách giao dịch đã khớp (status=completed) theo fund."""
        try:
            try:
                payload = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            except Exception:
                payload = {}
            fund_id = payload.get('fund_id')
            limit = int(payload.get('limit') or 500)
            if not fund_id:
                return request.make_response(json.dumps({"success": False, "message": "Thiếu fund_id"}, ensure_ascii=False), headers=[("Content-Type", "application/json")])
            Tx = request.env['portfolio.transaction'].sudo()
            domain = [
                ('fund_id', '=', int(fund_id)),
                ('status', 'in', ['completed', 'pending']),
                ('matched_units', '>', 0),  # Lấy cả lệnh khớp một phần
            ]
            recs = Tx.search(domain, order='created_at desc', limit=limit)

            def _format_executions(parent):
                """Trả về danh sách executions (transaction.matched.orders) gắn với lệnh gốc."""
                # Nếu là lệnh mua: matched_order_ids; lệnh bán: matched_sell_order_ids
                execs = []
                if parent.transaction_type == 'buy':
                    records = parent.matched_order_ids
                elif parent.transaction_type == 'sell':
                    records = parent.matched_sell_order_ids
                else:
                    records = parent.env['transaction.matched.orders']

                for m in records:
                    # Xác định đối ứng
                    counter_order = m.sell_order_id if parent.transaction_type == 'buy' else m.buy_order_id
                    execs.append({
                        'id': m.id,
                        'reference': m.name,
                        'matched_quantity': m.matched_quantity,
                        'matched_price': m.matched_price,
                        'total_value': m.total_value,
                        'match_date': format_datetime_user_tz(request.env, m.match_date) or '',
                        'counter_order_id': counter_order.id if counter_order else False,
                        'counter_investor': counter_order.user_id.name if counter_order and counter_order.user_id else '',
                        'counter_type': 'sell' if parent.transaction_type == 'buy' else 'buy',
                    })
                return execs

            def _format_split_orders(parent):
                children = parent.split_order_ids.sudo()
                return [{
                    'id': child.id,
                    'user_name': child.user_id.name if child.user_id else 'N/A',
                    'type': child.transaction_type,
                    'price': child.price,
                    'units': child.units,
                    'amount': child.amount,
                    'created_at': format_datetime_user_tz(request.env, child.created_at if hasattr(child, 'created_at') and child.created_at else child.create_date) or '',
                    'date_end': format_datetime_user_tz(request.env, child.date_end if hasattr(child, 'date_end') and child.date_end else None) or '',
                    'status': child.status,
                    'is_split_order': bool(child.parent_order_id),
                    'remaining_units': child.remaining_units,
                    'split_order_ids': [],
                } for child in children]

            data = []
            for r in recs:
                entry = {
                'id': r.id,
                'user_name': r.user_id.name if r.user_id else 'N/A',
                'type': r.transaction_type,
                'price': r.price,
                'units': r.units,
                'matched_units': r.matched_units,
                'amount': r.amount,
                'created_at': format_datetime_user_tz(request.env, r.created_at if hasattr(r, 'created_at') and r.created_at else r.create_date) or '',
                'date_end': format_datetime_user_tz(request.env, r.date_end if hasattr(r, 'date_end') and r.date_end else None) or '',
                    'status': r.status,
                    'remaining_units': r.remaining_units,
                    'is_split_order': bool(r.parent_order_id),
                    'split_order_ids': _format_split_orders(r),
                    'executions': _format_executions(r),
                }
                data.append(entry)
            return request.make_response(json.dumps({"success": True, "data": data, "total": len(data)}, ensure_ascii=False), headers=[("Content-Type", "application/json")])
        except Exception as e:
            return request.make_response(json.dumps({"success": False, "message": str(e), "data": []}, ensure_ascii=False), headers=[("Content-Type", "application/json")], status=500)

    # ==== API NEGOTIATED MATCHED ORDERS ====
    @http.route('/api/transaction-list/negotiated', type='http', auth='user', methods=['POST'], csrf=False)
    def get_negotiated_orders(self, **kwargs):
        """Các giao dịch khớp theo thỏa thuận (bao gồm cả nhà đầu tư với nhau và nhà tạo lập với nhà đầu tư).
        filter_type: 'investor' - chỉ lệnh nhà đầu tư với nhau, 'market_maker' - chỉ lệnh có NTL, None - tất cả (trừ NTL-NTL)
        """
        try:
            try:
                payload = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            except Exception:
                payload = {}
            limit = int(payload.get('limit') or 500)
            fund_id = payload.get('fund_id')
            filter_type = payload.get('filter_type')  # 'investor' hoặc 'market_maker'
            Model = request.env['transaction.matched.orders'].sudo()
            # Execution hiện chỉ dùng 'done'/'draft'/'cancelled', không còn 'partial'
            domain = [('status', '=', 'done')]
            if fund_id:
                domain.append(('fund_id', '=', int(fund_id)))
            
            # Filter theo loại khớp
            if filter_type == 'investor':
                # Chỉ lấy lệnh nhà đầu tư với nhau
                domain.append(('buy_user_type', '=', 'investor'))
                domain.append(('sell_user_type', '=', 'investor'))
            elif filter_type == 'market_maker':
                # Chỉ lấy lệnh có NTL (một bên là NTL, một bên là nhà đầu tư)
                # Loại trừ NTL-NTL
                domain.append('|')
                domain.append('&')
                domain.append(('buy_user_type', '=', 'market_maker'))
                domain.append(('sell_user_type', '=', 'investor'))
                domain.append('&')
                domain.append(('buy_user_type', '=', 'investor'))
                domain.append(('sell_user_type', '=', 'market_maker'))
            else:
                # Mặc định: tất cả trừ NTL-NTL (nhà đầu tư với nhau hoặc có NTL)
                domain.append('|')
                domain.append('&')
                domain.append(('buy_user_type', '=', 'investor'))
                domain.append(('sell_user_type', '=', 'investor'))
                domain.append('|')
                domain.append('&')
                domain.append(('buy_user_type', '=', 'market_maker'))
                domain.append(('sell_user_type', '=', 'investor'))
                domain.append('&')
                domain.append(('buy_user_type', '=', 'investor'))
                domain.append(('sell_user_type', '=', 'market_maker'))
            
            recs = Model.search(domain, order='match_date desc', limit=limit)
            
            # Lọc lại ở Python để đảm bảo loại bỏ NTL-NTL (nếu có)
            filtered_recs = []
            for r in recs:
                # Loại bỏ NTL-NTL
                if r.buy_user_type == 'market_maker' and r.sell_user_type == 'market_maker':
                    continue
                filtered_recs.append(r)
            
            data = [{
                'id': r.id,
                'fund_name': r.fund_id.name if r.fund_id else '',
                'matched_quantity': r.matched_quantity,
                'matched_price': r.matched_price,
                'total_value': r.total_value,
                'match_date': format_datetime_user_tz(request.env, r.match_date) or '',
                'buy_user_type': r.buy_user_type,
                'sell_user_type': r.sell_user_type,
            } for r in filtered_recs]
            return request.make_response(json.dumps({"success": True, "data": data, "total": len(data)}, ensure_ascii=False), headers=[("Content-Type", "application/json")])
        except Exception as e:
            return request.make_response(json.dumps({"success": False, "message": str(e), "data": []}, ensure_ascii=False), headers=[("Content-Type", "application/json")], status=500)

    def _calculate_priority_score(self, order, order_type):
        """
        Tính điểm ưu tiên theo Price-Time Priority CHUẨN Stock Exchange
        Sử dụng PartialMatchingEngine để tránh duplicate code
        
        Args:
            order: portfolio.transaction record
            order_type: 'buy' hoặc 'sell'
        
        Returns:
            float: Priority score (cao hơn = ưu tiên hơn)
        """
        try:
            # Sử dụng helper method từ PartialMatchingEngine
            matching_engine = request.env['transaction.partial.matching.engine']
            return matching_engine.calculate_priority_score_for_order(order)
        except Exception:
            return 0
