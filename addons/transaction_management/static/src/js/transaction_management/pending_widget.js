/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";

export class PendingWidget extends Component {
    static template = xml`
        <div class="tm-container">
            <div class="tm-scope container py-4">
                <!-- Tabs -->
                <div class="tm-tabs mb-4">
                    <a href="/transaction_management/pending" class="nav-link active">Lệnh chờ xử lý</a>
                    <a href="/transaction_management/order" class="nav-link">Lịch sử giao dịch</a>
                    <!-- <a href="/transaction_management/periodic" class="nav-link">Quản lý định kỳ</a> -->
                </div>

                <!-- Section header -->
                <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3 mb-4">
                    <div>
                        <h2 class="h4 fw-bold mb-1">
                            Lệnh chờ <t t-esc="state.currentFilter === 'buy' ? 'mua' : state.currentFilter === 'sell' ? 'bán' : 'chuyển đổi'"/>
                        </h2>
                        <p class="mb-0 text-muted small">
                            Tổng số lệnh: <span class="fw-semibold text-dark"><t t-esc="state.filteredOrders.length"/></span>
                        </p>
                    </div>

                    <!-- Filter & Actions -->
                    <div class="tm-filter">
                        <button t-att-data-filter="'buy'"
                                t-attf-class="btn-filter buy #{state.currentFilter === 'buy' ? 'active' : ''}"
                                t-on-click="() => this.filterOrders('buy')" type="button">
                            Lệnh chờ mua
                        </button>
                        <button t-att-data-filter="'sell'"
                                t-attf-class="btn-filter sell #{state.currentFilter === 'sell' ? 'active' : ''}"
                                t-on-click="() => this.filterOrders('sell')" type="button">
                            Lệnh chờ bán
                        </button>
                        <button id="create-order-btn"
                                class="btn-create ms-md-2"
                                type="button"
                                t-on-click="() => this.createOrder()">
                            <i class="fas fa-plus me-2"></i>
                            <span id="create-btn-text">
                                <t t-esc="state.currentFilter === 'buy' ? 'Tạo lệnh mua' : 'Tạo lệnh bán'"/>
                            </span>
                        </button>
                    </div>
                </div>

                <!-- Table container -->
                <div class="tm-card mb-4 p-0">
                    <div class="table-responsive" style="min-height: 250px;">
                        <table class="tm-table mb-0">
                            <thead>
                                <tr>
                                    <th>TK Giao dịch</th>
                                    <th>Quỹ - Chương trình</th>
                                    <th>Ngày đặt lệnh</th>
                                    <th>Mã lệnh</th>
                                    <th>Số lượng (CCQ)</th>
                                    <th>Giá</th>
                                    <th id="amount-column">
                                        <t t-if="state.currentFilter === 'buy'">Giá trị đầu tư</t>
                                        <t t-elif="state.currentFilter === 'sell' or state.currentFilter === 'exchange'">Giá trị ước tính</t>
                                        <t t-else="">Số tiền</t>
                                    </th>
                                    <th>Phiên giao dịch</th>
                                    <th>Trạng thái</th>
                                    <th>Hợp đồng</th>
                                    <th>Khớp</th>
                                    <th>Thao tác</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-if="state.filteredOrders and state.filteredOrders.length > 0">
                                    <t t-foreach="state.filteredOrders" t-as="order" t-key="order.order_code">
                                        <tr>
                                            <td class="text-center"><t t-esc="order.account_number"/></td>
                                            <td class="text-center fw-semibold text-primary"><t t-esc="order.fund_name"/><t t-if="order.fund_ticker"> (<t t-esc="order.fund_ticker"/>)</t></td>
                                            <td class="text-center"><t t-esc="order.order_date"/></td>
                                            <td class="text-center font-monospace text-muted small" style="max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" t-att-title="order.order_code">
                                                <t t-esc="order.order_code"/>
                                            </td>
                                            <td class="text-center fw-semibold">
                                                <t t-esc="formatNumber(order.units)"/>
                                            </td>
                                            <td class="text-center">
                                                <t t-esc="formatPrice(order.price)"/>
                                            </td>
                                            <td class="text-center">
                                                <t t-esc="formatCurrency(order.amount)"/>
                                            </td>
                                            <td class="text-center"><t t-esc="order.session_date"/></td>
                                            <td class="text-center">
                                                <span t-attf-class="badge-premium #{ this.badgeClass(order.status) }">
                                                    <t t-esc="order.status"/>
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <t t-if="order.order_mode !== 'normal' and (order.has_contract or order.contract_url)">
                                                    <div class="dropdown">
                                                        <button class="btn btn-sm btn-outline-primary dropdown-toggle rounded-pill px-3" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                                            Hợp đồng
                                                        </button>
                                                        <ul class="dropdown-menu">
                                                            <li><a class="dropdown-item" t-att-href="order.contract_url" target="_blank"><i class="fas fa-eye me-2 text-info"></i>Xem</a></li>
                                                            <li><a class="dropdown-item" t-att-href="order.contract_download_url"><i class="fas fa-download me-2 text-success"></i>Tải về</a></li>
                                                        </ul>
                                                    </div>
                                                </t>
                                                <t t-else="">
                                                    <span class="text-muted small">—</span>
                                                </t>
                                            </td>
                                            <td class="text-center">
                                                <t t-if="order.executions and order.executions.length">
                                                    <button class="btn btn-xs btn-outline-secondary" t-on-click="() => this.toggleExecutionDetail(order.id)">
                                                        <i t-att-class="state.expandedExecutionRows.includes(order.id) ? 'fas fa-minus-square' : 'fas fa-plus-square'"></i>
                                                    </button>
                                                </t>
                                                <t t-else="">—</t>
                                            </td>
                                            <td class="text-center">
                                                <div class="btn-group">
                                                    <button class="btn btn-sm btn-info text-white me-1" t-on-click="() => this.openDetailPopup(order)" title="Chi tiết" style="width: 32px; height: 32px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center;">
                                                        <i class="fas fa-eye"></i>
                                                    </button>
                                                    <button class="btn btn-sm btn-danger text-white" t-on-click="() => this.cancelOrder(order)" title="Huỷ lệnh" style="width: 32px; height: 32px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center;">
                                                        <i class="fas fa-times"></i>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                        <!-- Execution detail rows -->
                                        <t t-if="state.expandedExecutionRows.includes(order.id)">
                                            <t t-foreach="order.executions || []" t-as="exec" t-key="'exec-' + exec.id">
                                                <tr class="execution-detail-row" style="background: #f8fafc;">
                                                    <td class="text-center text-muted" colspan="2"><i class="fas fa-link me-1"></i>Chi tiết khớp</td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center fw-semibold"><t t-esc="formatNumber(exec.matched_quantity)"/></td>
                                                    <td class="text-center"><t t-esc="formatCurrency(exec.matched_price)"/></td>
                                                    <td class="text-center"><t t-esc="exec.match_date"/></td>
                                                    <td class="text-center"><span class="badge-premium badge-success">Khớp</span></td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center"></td>
                                                </tr>
                                            </t>
                                        </t>
                                    </t>
                                </t>
                                <t t-if="!state.filteredOrders or state.filteredOrders.length === 0">
                                    <tr>
                                        <td colspan="11" class="text-center text-muted py-5">
                                            <i class="fas fa-inbox fa-2x mb-3 text-muted opacity-50"></i>
                                            <div>Không có dữ liệu lệnh chờ xử lý</div>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Pagination -->
                <div class="d-flex flex-column flex-md-row align-items-center justify-content-between gap-3 text-secondary small">
                    <div>
                        Hiển thị <span class="fw-semibold text-dark"><t t-esc="state.filteredOrders.length"/></span> kết quả
                    </div>
                    
                    <div class="tm-pagination">
                         <button class="btn-page" disabled="1"><i class="fas fa-chevron-left"></i></button>
                         <button class="btn-page active">1</button>
                         <button class="btn-page" disabled="1"><i class="fas fa-chevron-right"></i></button>
                    </div>

                    <!-- Pagination selector removed per user request -->
                    <div></div>
                </div>
            </div>
        </div>
        
        <!-- Detail Popup (Keeping mostly same structure but cleaning classes) -->
        <t t-if="state.showDetailPopup">
            <div class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);z-index:2000;">
                <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable" style="z-index:2001;">
                    <div class="modal-content tm-card border-0 p-0 overflow-hidden">
                        <div class="modal-header text-white" style="background: linear-gradient(135deg, #F26522, #d9581b);">
                            <h2 class="modal-title h6 fw-bold mb-0 text-white">Thông tin giao dịch</h2>
                            <button type="button" class="btn-close btn-close-white" t-on-click="() => this.state.showDetailPopup = false"></button>
                        </div>
                        <div class="modal-body p-4">
                             <!-- ... (Content inside mostly fine, just ensuring classes are standard) ... -->
                                    <div class="mb-4 pb-3 border-bottom">
                                        <h6 class="text-primary fw-bold mb-3">Thông tin chi tiết lệnh</h6>
                                        <div class="row g-3 small">
                                            <div class="col-4 text-muted">Quỹ đầu tư:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.fund_full_name || state.selectedOrder.fund_name"/></div>
                                            <div class="col-4 text-muted">Chương trình:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.fund_name"/></div>
                                            
                                            <!-- New Fields -->
                                            <div class="col-4 text-muted">Loại hình:</div>
                                            <div class="col-8 fw-medium text-dark">
                                                <t t-if="state.selectedOrder.investment_type === 'fund_certificate'">Chứng chỉ quỹ</t>
                                                <t t-elif="state.selectedOrder.investment_type === 'stock'">Cổ phiếu</t>
                                                <t t-elif="state.selectedOrder.investment_type === 'bond'">Trái phiếu</t>
                                                <t t-else=""><t t-esc="state.selectedOrder.investment_type"/></t>
                                            </div>
                                            
                                            <div class="col-4 text-muted">Phương thức:</div>
                                            <div class="col-8 fw-medium text-dark">
                                                <t t-if="state.selectedOrder.order_mode === 'normal'">Lệnh thường</t>
                                                <t t-elif="state.selectedOrder.order_mode === 'negotiated'">Lệnh thỏa thuận</t>
                                                <t t-else="">Lệnh thường</t>
                                            </div>

                                            <div class="col-4 text-muted">Loại lệnh:</div><div class="col-8 fw-medium text-dark">
                                                <span class="badge bg-light text-dark border">
                                                    <t t-if="state.selectedOrder.order_type_detail"><t t-esc="state.selectedOrder.order_type_detail"/></t>
                                                    <t t-else=""><t t-esc="state.selectedOrder.transaction_type === 'buy' ? 'MUA' : (state.selectedOrder.transaction_type === 'sell' ? 'BÁN' : 'HOÁN ĐỔI')"/></t>
                                                </span>
                                            </div>

                                            <div class="col-4 text-muted">Sàn giao dịch:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.market || 'HOSE'"/></div>

                                            <div class="col-4 text-muted">Ngày đặt lệnh:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.order_date || state.selectedOrder.session_date"/></div>
                                            <div class="col-4 text-muted">Số lượng:</div><div class="col-8 fw-bold text-primary"><t t-esc="formatNumber(state.selectedOrder.units || 0)"/></div>
                                            <div class="col-4 text-muted">Giá đặt:</div><div class="col-8 fw-bold text-dark"><t t-esc="formatPrice(state.selectedOrder.price)"/></div>
                                            <div class="col-4 text-muted">Tổng giá trị:</div><div class="col-8 fw-bold text-danger"><t t-esc="formatCurrency(state.selectedOrder.amount)"/></div>
                                            
                                            <t t-if="state.selectedOrder.t2_date">
                                                <div class="col-4 text-muted"><t t-esc="state.selectedOrder.transaction_type === 'sell' ? 'Ngày tiền về' : 'Ngày hàng về'"/>:</div><div class="col-8 fw-medium text-primary"><t t-esc="state.selectedOrder.t2_date"/></div>
                                            </t>
                                        </div>
                                    </div>
                                    <!-- End of shared template section, simplifying logic by using one block for both buy/sell/exchange since fields are mostly same -->
                         </div>
                    </div>
                </div>
                <div class="modal-backdrop fade show" style="z-index:1999;" t-on-click="() => this.state.showDetailPopup = false"></div>
            </div>
        </t>
    `;

    setup() {
        this.state = useState({
            orders: this.props.orders || [],
            filteredOrders: [],
            currentFilter: 'buy',
            pageSize: 10,
            currentPage: 1,
            showDetailPopup: false,
            selectedOrder: {}, // Init as empty object to avoid null access
            expandedExecutionRows: [],
        });

        this.filterOrders('buy'); 
    }

    toggleExecutionDetail(orderId) {
        const idx = this.state.expandedExecutionRows.indexOf(orderId);
        if (idx === -1) {
            this.state.expandedExecutionRows.push(orderId);
        } else {
            this.state.expandedExecutionRows.splice(idx, 1);
        }
        this.state.expandedExecutionRows = [...this.state.expandedExecutionRows];
    }

    formatNumber(value) {
        if (value === null || value === undefined) return '0';
        const num = Number(String(value).replace(/[^0-9.-]+/g, '')) || 0;
        return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(num);
    }

    formatPrice(value) {
        if (value === null || value === undefined) return '0';
        const num = Number(String(value).replace(/[^0-9.-]+/g, '')) || 0;
        return new Intl.NumberFormat('vi-VN', { minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(num);
    }

    formatCurrency(value) {
        if (value === null || value === undefined) return '0đ';
        const num = Number(String(value).replace(/[^0-9.-]+/g, '')) || 0;
        return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(num) + 'đ';
    }

    async cancelOrder(order) {
        // Confirm before cancelling
        const confirmed = confirm(`Bạn có chắc chắn muốn huỷ lệnh ${order.order_code}?`);
        if (!confirmed) return;

        try {
            const response = await fetch('/transaction_management/cancel_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { order_id: order.id },
                }),
            });
            const result = await response.json();
            if (result.result && result.result.success) {
                alert('Huỷ lệnh thành công!');
                // Reload page to refresh data
                window.location.reload();
            } else {
                alert(result.result?.message || 'Có lỗi xảy ra khi huỷ lệnh');
            }
        } catch (error) {
            console.error('Cancel order error:', error);
            alert('Có lỗi xảy ra khi huỷ lệnh');
        }
    }

    badgeStyle(status) {
        // Các trạng thái dùng cam #f97316
        const orangeStatuses = ['pending', 'cancelled', 'Chờ khớp lệnh', 'Đang chờ'];
        if (orangeStatuses.includes(status)) {
            return 'background-color:#f97316;color:#fff';
        }
        // Mặc định giữ nguyên màu chữ tối để tương phản với các bg-* mặc định
        return '';
    }

    badgeClass(status) {
        // Chuẩn hóa status về chữ thường để map dễ hơn
        const normalized = (status || '').toString().trim().toLowerCase();
        // Map trạng thái -> màu Bootstrap hợp lý
        switch (normalized) {
            case 'pending':
            case 'chờ khớp lệnh':
            case 'đang chờ':
                return 'badge-warning';
            case 'completed':
            case 'hoàn tất':
            case 'khớp thành công':
                return 'badge-success';
            case 'cancelled':
            case 'đã hủy':
                return 'badge-danger';
            case 'đang xử lý':
            case 'processing':
                return 'badge-info';
            case 'đã từ chối':
            case 'rejected':
                return 'badge-secondary';
            default:
                return 'badge-secondary';
        }
    }

    filterOrders(filterType) {
        this.state.currentFilter = filterType;
        // Lọc dữ liệu theo loại giao dịch
        let filtered = this.state.orders;
        if (filterType === 'buy') {
            filtered = this.state.orders.filter(order => order.transaction_type === 'buy');
        } else if (filterType === 'sell') {
            filtered = this.state.orders.filter(order => order.transaction_type === 'sell');
        } else if (filterType === 'exchange') {
            filtered = this.state.orders.filter(order => order.transaction_type === 'exchange');
        }
        this.state.filteredOrders = filtered;
    }

    changePageSize(size) {
        this.state.pageSize = parseInt(size);
        // Có thể thêm logic phân trang ở đây
    }

    createOrder() {
        const filterType = this.state.currentFilter;
        let url = '/fund_buy'; // Mặc định

        if (filterType === 'sell') {
            url = '/fund_sell';
        } else if (filterType === 'exchange') {
            url = '/fund_swap';
        }

        window.location.href = url;
    }

    openDetailPopup(order) {
        this.state.selectedOrder = order;
        this.state.showDetailPopup = true;
    }

    copyToClipboard(text) {
        if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text);
        } else {
            // Fallback cho trình duyệt không hỗ trợ navigator.clipboard
            const input = document.createElement('input');
            input.value = text;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
        }
    }

    formatCurrency(val) {
        return Number(val).toLocaleString('vi-VN') + 'đ';
    }
}

window.PendingWidget = PendingWidget;
