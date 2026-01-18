/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";

export class PeriodicWidget extends Component {
    static template = xml`
        <div class="tm-container">
            <div class="tm-scope container py-4">
                <!-- Tabs -->
                <div class="tm-tabs mb-4">
                    <a href="/transaction_management/pending" class="nav-link">Lệnh chờ xử lý</a>
                    <a href="/transaction_management/order" class="nav-link">Lịch sử giao dịch</a>
                    <!-- <a href="/transaction_management/periodic" class="nav-link active">Quản lý định kỳ</a> -->
                </div>

                <!-- Section header -->
                <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3 mb-4">
                    <div>
                        <h2 class="h4 fw-bold mb-1">Quản lý định kỳ</h2>
                        <div class="d-flex align-items-center gap-3 text-sm">
                             <div class="d-flex align-items-center gap-2">
                                <span class="text-muted small">Tổng số lệnh:</span>
                                <span class="fw-bold text-dark"><t t-esc="state.orders.length"/></span>
                            </div>
                            <div class="d-flex align-items-center gap-1">
                                <span class="badge-dot bg-info"></span>
                                <span class="text-muted small">Mua:</span>
                                <span class="fw-bold text-dark"><t t-esc="state.orders.filter(o => o.transaction_type === 'Mua').length"/></span>
                            </div>
                            <div class="d-flex align-items-center gap-1">
                                <span class="badge-dot bg-success"></span>
                                <span class="text-muted small">Bán:</span>
                                <span class="fw-bold text-dark"><t t-esc="state.orders.filter(o => o.transaction_type === 'Bán').length"/></span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tm-filter pt-0 ms-md-auto">
                         <button type="button" class="btn-create" t-on-click="() => console.log('Create Generic')">
                            <i class="fas fa-plus me-2"></i> Tạo lệnh định kỳ
                        </button>
                    </div>
                </div>

                <!-- Table -->
                <div class="tm-card mb-4 p-0">
                    <div class="table-responsive" style="min-height: 250px;">
                        <table class="tm-table mb-0">
                            <thead>
                                <tr>
                                    <th>Tên CCQ</th>
                                    <th>Số tiền đăng ký đầu tư</th>
                                    <th>Số kỳ hạn</th>
                                    <th>Lãi suất</th>
                                    <th>Ngày đáo hạn</th>
                                    <th>Số ngày còn lại</th>
                                    <th>Trạng thái đầu tư</th>
                                    <th>Kỳ đầu tư tiếp theo</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-if="state.orders and state.orders.length > 0">
                                    <t t-foreach="state.orders" t-as="order" t-key="order.order_code">
                                        <tr>
                                            <td class="text-center fw-semibold text-primary"><t t-esc="order.fund_name"/><t t-if="order.fund_ticker"> (<t t-esc="order.fund_ticker"/>)</t></td>
                                            <td class="text-center fw-bold text-dark"><t t-esc="order.amount"/><t t-esc="order.currency"/></td>
                                            <td class="text-center">
                                                <span class="badge-premium badge-info">
                                                    <t t-esc="order.tenor_months || 'N/A'"/> tháng
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span class="badge-premium badge-success">
                                                    <t t-esc="order.interest_rate || 'N/A'"/>
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span class="text-primary fw-medium">
                                                    <t t-esc="order.maturity_date || 'N/A'"/>
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <span class="badge-premium badge-warning">
                                                    <t t-esc="order.days_to_maturity || 'N/A'"/> ngày
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <div class="d-flex flex-column align-items-center">
                                                    <span class="badge-premium badge-secondary mb-1">
                                                        <t t-esc="order.invest_status || 'Đang tham gia'"/>
                                                    </span>
                                                    <span class="text-muted small" style="font-size:0.75rem"><t t-esc="order.invest_status_detail"/></span>
                                                </div>
                                            </td>
                                            <td class="text-center"><t t-esc="order.session_date"/></td>
                                            <td class="text-center">
                                                <div class="dropdown">
                                                    <button class="btn btn-link text-secondary p-0" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                                        <i class="fas fa-ellipsis-h text-primary"></i>
                                                    </button>
                                                     <ul class="dropdown-menu">
                                                         <li><a class="dropdown-item" href="#">Chi tiết</a></li>
                                                         <li><a class="dropdown-item text-danger" href="#">Hủy lệnh</a></li>
                                                     </ul>
                                                </div>
                                            </td>
                                        </tr>
                                    </t>
                                </t>
                                <t t-if="!state.orders or state.orders.length === 0">
                                    <tr>
                                        <td colspan="9" class="text-center text-muted py-5">
                                            <i class="fas fa-calendar-check fa-2x mb-3 text-muted opacity-50"></i>
                                            <div>Không có dữ liệu quản lý định kỳ</div>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Pagination and info -->
                <div class="d-flex flex-column flex-md-row align-items-center justify-content-between gap-3 text-secondary small">
                    <div>
                        Hiển thị <span class="fw-semibold text-dark"><t t-esc="state.orders.length"/></span> kết quả
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
    `;

    setup() {
        this.state = useState({
            orders: this.props.orders || [],
            pageSize: 10,
            currentPage: 1
        });
    }

    changePageSize(size) {
        this.state.pageSize = parseInt(size);
        // Có thể thêm logic phân trang ở đây
    }
}

window.PeriodicWidget = PeriodicWidget; 