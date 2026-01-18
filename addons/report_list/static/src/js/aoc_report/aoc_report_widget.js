/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

class AOCReportWidget extends Component {
    static template = xml`
        <div class="report-contract-statistics-container">
            <!-- Header -->
            <div class="report-contract-statistics-header">
                <h1 class="report-contract-statistics-title">Báo cáo Mở/Đóng Tài khoản</h1>
                <p class="report-contract-statistics-subtitle">Thống kê tình hình mở và đóng tài khoản</p>
            </div>

            <!-- Filters -->
            <div class="report-contract-statistics-filters">
                <!-- Inline search by fields -->
                <div class="report-contract-statistics-filter-row">
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="searchAccount">Số TK:</label>
                        <input id="searchAccount" type="text" class="report-contract-statistics-filter-input" placeholder="Nhập số TK"
                            t-model="state.searchValues.account_number" t-on-input="onSearchChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="searchCustomer">Khách hàng:</label>
                        <input id="searchCustomer" type="text" class="report-contract-statistics-filter-input" placeholder="Nhập khách hàng"
                            t-model="state.searchValues.customer_name" t-on-input="onSearchChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="searchAM">NVCS:</label>
                        <input id="searchAM" type="text" class="report-contract-statistics-filter-input" placeholder="Nhập NVCS"
                            t-model="state.searchValues.account_manager" t-on-input="onSearchChange"/>
                    </div>
                </div>
                <div class="report-contract-statistics-filter-row">
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="dateFromFilter">Từ ngày:</label>
                        <input type="date" id="dateFromFilter" class="report-contract-statistics-filter-input" t-model="state.filters.dateFrom" t-on-change="onFilterChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="dateToFilter">Đến ngày:</label>
                        <input type="date" id="dateToFilter" class="report-contract-statistics-filter-input" t-model="state.filters.dateTo" t-on-change="onFilterChange"/>
                    </div>
                    <div class="report-contract-statistics-filter-group">
                        <label class="report-contract-statistics-filter-label" for="statusFilter">Trạng thái:</label>
                        <select id="statusFilter" class="report-contract-statistics-filter-input" t-model="state.filters.status" t-on-change="onFilterChange">
                            <option value="">Tất cả</option>
                            <option value="active">Hoạt động</option>
                            <option value="inactive">Đã đóng</option>
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
                                <th style="width: 60px;">STT</th>
                                <th style="width: 120px;">Số TK</th>
                                <th style="width: 120px;">TK GDCK</th>
                                <th style="width: 150px;">Khách hàng</th>
                                <th style="width: 150px;">Số CCCD/CC/GPKD</th>
                                <th style="width: 120px;">Ngày cấp</th>
                                <th style="width: 140px;">Nơi cấp</th>
                                <th style="width: 180px;">Địa chỉ thường trú</th>
                                <th style="width: 180px;">Địa chỉ liên hệ</th>
                                <th style="width: 130px;">Số điện thoại</th>
                                <th style="width: 180px;">Email</th>
                                <th style="width: 120px;">Ngày mở TK</th>
                                <th style="width: 120px;">Ngày đóng TK</th>
                                <th style="width: 110px;">Trạng thái</th>
                                <th style="width: 100px;">Loại KH</th>
                                <th style="width: 90px;">TN/NN</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr t-if="!state.records or state.records.length === 0">
                                <td colspan="16" class="text-center py-3" style="font-size: 0.85rem;">
                                    <i class="fas fa-inbox me-2"></i>Không có dữ liệu báo cáo mở/đóng tài khoản
                                </td>
                            </tr>
                            <tr t-foreach="state.records" t-as="record" t-key="record.id">
                                <td style="font-size: 0.8rem;" t-esc="record.stt or (state.records.indexOf(record) + 1)"/>
                                <td style="font-size: 0.8rem;" t-esc="record.account_number or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.trading_account or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.customer_name or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.id_number or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.id_issue_date or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.id_issue_place or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.permanent_address or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.contact_address or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.phone_number or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.email or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.open_date or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.close_date or ''"/>
                                <td style="font-size: 0.8rem;">
                                    <span class="badge" t-att-class="record.status === 'active' ? 'badge-approved' : 'badge-cancelled'">
                                        <t t-esc="record.status === 'active' ? 'Hoạt động' : 'Đã đóng'"/>
                                    </span>
                                </td>
                                <td style="font-size: 0.8rem;" t-esc="record.customer_type or ''"/>
                                <td style="font-size: 0.8rem;" t-esc="record.nationality_type or ''"/>
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
            filters: {
                dateFrom: '',
                dateTo: '',
                status: ''
            },
            searchValues: {
                account_number: '',
                customer_name: '',
                account_manager: ''
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
            console.log('AOCReportWidget OWL component mounted');
            this.initDropdown();
            this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        
        try {
            const response = await this.rpc('/aoc_report/get_data', {
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

            // Chuẩn hoá dữ liệu theo cột hiển thị
            const raw = response && (response.data || response.records) || [];
            const items = Array.isArray(raw) ? raw : [];
            this.state.records = items.map((it) => ({
                id: it.id,
                stt: it.stt || '',
                account_number: it.account_number || '',
                trading_account: it.trading_account || '',
                customer_name: it.customer_name || '',
                id_number: it.id_number || '',
                id_issue_date: it.id_issue_date || '',
                id_issue_place: it.id_issue_place || '',
                permanent_address: it.permanent_address || '',
                contact_address: it.contact_address || '',
                phone_number: it.phone_number || '',
                email: it.email || '',
                open_date: it.open_date || '',
                close_date: it.close_date || '',
                status: it.status || '',
                customer_type: it.customer_type || '',
                nationality_type: it.nationality_type || '',
                account_manager: it.account_manager || '',
                unit: it.unit || ''
            }));
            if (response.page) this.state.pagination.currentPage = response.page;
            if (response.limit) this.state.pagination.pageSize = response.limit;
            this.state.pagination.totalRecords = response.total || 0;
            this.updatePaginationInfo();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Lỗi khi tải dữ liệu');
        } finally {
            this.state.loading = false;
        }
    }

    onFilterChange() {
        this.state.pagination.currentPage = 1;
        this.loadData();
    }

    onSearchChange() {
        this.state.pagination.currentPage = 1;
        this.loadData();
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
            dateFrom: '',
            dateTo: '',
            status: ''
        };
        this.state.searchValues = {
            account_number: '',
            customer_name: '',
            account_manager: ''
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
            
            // Thêm search values
            Object.keys(this.state.searchValues).forEach(key => {
                if (this.state.searchValues[key]) {
                    params.append(key, this.state.searchValues[key]);
                }
            });

            const response = await fetch(`/aoc_report/export_pdf?${params.toString()}`, {
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
            a.download = `aoc_report_${new Date().toISOString().split('T')[0]}.pdf`;
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
            
            // Thêm search values
            Object.keys(this.state.searchValues).forEach(key => {
                if (this.state.searchValues[key]) {
                    params.append(key, this.state.searchValues[key]);
                }
            });

            const response = await fetch(`/aoc_report/export_xlsx?${params.toString()}`, {
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
            a.download = `aoc_report_${new Date().toISOString().split('T')[0]}.xlsx`;
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
}

export { AOCReportWidget };