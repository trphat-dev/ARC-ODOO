/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class ReportOrderHistoryWidget extends Component {
    static template = xml`
        <div class="report-contract-statistics-container">
            <!-- Header -->
            <div class="report-contract-statistics-header">
                <h1 class="report-contract-statistics-title">
                    <i class="fas fa-history me-2"></i>Báo cáo Lịch sử Lệnh
                </h1>
                <p class="report-contract-statistics-subtitle">Theo dõi trạng thái và lịch sử lệnh đặt của nhà đầu tư</p>
            </div>

            <!-- Filters -->
            <div class="report-contract-statistics-filters">
                <!-- Top Row: Global Search -->
                <div class="report-contract-statistics-filter-row mb-3">
                    <div class="report-contract-statistics-filter-group">
                         <label class="report-contract-statistics-filter-label">Tìm kiếm</label>
                         <div class="report-contract-statistics-search">
                            <input type="text" class="report-contract-statistics-search-input" 
                                placeholder="Nhập Số TK, Tên KH, Mã CK, Số lệnh..." 
                                t-model="state.globalSearch" t-on-input="onGlobalSearchChange"/>
                            <i class="fas fa-search report-contract-statistics-search-icon"></i>
                         </div>
                    </div>
                    <div class="report-contract-statistics-filter-group" style="flex: 0 0 auto; display: flex; align-items: flex-end;">
                        <div class="dropdown" t-ref="exportDropdown">
                            <button class="report-contract-statistics-btn report-contract-statistics-btn-success dropdown-toggle" type="button" t-on-click="toggleExportDropdown">
                                <i class="fas fa-download"></i> Xuất dữ liệu
                                <i class="fas fa-chevron-down ms-2"></i>
                            </button>
                            <div class="dropdown-menu" t-if="state.showExportDropdown" style="display: block; position: absolute; top: 100%; right: 0; z-index: 1000; min-width: 180px; margin-top: 5px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid #eee; border-radius: 8px;">
                                <a class="dropdown-item" href="#" t-on-click.prevent="exportPdf" style="padding: 10px 15px; display: flex; align-items: center; gap: 10px; color: #495057; text-decoration: none; transition: background 0.2s;">
                                    <i class="fas fa-file-pdf text-danger"></i> Xuất PDF
                                </a>
                                <a class="dropdown-item" href="#" t-on-click.prevent="exportXlsx" style="padding: 10px 15px; display: flex; align-items: center; gap: 10px; color: #495057; text-decoration: none; transition: background 0.2s;">
                                    <i class="fas fa-file-excel text-success"></i> Xuất Excel
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Bottom Row: Detailed Filters -->
                <div class="report-contract-statistics-filter-row">
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label">Quỹ</label>
                        <select class="report-contract-statistics-filter-input" t-model="state.filters.fund" t-on-change="onFilterChange">
                            <option value="">-- Tất cả Quỹ --</option>
                            <option t-foreach="state.fundOptions" t-as="fund" t-key="fund.id" 
                                    t-att-value="fund.id" t-esc="fund.label"/>
                        </select>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label">Trạng thái</label>
                        <select class="report-contract-statistics-filter-input" t-model="state.filters.status" t-on-change="onFilterChange">
                            <option value="">Tất cả</option>
                            <option value="pending">Chờ khớp (Pending)</option>
                            <option value="matched">Đã khớp (Matched)</option>
                            <option value="cancelled">Đã hủy (Cancelled)</option>
                        </select>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label">Từ ngày</label>
                        <input type="date" class="report-contract-statistics-filter-input" t-model="state.filters.dateFrom" t-on-change="onFilterChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label">Đến ngày</label>
                        <input type="date" class="report-contract-statistics-filter-input" t-model="state.filters.dateTo" t-on-change="onFilterChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group" style="flex: 0 0 auto; display: flex; align-items: flex-end;">
                        <button class="report-contract-statistics-btn report-contract-statistics-btn-secondary" t-on-click="resetFilters" title="Xóa bộ lọc">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div class="report-contract-statistics-table-container">
                <div class="report-contract-statistics-table-wrapper">
                    <table class="report-contract-statistics-table">
                        <thead>
                            <tr>
                                <th style="width: 50px;">STT</th>
                                <th class="sortable" t-on-click="() => this.sortBy('gio_dat')">
                                    Giờ đặt <i t-att-class="this.getSortIcon('gio_dat')"></i>
                                </th>
                                <th class="sortable" t-on-click="() => this.sortBy('trang_thai')">
                                    Trạng thái <i t-att-class="this.getSortIcon('trang_thai')"></i>
                                </th>
                                <th>Số TK</th>
                                <th>Số TK GDCK</th>
                                <th class="sortable" t-on-click="() => this.sortBy('khach_hang')">
                                    Khách hàng <i t-att-class="this.getSortIcon('khach_hang')"></i>
                                </th>
                                <th>NVCS</th>
                                <th class="sortable" t-on-click="() => this.sortBy('loai_lenh')">
                                    Loại lệnh <i t-att-class="this.getSortIcon('loai_lenh')"></i>
                                </th>
                                <th>Lệnh</th>
                                <th class="sortable" t-on-click="() => this.sortBy('ma_ck')">
                                    Mã CK <i t-att-class="this.getSortIcon('ma_ck')"></i>
                                </th>
                                <th class="text-right">KL đặt</th>
                                <th class="text-right">Giá đặt</th>
                                <th class="text-right">KL khớp</th>
                                <th class="text-right">Giá khớp</th>
                                <th class="text-right">KL chờ</th>
                                <th class="text-right">Giá chờ</th>
                                <th>SHL</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Loading -->
                            <tr t-if="state.loading">
                                <td colspan="17" class="report-contract-statistics-loading">
                                    <i class="fas fa-circle-notch fa-spin fa-2x mb-2"></i>
                                    <p class="mb-0">Đang tải dữ liệu...</p>
                                </td>
                            </tr>
                            
                            <!-- Empty -->
                            <tr t-elif="!state.records || state.records.length === 0">
                                <td colspan="17" class="report-contract-statistics-no-data">
                                    <i class="fas fa-search mb-2"></i>
                                    <p class="mb-0">Không tìm thấy dữ liệu lệnh</p>
                                </td>
                            </tr>

                            <!-- Data -->
                            <tr t-foreach="state.records" t-as="record" t-key="record.id">
                                <td class="text-center" t-esc="record.stt || (this.getStartIndex() + record_index + 1)"/>
                                <td><t t-esc="record.gio_dat"/></td>
                                <td>
                                    <span t-att-class="this.getStatusBadgeClass(record.trang_thai)">
                                        <t t-esc="this.getStatusLabel(record.trang_thai)"/>
                                    </span>
                                </td>
                                <td><t t-esc="record.so_tk"/></td>
                                <td><t t-esc="record.so_tk_gdck"/></td>
                                <td class="fw-bold"><t t-esc="record.khach_hang"/></td>
                                <td><t t-esc="record.nvcs"/></td>
                                <td>
                                    <span t-att-class="this.getOrderTypeBadgeClass(record.loai_lenh)">
                                        <t t-esc="this.getOrderTypeLabel(record.loai_lenh)"/>
                                    </span>
                                </td>
                                <td><t t-esc="record.lenh"/></td>
                                <td><span class="badge badge--term"><t t-esc="record.ma_ck"/></span></td>
                                <td class="text-right"><t t-esc="this.formatNumber(record.kl_dat)"/></td>
                                <td class="text-right price-cell"><t t-esc="this.formatPrice50(record.gia_dat)"/></td>
                                <td class="text-right"><t t-esc="this.formatNumber(record.kl_khop)"/></td>
                                <td class="text-right price-cell"><t t-esc="this.formatPrice50(record.gia_khop)"/></td>
                                <td class="text-right"><t t-esc="this.formatNumber(record.kl_cho)"/></td>
                                <td class="text-right price-cell"><t t-esc="this.formatPrice50(record.gia_cho)"/></td>
                                <td><t t-esc="record.shl"/></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Pagination -->
            <div class="report-contract-statistics-pagination" t-if="state.pagination.totalRecords > 0">
                <div class="report-contract-statistics-pagination-info">
                    Hiển thị <strong t-esc="state.pagination.startRecord"/> - <strong t-esc="state.pagination.endRecord"/> 
                    trong tổng <strong t-esc="state.pagination.totalRecords"/> bản ghi
                </div>
                <div class="report-contract-statistics-pagination-controls">
                    <button class="report-contract-statistics-pagination-btn" 
                            t-att-disabled="state.pagination.currentPage === 1"
                            t-on-click="() => this.goToPage(state.pagination.currentPage - 1)">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    
                    <t t-foreach="this.getVisiblePages()" t-as="page" t-key="page">
                        <button class="report-contract-statistics-pagination-btn" 
                                t-att-class="page === state.pagination.currentPage ? 'active' : ''"
                                t-on-click="() => this.goToPage(page)">
                            <t t-esc="page"/>
                        </button>
                    </t>

                    <button class="report-contract-statistics-pagination-btn" 
                            t-att-disabled="state.pagination.currentPage === state.pagination.totalPages"
                            t-on-click="() => this.goToPage(state.pagination.currentPage + 1)">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    setup() {
        this.state = useState({
            loading: false,
            records: [],
            fundOptions: [],
            filters: {
                fund: '',
                dateFrom: '',
                dateTo: '',
                status: ''
            },
            searchValues: {
                so_tk: '',
                khach_hang: '',
                ma_ck: '',
                lenh: ''
            },
            globalSearch: '',
            pagination: {
                currentPage: 1,
                pageSize: 15,
                totalRecords: 0,
                startRecord: 0,
                endRecord: 0,
                totalPages: 1
            },
            showExportDropdown: false,
            sortColumn: 'gio_dat',
            sortDirection: 'desc'
        });

        onMounted(() => {
            this.initDropdown();
            this.loadFunds();
            this.loadData();
        });
    }

    async loadFunds() {
        try {
            const res = await this.rpc('/api/transaction-list/funds', {});
            if (res && res.success && Array.isArray(res.data)) {
                this.state.fundOptions = res.data.map(f => ({
                    id: f.id,
                    label: (f.ticker || f.symbol || f.name || '').trim() || f.name || ''
                }));
            }
        } catch (e) {
            console.error('Error loading funds:', e);
        }
    }

    async loadData() {
        this.state.loading = true;
        try {
            if (this.state.globalSearch) {
                // Weak global search mapping
                this.state.searchValues.khach_hang = this.state.globalSearch; 
                // Could verify if query looks like number, then map to so_tk?
                if (/^\d+$/.test(this.state.globalSearch)) {
                    this.state.searchValues.so_tk = this.state.globalSearch;
                    this.state.searchValues.lenh = this.state.globalSearch;
                }
            }

            const response = await this.rpc('/report-order-history/data', {
                filters: this.state.filters,
                search_values: this.state.searchValues,
                page: this.state.pagination.currentPage,
                limit: this.state.pagination.pageSize
            });

            if (response.error) throw new Error(response.error);

            this.state.records = response.data || [];
            
            // Client side sorting for current page (since backend pagination is basic)
            this.applyClientSorting();

            this.state.pagination.totalRecords = response.total || 0;
            this.state.pagination.totalPages = Math.ceil(this.state.pagination.totalRecords / this.state.pagination.pageSize);
            this.updatePaginationInfo();
            
        } catch (error) {
            console.error('Error:', error);
            alert('Lỗi tải dữ liệu: ' + error.message);
        } finally {
            this.state.loading = false;
        }
    }

    // --- Helpers ---

    applyClientSorting() {
        const col = this.state.sortColumn;
        const dir = this.state.sortDirection;
        if (!col) return;

        this.state.records.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];

            // Handle numbers
            if (['kl_dat', 'gia_dat', 'kl_khop', 'gia_khop', 'kl_cho', 'gia_cho'].includes(col)) {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            }
            // Handle strings/dates
            else {
                valA = (valA || '').toString().toLowerCase();
                valB = (valB || '').toString().toLowerCase();
            }

            if (valA < valB) return dir === 'asc' ? -1 : 1;
            if (valA > valB) return dir === 'asc' ? 1 : -1;
            return 0;
        });
    }

    getStatusBadgeClass(status) {
        const map = {
            'pending': 'badge-pending',
            'matched': 'badge-approved',
            'cancelled': 'badge-cancelled'
        };
        return `badge ${map[status] || 'badge-secondary'}`;
    }

    getStatusLabel(status) {
        const map = {
            'pending': 'Chờ khớp',
            'matched': 'Đã khớp',
            'cancelled': 'Đã hủy'
        };
        return map[status] || status;
    }

    getOrderTypeBadgeClass(type) {
        const t = (type || '').toLowerCase();
        if (t === 'mua' || t === 'buy') return 'badge badge-buy';
        if (t === 'ban' || t === 'sell') return 'badge badge-sell';
        return 'badge badge-secondary';
    }

    getOrderTypeLabel(type) {
        const t = (type || '').toLowerCase();
        if (t === 'mua' || t === 'buy') return 'Mua';
        if (t === 'ban' || t === 'sell') return 'Bán';
        return type;
    }

    formatNumber(value) {
        if (!value) return '0';
        return parseFloat(value).toLocaleString('vi-VN');
    }

    formatPrice50(value) {
        if (!value) return '0';
        // Logic from controller: round to nearest 50? Or just display?
        // JS display logic:
        return parseFloat(value).toLocaleString('vi-VN');
    }

    getStartIndex() {
        return (this.state.pagination.currentPage - 1) * this.state.pagination.pageSize;
    }

    updatePaginationInfo() {
        if (this.state.pagination.totalRecords === 0) {
            this.state.pagination.startRecord = 0;
            this.state.pagination.endRecord = 0;
            return;
        }
        const start = this.getStartIndex() + 1;
        const end = Math.min(start + this.state.pagination.pageSize - 1, this.state.pagination.totalRecords);
        this.state.pagination.startRecord = start;
        this.state.pagination.endRecord = end;
    }

    getVisiblePages() {
        const total = this.state.pagination.totalPages;
        const current = this.state.pagination.currentPage;
        const max = 5;
        let start = Math.max(1, current - Math.floor(max / 2));
        let end = Math.min(total, start + max - 1);
        if (end - start + 1 < max) start = Math.max(1, end - max + 1);
        const pages = [];
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    }

    // --- Handlers ---

    onFilterChange() {
        this.state.pagination.currentPage = 1;
        this.loadData();
    }

    onGlobalSearchChange(ev) {
        this.state.pagination.currentPage = 1;
        this.loadData();
    }

    resetFilters() {
        this.state.filters = { fund: '', dateFrom: '', dateTo: '', status: '' };
        this.state.searchValues = { so_tk: '', khach_hang: '', ma_ck: '', lenh: '' };
        this.state.globalSearch = '';
        this.loadData();
    }

    sortBy(column) {
        if (this.state.sortColumn === column) {
            this.state.sortDirection = this.state.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortColumn = column;
            this.state.sortDirection = 'asc';
        }
        this.applyClientSorting();
    }

    getSortIcon(column) {
        if (this.state.sortColumn !== column) return 'fas fa-sort text-muted ms-1';
        return this.state.sortDirection === 'asc' ? 'fas fa-sort-up ms-1' : 'fas fa-sort-down ms-1';
    }

    goToPage(page) {
        if (page < 1 || page > this.state.pagination.totalPages) return;
        this.state.pagination.currentPage = page;
        this.loadData();
    }

    // --- Export ---
    
    initDropdown() {
        document.addEventListener('click', (ev) => {
            if (this.state.showExportDropdown && !ev.target.closest('.dropdown')) {
                this.state.showExportDropdown = false;
            }
        });
    }

    toggleExportDropdown() {
        this.state.showExportDropdown = !this.state.showExportDropdown;
    }

    async exportPdf() {
        this.state.showExportDropdown = false;
        await this.handleExport('pdf');
    }

    async exportXlsx() {
        this.state.showExportDropdown = false;
        await this.handleExport('xlsx');
    }

    async handleExport(type) {
        try {
            const params = new URLSearchParams();
            if (this.state.filters.fund) {
                const f = this.state.fundOptions.find(opt => opt.id == this.state.filters.fund);
                if (f) params.append('product', f.label);
            }
            if (this.state.filters.dateFrom) params.append('from_date', this.state.filters.dateFrom);
            if (this.state.filters.dateTo) params.append('to_date', this.state.filters.dateTo);
            
            const endpoint = `/report-order-history/export-${type}`;
            window.location.href = `${endpoint}?${params.toString()}`;
        } catch (e) {
            console.error(e);
            alert('Lỗi export: ' + e.message);
        }
    }

    async rpc(route, params) {
        const res = await fetch(route, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params
            })
        });
        const data = await res.json();
        return data.result;
    }
}