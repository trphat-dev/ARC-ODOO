# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TransactionList(models.Model):
    """
    Transaction List Model - Chỉ quản lý danh sách lệnh giao dịch
    Không thêm field mới, chỉ inherit để có thể thêm methods riêng cho transaction list
    """
    _inherit = "portfolio.transaction"
    _description = "Transaction List"

    @api.model
    def get_transaction_data(self, status_filter=None, source_filter=None):
        """Get transaction data for the frontend"""
        domain = []
        
        if status_filter and status_filter.strip():
            status_filter = status_filter.lower().strip()
            # Map status from frontend to database
            frontend_to_db_mapping = {
                'pending': ['pending'],
                'completed': ['completed'],
                'approved': ['completed'],  # Approved tab should show completed transactions
                'cancelled': ['cancelled']
            }
            
            mapped_statuses = frontend_to_db_mapping.get(status_filter, [status_filter])
            if len(mapped_statuses) == 1:
                domain.append(('status', '=', mapped_statuses[0]))
            else:
                domain.append(('status', 'in', mapped_statuses))
        
        if source_filter and source_filter.strip():
            domain.append(('source', '=', source_filter))
        
        # Chỉ hiển thị lệnh gốc cho nhà đầu tư (không hiển thị lệnh con đã tách)
        # Lệnh gốc là lệnh không có parent_order_id (parent_order_id = False)
        if hasattr(self, 'parent_order_id'):
            domain.append(('parent_order_id', '=', False))
        
        transactions = self.search(domain)
        
        result = []
        for trans in transactions:
            def _amount_ex_fee(tx):
                try:
                    fee_val = getattr(tx, 'fee', 0) or 0
                    amt_val = tx.amount or 0
                    return max(amt_val - fee_val, 0)
                except Exception:
                    return tx.amount or 0
            
            # Kiểm tra xem có hợp đồng không
            has_contract = bool(getattr(trans, 'contract_pdf_path', False))
            contract_url = ''
            contract_download_url = ''
            if has_contract:
                contract_url = f"/transaction-list/contract/{trans.id}"
                contract_download_url = f"/transaction-list/contract/{trans.id}?download=1"
            
            # Map status trước khi thêm vào result
            frontend_status = trans.status
            try:
                # Đồng bộ với logic khớp lệnh: nếu đã khớp hết (remaining_units = 0)
                # và đã có matched_units nhưng status vẫn là pending thì coi như completed trên frontend.
                remaining_val = getattr(trans, 'remaining_units', None)
                matched_val = getattr(trans, 'matched_units', 0) if hasattr(trans, 'matched_units') else 0
                if frontend_status == 'pending' and matched_val > 0 and remaining_val is not None and remaining_val <= 0:
                    frontend_status = 'completed'
            except Exception:
                # Không để lỗi nhỏ ảnh hưởng tới API
                pass
            
            result.append({
                'id': trans.id,
                'name': trans.name,
                'user_id': trans.user_id.id,
                'account_number': getattr(trans, 'account_number', '') or '',
                'investor_name': getattr(trans, 'investor_name', '') or '',
                'investor_phone': getattr(trans, 'investor_phone', '') or '',
                'fund_id': trans.fund_id.id if trans.fund_id else None,
                'fund_name': trans.fund_id.name if trans.fund_id else '',
                'fund_ticker': trans.fund_id.ticker if trans.fund_id else '',
                'transaction_code': trans.reference or '',
                'transaction_type': trans.transaction_type,
                'target_fund': trans.destination_fund_id.name if trans.destination_fund_id else '',
                'target_fund_ticker': trans.destination_fund_id.ticker if trans.destination_fund_id else '',
                'units': trans.units,
                'price': getattr(trans, 'price', 0) if hasattr(trans, 'price') and getattr(trans, 'price', 0) else 0.0,
                'destination_units': trans.destination_units or 0,
                'amount': _amount_ex_fee(trans),
                'calculated_amount': _amount_ex_fee(trans),
                # Giá đơn vị: ưu tiên price (giá giao dịch), fallback current_nav/fund.current_nav
                'current_nav': (getattr(trans, 'price', 0) or 
                              (getattr(trans, 'current_nav', 0) or 
                               (trans.fund_id.current_nav if trans.fund_id else 0.0))),
                'unit_price': (getattr(trans, 'price', 0) or 
                             (getattr(trans, 'current_nav', 0) or 
                              (trans.fund_id.current_nav if trans.fund_id else 0.0))),
                'matched_units': getattr(trans, 'matched_units', 0) if hasattr(trans, 'matched_units') else 0,
                'ccq_remaining_to_match': getattr(trans, 'ccq_remaining_to_match', 0) if hasattr(trans, 'ccq_remaining_to_match') else 0,
                'currency': trans.currency_id.symbol if trans.currency_id else '',
                'status': frontend_status,
                'original_status': trans.status,
                'source': getattr(trans, 'source', 'portfolio') or 'portfolio',
                'investment_type': trans.investment_type,
                'created_at': (trans.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trans, 'created_at') and trans.created_at else 
                              (trans.create_date.strftime('%Y-%m-%d %H:%M:%S') if trans.create_date else '')),
                'date_end': (trans.date_end.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trans, 'date_end') and trans.date_end else ''),
                'transaction_date': (trans.date_end.strftime('%Y-%m-%d') if hasattr(trans, 'date_end') and trans.date_end else 
                                    (trans.created_at.strftime('%Y-%m-%d') if hasattr(trans, 'created_at') and trans.created_at else 
                                     (trans.create_date.strftime('%Y-%m-%d') if trans.create_date else ''))),
                'first_in_time': (trans.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trans, 'created_at') and trans.created_at else 
                                 (trans.create_date.strftime('%Y-%m-%d %H:%M:%S') if trans.create_date else '')),
                'in_time': (trans.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trans, 'created_at') and trans.created_at else 
                           (trans.create_date.strftime('%Y-%m-%d %H:%M:%S') if trans.create_date else '')),
                'out_time': (trans.date_end.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trans, 'date_end') and trans.date_end else ''),
                'approved_by': getattr(trans, 'approved_by', False).name if hasattr(trans, 'approved_by') and getattr(trans, 'approved_by', False) else '',
                'approved_at': (getattr(trans, 'approved_at', False).strftime('%Y-%m-%d %H:%M:%S') 
                               if hasattr(trans, 'approved_at') and getattr(trans, 'approved_at', False) else ''),
                'description': trans.description or '',
                'has_contract': has_contract,
                'contract_url': contract_url,
                'contract_download_url': contract_download_url,
                'is_split_order': getattr(trans, 'is_split_order', False) if hasattr(trans, 'is_split_order') else False,
                'parent_order_id': (trans.parent_order_id.id if hasattr(trans, 'parent_order_id') and 
                                   getattr(trans, 'parent_order_id', False) and trans.parent_order_id else None),
                'parent_order_name': (trans.parent_order_id.name if hasattr(trans, 'parent_order_id') and 
                                     getattr(trans, 'parent_order_id', False) and trans.parent_order_id else ''),
                'split_order_count': (len(trans.split_order_ids) if hasattr(trans, 'split_order_ids') else 0),
            })
        
        return result

    @api.model
    def get_transaction_stats(self):
        """Get transaction statistics"""
        total_pending = self.search_count([('status', '=', 'pending')])
        total_approved = self.search_count([('status', '=', 'completed')])
        total_cancelled = self.search_count([('status', '=', 'cancelled')])
        
        portal_pending = self.search_count([('status', '=', 'pending'), ('source', '=', 'portal')])
        sale_pending = self.search_count([('status', '=', 'pending'), ('source', '=', 'sale')])
        portfolio_pending = self.search_count([('status', '=', 'pending'), ('source', '=', 'portfolio')])
        
        return {
            'total_pending': total_pending,
            'total_approved': total_approved,
            'total_cancelled': total_cancelled,
            'portal_pending': portal_pending,
            'sale_pending': sale_pending,
            'portfolio_pending': portfolio_pending,
            'portfolio_approved': total_approved,
            'portfolio_cancelled': total_cancelled,
            'list_total': total_pending + total_approved + total_cancelled,
            'portfolio_total': total_pending + total_approved + total_cancelled,
        }

    @api.model
    def get_matched_orders(self, transaction_id=None):
        """Get matched orders information - simplified version"""
        domain = []
        if transaction_id:
            domain = ['|', 
                ('buy_order_id', '=', transaction_id),
                ('sell_order_id', '=', transaction_id)
            ]
        
        # Kiểm tra xem model transaction.matched.orders có tồn tại không
        if 'transaction.matched.orders' not in self.env:
            return []
        
        MatchedOrders = self.env['transaction.matched.orders']
        matched_orders = MatchedOrders.search(domain, order='match_date desc')
        
        result = []
        for match in matched_orders:
            result.append({
                'id': match.id,
                'reference': match.name,
                'match_date': match.match_date.strftime('%Y-%m-%d %H:%M:%S') if match.match_date else '',
                'status': match.status,
                'matched_quantity': match.matched_quantity,
                'matched_price': match.matched_price,
                'total_value': match.total_value,
            })
        
        return result

