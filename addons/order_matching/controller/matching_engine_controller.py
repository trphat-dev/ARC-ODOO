# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MatchingEngineController(http.Controller):
    """
    Controller cho Matching Engine API
    
    Controller này là wrapper cho PartialMatchingEngine đã được chuẩn hóa theo thuật toán Stock Exchange:
    - Price-Time Priority (FIFO)
    - Giá khớp = giá sell order
    - Tính toán remaining_units chính xác từ units - matched_units
    """

    @http.route('/api/transaction-list/partial-matching/create-engine', type='http', auth='user', methods=['POST'], csrf=False)
    def create_engine(self, **kwargs):
        """Tạo engine mới cho một quỹ"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            fund_id = data.get('fund_id')
            
            if not fund_id:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Thiếu fund_id"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=400
                )
            
            # Tạo engine
            engine = request.env['transaction.partial.matching.engine'].create_engine_for_fund(fund_id)
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "message": _("Đã tạo engine cho quỹ %s") % fund_id,
                    "engine_id": engine.id,
                    "engine_name": engine.name
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error creating engine: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/partial-matching/add-order', type='http', auth='user', methods=['POST'], csrf=False)
    def add_order(self, **kwargs):
        """Thêm lệnh vào engine và thực hiện khớp"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            order_id = data.get('order_id')
            engine_id = data.get('engine_id')
            
            if not order_id or not engine_id:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Thiếu order_id hoặc engine_id"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=400
                )
            
            # Lấy engine và order
            engine = request.env['transaction.partial.matching.engine'].browse(engine_id)
            order = request.env['portfolio.transaction'].browse(order_id)
            
            if not engine.exists() or not order.exists():
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không tìm thấy engine hoặc order"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=404
                )
            
            # Thêm lệnh vào engine
            matched_pairs = engine.add_order(order)
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "message": _("Đã thêm lệnh và khớp %s cặp") % len(matched_pairs),
                    "matched_pairs": matched_pairs,
                    "engine_stats": {
                        "total_matches": engine.total_matches,
                        "total_partial_matches": engine.total_partial_matches,
                        "last_match_date": engine.last_match_date.strftime('%Y-%m-%d %H:%M:%S') if engine.last_match_date else None
                    }
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error adding order: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/partial-matching/process-all', type='http', auth='user', methods=['POST'], csrf=False)
    def process_all_orders(self, **kwargs):
        """Xử lý tất cả lệnh pending trong engine"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            engine_id = data.get('engine_id')
            
            if not engine_id:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Thiếu engine_id"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=400
                )
            
            # Lấy engine
            engine = request.env['transaction.partial.matching.engine'].browse(engine_id)
            
            if not engine.exists():
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không tìm thấy engine"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=404
                )
            
            # Xử lý tất cả lệnh pending
            matched_pairs = engine.process_all_pending_orders()
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "message": _("Đã xử lý và khớp %s cặp lệnh") % len(matched_pairs),
                    "matched_pairs": matched_pairs,
                    "engine_stats": {
                        "total_matches": engine.total_matches,
                        "total_partial_matches": engine.total_partial_matches,
                        "last_match_date": engine.last_match_date.strftime('%Y-%m-%d %H:%M:%S') if engine.last_match_date else None
                    }
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error processing all orders: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/partial-matching/queue-status', type='http', auth='user', methods=['POST'], csrf=False)
    def get_queue_status(self, **kwargs):
        """Lấy trạng thái queue của engine"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            engine_id = data.get('engine_id')
            
            if not engine_id:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Thiếu engine_id"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=400
                )
            
            # Lấy engine
            engine = request.env['transaction.partial.matching.engine'].browse(engine_id)
            
            if not engine.exists():
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không tìm thấy engine"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=404
                )
            
            # Lấy trạng thái queue
            queue_status = engine.get_queue_status()
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "queue_status": queue_status,
                    "engine_info": {
                        "id": engine.id,
                        "name": engine.name,
                        "fund_id": engine.fund_id.id,
                        "fund_name": engine.fund_id.name,
                        "is_active": engine.is_active,
                        "total_matches": engine.total_matches,
                        "total_partial_matches": engine.total_partial_matches,
                        "last_match_date": engine.last_match_date.strftime('%Y-%m-%d %H:%M:%S') if engine.last_match_date else None
                    }
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error getting queue status: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/partial-matching/clear-queue', type='http', auth='user', methods=['POST'], csrf=False)
    def clear_queue(self, **kwargs):
        """Xóa tất cả lệnh trong queue"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            engine_id = data.get('engine_id')
            
            if not engine_id:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Thiếu engine_id"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=400
                )
            
            # Lấy engine
            engine = request.env['transaction.partial.matching.engine'].browse(engine_id)
            
            if not engine.exists():
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không tìm thấy engine"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")],
                    status=404
                )
            
            # Xóa queue
            engine.clear_queue()
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "message": "Đã xóa tất cả lệnh trong queue"
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error clearing queue: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/partial-matching/engines', type='http', auth='user', methods=['GET'], csrf=False)
    def list_engines(self, **kwargs):
        """Lấy danh sách tất cả engines"""
        try:
            engines = request.env['transaction.partial.matching.engine'].search([
                ('is_active', '=', True)
            ])
            
            engines_data = []
            for engine in engines:
                queue_status = engine.get_queue_status()
                engines_data.append({
                    "id": engine.id,
                    "name": engine.name,
                    "fund_id": engine.fund_id.id,
                    "fund_name": engine.fund_id.name,
                    "is_active": engine.is_active,
                    "total_matches": engine.total_matches,
                    "total_partial_matches": engine.total_partial_matches,
                    "last_match_date": engine.last_match_date.strftime('%Y-%m-%d %H:%M:%S') if engine.last_match_date else None,
                    "queue_status": queue_status
                })
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "engines": engines_data,
                    "total": len(engines_data)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error listing engines: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    @http.route('/api/transaction-list/partial-matching/cleanup', type='http', auth='user', methods=['POST'], csrf=False)
    def cleanup_old_queues(self, **kwargs):
        """Dọn dẹp queue cũ"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            days = data.get('days', 7)
            
            # Dọn dẹp queue cũ
            cleaned_count = request.env['transaction.order.queue'].cleanup_old_queues(days)
            
            return request.make_response(
                json.dumps({
                    "success": True,
                    "message": _("Đã dọn dẹp %s queue cũ (>%s ngày)") % (cleaned_count, days),
                    "cleaned_count": cleaned_count
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            _logger.error("Error cleaning up queues: %s", str(e))
            return request.make_response(
                json.dumps({
                    "success": False,
                    "message": str(e)
                }, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )
