/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class ReportContractStatisticsWidget extends Component {
    static template = xml`
        <div class="report-contract-statistics-container">
            <!-- Header -->
            <div class="report-contract-statistics-header">
                <h1 class="report-contract-statistics-title">Báo cáo Thống kê Hợp đồng</h1>
                <p class="report-contract-statistics-subtitle">Thống kê hợp đồng mua bán</p>
            </div>

            <!-- Navigation (rendered in JS template to follow transaction_list style) -->
            <nav class="report-navigation-bar">
                <a class="report-nav-item" href="/report-contract-statistics">
                    <i class="fa-solid fa-chart-column"></i><span>Thống kê  HĐ theo kỳ hạn</span>
                </a>
                <a class="report-nav-item" href="/report-contract-summary">
                    <i class="fa-solid fa-list-check"></i><span>Danh sách HĐ mua/bán</span>
                </a>
                <a class="report-nav-item" href="/report-purchase-contract">
                    <i class="fa-solid fa-cart-plus"></i><span>Danh sách HĐ mua</span>
                </a>
                <a class="report-nav-item" href="/report-sell-contract">
                    <i class="fa-solid fa-cart-arrow-down"></i><span>Danh sách HĐ bán</span>
                </a>
            </nav>

            <!-- Filters -->
            <div class="report-contract-statistics-filters">
                <!-- Inline search by fields -->
                <div class="report-contract-statistics-filter-row">
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="searchContract">Số HĐ:</label>
                        <input id="searchContract" type="text" class="report-contract-statistics-filter-input" placeholder="Nhập số HĐ"
                            t-model="state.searchValues.so_hop_dong" t-on-input="onSearchChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="searchAccount">Số TK:</label>
                        <input id="searchAccount" type="text" class="report-contract-statistics-filter-input" placeholder="Nhập số TK"
                            t-model="state.searchValues.so_tk" t-on-input="onSearchChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="searchCustomer">Khách hàng:</label>
                        <input id="searchCustomer" type="text" class="report-contract-statistics-filter-input" placeholder="Nhập khách hàng"
                            t-model="state.searchValues.khach_hang" t-on-input="onSearchChange"/>
                    </div>
                </div>
                <div class="report-contract-statistics-filter-row">
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="filterFund">Quỹ:</label>
                        <select id="filterFund" class="report-contract-statistics-filter-input" t-model="state.filters.fund" t-on-change="onFilterChange">
                            <option value="">Tất cả</option>
                            <option t-foreach="state.fundOptions" t-as="fund" t-key="fund.id" 
                                    t-att-value="fund.id" t-esc="fund.label"/>
                        </select>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="dateFromFilter">Từ ngày:</label>
                        <input type="date" id="dateFromFilter" class="report-contract-statistics-filter-input" t-model="state.filters.dateFrom" t-on-change="onFilterChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="dateToFilter">Đến ngày:</label>
                        <input type="date" id="dateToFilter" class="report-contract-statistics-filter-input" t-model="state.filters.dateTo" t-on-change="onFilterChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="termFilter">Kỳ hạn:</label>
                        <select id="termFilter" class="report-contract-statistics-filter-input" t-model="state.filters.term" t-on-change="onFilterChange">
                            <option value="">Tất cả</option>
                            <option t-foreach="state.termOptions" t-as="term" t-key="term.id"
                                    t-att-value="term.id" t-esc="term.name"/>
                        </select>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <button class="report-contract-statistics-btn report-contract-statistics-btn-secondary" t-on-click="resetFilters">
                            <i class="fas fa-undo"></i> Làm mới
                        </button>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <div class="dropdown" t-ref="exportDropdown">
                            <button class="report-contract-statistics-btn report-contract-statistics-btn-success dropdown-toggle" type="button" t-on-click="toggleExportDropdown">
                                <i class="fas fa-download"></i> Xuất file
                                <i class="fas fa-chevron-down" style="margin-left: 5px;"></i>
                            </button>
                            <div class="dropdown-menu" t-if="state.showExportDropdown" style="display: block; position: absolute; top: 100%; left: 0; z-index: 1000; min-width: 160px; padding: 5px 0; margin: 2px 0 0; background-color: #fff; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 6px 12px rgba(0,0,0,.175);">
                                <a class="dropdown-item" href="#" t-on-click="exportPdf" style="display: block; padding: 3px 20px; clear: both; font-weight: normal; line-height: 1.42857143; color: #333; white-space: nowrap; text-decoration: none;">
                                    <i class="fas fa-file-pdf"></i> Xuất PDF
                                </a>
                                <a class="dropdown-item" href="#" t-on-click="exportXlsx" style="display: block; padding: 3px 20px; clear: both; font-weight: normal; line-height: 1.42857143; color: #333; white-space: nowrap; text-decoration: none;">
                                    <i class="fas fa-file-excel"></i> Xuất XLSX
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Loading -->
            <div t-if="state.loading" class="report-contract-statistics-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Đang tải dữ liệu...</p>
            </div>

            <!-- Table -->
            <div class="report-contract-statistics-table-container">
                <div class="report-contract-statistics-table-wrapper">
                    <table class="report-contract-statistics-table">
                        <thead>
                            <tr>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 60px;">STT</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 120px;">Số Hợp đồng</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 100px;">Số TK</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 120px;">Số TK GDCK</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 150px;">Khách hàng</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 80px;">Kỳ hạn</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 120px;">Số tiền</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 120px;">Ngày Hợp đồng</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 120px;">Ngày đến hạn</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 100px;">NVCS</th>
                                <th style="font-size: 0.8rem; font-weight: 600; width: 120px;">Đơn vị</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr t-if="!state.records || state.records.length === 0">
                                <td colspan="11" class="text-center py-3" style="font-size: 0.85rem;">
                                    <i class="fas fa-inbox me-2"></i>Không có dữ liệu thống kê hợp đồng
                                </td>
                            </tr>
                            <tr t-foreach="state.records" t-as="record" t-key="record.id">
                                <td style="font-size: 0.8rem;" t-esc="record.stt || (state.records.indexOf(record) + 1)"/>
                                <td style="font-size: 0.8rem;" t-esc="record.so_hop_dong || ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.so_tk || ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.so_tk_gdck || ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.khach_hang || ''"/>
                                <td style="font-size: 0.8rem;">
                                    <span class="chip chip-term" t-esc="record.ky_han || 0"/>
                                </td>
                                <td style="font-size: 0.8rem;" class="text-right price-cell" t-esc="this.formatNumber(record.so_tien)"/>
                                <td style="font-size: 0.8rem;" t-esc="record.ngay_hop_dong || ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.ngay_den_han || ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.nvcs || ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.don_vi || ''"/>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Pagination -->
            <div class="report-contract-statistics-pagination">
                <div class="report-contract-statistics-pagination-info">
                    Hiển thị <span t-esc="state.pagination.startRecord"/> đến <span t-esc="state.pagination.endRecord"/> 
                    trong tổng số <span t-esc="state.pagination.totalRecords"/> bản ghi
                </div>
                <div class="report-contract-statistics-pagination-controls">
                    <button t-foreach="state.pagination.pages" t-as="page" t-key="page" 
                            class="report-contract-statistics-pagination-btn" 
                            t-att-class="page === state.pagination.currentPage ? 'active' : ''"
                            t-on-click="() => this.goToPage(page)"
                            t-esc="page"/>
                </div>
            </div>
        </div>
    `;

    setup() {
        this.state = useState({
            loading: false,
            records: [],
            fundOptions: [],
            termOptions: [],
            filters: {
                fund: '',
                dateFrom: '',
                dateTo: '',
                term: ''
            },
            searchValues: {
                so_hop_dong: '',
                so_tk: '',
                khach_hang: ''
            },
            pagination: {
                currentPage: 1,
                pageSize: 10,
                totalRecords: 0,
                startRecord: 0,
                endRecord: 0,
                pages: []
            },
            showExportDropdown: false
        });

        onMounted(() => {
            console.log('ReportContractStatisticsWidget OWL component mounted');
            this.initDropdown();
        // Highlight active nav
        const currentPath = window.location.pathname;
        document.querySelectorAll('.report-nav-item').forEach((link) => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
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

            // Load terms from nav_management (backend aggregates term_months)
            const terms = await this.rpc('/report-contract-statistics/terms', {});
            if (Array.isArray(terms)) {
                this.state.termOptions = terms;
            }
        } catch (e) {
            console.error('Error loading funds:', e);
        }
    }

    async loadData() {
        this.state.loading = true;
        
        try {
            const response = await this.rpc('/report-contract-statistics/data', {
                filters: this.state.filters,
                search_values: this.state.searchValues,
                page: this.state.pagination.currentPage,
                limit: this.state.pagination.pageSize
            });

            if (response.error) {
                console.error('Error loading data:', response.error);
                this.showError('Lỗi khi tải dữ liệu: ' + response.error);
                return;
            }

            this.state.records = response.data || [];
            this.state.pagination.totalRecords = response.total || 0;
            this.updatePaginationInfo();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Lỗi khi tải dữ liệu');
        } finally {
            this.state.loading = false;
        }
    }

    updatePaginationInfo() {
        const startRecord = this.state.pagination.totalRecords > 0 ? 
            (this.state.pagination.currentPage - 1) * this.state.pagination.pageSize + 1 : 0;
        const endRecord = Math.min(
            this.state.pagination.currentPage * this.state.pagination.pageSize, 
            this.state.pagination.totalRecords
        );
        
        this.state.pagination.startRecord = startRecord;
        this.state.pagination.endRecord = endRecord;
        
        // Generate page numbers
        const totalPages = Math.ceil(this.state.pagination.totalRecords / this.state.pagination.pageSize);
        this.state.pagination.pages = [];
        for (let i = 1; i <= totalPages; i++) {
            this.state.pagination.pages.push(i);
        }
    }

    goToPage(page) {
        this.state.pagination.currentPage = page;
        this.loadData();
    }

    resetFilters() {
        this.state.filters = {
            fund: '',
            dateFrom: '',
            dateTo: '',
            term: ''
        };
        this.state.searchValues = {
            so_hop_dong: '',
            so_tk: '',
            khach_hang: ''
        };
        this.state.pagination.currentPage = 1;
        this.loadData();
    }

    initDropdown() {
        // Đóng dropdown khi click bên ngoài
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.dropdown')) {
                this.state.showExportDropdown = false;
            }
        });
    }

    toggleExportDropdown() {
        this.state.showExportDropdown = !this.state.showExportDropdown;
    }

    onFilterChange() {
        this.state.pagination.currentPage = 1;
        this.loadData();
    }

    onSearchChange() {
        this.state.pagination.currentPage = 1;
        this.loadData();
    }

    async exportPdf() {
        this.state.showExportDropdown = false;
        try {
            this.state.loading = true;
            
            const params = new URLSearchParams();
            Object.keys(this.state.filters).forEach(key => {
                if (this.state.filters[key]) {
                    params.append(key, this.state.filters[key]);
                }
            });

            const response = await fetch(`/report-contract-statistics/export-pdf?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/pdf',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_contract_statistics_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error('Error exporting PDF:', error);
            this.showError('Lỗi khi xuất PDF: ' + error.message);
        } finally {
            this.state.loading = false;
        }
    }

    async exportXlsx() {
        this.state.showExportDropdown = false;
        try {
            this.state.loading = true;
            
            const params = new URLSearchParams();
            Object.keys(this.state.filters).forEach(key => {
                if (this.state.filters[key]) {
                    params.append(key, this.state.filters[key]);
                }
            });

            const response = await fetch(`/report-contract-statistics/export-xlsx?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_contract_statistics_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error('Error exporting XLSX:', error);
            this.showError('Lỗi khi xuất XLSX: ' + error.message);
        } finally {
            this.state.loading = false;
        }
    }

    showError(message) {
        alert(message);
    }

    async rpc(route, params) {
        try {
            const response = await fetch(route, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: params
                })
            });

            const data = await response.json();
            return data.result;
        } catch (error) {
            console.error('RPC Error:', error);
            throw error;
        }
    }

    formatNumber(value) {
        const num = (value === undefined || value === null || value === '')
            ? 0
            : (typeof value === 'number' ? value : parseFloat(String(value).toString().replace(/[\,\s]/g, '')));
        if (isNaN(num)) return '0';
        return num.toLocaleString('vi-VN');
    }
}