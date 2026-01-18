/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class ReportContractSummaryWidget extends Component {
    static template = xml`
        <div class="report-contract-statistics-container">
            <!-- Header -->
            <div class="report-contract-statistics-header">
                <h1 class="report-contract-statistics-title">
                    <i class="fas fa-file-contract me-2"></i>Báo cáo Tổng hợp Hợp đồng
                </h1>
                <p class="report-contract-statistics-subtitle">Thống kê chi tiết hợp đồng mua bán và trạng thái</p>
            </div>

            <!-- Navigation -->
            <nav class="report-navigation-bar">
                <a class="report-nav-item" href="/report-contract-statistics">
                    <i class="fas fa-chart-column"></i><span>Thống kê theo Kỳ hạn</span>
                </a>
                <a class="report-nav-item active" href="#">
                    <i class="fas fa-list-check"></i><span>Danh sách HĐ Mua/Bán</span>
                </a>
                <a class="report-nav-item" href="/report-purchase-contract">
                    <i class="fas fa-cart-plus"></i><span>Danh sách HĐ Mua</span>
                </a>
                <a class="report-nav-item" href="/report-sell-contract">
                    <i class="fas fa-cart-arrow-down"></i><span>Danh sách HĐ Bán</span>
                </a>
            </nav>

            <!-- Filters -->
            <div class="report-contract-statistics-filters">
                <!-- Top Row: Global Search -->
                <div class="report-contract-statistics-filter-row mb-3">
                    <div class="report-contract-statistics-filter-group">
                         <label class="report-contract-statistics-filter-label">Tìm kiếm</label>
                         <div class="report-contract-statistics-search">
                            <input type="text" class="report-contract-statistics-search-input" 
                                placeholder="Số HĐ, Số TK, Tên KH..." 
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

            <!-- Table Section -->
            <div class="report-contract-statistics-table-container">
                <div class="report-contract-statistics-table-wrapper">
                    <table class="report-contract-statistics-table">
                        <thead>
                            <tr>
                                <th style="width: 50px;">STT</th>
                                <th class="sortable" t-on-click="() => this.sortBy('so_hop_dong')">
                                    Số Hợp đồng <i t-att-class="this.getSortIcon('so_hop_dong')"></i>
                                </th>
                                <th class="sortable" t-on-click="() => this.sortBy('so_tk')">
                                    Số TK <i t-att-class="this.getSortIcon('so_tk')"></i>
                                </th>
                                <th>Số TK GDCK</th>
                                <th class="sortable" t-on-click="() => this.sortBy('khach_hang')">
                                    Khách hàng <i t-att-class="this.getSortIcon('khach_hang')"></i>
                                </th>
                                <th class="sortable" t-on-click="() => this.sortBy('ngay_mua')">
                                    Ngày mua <i t-att-class="this.getSortIcon('ngay_mua')"></i>
                                </th>
                                <th>Ngày TT</th>
                                <th class="text-right">Số lượng</th>
                                <th class="text-right">Giá mua</th>
                                <th class="text-right">Thành tiền</th>
                                <th>Kỳ hạn</th>
                                <th>Lãi suất</th>
                                <th>Số ngày</th>
                                <th class="text-right">Lãi dự kiến</th>
                                <th class="text-right">Giá bán dự kiến</th>
                                <th class="text-right">Gốc+Lãi dự kiến</th>
                                <th>Ngày bán (DK)</th>
                                <th>Ngày đáo hạn</th>
                                <th>Ngày bán</th>
                                <th>Ngày TT bán</th>
                                <th>LS bán</th>
                                <th class="text-right">Tiền lãi</th>
                                <th class="text-right">Gốc+Lãi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Loading -->
                            <tr t-if="state.loading">
                                <td colspan="23" class="report-contract-statistics-loading">
                                    <i class="fas fa-circle-notch fa-spin fa-2x mb-2"></i>
                                    <p class="mb-0">Đang tải dữ liệu...</p>
                                </td>
                            </tr>
                            
                            <!-- Empty -->
                            <tr t-elif="!state.records || state.records.length === 0">
                                <td colspan="23" class="report-contract-statistics-no-data">
                                    <i class="fas fa-search mb-2"></i>
                                    <p class="mb-0">Không tìm thấy dữ liệu hợp đồng</p>
                                </td>
                            </tr>

                            <!-- Data Rows -->
                            <tr t-foreach="state.records" t-as="record" t-key="record.id">
                                <td class="text-center" t-esc="record.stt || (this.getStartIndex() + record_index + 1)"/>
                                <td class="fw-bold"><t t-esc="record.so_hop_dong"/></td>
                                <td><t t-esc="record.so_tk"/></td>
                                <td><t t-esc="record.so_tk_gdck"/></td>
                                <td><t t-esc="record.khach_hang"/></td>
                                <td><t t-esc="record.ngay_mua"/></td>
                                <td><t t-esc="record.ngay_thanh_toan"/></td>
                                <td class="text-right"><t t-esc="this.formatNumber(record.so_luong)"/></td>
                                <td class="text-right price-cell"><t t-esc="this.formatNumber(record.gia_mua)"/></td>
                                <td class="text-right price-cell fw-bold"><t t-esc="this.formatNumber(record.thanh_tien)"/></td>
                                <td><span class="chip chip-term"><t t-esc="record.ky_han"/></span></td>
                                <td><span class="chip chip-rate"><t t-esc="record.lai_suat"/>%</span></td>
                                <td><span class="chip chip-days"><t t-esc="record.so_ngay"/></span></td>
                                <td class="text-right price-cell"><t t-esc="this.formatNumber(this.mround(record.tien_lai_du_kien || 0, 50))"/></td>
                                <td class="text-right price-cell"><t t-esc="this.formatNumber(this.mround(record.gia_ban_lai_du_kien || 0, 50))"/></td>
                                <td class="text-right price-cell fw-bold"><t t-esc="this.formatNumber(this.mround(record.goc_lai_du_kien || 0, 50))"/></td>
                                <td><t t-esc="record.ngay_ban_lai_du_kien"/></td>
                                <td><t t-esc="record.ngay_den_han"/></td>
                                <td><t t-esc="record.ngay_ban_lai"/></td>
                                <td><t t-esc="record.ngay_thanh_toan_ban_lai"/></td>
                                <td><t t-esc="record.ls_ban_lai"/></td>
                                <td class="text-right price-cell"><t t-esc="this.formatNumber(record.tien_lai)"/></td>
                                <td class="text-right price-cell fw-bold"><t t-esc="this.formatNumber(record.goc_lai)"/></td>
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
                dateTo: ''
            },
            searchValues: {
                so_hop_dong: '',
                so_tk: '',
                khach_hang: ''
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
            sortColumn: 'so_hop_dong',
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
                this.state.searchValues.so_hop_dong = this.state.globalSearch;
                this.state.searchValues.khach_hang = this.state.globalSearch;
                if (/^\d+$/.test(this.state.globalSearch)) {
                    this.state.searchValues.so_tk = this.state.globalSearch;
                }
            }

            const response = await this.rpc('/report-contract-summary/data', {
                filters: this.state.filters,
                search_values: this.state.searchValues,
                page: this.state.pagination.currentPage,
                limit: this.state.pagination.pageSize
            });

            if (response.error) throw new Error(response.error);

            this.state.records = response.data || [];
            this.applyClientSorting();

            this.state.pagination.totalRecords = response.total || 0;
            this.state.pagination.totalPages = Math.ceil(this.state.pagination.totalRecords / this.state.pagination.pageSize) || 1;
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

            // Handle numbers (monetary, quantity, dates as nums if converted, but dates likely strings here)
            // List of numeric columns
            const numCols = ['so_luong', 'gia_mua', 'thanh_tien', 'ky_han', 'lai_suat', 'so_ngay', 
                             'tien_lai_du_kien', 'gia_ban_lai_du_kien', 'goc_lai_du_kien', 
                             'ls_ban_lai', 'tien_lai', 'goc_lai'];
            
            if (numCols.includes(col)) {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else {
                valA = (valA || '').toString().toLowerCase();
                valB = (valB || '').toString().toLowerCase();
            }

            if (valA < valB) return dir === 'asc' ? -1 : 1;
            if (valA > valB) return dir === 'asc' ? 1 : -1;
            return 0;
        });
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
        this.state.filters = { fund: '', dateFrom: '', dateTo: '' };
        this.state.searchValues = { so_hop_dong: '', so_tk: '', khach_hang: '' };
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
            
            const endpoint = `/report-contract-summary/export-${type}`;
            window.location.href = `${endpoint}?${params.toString()}`;
        } catch (e) {
            console.error(e);
            alert('Lỗi export: ' + e.message);
        }
    }

    // --- Utils ---

    async rpc(route, params) {
        const res = await fetch(route, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params })
        });
        const data = await res.json();
        return data.result;
    }

    formatNumber(value) {
        if (!value) return '0';
        return parseFloat(value).toLocaleString('vi-VN');
    }

     mround(value, step) {
        const num = parseFloat(value) || 0;
        return Math.round(num / step) * step;
    }
}