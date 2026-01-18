/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";

export class OrderWidget extends Component {
    static template = xml`
        <div class="tm-container">
            <div class="tm-scope container py-4">
                <!-- Tabs -->
                <div class="tm-tabs mb-4">
                    <a href="/transaction_management/pending" class="nav-link">Lệnh chờ xử lý</a>
                    <a href="/transaction_management/order" class="nav-link active">Lịch sử giao dịch</a>
                    <!-- <a href="/transaction_management/periodic" class="nav-link">Quản lý định kỳ</a> -->
                </div>

                <!-- Section header + Search/Filter -->
                <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3 mb-4">
                    <div>
                        <h2 class="h4 fw-bold mb-1">Lịch sử giao dịch</h2>
                        <p class="mb-0 text-muted small">
                            Tổng số lệnh: <span class="fw-semibold text-dark"><t t-esc="state.orders.length"/></span>
                        </p>
                    </div>
                    
                    <div class="tm-filter pt-0 ms-md-auto">
                        <form class="d-flex flex-wrap gap-2 align-items-center" t-on-submit.prevent="() => this.search()">
                            <input type="text" placeholder="Nhập mã lệnh"
                                   class="form-control form-control-sm px-3 py-2 text-secondary bg-white"
                                   t-model="state.searchOrderCode"/>
                            <select class="form-select form-select-sm px-3 py-2 text-secondary bg-white"
                                    t-model="state.searchFund" t-on-change="() => this.filterOrders()">
                                <option value="">Chọn sản phẩm</option>
                                <t t-foreach="state.uniqueFunds" t-as="fund" t-key="fund">
                                    <option t-att-value="fund"><t t-esc="fund"/></option>
                                </t>
                            </select>
                            <select class="form-select form-select-sm px-3 py-2 text-secondary bg-white"
                                    t-model="state.searchType" t-on-change="() => this.filterOrders()">
                                <option value="">Chọn loại lệnh</option>
                                <option value="Mua">Lệnh mua</option>
                                <option value="Bán">Lệnh bán</option>
                            </select>
                            <input type="date" class="form-control form-control-sm px-3 py-2 text-secondary bg-white" 
                                   t-model="state.filterDate" t-on-change="() => this.filterOrders()" placeholder="Chọn ngày"/>
                            <button type="submit" class="btn-filter active d-flex align-items-center gap-2" aria-label="Search">
                                <i class="fas fa-search"></i>
                                <span>Tìm kiếm</span>
                            </button>
                            <button type="button" class="btn-filter px-2" aria-label="Settings" t-on-click="() => this.state.showColumnModal = true">
                                <i class="fas fa-cog"></i>
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Table container -->
                <div class="tm-card mb-4 p-0">
                    <div class="table-responsive" style="min-height: 250px;">
                        <table class="tm-table mb-0">
                            <thead>
                                <tr>
                                    <th t-if="state.visibleColumns.account_number">TK Giao dịch</th>
                                    <th t-if="state.visibleColumns.fund_name">Quỹ - Chương trình</th>
                                    <th t-if="state.visibleColumns.order_code">Mã lệnh</th>
                                    <th t-if="state.visibleColumns.transaction_type">Loại lệnh</th>
                                    <th t-if="state.visibleColumns.session_date">Ngày giao dịch</th>
                                    <th t-if="state.visibleColumns.units">Số lượng</th>
                                    <th t-if="state.visibleColumns.nav">Giá</th>
                                    <th t-if="state.visibleColumns.amount">Giá trị đầu tư</th>
                                    <th t-if="state.visibleColumns.purchase_fee">Phí</th>
                                    <th t-if="state.visibleColumns.status">Trạng thái</th>
                                    <th t-if="state.visibleColumns.contract">Hợp đồng</th>
                                    <th>Khớp</th>
                                    <th>Thao tác</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-if="state.filteredOrders and state.filteredOrders.length > 0">
                                    <t t-foreach="state.filteredOrders" t-as="order" t-key="order.order_code">
                                        <tr>
                                            <td class="text-center" t-if="state.visibleColumns.account_number"><t t-esc="order.account_number"/></td>
                                            <td class="text-center fw-semibold text-primary" t-if="state.visibleColumns.fund_name"><t t-esc="order.fund_name"/><t t-if="order.fund_ticker"> (<t t-esc="order.fund_ticker"/>)</t></td>
                                            <td class="text-center font-monospace text-muted small" t-if="state.visibleColumns.order_code" style="max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" t-att-title="order.order_code">
                                                <t t-esc="order.order_code"/>
                                            </td>
                                            <td class="text-center" t-if="state.visibleColumns.transaction_type">
                                                <span t-attf-class="badge-premium #{ this.typeClass(order.transaction_type) }">
                                                    <t t-if="order.transaction_type === 'buy'">Mua</t>
                                                    <t t-elif="order.transaction_type === 'sell'">Bán</t>
                                                    <t t-elif="order.transaction_type === 'exchange'">Hoán đổi</t>
                                                    <t t-else=""><t t-esc="order.transaction_type"/></t>
                                                </span>
                                            </td>
                                            <td class="text-center" t-if="state.visibleColumns.session_date"><t t-esc="order.session_date"/></td>
                                            <td class="text-center fw-semibold" t-if="state.visibleColumns.units"><t t-esc="formatNumber(order.units)"/></td>
                                            <td class="text-center" t-if="state.visibleColumns.nav"><t t-esc="formatPrice(order.nav || order.price)"/></td>
                                            <td class="text-center" t-if="state.visibleColumns.amount"><t t-esc="formatCurrency(order.amount)"/></td>
                                            <td class="text-center" t-if="state.visibleColumns.purchase_fee"><t t-esc="formatCurrency(order.fee)"/></td>
                                            <td class="text-center" t-if="state.visibleColumns.status">
                                                <span t-attf-class="badge-premium #{ this.statusClass(order.status) }">
                                                    <t t-esc="order.status"/>
                                                </span>
                                            </td>
                                            <td class="text-center" t-if="state.visibleColumns.contract">
                                                <t t-if="order.order_mode !== 'normal' and order.has_contract">
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
                                                <t t-else=""><span class="text-muted">—</span></t>
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
                                                <button class="btn btn-sm btn-info text-white" t-on-click="() => this.openDetail(order)" title="Chi tiết" style="width: 32px; height: 32px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center;">
                                                    <i class="fas fa-eye"></i>
                                                </button>
                                            </td>
                                        </tr>
                                        <!-- Execution detail rows -->
                                        <t t-if="state.expandedExecutionRows.includes(order.id)">
                                            <t t-foreach="order.executions || []" t-as="exec" t-key="'exec-' + exec.id">
                                                <tr class="execution-detail-row" style="background: #f8fafc;">
                                                    <td class="text-center text-muted" colspan="2"><i class="fas fa-link me-1"></i>Chi tiết khớp</td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center"><t t-esc="exec.match_date"/></td>
                                                    <td class="text-center fw-semibold"><t t-esc="formatNumber(exec.matched_quantity)"/></td>
                                                    <td class="text-center"><t t-esc="formatPrice(exec.matched_price)"/></td>
                                                    <td class="text-center"><t t-esc="formatCurrency(exec.total_value)"/></td>
                                                    <td class="text-center" colspan="3"></td>
                                                    <td class="text-center"><span class="badge-premium badge-success">Khớp</span></td>
                                                    <td class="text-center"></td>
                                                    <td class="text-center"></td>
                                                </tr>
                                            </t>
                                        </t>
                                    </t>
                                </t>
                                <t t-if="!state.filteredOrders or state.filteredOrders.length === 0">
                                    <tr>
                                        <td colspan="15" class="text-center text-muted py-5">
                                            <i class="fas fa-history fa-2x mb-3 text-muted opacity-50"></i>
                                            <div>Không có dữ liệu lịch sử giao dịch</div>
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

                <!-- Modal chọn cột -->
                <t t-if="state.showColumnModal">
                    <div class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);z-index:2000;">
                        <div class="modal-dialog modal-dialog-centered" style="z-index:2001;">
                            <div class="modal-content tm-card border-0 p-0 overflow-hidden">
                                <div class="modal-header text-white" style="background: linear-gradient(135deg, #F26522, #d9581b);">
                                    <h3 class="modal-title h6 fw-bold mb-0 text-white">Chọn cột hiển thị</h3>
                                    <button type="button" class="btn-close btn-close-white" t-on-click="() => this.state.showColumnModal = false"></button>
                                </div>
                                <div class="modal-body p-4">
                                    <div class="row g-2 mb-3">
                                        <div class="col-12 mb-2">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" t-on-change="toggleAllColumns" id="checkAll"/>
                                                <label class="form-check-label fw-semibold" for="checkAll">Chọn tất cả</label>
                                            </div>
                                        </div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.account_number"/><label class="form-check-label">TK Chứng khoán</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.fund_name"/><label class="form-check-label">Quỹ - Chương trình</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.order_code"/><label class="form-check-label">Mã lệnh</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.transaction_type"/><label class="form-check-label">Loại lệnh</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.session_date"/><label class="form-check-label">Ngày giao dịch</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.units"/><label class="form-check-label">Số lượng</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.nav"/><label class="form-check-label">NAV</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.amount"/><label class="form-check-label">Tổng tiền</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.purchase_fee"/><label class="form-check-label">Phí</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.tax"/><label class="form-check-label">Thuế</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.total_after_fee"/><label class="form-check-label">Số tiền sau thuế/phí</label></div></div>
                                        <div class="col-6"><div class="form-check"><input class="form-check-input" type="checkbox" t-model="state.visibleColumns.status"/><label class="form-check-label">Trạng thái</label></div></div>
                                    </div>
                                    <div class="d-flex justify-content-end gap-2">
                                        <button class="btn btn-light" t-on-click="() => this.state.showColumnModal = false">Đóng</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-backdrop fade show" t-on-click="() => this.state.showColumnModal = false"></div>
                    </div>
                </t>
                <!-- Popup chi tiết giao dịch -->
                <t t-if="state.showDetailPopup">
                    <div class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);z-index:2000;">
                        <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable" style="z-index:2001;">
                            <div class="modal-content tm-card border-0 p-0 overflow-hidden">
                                <div class="modal-header text-white" style="background: linear-gradient(135deg, #F26522, #d9581b);">
                                    <h2 class="modal-title h6 fw-bold mb-0 text-white">Thông tin giao dịch</h2>
                                    <button type="button" class="btn-close btn-close-white" t-on-click="() => this.state.showDetailPopup = false"></button>
                                </div>
                                <div class="modal-body p-4">
                                    <div class="mb-4 pb-3 border-bottom">
                                        <h6 class="text-primary fw-bold mb-3">Thông tin chi tiết giao dịch</h6>
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

                                            <!-- Existing Fields -->
                                            <div class="col-4 text-muted">Loại giao dịch:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.transaction_type"/></div>
                                            <div class="col-4 text-muted">Ngày đặt lệnh:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.order_date || state.selectedOrder.session_date"/></div>
                                            <div class="col-4 text-muted">Phiên giao dịch:</div><div class="col-8 fw-medium text-dark"><t t-esc="state.selectedOrder.session_date"/></div>
                                            <div class="col-4 text-muted">Số lượng (CCQ):</div><div class="col-8 fw-bold text-primary"><t t-esc="formatNumber(state.selectedOrder.units || 0)"/> CCQ</div>
                                            <div class="col-4 text-muted">Giá:</div><div class="col-8 fw-bold text-dark"><t t-esc="formatPrice(state.selectedOrder.nav || state.selectedOrder.price)"/></div>
                                            <div class="col-4 text-muted">Số tiền:</div><div class="col-8 fw-bold text-danger"><t t-esc="formatCurrency(state.selectedOrder.amount)"/></div>
                                            <t t-if="state.selectedOrder.t2_date">
                                                <div class="col-4 text-muted"><t t-esc="state.selectedOrder.transaction_type === 'sell' ? 'Ngày tiền về' : 'Ngày hàng về'"/>:</div><div class="col-8 fw-medium text-primary"><t t-esc="state.selectedOrder.t2_date"/></div>
                                            </t>
                                        </div>
                                    </div>
                                    <t t-if="state.selectedOrder.has_contract">
                                        <div class="mb-2">
                                            <div class="fw-bold mb-2 text-dark">Hợp đồng</div>
                                            <div class="d-flex gap-2">
                                                <a t-att-href="state.selectedOrder.contract_url" target="_blank" class="badge-premium badge-info text-decoration-none">Xem hợp đồng</a>
                                                <a t-att-href="state.selectedOrder.contract_download_url" class="badge-premium badge-info text-decoration-none">Tải về</a>
                                            </div>
                                        </div>
                                    </t>
                                </div>
                            </div>
                        </div>
                        <div class="modal-backdrop fade show" t-on-click="() => this.state.showDetailPopup = false"></div>
                    </div>
                </t>
            </div>
        </div>
    `;

    setup() {
        const safeOrders = Array.isArray(this.props.orders) ? this.props.orders.filter(Boolean) : [];
        this.state = useState({
            orders: safeOrders,
            filteredOrders: [],
            searchOrderCode: '',
            searchFund: '',
            searchType: '',
            filterDate: new Date().toLocaleDateString('en-CA'), // YYYY-MM-DD
            pageSize: 10,
            currentPage: 1,
            uniqueFunds: [...new Set(safeOrders.map(order => order.fund_name))],
            showColumnModal: false,
            showDetailPopup: false,
            selectedOrder: null,
            visibleColumns: {
                account_number: true,
                fund_name: true,
                order_code: true,
                transaction_type: true,
                session_date: true,
                units: true,
                nav: true,
                amount: true,
                purchase_fee: true,
                tax: true,
                total_after_fee: true,
                status: true,
                contract: true,
            },
            expandedExecutionRows: [],
        });
        this.filterOrders();
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

    toDateString(dateStr) {
        if (!dateStr) return '';
        // Nếu đã đúng dạng YYYY-MM-DD thì trả về luôn
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
        // Nếu có dạng YYYY-MM-DD HH:mm:ss
        if (/^\d{4}-\d{2}-\d{2}/.test(dateStr)) return dateStr.slice(0, 10);
        // Nếu dạng DD/MM/YYYY
        if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
            const [d, m, y] = dateStr.split('/');
            return `${y}-${m}-${d}`;
        }
        // Nếu dạng MM/DD/YYYY
        if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
            const [m, d, y] = dateStr.split('/');
            return `${y}-${m}-${d}`;
        }
        return dateStr;
    }

    filterOrders() {
        let filtered = this.state.orders;
        // Lọc theo mã lệnh
        if (this.state.searchOrderCode) {
            filtered = filtered.filter(order =>
                order.order_code && order.order_code.toLowerCase().includes(this.state.searchOrderCode.toLowerCase())
            );
        }
        // Lọc theo quỹ/sản phẩm
        if (this.state.searchFund) {
            filtered = filtered.filter(order => order.fund_name === this.state.searchFund);
        }
        // Lọc theo loại lệnh
        if (this.state.searchType) {
            filtered = filtered.filter(order => order.transaction_type === this.state.searchType);
        }
        // Lọc theo ngày giao dịch (Filter by specific date)
        if (this.state.filterDate) {
            filtered = filtered.filter(order => this.toDateString(order.session_date) === this.state.filterDate);
        }
        this.state.filteredOrders = Array.isArray(filtered) ? filtered.filter(Boolean).map(order => {
            // Use actual values from backend - already raw numbers
            const amount = Number(order.amount) || 0;
            const fee = Number(order.fee) || 0;  // Use actual fee from record
            return {
                ...order,
                amount: amount,
                fee: fee,
            };
        }) : [];
    }

    search() {
        this.filterOrders();
    }

    changePageSize(size) {
        this.state.pageSize = parseInt(size);
        // Có thể thêm logic phân trang ở đây
    }

    toggleAllColumns(ev) {
        const checked = ev.target.checked;
        Object.keys(this.state.visibleColumns).forEach(key => {
            this.state.visibleColumns[key] = checked;
        });
    }

    calculateFee(amount) {
        if (amount < 10000000) return amount * 0.003;
        else if (amount < 20000000) return amount * 0.002;
        else return amount * 0.001;
    }

    formatCurrency(val) {
        return Number(val).toLocaleString('vi-VN') + 'đ';
    }

    openDetail(order) {
        this.state.selectedOrder = order;
        this.state.showDetailPopup = true;
    }

    // Màu sắc cho loại lệnh
    // Màu sắc cho loại lệnh
    typeClass(type) {
        const t = (type || '').toString().trim().toLowerCase();
        switch (t) {
            case 'buy':
            case 'mua':
                return 'badge-success';
            case 'sell':
            case 'bán':
                return 'badge-danger';
            case 'exchange':
            case 'hoán đổi':
                return 'badge-info';
            default:
                return 'badge-secondary';
        }
    }

    // Màu sắc cho trạng thái
    statusClass(status) {
        const s = (status || '').toString().trim().toLowerCase();
        switch (s) {
            case 'pending':
            case 'chờ khớp lệnh':
            case 'đang chờ':
                return 'badge-warning';
            case 'completed':
            case 'hoàn tất':
            case 'khớp thành công':
            case 'đã khớp lệnh':
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
}

window.OrderWidget = OrderWidget; 