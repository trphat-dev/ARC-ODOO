# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
from datetime import timedelta

from ..constants import (
    MAX_CONSECUTIVE_ERRORS,
    TransactionStatus,
    InventoryStatus,
    TransactionType,
    DEFAULT_CCQ_QUANTITY,
    DEFAULT_NAV_PRICE,
)

_logger = logging.getLogger(__name__)


class NavDailyInventory(models.Model):
    """Daily inventory tracking for NAV (Net Asset Value) management."""
    
    _name = 'nav.daily.inventory'
    _description = _('NAV Daily Inventory')
    _order = 'inventory_date desc, fund_id'
    _rec_name = 'display_name'
    _sql_constraints = [
        ('uniq_fund_date', 'unique(fund_id, inventory_date)', 
         _('Each fund can only have one inventory record per day.'))
    ]

    # Basic fields
    fund_id = fields.Many2one(
        'portfolio.fund', 
        string=_('Fund'), 
        required=True, 
        tracking=True
    )
    inventory_date = fields.Date(
        string=_('Inventory Date'), 
        required=True, 
        tracking=True, 
        default=fields.Date.today
    )
    status = fields.Selection([
        (InventoryStatus.DRAFT, _('Draft')),
        (InventoryStatus.CONFIRMED, _('Confirmed')),
        (InventoryStatus.COMPLETE, _('Complete'))
    ], string=_('Status'), default=InventoryStatus.DRAFT, required=True, tracking=True)
    
    # Opening values
    opening_ccq = fields.Float(
        string=_('Opening CCQ'), 
        digits=(16, 2), 
        tracking=True
    )
    opening_avg_price = fields.Float(
        string=_('Opening Average Price'), 
        digits=(16, 2), 
        tracking=True
    )
    opening_value = fields.Float(
        string=_('Opening Value'), 
        compute='_compute_opening_value', 
        store=True, 
        digits=(16, 2)
    )
    
    # Closing values - computed realtime without store
    closing_ccq = fields.Float(
        string=_('Closing CCQ'), 
        compute='_compute_closing_ccq', 
        store=False, 
        digits=(16, 2)
    )
    closing_avg_price = fields.Float(
        string=_('Closing Average Price'), 
        compute='_compute_closing_avg_price', 
        store=False, 
        digits=(16, 2)
    )
    closing_value = fields.Float(
        string=_('Closing Value'), 
        compute='_compute_closing_value', 
        store=False, 
        digits=(16, 2)
    )
    
    # Change tracking fields - computed realtime
    ccq_change = fields.Float(
        string=_('CCQ Change'), 
        compute='_compute_changes', 
        store=False, 
        digits=(16, 2)
    )
    price_change = fields.Float(
        string=_('Price Change'), 
        compute='_compute_changes', 
        store=False, 
        digits=(16, 2)
    )
    value_change = fields.Float(
        string=_('Value Change'), 
        compute='_compute_changes', 
        store=False, 
        digits=(16, 2)
    )
    
    # Additional computed fields
    transaction_details = fields.Html(
        string=_('Transaction Details'), 
        compute='_compute_transaction_details'
    )
    calculation_details = fields.Text(
        string=_('Calculation Details'), 
        compute='_compute_calculation_details'
    )
    fund_config_info = fields.Text(
        string=_('Fund Config Info'), 
        compute='_compute_fund_config_info'
    )
    description = fields.Text(string=_('Description'))
    
    # Display name
    display_name = fields.Char(
        string=_('Display Name'), 
        compute='_compute_display_name', 
        store=True
    )
    
    @api.depends('fund_id', 'inventory_date')
    def _compute_display_name(self):
        for record in self:
            if record.fund_id and record.inventory_date:
                record.display_name = f"{record.fund_id.name} - {record.inventory_date}"
            else:
                record.display_name = "New Daily Inventory"
    
    @api.depends('opening_ccq', 'opening_avg_price')
    def _compute_opening_value(self):
        for record in self:
            record.opening_value = record.opening_ccq * record.opening_avg_price
    
    @api.depends('closing_ccq', 'closing_avg_price')
    def _compute_closing_value(self):
        for record in self:
            # Tính giá trị cuối ngày dựa trên CCQ và giá trung bình đã tính
            record.closing_value = (record.closing_ccq or 0.0) * (record.closing_avg_price or 0.0)
    
    @api.depends('opening_ccq', 'opening_avg_price', 'opening_value', 'closing_ccq', 'closing_avg_price', 'closing_value')
    def _compute_changes(self):
        for record in self:
            # Tính thay đổi dựa trên các giá trị đã được tính toán
            record.ccq_change = (record.closing_ccq or 0.0) - (record.opening_ccq or 0.0)
            record.price_change = (record.closing_avg_price or 0.0) - (record.opening_avg_price or 0.0)
            record.value_change = (record.closing_value or 0.0) - (record.opening_value or 0.0)
    
    @api.depends('fund_id', 'inventory_date')
    def _compute_transaction_details(self):
        for record in self:
            if not record.fund_id or not record.inventory_date:
                record.transaction_details = "<p><em>Chưa có thông tin giao dịch</em></p>"
                continue
            
            try:
                # Get completed NEGOTIATED transactions for the fund on this date
                transactions = self.env['portfolio.transaction'].search([
                    ('fund_id', '=', record.fund_id.id),
                    ('status', '=', 'completed'),
                    ('order_mode', '=', 'negotiated'),
                    ('created_at', '>=', f"{record.inventory_date} 00:00:00"),
                    ('created_at', '<=', f"{record.inventory_date} 23:59:59")
                ])
                
                _logger.info(f"Hiển thị giao dịch cho fund {record.fund_id.name} ngày {record.inventory_date}: {len(transactions)} giao dịch")
            
                if not transactions:
                    record.transaction_details = "<p><em>Không có giao dịch trong ngày</em></p>"
                    continue
                
                # Tạo HTML table đẹp
                html_content = f"""
                <div class="transaction-details">
                    <h4>Tồn kho đầu ngày: {record.opening_ccq:,.0f} CCQ × {record.opening_avg_price:,.0f} = {record.opening_value:,.0f} VND</h4>
                    
                    <table class="table table-striped table-bordered">
                        <thead class="table-dark">
                            <tr>
                                <th>Thời gian</th>
                                <th>Loại</th>
                                <th>Số lượng CCQ</th>
                                <th>Giá</th>
                                <th>Thành tiền</th>
                            </tr>
                        </thead>
                        <tbody>
                """
            
                total_value = record.opening_value
                total_ccq = record.opening_ccq
                total_buy_ccq = 0
                total_sell_ccq = 0
                
                for tx in transactions:
                    try:
                        # Đảm bảo giao dịch thuộc đúng fund
                        if tx.fund_id.id != record.fund_id.id:
                            _logger.warning(f"Giao dịch {tx.id} không thuộc fund {record.fund_id.name}")
                            continue
                            
                        # Lấy số lượng CCQ thực tế
                        matched_units = getattr(tx, 'matched_units', False)
                        if matched_units is not False:
                            units_value = matched_units
                        else:
                            units_value = tx.units or 0
                        
                        # Tính giá đơn vị
                        if getattr(tx, 'amount', 0) and tx.units:
                            unit_price = tx.amount / tx.units
                        else:
                            unit_price = tx.current_nav or 0
                        
                        transaction_value = units_value * unit_price
                        
                        # Cập nhật tổng
                        if tx.transaction_type == 'buy':
                            total_value += transaction_value
                            total_ccq += units_value
                            total_buy_ccq += units_value
                        elif tx.transaction_type == 'sell':
                            total_value -= transaction_value
                            total_ccq = max(0, total_ccq - units_value)
                            total_sell_ccq += units_value
                        
                        # Thêm row vào table
                        html_content += f"""
                        <tr>
                            <td>{tx.created_at.strftime('%H:%M:%S') if tx.created_at else 'N/A'}</td>
                            <td><span class="badge {'bg-success' if tx.transaction_type == 'buy' else 'bg-danger'}">{'Mua' if tx.transaction_type == 'buy' else 'Bán'}</span></td>
                            <td>{units_value:,.0f}</td>
                            <td>{unit_price:,.0f}</td>
                            <td>{transaction_value:,.0f}</td>
                        </tr>
                        """
                    except Exception as e:
                        _logger.warning(f"Lỗi xử lý giao dịch {tx.id}: {e}")
                        continue
                
                html_content += f"""
                        </tbody>
                    </table>
                    
                    <div class="alert alert-info">
                        <h5>Tồn kho cuối ngày: {total_ccq:,.0f} CCQ × {total_value/total_ccq if total_ccq > 0 else 0:,.0f} = {total_value:,.0f} VND</h5>
                    </div>
                </div>
                """
                
                record.transaction_details = html_content
                
            except Exception as e:
                _logger.error(f"Lỗi tính toán transaction details cho fund {record.fund_id.name}: {e}")
                record.transaction_details = f"<p><em>Lỗi hiển thị giao dịch: {str(e)}</em></p>"
    
    @api.depends('opening_ccq', 'fund_id', 'inventory_date')
    def _compute_closing_ccq(self):
        for record in self:
            # Prevent recursive compute loops via context flag
            if self.env.context.get('_computing_closing_ccq'):
                record.closing_ccq = record.opening_ccq or 0.0
                continue
            try:
                if record.fund_id and record.inventory_date:
                    # Tính toán CCQ cuối ngày dựa trên giao dịch
                    record.closing_ccq = record.with_context(_computing_closing_ccq=True)._calculate_daily_ccq()
                else:
                    record.closing_ccq = record.opening_ccq or 0.0
            except Exception as e:
                _logger.error(f"Lỗi tính CCQ cho fund {record.fund_id.name if record.fund_id else 'Unknown'}: {e}")
                record.closing_ccq = record.opening_ccq or 0.0
    
    @api.depends('opening_avg_price', 'closing_ccq', 'fund_id', 'inventory_date')
    def _compute_closing_avg_price(self):
        for record in self:
            # Prevent recursive compute loops via context flag
            if self.env.context.get('_computing_closing_avg_price'):
                record.closing_avg_price = record.opening_avg_price or 0.0
                continue
            try:
                if record.fund_id and record.inventory_date and record.closing_ccq > 0:
                    # Tính giá trung bình cuối ngày dựa trên CCQ đã tính
                    record.closing_avg_price = record.with_context(_computing_closing_avg_price=True)._calculate_weighted_average_price()
                else:
                    record.closing_avg_price = record.opening_avg_price or 0.0
            except Exception as e:
                _logger.error(f"Lỗi tính giá TB cho fund {record.fund_id.name if record.fund_id else 'Unknown'}: {e}")
                record.closing_avg_price = record.opening_avg_price or 0.0
    
    def _calculate_daily_ccq(self):
        """Tính CCQ cuối ngày dựa trên giao dịch trong ngày"""
        # Use constant for max consecutive errors before breaking
        try:
            if not self.fund_id or not self.inventory_date:
                return self.opening_ccq or 0.0
            
            # Get completed NEGOTIATED transactions for the fund on this date
            transactions = self.env['portfolio.transaction'].search([
                ('fund_id', '=', self.fund_id.id),
                ('status', '=', 'completed'),
                ('order_mode', '=', 'negotiated'),
                ('created_at', '>=', f"{self.inventory_date} 00:00:00"),
                ('created_at', '<=', f"{self.inventory_date} 23:59:59")
            ], order='create_date')
            
            _logger.debug(f"Tính CCQ cho fund {self.fund_id.name} ngày {self.inventory_date}: {len(transactions)} giao dịch thỏa thuận")
        
            current_ccq = self.opening_ccq or 0.0
            error_count = 0  # Reset for processing loop
            
            # Xử lý từng giao dịch theo thứ tự thời gian
            for tx in transactions:
                try:
                    # Đảm bảo giao dịch thuộc đúng fund
                    if tx.fund_id.id != self.fund_id.id:
                        continue
                        
                    # Lấy số lượng CCQ thực tế từ giao dịch
                    matched_units = getattr(tx, 'matched_units', False)
                    if matched_units is not False:
                        units_value = matched_units
                    else:
                        units_value = tx.units or 0
            
                    if tx.transaction_type == 'buy':
                        # Mua: thêm CCQ
                        current_ccq += units_value
                    elif tx.transaction_type == 'sell':
                        # Bán: trừ CCQ (không được âm)
                        current_ccq = max(0, current_ccq - units_value)
                    error_count = 0  # Reset on success
                except Exception as e:
                    error_count += 1
                    _logger.warning(f"Lỗi xử lý giao dịch {tx.id}: {e}")
                    if error_count >= MAX_CONSECUTIVE_ERRORS:
                        _logger.error(_("Stopping transaction processing after %s consecutive errors"), MAX_CONSECUTIVE_ERRORS)
                        break
                    continue
            
            return current_ccq
        
        except Exception as e:
            _logger.error(f"Lỗi tính CCQ cho fund {self.fund_id.name if self.fund_id else 'Unknown'}: {e}")
            return self.opening_ccq or 0.0
    
    def _calculate_weighted_average_price(self):
        """Tính giá trung bình có trọng số chính xác theo công thức"""
        # Use constant for max consecutive errors before breaking
        try:
            if not self.fund_id or not self.inventory_date:
                return self.opening_avg_price or 0.0
            
            # Get completed NEGOTIATED transactions for the fund on this date
            transactions = self.env['portfolio.transaction'].search([
                ('fund_id', '=', self.fund_id.id),
                ('status', '=', 'completed'),
                ('order_mode', '=', 'negotiated'),
                ('created_at', '>=', f"{self.inventory_date} 00:00:00"),
                ('created_at', '<=', f"{self.inventory_date} 23:59:59")
            ], order='create_date')
            
            _logger.debug(f"Tính giá TB cho fund {self.fund_id.name} ngày {self.inventory_date}: {len(transactions)} giao dịch thỏa thuận")
            
            # Khởi tạo với dữ liệu đầu ngày
            weighted_sum = self.opening_value or 0.0  # = self.opening_ccq * self.opening_avg_price
            total_ccq = self.opening_ccq or 0.0       # Tổng CCQ
            error_count = 0  # Reset for processing loop
            
            # Xử lý từng giao dịch
            for tx in transactions:
                try:
                    # Đảm bảo giao dịch thuộc đúng fund
                    if tx.fund_id.id != self.fund_id.id:
                        continue
                        
                    # Lấy số lượng CCQ thực tế
                    matched_units = getattr(tx, 'matched_units', False)
                    if matched_units is not False:
                        units_value = matched_units
                    else:
                        units_value = tx.units or 0
                    
                    # Tính giá đơn vị
                    if getattr(tx, 'amount', 0) and tx.units:
                        unit_price = tx.amount / tx.units
                    else:
                        unit_price = tx.current_nav or 0
            
                    if tx.transaction_type == 'buy':
                        # Mua: thêm vào tổng giá trị và CCQ
                        weighted_sum += units_value * unit_price
                        total_ccq += units_value
                    elif tx.transaction_type == 'sell':
                        # Bán: trừ theo giá bán thực tế
                        weighted_sum -= units_value * unit_price
                        total_ccq = max(0, total_ccq - units_value)
                    error_count = 0  # Reset on success
                except Exception as e:
                    error_count += 1
                    _logger.warning(f"Lỗi xử lý giao dịch {tx.id}: {e}")
                    if error_count >= MAX_CONSECUTIVE_ERRORS:
                        _logger.error(_("Stopping transaction processing after %s consecutive errors"), MAX_CONSECUTIVE_ERRORS)
                        break
                    continue
            
            # Trả về giá trung bình có trọng số
            if total_ccq > 0:
                return weighted_sum / total_ccq
            else:
                return self.opening_avg_price or 0.0
                
        except Exception as e:
            _logger.error(f"Lỗi tính giá TB cho fund {self.fund_id.name if self.fund_id else 'Unknown'}: {e}")
            return self.opening_avg_price or 0.0
    
    @api.depends('fund_id', 'inventory_date', 'opening_ccq', 'opening_avg_price')
    def _compute_calculation_details(self):
        for record in self:
            try:
                record.calculation_details = record._get_calculation_details()
            except Exception as e:
                _logger.error(f"Lỗi tính calculation details cho fund {record.fund_id.name}: {e}")
                record.calculation_details = f"Lỗi tính toán: {str(e)}"
    
    def _get_calculation_details(self):
        """Lấy chi tiết tính toán để debug và hiển thị"""
        if not self.fund_id or not self.inventory_date:
            return "Không có dữ liệu để tính toán"
        
        try:
            # Get completed NEGOTIATED transactions for the fund on this date
            transactions = self.env['portfolio.transaction'].search([
                ('fund_id', '=', self.fund_id.id),
                ('status', '=', 'completed'),
                ('order_mode', '=', 'negotiated'),
                ('created_at', '>=', f"{self.inventory_date} 00:00:00"),
                ('created_at', '<=', f"{self.inventory_date} 23:59:59")
            ], order='create_date')
            
            details = []
            details.append(f"=== CHI TIẾT TÍNH TOÁN TỒN KHO ===")
            details.append(f"Ngày: {self.inventory_date}")
            details.append(f"Quỹ: {self.fund_id.name}")
            details.append(f"")
            details.append(f"ĐẦU NGÀY:")
            details.append(f"  - CCQ: {self.opening_ccq:,.0f}")
            details.append(f"  - Giá TB: {self.opening_avg_price:,.0f}")
            details.append(f"  - Giá trị: {self.opening_value:,.0f} (= {self.opening_ccq:,.0f} × {self.opening_avg_price:,.0f})")
            details.append(f"")
            
            # Khởi tạo với dữ liệu đầu ngày
            weighted_sum = self.opening_value
            total_ccq = self.opening_ccq
            
            details.append(f"GIAO DỊCH TRONG NGÀY:")
            for i, tx in enumerate(transactions, 1):
                try:
                    # Đảm bảo giao dịch thuộc đúng fund
                    if tx.fund_id.id != self.fund_id.id:
                        _logger.warning(f"Giao dịch {tx.id} không thuộc fund {self.fund_id.name}")
                        continue
                        
                    # Lấy số lượng CCQ thực tế
                    matched_units = getattr(tx, 'matched_units', False)
                    if matched_units is not False:
                        units_value = matched_units
                    else:
                        units_value = tx.units or 0
                    
                    # Tính giá đơn vị
                    if getattr(tx, 'amount', 0) and tx.units:
                        unit_price = tx.amount / tx.units
                    else:
                        unit_price = tx.current_nav or 0
                    
                    transaction_value = units_value * unit_price
                    
                    details.append(f"  {i}. {tx.transaction_type.upper()}: {units_value:,.0f} CCQ × {unit_price:,.0f} = {transaction_value:,.0f}")
                    
                    if tx.transaction_type == 'buy':
                        weighted_sum += transaction_value
                        total_ccq += units_value
                    elif tx.transaction_type == 'sell':
                        weighted_sum -= transaction_value
                        total_ccq = max(0, total_ccq - units_value)
                except Exception as e:
                    _logger.warning(f"Lỗi xử lý giao dịch {tx.id}: {e}")
                    continue
            
            details.append(f"")
            details.append(f"CUỐI NGÀY:")
            details.append(f"  - CCQ: {total_ccq:,.0f}")
            if total_ccq > 0:
                avg_price = weighted_sum / total_ccq
                details.append(f"  - Giá TB: {avg_price:,.0f}")
                details.append(f"  - Giá trị: {weighted_sum:,.0f}")
            else:
                details.append(f"  - Giá TB: {self.opening_avg_price:,.0f} (không có CCQ)")
                details.append(f"  - Giá trị: 0")
            
            return "\n".join(details)
            
        except Exception as e:
            _logger.error(f"Lỗi tính chi tiết cho fund {self.fund_id.name}: {e}")
            return f"Lỗi tính toán: {str(e)}"
    
    @api.depends('fund_id')
    def _compute_fund_config_info(self):
        for record in self:
            if not record.fund_id:
                record.fund_config_info = "Chưa chọn quỹ"
                continue
            
            try:
                # Lấy thông tin từ fund.certificate trong fund_management_control
                cert = record.fund_id.certificate_id
                
                if cert and cert.exists():
                    total_value = (cert.initial_certificate_quantity or 0.0) * (cert.initial_certificate_price or 0.0)
                    record.fund_config_info = f"""
                    Thông tin quỹ từ fund.certificate:
                    - Giá CCQ ban đầu: {cert.initial_certificate_price:,.0f}
                    - CCQ ban đầu: {cert.initial_certificate_quantity:,.0f}
                    - Chi phí vốn: {cert.capital_cost:,.2f}%
                    - Tổng giá trị: {total_value:,.0f}
                    - Tên quỹ: {cert.short_name_vn or cert.symbol}
                    """
                else:
                    record.fund_config_info = "Chưa có thông tin quỹ từ fund.certificate"
            except Exception as e:
                _logger.error(f"Lỗi lấy thông tin từ fund.certificate: {e}")
                record.fund_config_info = f"Lỗi: {str(e)}"
    
    # Constraints
    @api.constrains('opening_ccq', 'opening_avg_price')
    def _check_positive_values(self):
        for record in self:
            if record.opening_ccq < 0:
                raise ValidationError(_('Opening CCQ cannot be negative'))
            if record.opening_avg_price < 0:
                raise ValidationError(_('Opening Average Price cannot be negative'))
    
    @api.constrains('inventory_date')
    def _check_inventory_date(self):
        for record in self:
            if record.inventory_date and record.inventory_date > fields.Date.today():
                raise ValidationError(_('Inventory date cannot be in the future'))
    
    # Onchange methods
    @api.onchange('fund_id', 'inventory_date')
    def _onchange_fund_date(self):
        """Tự động lấy dữ liệu khi chọn fund và ngày"""
        if self.fund_id and self.inventory_date:
            try:
                # 1. Thử lấy dữ liệu từ ngày trước
                previous_values = self._get_previous_closing_values()
                if previous_values:
                    self.opening_ccq = previous_values['closing_ccq']
                    self.opening_avg_price = previous_values['closing_avg_price']
                    _logger.info(f"Đã lấy dữ liệu từ ngày trước: CCQ={self.opening_ccq}, Giá={self.opening_avg_price}")
                    return

                # 2. Thử lấy từ nav.fund.config (nếu có model này)
                try:
                    if 'nav.fund.config' in self.env:
                        fund_config = self.env['nav.fund.config'].search([
                            ('fund_id', '=', self.fund_id.id),
                            ('active', '=', True)
                        ], limit=1)
                        # Chỉ lấy nếu có dữ liệu thực sự (> 0)
                        if fund_config and (fund_config.initial_ccq_quantity > 0 or fund_config.initial_nav_price > 0):
                            self.opening_ccq = fund_config.initial_ccq_quantity
                            self.opening_avg_price = fund_config.initial_nav_price
                            # Force compute
                            self.opening_value = self.opening_ccq * self.opening_avg_price
                            _logger.info(f"Đã lấy dữ liệu từ cấu hình quỹ: CCQ={self.opening_ccq}, Giá={self.opening_avg_price}")
                            return
                        elif fund_config:
                             _logger.warning(f"Tìm thấy cấu hình quỹ nhưng giá trị = 0, bỏ qua để fallback sang fund.certificate")
                except Exception as e:
                    _logger.warning(f"Lỗi check nav.fund.config: {e}")

                # 3. Thử lấy từ fund.certificate (Logic fallback chính)
                # Dùng sudo() để đảm bảo quyền truy cập nếu cần
                fund_sudo = self.fund_id.sudo()
                if fund_sudo.certificate_id and fund_sudo.certificate_id.exists():
                     cert = fund_sudo.certificate_id
                     self.opening_ccq = cert.initial_certificate_quantity or 0.0
                     self.opening_avg_price = cert.initial_certificate_price or 0.0
                     # Force compute opening_value cho UI hiển thị ngay
                     self.opening_value = self.opening_ccq * self.opening_avg_price
                     _logger.info(f"Đã lấy dữ liệu từ fund.certificate ({cert.symbol}): CCQ={self.opening_ccq}, Giá={self.opening_avg_price}, Giá trị={self.opening_value}")
                     return
                else:
                    _logger.warning(f"Fund {self.fund_id.name} không có certificate_id linked")

                # 4. Mặc định
                self.opening_ccq = 0.0
                self.opening_avg_price = 0.0
                _logger.warning(f"Không tìm thấy dữ liệu đầu ngày cho {self.fund_id.name}")

            except Exception as e:
                _logger.error(f"Lỗi lấy dữ liệu mặc định: {e}")
                self.opening_ccq = 0.0
                self.opening_avg_price = 0.0

    # Methods
    def _auto_load_opening_data(self):
        """Tự động lấy dữ liệu đầu ngày khi cần thiết - chỉ khi dữ liệu chưa có hoặc = 0"""
        try:
            if not self.fund_id or not self.inventory_date:
                return
            
            # Chỉ lấy dữ liệu khi thực sự cần thiết
            need_ccq = not self.opening_ccq or self.opening_ccq == 0.0
            need_price = not self.opening_avg_price or self.opening_avg_price == 0.0
            
            if not need_ccq and not need_price:
                _logger.info(f"Đã có dữ liệu đầu ngày: CCQ={self.opening_ccq}, Giá={self.opening_avg_price}")
                return
            
            # Lấy dữ liệu từ ngày trước
            previous_values = self._get_previous_closing_values()
            if previous_values:
                if need_ccq:
                    self.opening_ccq = previous_values.get('closing_ccq', 0.0)
                if need_price:
                    self.opening_avg_price = previous_values.get('closing_avg_price', 0.0)
                _logger.info(f"Auto-loaded từ ngày trước: CCQ={self.opening_ccq}, Giá={self.opening_avg_price}")
            else:
                # Lấy từ fund.certificate trong fund_management_control
                cert = self.fund_id.certificate_id
                if cert and cert.exists():
                    if need_ccq:
                        self.opening_ccq = cert.initial_certificate_quantity or 0.0
                    if need_price:
                        self.opening_avg_price = cert.initial_certificate_price or 0.0
                    _logger.info(f"Auto-loaded từ fund.certificate: CCQ={self.opening_ccq}, Giá={self.opening_avg_price}")
                else:
                    if need_ccq:
                        self.opening_ccq = 0.0
                    if need_price:
                        self.opening_avg_price = 0.0
                    _logger.warning(f"Không tìm thấy fund.certificate cho {self.fund_id.name}")
        except Exception as e:
            _logger.error(f"Lỗi auto-load dữ liệu đầu ngày: {e}")
            if not self.opening_ccq or self.opening_ccq == 0.0:
                self.opening_ccq = 0.0
            if not self.opening_avg_price or self.opening_avg_price == 0.0:
                self.opening_avg_price = 0.0

    @api.model
    def sync_from_fund_certificate(self, fund_id, certificate_data):
        """Đồng bộ dữ liệu từ fund.certificate sang tất cả bản ghi tồn kho của quỹ"""
        try:
            if not fund_id or not certificate_data:
                return
            
            # Tìm tất cả bản ghi tồn kho của quỹ này
            inventories = self.search([('fund_id', '=', fund_id)])
            
            if not inventories:
                _logger.info(f"Không tìm thấy bản ghi tồn kho cho quỹ {fund_id}")
                return
            
            updated_count = 0
            for inventory in inventories:
                try:
                    # Cập nhật dữ liệu từ fund.certificate
                    inventory.with_context(
                        skip_fund_sync=True,
                        skip_nav_config_sync=True,
                        skip_certificate_sync=True
                    ).write({
                        'opening_ccq': certificate_data.get('initial_certificate_quantity', 0.0),
                        'opening_avg_price': certificate_data.get('initial_certificate_price', 0.0),
                    })
                    updated_count += 1
                    _logger.info(f"Đã cập nhật tồn kho {inventory.id} từ fund.certificate")
                    
                except Exception as e:
                    _logger.error(f"Lỗi cập nhật tồn kho {inventory.id}: {e}")
                    continue
            
            _logger.info(f"Hoàn thành đồng bộ: cập nhật {updated_count}/{len(inventories)} bản ghi tồn kho cho quỹ {fund_id}")
            
        except Exception as e:
            _logger.error(f"Lỗi đồng bộ từ fund.certificate: {e}")

    def _onchange_load_previous_defaults(self):
        """Tự động lấy dữ liệu từ ngày trước hoặc cấu hình quỹ"""
        for record in self:
            if not record.fund_id or not record.inventory_date:
                _logger.warning(f"Thiếu thông tin fund_id hoặc inventory_date")
                return
            
            try:
                _logger.info(f"Bắt đầu load dữ liệu mặc định cho quỹ {record.fund_id.name} ngày {record.inventory_date}")
                
                # 1. Thử lấy dữ liệu từ ngày trước
                previous_values = record._get_previous_closing_values()
                if previous_values:
                    record.opening_ccq = previous_values.get('closing_ccq', 0.0)
                    record.opening_avg_price = previous_values.get('closing_avg_price', 0.0)
                    _logger.info(f"Đã lấy dữ liệu từ ngày trước: CCQ={record.opening_ccq}, Giá={record.opening_avg_price}")
                    return

                # 2. Thử lấy từ nav.fund.config (nếu có model này)
                try:
                    if 'nav.fund.config' in self.env:
                        fund_config = self.env['nav.fund.config'].search([
                            ('fund_id', '=', record.fund_id.id),
                            ('active', '=', True)
                        ], limit=1)
                        if fund_config and (fund_config.initial_ccq_quantity > 0 or fund_config.initial_nav_price > 0):
                            record.opening_ccq = fund_config.initial_ccq_quantity
                            record.opening_avg_price = fund_config.initial_nav_price
                            # Force compute
                            record.opening_value = record.opening_ccq * record.opening_avg_price
                            _logger.info(f"Đã lấy dữ liệu từ cấu hình quỹ: CCQ={record.opening_ccq}, Giá={record.opening_avg_price}")
                            return
                        elif fund_config:
                             _logger.warning(f"Tìm thấy cấu hình quỹ {record.fund_id.name} nhưng giá trị = 0, bỏ qua")
                except Exception as e:
                    _logger.warning(f"Lỗi check nav.fund.config: {e}")

                # 3. Thử lấy từ fund.certificate (Logic fallback chính)
                fund_sudo = record.fund_id.sudo()
                if fund_sudo.certificate_id and fund_sudo.certificate_id.exists():
                     cert = fund_sudo.certificate_id
                     record.opening_ccq = cert.initial_certificate_quantity or 0.0
                     record.opening_avg_price = cert.initial_certificate_price or 0.0
                     # Force compute opening_value
                     record.opening_value = record.opening_ccq * record.opening_avg_price
                     _logger.info(f"Đã lấy dữ liệu từ fund.certificate ({cert.symbol}): CCQ={record.opening_ccq}, Giá={record.opening_avg_price}, Giá trị={record.opening_value}")
                     return
                else:
                    _logger.warning(f"Fund {record.fund_id.name} không có certificate_id linked")

                # 4. Mặc định
                record.opening_ccq = 0.0
                record.opening_avg_price = 0.0
                _logger.warning(f"Không tìm thấy dữ liệu đầu ngày cho {record.fund_id.name}, sử dụng giá trị mặc định")
            except Exception as e:
                _logger.error(f"Lỗi lấy dữ liệu mặc định: {e}")
                record.opening_ccq = 0.0
                record.opening_avg_price = 0.0
    
    def _get_previous_closing_values(self):
        """Lấy giá trị cuối ngày từ ngày trước"""
        try:
            if not self.fund_id or not self.inventory_date:
                return None
            
            # Tìm bản ghi ngày trước
            previous_date = self.inventory_date - timedelta(days=1)
            previous_record = self.search([
                ('fund_id', '=', self.fund_id.id),
                ('inventory_date', '=', previous_date)
            ], limit=1)
            
            if previous_record and previous_record.closing_ccq > 0:
                _logger.info(f"Tìm thấy dữ liệu ngày trước: {previous_date}")
                return {
                    'closing_ccq': previous_record.closing_ccq,
                    'closing_avg_price': previous_record.closing_avg_price
                }
            
            # Nếu không có ngày trước, tìm bản ghi gần nhất trước ngày hiện tại
            nearest_record = self.search([
                ('fund_id', '=', self.fund_id.id),
                ('inventory_date', '<', self.inventory_date),
                ('closing_ccq', '>', 0)  # Chỉ lấy bản ghi có dữ liệu
            ], order='inventory_date desc', limit=1)
            
            if nearest_record:
                _logger.info(f"Tìm thấy dữ liệu gần nhất: {nearest_record.inventory_date}")
                return {
                    'closing_ccq': nearest_record.closing_ccq,
                    'closing_avg_price': nearest_record.closing_avg_price
                }
            
            _logger.info(f"Không tìm thấy dữ liệu ngày trước cho fund {self.fund_id.name}")
            return None
        except Exception as e:
            _logger.error(f"Lỗi lấy dữ liệu ngày trước: {e}")
            return None
    
    @api.model
    def create(self, vals):
        """Tự động lấy dữ liệu mặc định khi tạo mới"""
        try:
            # Guard: tránh duplicate theo (fund_id, inventory_date)
            fund_id = vals.get('fund_id')
            inventory_date = vals.get('inventory_date') or fields.Date.today()
            if fund_id and inventory_date:
                exists = self.search([
                    ('fund_id', '=', fund_id),
                    ('inventory_date', '=', inventory_date)
                ], limit=1)
                if exists:
                    raise ValidationError(_('Đã tồn tại tồn kho cho quỹ này trong ngày %s') % inventory_date)

            record = super().create(vals)
            # Chỉ gọi các method nếu record đã được tạo thành công
            if record:
                try:
                    record._onchange_load_previous_defaults()
                except Exception as e:
                    _logger.warning(f"Lỗi khi load previous defaults: {e}")
                
                # Chỉ tính toán nếu chưa có dữ liệu để tránh vòng lặp
                if not record.closing_ccq and not record.closing_avg_price:
                    try:
                        record._auto_calculate_inventory()
                    except Exception as e:
                        _logger.warning(f"Lỗi khi auto calculate inventory: {e}")
            return record
        except Exception as e:
            _logger.error(f"Lỗi khi tạo nav.daily.inventory: {e}")
            raise

    def write(self, vals):
        """Chặn cập nhật gây trùng (fund_id, inventory_date) và tự động tính toán lại khi cần"""
        try:
            # 1. Kiểm tra trùng lặp nếu có thay đổi fund_id hoặc inventory_date
            change_fund = 'fund_id' in vals
            change_date = 'inventory_date' in vals
            if change_fund or change_date:
                for rec in self:
                    target_fund = vals.get('fund_id', rec.fund_id.id)
                    target_date = vals.get('inventory_date', rec.inventory_date)
                    if target_fund and target_date:
                        dup = self.search([
                            ('id', '!=', rec.id),
                            ('fund_id', '=', target_fund),
                            ('inventory_date', '=', target_date)
                        ], limit=1)
                        if dup:
                            raise ValidationError(_('Đã tồn tại tồn kho cho quỹ này trong ngày %s') % target_date)
            
            # 2. Thực hiện write
            result = super().write(vals)
            
            # 3. Tự động tính toán lại nếu có thay đổi quan trọng
            important_fields = ['fund_id', 'inventory_date', 'opening_ccq', 'opening_avg_price']
            if any(field in vals for field in important_fields):
                for record in self:
                    try:
                        _logger.debug(f"Phát hiện thay đổi quan trọng, tính toán lại tồn kho cho {record.fund_id.name}")
                        record.force_recompute_all_fields()
                    except Exception as e:
                        _logger.warning(f"Lỗi khi auto calculate inventory cho record {record.id}: {e}")
            
            return result
        except ValidationError:
            raise
        except Exception as e:
            _logger.error(f"Lỗi khi cập nhật nav.daily.inventory: {e}")
            raise
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Override để tự động tạo tồn kho khi mở view"""
        result = super().fields_view_get(view_id, view_type, toolbar, submenu)
        
        # Tự động tạo tồn kho thiếu khi mở list view
        if view_type == 'list' and self.env.context.get('search_default_today'):
            try:
                self._auto_create_missing_inventories()
            except Exception as e:
                _logger.error(f"Lỗi tự động tạo tồn kho khi mở view: {e}")
        
        return result
    
    def _auto_calculate_inventory(self):
        """Tự động tính toán tồn kho"""
        for record in self:
            try:
                # Kiểm tra flag để tránh vòng lặp
                if hasattr(record, '_calculating_inventory') and record._calculating_inventory:
                    return
                
                # Set flag để tránh vòng lặp
                record._calculating_inventory = True
                
                # Force refresh các trường computed để đảm bảo tính toán mới nhất
                record.invalidate_cache(['closing_ccq', 'closing_avg_price', 'closing_value', 'ccq_change', 'price_change', 'value_change'])
                
                # Kiểm tra dữ liệu đầu vào
                if not record.opening_ccq or not record.opening_avg_price:
                    try:
                        record._onchange_load_previous_defaults()
                    except Exception as e:
                        _logger.warning(f"Lỗi khi load previous defaults: {e}")
                
                # Tính toán các giá trị theo thứ tự đúng với logging chi tiết
                try:
                    # 1. Tính CCQ cuối ngày trước
                    record._compute_closing_ccq()
                    _logger.info(f"Đã tính CCQ cuối ngày cho {record.fund_id.name}: {record.closing_ccq}")
                except Exception as e:
                    _logger.warning(f"Lỗi tính closing CCQ: {e}")
                
                try:
                    # 2. Tính giá trung bình cuối ngày (phụ thuộc vào CCQ)
                    record._compute_closing_avg_price()
                    _logger.info(f"Đã tính giá TB cuối ngày cho {record.fund_id.name}: {record.closing_avg_price}")
                except Exception as e:
                    _logger.warning(f"Lỗi tính closing avg price: {e}")
                
                try:
                    # 3. Tính giá trị cuối ngày (phụ thuộc vào CCQ và giá TB)
                    record._compute_closing_value()
                    _logger.info(f"Đã tính giá trị cuối ngày cho {record.fund_id.name}: {record.closing_value}")
                except Exception as e:
                    _logger.warning(f"Lỗi tính closing value: {e}")
                
                try:
                    # 4. Tính các thay đổi (phụ thuộc vào tất cả giá trị trên)
                    record._compute_changes()
                    _logger.info(f"Đã tính thay đổi cho {record.fund_id.name}: CCQ={record.ccq_change}, Giá={record.price_change}, Giá trị={record.value_change}")
                except Exception as e:
                    _logger.warning(f"Lỗi tính changes: {e}")
                
                try:
                    # 5. Tính chi tiết giao dịch (phụ thuộc vào dữ liệu giao dịch)
                    record._compute_transaction_details()
                except Exception as e:
                    _logger.warning(f"Lỗi tính transaction details: {e}")
                
                try:
                    # 6. Tính chi tiết tính toán (phụ thuộc vào tất cả giá trị)
                    record._compute_calculation_details()
                except Exception as e:
                    _logger.warning(f"Lỗi tính calculation details: {e}")
                
                # Clear flag
                record._calculating_inventory = False
                
                # Log kết quả cuối cùng
                _logger.info(f"Hoàn thành tính toán tồn kho cho {record.fund_id.name}: CCQ={record.closing_ccq}, Giá TB={record.closing_avg_price}, Giá trị={record.closing_value}")
                
                # Force refresh UI để hiển thị dữ liệu mới nhất
                record.refresh()
                    
            except Exception as e:
                _logger.error(f"Lỗi tự động tính toán tồn kho: {e}")
                # Clear flag trong trường hợp lỗi
                if hasattr(record, '_calculating_inventory'):
                    record._calculating_inventory = False
    
    def force_refresh_calculations(self):
        """Force refresh tất cả các tính toán để đảm bảo dữ liệu mới nhất"""
        for record in self:
            try:
                _logger.info(f"Force refresh calculations cho {record.fund_id.name}")
                # Invalidate cache tất cả trường computed
                record.invalidate_cache(['closing_ccq', 'closing_avg_price', 'closing_value', 'ccq_change', 'price_change', 'value_change', 'transaction_details', 'calculation_details'])
                # Tính toán lại
                record._auto_calculate_inventory()
                # Refresh record
                record.refresh()
            except Exception as e:
                _logger.error(f"Lỗi force refresh calculations: {e}")
    
    def force_recompute_all_fields(self):
        """Force recompute tất cả các trường computed để đảm bảo dữ liệu mới nhất"""
        for record in self:
            try:
                _logger.info(f"Force recompute all fields cho {record.fund_id.name}")
                # Force recompute tất cả trường computed
                record._compute_closing_ccq()
                record._compute_closing_avg_price()
                record._compute_closing_value()
                record._compute_changes()
                record._compute_transaction_details()
                record._compute_calculation_details()
                _logger.info(f"Hoàn thành recompute: CCQ={record.closing_ccq}, Giá TB={record.closing_avg_price}, Giá trị={record.closing_value}")
            except Exception as e:
                _logger.error(f"Lỗi force recompute all fields: {e}")
    
    @api.model
    def create_daily_inventory_for_fund(self, fund_id, inventory_date):
        """Tạo bản ghi tồn kho cho quỹ và ngày cụ thể"""
        try:
            _logger.info(f"Bắt đầu tạo tồn kho cho quỹ {fund_id} ngày {inventory_date}")
            
            # Kiểm tra xem đã có bản ghi chưa
            existing = self.search([
                ('fund_id', '=', fund_id),
                ('inventory_date', '=', inventory_date)
            ], limit=1)
            
            if existing:
                _logger.info(f"Đã tồn tại bản ghi tồn kho cho quỹ {fund_id} ngày {inventory_date}")
                return existing
            
            # Tạo bản ghi mới với dữ liệu ban đầu
            vals = {
                'fund_id': fund_id,
                'inventory_date': inventory_date,
                'status': 'draft'
            }
            
            _logger.info(f"Tạo bản ghi mới với dữ liệu: {vals}")
            
            # Tạo bản ghi
            inventory = self.create(vals)
            
            if not inventory:
                _logger.error(f"Không thể tạo bản ghi tồn kho cho quỹ {fund_id}")
                return None
            
            _logger.info(f"Đã tạo bản ghi tồn kho ID {inventory.id}")
            
            # Tự động lấy dữ liệu ban đầu
            try:
                inventory._onchange_load_previous_defaults()
                _logger.info(f"Đã load dữ liệu ban đầu: CCQ={inventory.opening_ccq}, Giá={inventory.opening_avg_price}")
            except Exception as e:
                _logger.warning(f"Lỗi load dữ liệu ban đầu: {e}")
            
            # Tự động tính toán
            try:
                inventory._auto_calculate_inventory()
                _logger.info(f"Đã tính toán tồn kho: CCQ cuối={inventory.closing_ccq}, Giá cuối={inventory.closing_avg_price}")
            except Exception as e:
                _logger.warning(f"Lỗi tính toán tồn kho: {e}")
            
            _logger.info(f"Hoàn thành tạo tồn kho cho quỹ {fund_id} ngày {inventory_date}")
            return inventory
            
        except Exception as e:
            _logger.error(f"Lỗi tạo tồn kho cho quỹ {fund_id} ngày {inventory_date}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @api.model
    def refresh_inventory_after_transaction_change(self, fund_id, inventory_date):
        """Refresh tồn kho sau khi có thay đổi giao dịch"""
        try:
            _logger.info(f"Refresh tồn kho sau thay đổi giao dịch cho quỹ {fund_id} ngày {inventory_date}")
            
            # Tìm bản ghi tồn kho
            inventory = self.search([
                ('fund_id', '=', fund_id),
                ('inventory_date', '=', inventory_date)
            ], limit=1)
            
            if inventory:
                # Force recompute tất cả trường computed
                inventory.force_recompute_all_fields()
                return {'success': True, 'message': 'Đã refresh tồn kho sau thay đổi giao dịch'}
            else:
                return {'success': False, 'message': 'Không tìm thấy bản ghi tồn kho'}
        except Exception as e:
            _logger.error(f"Lỗi refresh tồn kho sau thay đổi giao dịch: {e}")
            return {'success': False, 'message': str(e)}
    
    @api.model
    def auto_refresh_all_inventories(self):
        """Tự động refresh tất cả tồn kho để đảm bảo dữ liệu mới nhất"""
        try:
            _logger.info("Bắt đầu auto refresh tất cả tồn kho")
            
            # Lấy tất cả tồn kho hôm nay
            today = fields.Date.today()
            inventories = self.search([
                ('inventory_date', '=', today)
            ])
            
            for inventory in inventories:
                try:
                    inventory.force_recompute_all_fields()
                    _logger.info(f"Đã refresh tồn kho cho {inventory.fund_id.name}")
                except Exception as e:
                    _logger.warning(f"Lỗi refresh tồn kho cho {inventory.fund_id.name}: {e}")
            
            return {'success': True, 'message': f'Đã refresh {len(inventories)} tồn kho'}
        except Exception as e:
            _logger.error(f"Lỗi auto refresh tất cả tồn kho: {e}")
            return {'success': False, 'message': str(e)}
    
    @api.model
    def auto_create_today_inventory(self):
        """Tự động tạo tồn kho cho ngày hôm nay"""
        try:
            today = fields.Date.today()
            _logger.info(f"Bắt đầu tự động tạo tồn kho cho ngày {today}")
            
            # Lấy tất cả quỹ đang hoạt động
            funds = self.env['portfolio.fund'].search([('active', '=', True)])
            _logger.info(f"Tìm thấy {len(funds)} quỹ đang hoạt động")
            
            if not funds:
                _logger.warning("Không tìm thấy quỹ nào đang hoạt động")
                return {'success': True, 'created': 0, 'total': 0, 'message': 'Không có quỹ nào đang hoạt động'}
            
            created_count = 0
            skipped_count = 0
            
            for fund in funds:
                try:
                    # Kiểm tra xem đã có bản ghi chưa
                    existing = self.search([
                        ('fund_id', '=', fund.id),
                        ('inventory_date', '=', today)
                    ], limit=1)
                    
                    if existing:
                        _logger.info(f"Đã tồn tại tồn kho cho quỹ {fund.name} ngày {today}")
                        skipped_count += 1
                        continue
                    
                    # Tạo bản ghi tồn kho cho quỹ
                    inventory = self.create_daily_inventory_for_fund(fund.id, today)
                    if inventory:
                        created_count += 1
                        _logger.info(f"Đã tạo tồn kho cho quỹ {fund.name} ngày {today}")
                    else:
                        _logger.error(f"Không thể tạo tồn kho cho quỹ {fund.name}")
                        
                except Exception as e:
                    _logger.error(f"Lỗi tạo tồn kho cho quỹ {fund.name}: {e}")
                    continue
            
            result = {
                'success': True, 
                'created': created_count, 
                'skipped': skipped_count,
                'total': len(funds),
                'message': f"Đã tạo {created_count} tồn kho mới, bỏ qua {skipped_count} đã tồn tại"
            }
            
            _logger.info(f"Hoàn thành: {result['message']}")
            return result
            
        except Exception as e:
            _logger.error(f"Lỗi tự động tạo tồn kho: {e}")
            return {'success': False, 'error': str(e), 'created': 0, 'total': 0}
    
    @api.model
    def cron_auto_create_daily_inventory(self):
        """Cron job để tự động tạo tồn kho hàng ngày - chạy mỗi giờ để kiểm tra"""
        try:
            today = fields.Date.today()
            _logger.info(f"Bắt đầu cron auto create daily inventory cho ngày {today}")
            
            # Lấy tất cả quỹ active
            funds = self.env['portfolio.fund'].search([('status', '=', 'active')])
            created_count = 0
            
            for fund in funds:
                try:
                    # Kiểm tra xem đã có bản ghi cho ngày hôm nay chưa
                    existing = self.search([
                        ('fund_id', '=', fund.id),
                        ('inventory_date', '=', today)
                    ], limit=1)
                    
                    if not existing:
                        # Tạo bản ghi mới cho ngày hôm nay
                        inventory = self.create_daily_inventory_for_fund(fund.id, today)
                        if inventory:
                            created_count += 1
                            _logger.info(f"Đã tạo tồn kho cho quỹ {fund.name} ngày {today}")
                        else:
                            _logger.warning(f"Không thể tạo tồn kho cho quỹ {fund.name}")
                    else:
                        _logger.info(f"Đã có tồn kho cho quỹ {fund.name} ngày {today}")
                        
                except Exception as e:
                    _logger.error(f"Lỗi tạo tồn kho cho quỹ {fund.name}: {e}")
                    continue
            
            _logger.info(f"Hoàn thành cron: tạo {created_count}/{len(funds)} tồn kho")
            return {'success': True, 'created': created_count, 'total': len(funds)}
            
        except Exception as e:
            _logger.error(f"Lỗi cron auto create daily inventory: {e}")
            return {'success': False, 'error': str(e)}

    @api.model
    def auto_create_daily_inventory_cron(self):
        """Cron job để tự động tạo tồn kho hàng ngày"""
        return self.auto_create_today_inventory()
    
    @api.model
    def ensure_daily_inventory_exists(self, fund_id, inventory_date=None):
        """Đảm bảo có bản ghi tồn kho cho quỹ và ngày cụ thể"""
        try:
            if not inventory_date:
                inventory_date = fields.Date.today()
            
            # Kiểm tra xem đã có bản ghi chưa
            existing = self.search([
                ('fund_id', '=', fund_id),
                ('inventory_date', '=', inventory_date)
            ], limit=1)
            
            if existing:
                return existing
            
            # Tạo bản ghi mới nếu chưa có
            inventory = self.create_daily_inventory_for_fund(fund_id, inventory_date)
            if inventory:
                _logger.info(f"Đã tạo tồn kho cho quỹ {fund_id} ngày {inventory_date}")
                return inventory
            else:
                _logger.warning(f"Không thể tạo tồn kho cho quỹ {fund_id} ngày {inventory_date}")
                return None
                
        except Exception as e:
            _logger.error(f"Lỗi ensure daily inventory: {e}")
            return None

    @api.model
    def close_yesterday_inventories(self):
        """Chuyển các tồn kho của ngày hôm qua về trạng thái 'confirmed' nếu chưa xác nhận."""
        try:
            today = fields.Date.today()
            from datetime import timedelta as _td
            yesterday = today - _td(days=1)
            records = self.search([
                ('inventory_date', '=', yesterday),
                ('status', '!=', 'confirmed')
            ])
            for rec in records:
                try:
                    rec.status = 'confirmed'
                    _logger.info(f"Đã tự động xác nhận tồn kho: fund={rec.fund_id.name}, date={rec.inventory_date}")
                except Exception as e:
                    _logger.warning(f"Không thể đóng tồn kho {rec.id}: {e}")
            return {'success': True, 'confirmed': len(records)}
        except Exception as e:
            _logger.error(f"Lỗi khi đóng tồn kho ngày hôm qua: {e}")
            return {'success': False, 'message': str(e)}

    @api.model
    def cron_rollover_daily_inventory(self):
        """Cron: đóng bản ghi ngày hôm qua rồi tạo bản ghi hôm nay."""
        try:
            self.close_yesterday_inventories()
        finally:
            return self.auto_create_today_inventory()
    
    def action_create_today_inventory(self):
        """Action để tạo tồn kho hôm nay thủ công"""
        try:
            # Sử dụng method tự động tạo tồn kho thiếu
            created_count = self.env['nav.daily.inventory']._auto_create_missing_inventories()
            
            if created_count > 0:
                message = f'Đã tự động tạo {created_count} tồn kho mới'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Thành công',
                        'message': message,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Thông tin',
                        'message': 'Tất cả quỹ đã có tồn kho cho ngày hôm nay',
                        'type': 'info',
                        'sticky': False,
                    }
                }
        except Exception as e:
            _logger.error(f"Lỗi tạo tồn kho thủ công: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_confirm(self):
        """Xác nhận tồn kho cuối ngày"""
        for record in self:
            if record.status == 'draft':
                record.status = 'confirmed'
                _logger.info(f"Đã xác nhận tồn kho cho quỹ {record.fund_id.name} ngày {record.inventory_date}")
        return True
    
    @api.model
    def _auto_create_missing_inventories(self):
        """Tự động tạo tồn kho thiếu cho ngày hôm nay"""
        try:
            today = fields.Date.today()
            _logger.info(f"Kiểm tra và tự động tạo tồn kho thiếu cho ngày {today}")
            
            # Lấy tất cả quỹ đang hoạt động
            funds = self.env['portfolio.fund'].search([('active', '=', True)])
            
            created_count = 0
            for fund in funds:
                # Kiểm tra xem đã có tồn kho chưa
                existing = self.search([
                    ('fund_id', '=', fund.id),
                    ('inventory_date', '=', today)
                ], limit=1)
                
                if not existing:
                    _logger.info(f"Tự động tạo tồn kho cho quỹ {fund.name} ngày {today}")
                    try:
                        inventory = self.create_daily_inventory_for_fund(fund.id, today)
                        if inventory:
                            created_count += 1
                    except Exception as e:
                        _logger.error(f"Lỗi tự động tạo tồn kho cho quỹ {fund.name}: {e}")
            
            if created_count > 0:
                _logger.info(f"Đã tự động tạo {created_count} tồn kho mới")
            
            return created_count
            
        except Exception as e:
            _logger.error(f"Lỗi trong quá trình tự động tạo tồn kho: {e}")
            return 0
    
    @api.model
    def auto_create_inventory_for_date(self, target_date):
        """Tự động tạo tồn kho cho ngày cụ thể"""
        try:
            # Lấy tất cả quỹ đang hoạt động
            funds = self.env['portfolio.fund'].search([('active', '=', True)])
            
            created_count = 0
            for fund in funds:
                try:
                    # Tạo bản ghi tồn kho cho quỹ
                    inventory = self.create_daily_inventory_for_fund(fund.id, target_date)
                    if inventory:
                        created_count += 1
                        _logger.info(f"Đã tạo tồn kho cho quỹ {fund.name} ngày {target_date}")
                except Exception as e:
                    _logger.error(f"Lỗi tạo tồn kho cho quỹ {fund.name}: {e}")
                    continue
            
            _logger.info(f"Đã tạo tồn kho cho {created_count}/{len(funds)} quỹ ngày {target_date}")
            return {'success': True, 'created': created_count, 'total': len(funds)}
        except Exception as e:
            _logger.error(f"Lỗi tự động tạo tồn kho cho ngày {target_date}: {e}")
            return {'success': False, 'error': str(e)}
    
    def recalculate_inventory_after_transaction_change(self, fund_id, inventory_date):
        """Tính lại tồn kho sau khi có thay đổi giao dịch"""
        try:
            # Tìm bản ghi tồn kho
            inventory = self.search([
                ('fund_id', '=', fund_id),
                ('inventory_date', '=', inventory_date)
            ], limit=1)
            
            if inventory:
                inventory._auto_calculate_inventory()
                return {'success': True, 'message': 'Đã tính lại tồn kho'}
            else:
                return {'success': False, 'message': 'Không tìm thấy bản ghi tồn kho'}
        except Exception as e:
            _logger.error(f"Lỗi tính lại tồn kho: {e}")
            return {'success': False, 'message': str(e)}