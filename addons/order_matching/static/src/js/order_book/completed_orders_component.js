/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";

export class CompletedOrdersComponent extends Component {
    static template = xml`
    <div class="order-book-page">
        <div class="order-book-hero">
            <div class="hero-content">
                <div class="hero-copy">
                    <div class="hero-pill">Trung tâm khớp lệnh</div>
                    <h1>Khoản đầu tư đã khớp</h1>
                    <p class="hero-lead">
                        Danh sách các giao dịch đã khớp lệnh theo từng quỹ, hỗ trợ bạn rà soát và đối soát nhanh chóng.
                    </p>
                    <div class="hero-meta">
                        <span>
                            Quỹ đang xem:
                            <strong t-if="state.selectedFund">
                                <t t-esc="state.selectedFund.name"/> (<t t-esc="state.selectedFund.ticker or ''"/>)
                            </strong>
                            <t t-else="">Chưa chọn</t>
                        </span>
                        <span class="status-chip">
                            <i class="fa fa-clock-o"></i>
                            Cập nhật:
                            <t t-esc="formatDateTime(state.lastUpdate)"/>
                        </span>
                    </div>
                    <div class="order-book-nav">
                        <a href="/order-book" class="nav-link">Khoản đầu tư chờ xử lý</a>
                        <a href="/completed-orders" class="nav-link active">Khoản đầu tư đã khớp</a>
                        <a href="/negotiated-orders" class="nav-link">Khoản đầu tư khớp theo thỏa thuận</a>

                    </div>
                    <t t-if="state.isMarketMaker">
                        <div class="mt-3">
                            <a href="/investment_dashboard" class="btn-back-market-maker" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: white; color: #2563EB; border: 2px solid #2563EB; border-radius: 8px; font-weight: 600; font-size: 14px; text-decoration: none; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2); transition: all 0.2s ease;">
                                <i class="fa fa-arrow-left"></i>Quay lại Dashboard
                            </a>
                        </div>
                    </t>
                </div>
            </div>
            <div class="hero-actions">
                <button class="btn btn-refresh" title="Làm mới dữ liệu" t-on-click="refreshData">
                    <i class="fa fa-refresh"></i>
                    Làm mới
                </button>
                <div class="hero-fund-card">
                    <div class="fund-control-header">
                        <p class="label">Chọn quỹ cần theo dõi</p>
                        <span class="helper-text">Lọc danh sách giao dịch đã khớp theo quỹ</span>
                    </div>
                    <div class="fund-combobox-wrapper">
                        <input 
                            id="fund-combobox-completed" 
                            type="text" 
                            class="fund-combobox-input"
                            placeholder="Nhập tên quỹ..." 
                            t-on-input="onFundComboboxInput"
                            t-on-focus="onFundComboboxFocus"
                            t-on-blur="onFundComboboxBlur"
                            t-on-keydown="onFundComboboxKeydown"
                        />
                        <i class="fa fa-chevron-down fund-combobox-arrow"></i>
                        <div class="fund-combobox-dropdown" t-att-class="{'show': state.showFundDropdown}">
                            <t t-if="getFilteredFunds().length === 0">
                                <div class="fund-combobox-no-results">Không tìm thấy quỹ</div>
                            </t>
                            <t t-foreach="getFilteredFunds()" t-as="fund" t-key="fund.id">
                                <div 
                                    class="fund-combobox-option"
                                    t-att-class="{'selected': state.selectedFund and state.selectedFund.id === fund.id}"
                                    t-on-click="onFundOptionClick"
                                    t-att-data-fund-id="fund.id"
                                >
                                    <div class="option-name"><t t-esc="fund.name"/></div>
                                    <div class="option-meta"><t t-esc="fund.ticker"/> • <t t-esc="fund.code or ''"/></div>
                                </div>
                            </t>
        </div>
                </div>
            </div>
            </div>
        </div>

        <div class="order-book-grid">
            <section class="order-column">
                <div class="column-header">
                    <div>
                        <p class="column-label">Danh sách giao dịch</p>
                        <h3><t t-esc="getFilteredOrders().length"/> lệnh đã khớp</h3>
                    </div>
                    <span class="column-badge">Hoàn tất khớp lệnh</span>
                </div>
                <div class="filter-bar" style="margin-bottom: 20px; padding: 12px 16px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div class="filter-nav type-filter-nav">
                        <nav class="nav nav-pills" style="gap: 8px;">
                            <a class="nav-link" t-att-class="state.typeFilter === 'all' ? 'active' : ''" href="#" t-on-click="() => this.changeTypeFilter('all')" style="padding: 8px 16px; border-radius: 6px; font-weight: 500;">Tất cả</a>
                            <a class="nav-link" t-att-class="state.typeFilter === 'buy' ? 'active' : ''" href="#" t-on-click="() => this.changeTypeFilter('buy')" style="padding: 8px 16px; border-radius: 6px; font-weight: 500;">Người mua</a>
                            <a class="nav-link" t-att-class="state.typeFilter === 'sell' ? 'active' : ''" href="#" t-on-click="() => this.changeTypeFilter('sell')" style="padding: 8px 16px; border-radius: 6px; font-weight: 500;">Người bán</a>
                            <a class="nav-link" t-att-class="state.typeFilter === 'partial' ? 'active' : ''" href="#" t-on-click="() => this.changeTypeFilter('partial')" style="padding: 8px 16px; border-radius: 6px; font-weight: 500;">Lệnh khớp một phần</a>
                        </nav>
                    </div>
                </div>
                <div class="column-body">
                    <div t-if="state.loading" class="state-card">
                        <i class="fa fa-spinner fa-spin"></i>
                        Đang tải dữ liệu...
                    </div>
                    <div t-if="!state.loading and state.orders.length === 0" class="state-card muted">
                        <i class="fa fa-info-circle"></i>
                        Không có giao dịch nào đã khớp
                </div>
                    <t t-if="!state.loading and state.orders.length > 0">
                            <div class="completed-table-wrapper">
                            <table class="order-table">
                                <thead t-att-class="{'collapsed': !state.showDetails}">
                                <tr>
                                        <th class="text-center">Loại</th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('price')">
                                            Giá <i t-att-class="getSortIcon('price')"></i>
                                        </th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('units')">
                                            SL đặt <i t-att-class="getSortIcon('units')"></i>
                                        </th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('matched_units')">
                                            SL đã khớp <i t-att-class="getSortIcon('matched_units')"></i>
                                        </th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('remaining_units')">
                                            SL còn lại <i t-att-class="getSortIcon('remaining_units')"></i>
                                        </th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('amount')">
                                            Thành tiền <i t-att-class="getSortIcon('amount')"></i>
                                        </th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('user_name')">
                                            Nhà đầu tư <i t-att-class="getSortIcon('user_name')"></i>
                                        </th>
                                        <th class="text-center sortable-header" style="cursor:pointer;" t-on-click="() => this.sortTable('created_at')">
                                            Thời gian đặt <i t-att-class="getSortIcon('created_at')"></i>
                                        </th>
                                        <th class="text-center">Trạng thái</th>
                                        <th class="text-center">Khớp</th>
                                </tr>
                            </thead>
                                <tbody t-att-class="{'collapsed-body': !state.showDetails}">
                                    <t t-foreach="getOrdersForPage()" t-as="order" t-key="order.id">
                                        <tr t-attf-class="#{order.type === 'sell' ? 'sell-order' : 'buy-order'}">
                                            <td class="text-center">
                                        <t t-if="order.type === 'sell'">Lệnh bán</t>
                                        <t t-else="">Lệnh mua</t>
                                    </td>
                                            <td class="text-center"><t t-esc="formatPrice(order.price)"/></td>
                                            <td class="text-center"><t t-esc="formatUnits(order.units)"/></td>
                                            <td class="text-center"><t t-esc="formatUnits(order.matched_units || 0)"/></td>
                                            <td class="text-center"><t t-esc="formatUnits(order.remaining_units || 0)"/></td>
                                            <td class="text-center"><t t-esc="formatAmount(order.amount)"/></td>
                                            <td class="text-center"><t t-esc="order.user_name"/></td>
                                            <td class="text-center"><t t-esc="formatDateTime(order.created_at)"/></td>
                                            <td class="text-center">
                                                <span t-attf-class="status-badge status-#{order.remaining_units > 0 ? 'info' : 'completed'}">
                                                    <t t-if="order.remaining_units > 0">Khớp một phần</t>
                                                    <t t-else="">Đã khớp</t>
                                                </span>
                                            </td>
                                            <td class="text-center">
                                                <t t-if="order.executions and order.executions.length">
                                                    <button class="btn btn-xs btn-outline-primary" t-on-click="() => this.toggleExecutionDetail(order.id)">
                                                        <i t-att-class="state.expandedExecutionRows.includes(order.id) ? 'fa fa-minus-square' : 'fa fa-plus-square'"></i>
                                                    </button>
                                                </t>
                                                <t t-else="">-</t>
                                            </td>
                                        </tr>
                                        <t t-if="state.expandedExecutionRows.includes(order.id)">
                                            <t t-foreach="order.executions or []" t-as="exec" t-key="'exec-' + exec.id">
                                                <tr class="split-detail-row">
                                                    <td class="text-center">
                                                        <i class="fa fa-link"></i>
                                                    </td>
                                                    <td class="text-center"><t t-esc="formatPrice(exec.matched_price)"/></td>
                                                    <td class="text-center"><t t-esc="formatUnits(exec.matched_quantity)"/></td>
                                                    <td class="text-center"><t t-esc="formatUnits(exec.matched_quantity)"/></td>
                                                    <td class="text-center">0</td>
                                                    <td class="text-center"><t t-esc="formatAmount(exec.total_value)"/></td>
                                                    <td class="text-center">
                                                        <t t-esc="exec.counter_investor || 'N/A'"/>
                                                        <span class="badge bg-light text-dark ms-1">
                                                            <t t-esc="exec.counter_type === 'sell' ? 'Bán' : 'Mua'"/>
                                                        </span>
                                                    </td>
                                                    <td class="text-center"><t t-esc="formatDateTime(exec.match_date)"/></td>
                                                    <td class="text-center">
                                                        <span class="status-badge status-completed">Khớp</span>
                                                    </td>
                                                    <td class="text-center">
                                                        <i class="fa fa-minus-square text-secondary"></i>
                                                    </td>
                                                </tr>
                                            </t>
                                        </t>
                                    </t>
                            </tbody>
                        </table>
                        </div>
                        <div class="matched-pagination d-flex justify-content-center align-items-center gap-2 mt-3">
                            <button class="btn btn-sm btn-outline-secondary" t-on-click="prevPage" t-att-disabled="isPrevPageDisabled()">
                                «
                            </button>
                            <t t-foreach="getPageNumbers()" t-as="p" t-key="'page-' + p">
                                <t t-if="p === 'ellipsis'">
                                    <span class="px-2">...</span>
                                </t>
                                <t t-else="">
                                    <button class="btn btn-sm" t-att-class="p === state.currentPage ? 'btn-primary' : 'btn-outline-secondary'" t-on-click="() => this.state.currentPage = p"><t t-esc="p"/></button>
                                </t>
                            </t>
                            <button class="btn btn-sm btn-outline-secondary" t-on-click="nextPage" t-att-disabled="isNextPageDisabled()">
                                »
                            </button>
                            <span class="ms-2 text-muted small">
                                (<t t-esc="state.orders.length"/> lệnh)
                            </span>
                        </div>
                    </t>
                </div>
            </section>
        </div>
    </div>`;

    setup() {
        this.state = useState({ 
            funds: [], 
            selectedFund: null, 
            orders: [], 
            loading: false, 
            lastUpdate: null,
            // Phân trang
            currentPage: 1,
            pageSize: 10,
            totalPages: 1,
            currentFundIndex: 0, // Track index quỹ hiện tại
            // Combobox quỹ
            fundSearchTerm: "",
            showFundDropdown: false,
            showDetails: true,
            expandedExecutionRows: [],
            typeFilter: 'all',
            isMarketMaker: false, // Track nếu user là Market Maker
            // Sort state
            sortField: '',
            sortOrder: 'asc' // 'asc' or 'desc'
        });
        this.autoRotateInterval = null;
        onMounted(async () => {
            await this.loadFunds();
            await this.refreshData();
            this.startAutoRotate();
            this.checkUserPermission();
        });
    }

    /**
     * Tải danh sách quỹ từ API
     */
    async loadFunds() {
        try {
            const res = await fetch('/api/transaction-list/funds', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({}) 
            });
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            const data = await res.json();
            
            if (data.success && data.funds) {
                this.state.funds = data.funds || [];
                if (this.state.funds.length > 0) {
                    this.state.currentFundIndex = 0;
                    this.state.selectedFund = this.state.funds[0];
                }
            } else {
                // Chỉ log lỗi thực sự
                if (data.message && !data.message.includes('Không có')) {
                    console.error('[LOAD FUNDS] Error:', data.message);
                }
                this.state.funds = [];
            }
        } catch (error) {
            // Chỉ log lỗi nghiêm trọng
            if (error.message && !error.message.includes('Network')) {
                console.error('[LOAD FUNDS] Unexpected error:', error);
            }
            this.state.funds = [];
        }
    }

    /**
     * Tải danh sách lệnh đã khớp hoàn toàn
     * 
     * Theo chuẩn Stock Exchange:
     * - Lệnh khớp hoàn toàn: remaining_units = 0 (units - matched_units = 0)
     * - Lệnh khớp một phần: remaining_units > 0 và matched_units > 0
     * 
     * Trang này chỉ hiển thị lệnh đã khớp hoàn toàn.
     * Lệnh khớp một phần được hiển thị ở trang "khớp một phần".
     */
    async refreshData() {
        if (!this.state.selectedFund) return;
        this.state.loading = true;
        try {
            const res = await fetch('/api/transaction-list/completed', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ fund_id: this.state.selectedFund.id }) 
            });
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            const data = await res.json();
            
            if (data.success && data.data) {
                // Lọc chỉ lấy lệnh đã khớp hoàn toàn (remaining_units = 0)
                // Tính toán: remaining_units = units - matched_units (theo chuẩn Stock Exchange)
                // Hiển thị cả lệnh khớp hoàn toàn và khớp một phần
                this.state.orders = data.data || [];
                // Cập nhật phân trang
                this.updatePagination();
            } else {
                // Chỉ log lỗi thực sự
                if (data.message && !data.message.includes('Không có')) {
                    console.error('[REFRESH DATA] Error:', data.message);
                }
                this.state.orders = [];
                this.updatePagination();
            }
            
            this.state.lastUpdate = new Date();
        } catch (error) {
            // Chỉ log lỗi nghiêm trọng
            if (error.message && !error.message.includes('Network')) {
                console.error('[REFRESH DATA] Unexpected error:', error);
            }
            this.state.orders = [];
            this.updatePagination();
        } finally {
            this.state.loading = false;
        }
    }

    async onFundChange(ev) {
        const id = parseInt(ev.target.value);
        const index = this.state.funds.findIndex(f => f.id === id);
        if (index !== -1) {
            this.state.currentFundIndex = index;
            this.state.selectedFund = this.state.funds[index];
            this.state.currentPage = 1; // Reset về trang 1 khi đổi fund
            await this.refreshData();
        }
    }

    /**
     * Bắt đầu tự động chuyển quỹ mỗi 1 phút
     * Hữu ích cho màn hình hiển thị công cộng
     */
    startAutoRotate() {
        // Dừng interval cũ nếu có
        if (this.autoRotateInterval) {
            clearInterval(this.autoRotateInterval);
        }
        // Tự động chuyển quỹ mỗi 1 phút (60 giây)
        this.autoRotateInterval = setInterval(() => {
            this.rotateToNextFund();
        }, 60000);
    }

    /**
     * Chuyển sang quỹ tiếp theo trong danh sách
     * Loop lại từ đầu nếu đã đến cuối danh sách
     */
    async rotateToNextFund() {
        if (!this.state.funds || this.state.funds.length <= 1) {
            return; // Không có quỹ hoặc chỉ có 1 quỹ thì không cần rotate
        }
        
        // Tăng index và loop lại từ đầu nếu đến cuối
        this.state.currentFundIndex = (this.state.currentFundIndex + 1) % this.state.funds.length;
        this.state.selectedFund = this.state.funds[this.state.currentFundIndex];
        this.state.currentPage = 1; // Reset về trang 1 khi đổi quỹ
        await this.refreshData();
    }

    /**
     * Cập nhật thông tin phân trang dựa trên số lượng lệnh hiện tại
     */
    updatePagination() {
        const total = this.getFilteredOrders().length;
        this.state.totalPages = Math.max(1, Math.ceil(total / this.state.pageSize));
        // Đảm bảo currentPage không vượt quá totalPages
        if (this.state.currentPage > this.state.totalPages) {
            this.state.currentPage = this.state.totalPages;
        }
    }

    changeTypeFilter(type) {
        this.state.typeFilter = type;
        this.state.currentPage = 1;
        this.updatePagination();
    }

    /**
     * Tính toán danh sách số trang để hiển thị
     * Hiển thị dạng rút gọn với ellipsis khi có nhiều trang
     * 
     * @returns {Array<number|string>} Danh sách số trang và ellipsis
     */
    getPageNumbers() {
        const totalPages = this.state.totalPages;
        const currentPage = this.state.currentPage;
        const pages = [];
        
        if (totalPages <= 7) {
            // Nếu tổng số trang <= 7, hiển thị tất cả
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Hiển thị dạng rút gọn: 1 2 3 4 5 ... 30 31 32
            pages.push(1);
            
            if (currentPage <= 4) {
                // Gần đầu: 1 2 3 4 5 ... last
                for (let i = 2; i <= 5; i++) {
                    pages.push(i);
                }
                pages.push('ellipsis');
                pages.push(totalPages);
            } else if (currentPage >= totalPages - 3) {
                // Gần cuối: 1 ... (n-4) (n-3) (n-2) (n-1) n
                pages.push('ellipsis');
                for (let i = totalPages - 4; i <= totalPages; i++) {
                    pages.push(i);
                }
            } else {
                // Ở giữa: 1 ... (current-1) current (current+1) ... last
                pages.push('ellipsis');
                for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                    pages.push(i);
                }
                pages.push('ellipsis');
                pages.push(totalPages);
            }
        }
        
        return pages;
    }

    // ===== Combobox chọn quỹ =====

    /**
     * Lọc danh sách quỹ theo từ khóa tìm kiếm
     * Tìm kiếm theo tên, ticker hoặc code
     * 
     * @returns {Array} Danh sách quỹ đã lọc
     */
    getFilteredFunds() {
        const funds = this.state.funds || [];
        const term = (this.state.fundSearchTerm || "").trim().toLowerCase();
        if (!term) {
            return funds;
        }

        const filtered = funds.filter((fund) => {
            const name = (fund.name || "").toLowerCase();
            const ticker = (fund.ticker || "").toLowerCase();
            const code = (fund.code || "").toLowerCase();
            return name.includes(term) || ticker.includes(term) || code.includes(term);
        });

        const selectedId = this.state.selectedFund && this.state.selectedFund.id;
        if (selectedId && !filtered.some((fund) => fund.id === selectedId)) {
            const currentFund = funds.find((fund) => fund.id === selectedId);
            if (currentFund) {
                return [currentFund, ...filtered];
            }
        }
        return filtered;
    }

    onFundComboboxInput(event) {
        if (!event || !event.target) {
            return;
        }
        const value = event.target.value || "";
        this.state.fundSearchTerm = value;
        this.state.showFundDropdown = true;
    }

    onFundComboboxFocus(event) {
        this.state.fundSearchTerm = "";
        if (event && event.target) {
            event.target.value = "";
        }
        this.state.showFundDropdown = true;
    }

    onFundComboboxBlur(event) {
        setTimeout(() => {
            this.state.showFundDropdown = false;
        }, 200);
    }

    onFundComboboxKeydown(event) {
        if (!event) return;
        
        const key = event.key;
        const filteredFunds = this.getFilteredFunds();
        
        if (key === 'Escape') {
            this.state.showFundDropdown = false;
            event.target.blur();
        } else if (key === 'Enter') {
            event.preventDefault();
            if (filteredFunds.length > 0) {
                this.selectFund(filteredFunds[0]);
            }
        } else if (key === 'ArrowDown' || key === 'ArrowUp') {
            event.preventDefault();
        }
    }

    onFundOptionClick(event) {
        if (!event || !event.currentTarget) {
            return;
        }
        const fundId = parseInt(event.currentTarget.getAttribute('data-fund-id'));
        const fund = this.state.funds.find(f => f.id === fundId);
        if (fund) {
            this.selectFund(fund);
        }
    }

    selectFund(fund) {
        this.state.selectedFund = fund;
        this.state.fundSearchTerm = "";
        this.state.showFundDropdown = false;
        const input = document.getElementById('fund-combobox-completed');
        if (input) {
            input.value = "";
        }
        this.state.currentPage = 1;
        this.refreshData();
    }

    toggleCollapse() {
        this.state.showDetails = !this.state.showDetails;
    }

    toggleSplitDetail(orderId) {
        const idx = this.state.expandedSplitRows.indexOf(orderId);
        if (idx === -1) {
            this.state.expandedSplitRows.push(orderId);
        } else {
            this.state.expandedSplitRows.splice(idx, 1);
        }
        this.state.expandedSplitRows = [...this.state.expandedSplitRows];
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

    getFilteredOrders() {
        const type = this.state.typeFilter;
        let data = this.state.orders || [];

        if (type === 'partial') {
            data = data.filter((o) => (o.remaining_units || 0) > 0 && (o.matched_units || 0) > 0);
        } else if (type !== 'all') {
            data = data.filter((o) => {
                const t = (o.type || o.transaction_type || '').toString();
                return type === 'buy' ? t === 'buy' : t === 'sell';
            });
        }

        return data;
    }

    changeTypeFilter(type) {
        this.state.typeFilter = type;
        this.state.currentPage = 1;
        this.updatePagination();
    }

    /**
     * Lấy danh sách lệnh cho trang hiện tại
     * 
     * @returns {Array} Danh sách lệnh cho trang hiện tại
     */
    getOrdersForPage() {
        const data = this.getFilteredOrders();
        const page = this.state.currentPage;
        const pageSize = this.state.pageSize;
        const start = (page - 1) * pageSize;
        const end = start + pageSize;
        return data.slice(start, end);
    }

    /**
     * Kiểm tra nút "Trang trước" có bị vô hiệu hóa không
     * 
     * @returns {boolean} true nếu đang ở trang đầu tiên
     */
    isPrevPageDisabled() {
        return this.state.currentPage <= 1;
    }

    /**
     * Kiểm tra nút "Trang sau" có bị vô hiệu hóa không
     * 
     * @returns {boolean} true nếu đang ở trang cuối cùng
     */
    isNextPageDisabled() {
        return this.state.currentPage >= this.state.totalPages;
    }

    /**
     * Chuyển sang trang trước
     */
    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
        }
    }

    /**
     * Chuyển sang trang sau
     */
    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
        }
    }

    /**
     * Định dạng giá theo chuẩn Việt Nam
     * 
     * @param {number} v - Giá trị cần định dạng
     * @returns {string} Giá đã được định dạng
     */
    formatPrice(v) {
        return new Intl.NumberFormat('vi-VN', { 
            maximumFractionDigits: 0 
        }).format(v || 0);
    }

    /**
     * Định dạng số lượng (units) theo chuẩn Việt Nam
     * 
     * @param {number} v - Số lượng cần định dạng
     * @returns {string} Số lượng đã được định dạng
     */
    formatUnits(v) {
        return new Intl.NumberFormat('vi-VN', { 
            maximumFractionDigits: 2 
        }).format(v || 0);
    }

    /**
     * Định dạng thành tiền theo chuẩn Việt Nam
     * 
     * @param {number} v - Thành tiền cần định dạng
     * @returns {string} Thành tiền đã được định dạng
     */
    formatAmount(v) {
        return new Intl.NumberFormat('vi-VN', { 
            maximumFractionDigits: 0 
        }).format(v || 0);
    }

    /**
     * Định dạng ngày giờ theo chuẩn Việt Nam
     * 
     * @param {string|Date} d - Ngày giờ cần định dạng
     * @returns {string} Ngày giờ đã được định dạng
     */
    formatDateTime(d) {
        if (!d) return '';
        try {
            return new Intl.DateTimeFormat('vi-VN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }).format(new Date(d));
        } catch {
            return '';
        }
    }

    /**
     * Kiểm tra quyền Market Maker của user
     */
    async checkUserPermission() {
        try {
            const response = await fetch('/api/user-permission/check-user-type', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {},
                    id: Math.floor(Math.random() * 1000000)
                })
            });
            const jsonRpcResponse = await response.json();
            const data = jsonRpcResponse.result || jsonRpcResponse;
            if (data && data.success) {
                this.state.isMarketMaker = data.is_market_maker === true && data.user_type === 'portal';
            }
        } catch (error) {
            console.error('Error checking user permission:', error);
        }
    }

    // Sort table by column
    sortTable(field) {
        if (this.state.sortField === field) {
            this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortField = field;
            this.state.sortOrder = 'asc';
        }
        this.applySorting();
    }

    // Get sort icon class
    getSortIcon(field) {
        if (this.state.sortField !== field) {
            return 'fa fa-sort text-muted';
        }
        return this.state.sortOrder === 'asc' 
            ? 'fa fa-sort-up text-primary' 
            : 'fa fa-sort-down text-primary';
    }

    // Apply sorting to orders
    applySorting() {
        if (!this.state.sortField) return;
        
        const field = this.state.sortField;
        const order = this.state.sortOrder;
        
        this.state.orders.sort((a, b) => {
            let valA = a[field];
            let valB = b[field];
            
            if (valA == null) valA = '';
            if (valB == null) valB = '';
            
            // Handle numeric fields
            if (['price', 'units', 'matched_units', 'remaining_units', 'amount'].includes(field)) {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else if (field === 'created_at') {
                valA = new Date(valA || 0).getTime();
                valB = new Date(valB || 0).getTime();
            } else if (typeof valA === 'string') {
                valA = valA.toLowerCase();
                valB = (valB || '').toLowerCase();
            }
            
            let comparison = 0;
            if (valA < valB) comparison = -1;
            else if (valA > valB) comparison = 1;
            
            return order === 'asc' ? comparison : -comparison;
        });
        
        this.state.currentPage = 1;
    }

    onWillUnmount() {
        if (this.autoRotateInterval) {
            clearInterval(this.autoRotateInterval);
            this.autoRotateInterval = null;
        }
    }
}

window.CompletedOrdersComponent = CompletedOrdersComponent;


