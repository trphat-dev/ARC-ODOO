/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class NavMonthlyWidget extends Component {
  static template = xml`
    <div class="nav-management-fund-overview-container">
      <div class="container-fluid py-4">
        
        <!-- Page Header -->
        <div class="nav-management-content-header mb-4 nav-management-fade-in">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <h1 class="nav-management-content-title mb-1">
                <i class="fas fa-chart-bar me-2"></i>Báo cáo NAV tháng
              </h1>
              <p class="nav-management-content-subtitle mb-0">
                Quản lý và theo dõi giá trị NAV hàng tháng của quỹ
              </p>
            </div>
            <div class="d-flex gap-2 flex-wrap">
              <button class="nav-management-btn-modern nav-management-btn-secondary-modern" 
                      t-on-click="exportData">
                <i class="fas fa-download me-2"></i>Xuất CSV
              </button>
              <button class="nav-management-btn-modern nav-management-btn-primary-modern" 
                      t-on-click="openAddModal">
                <i class="fas fa-plus me-2"></i>Thêm mới
              </button>
              <button class="nav-management-btn-modern nav-management-btn-primary-modern" 
                      t-on-click="refreshData">
                <i class="fas fa-sync-alt"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Stats Cards Row -->
        <div class="nav-management-stats-grid mb-4">
          <div class="nav-management-stat-card">
            <div class="nav-management-stat-icon" style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); color: #1e40af;">
              <i class="fas fa-calendar-alt"></i>
            </div>
            <div class="nav-management-stat-number"><t t-esc="state.totalMonthlyNav"/></div>
            <div class="nav-management-stat-label">Tổng bản ghi</div>
          </div>
          <div class="nav-management-stat-card">
            <div class="nav-management-stat-icon" style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); color: #065f46;">
              <i class="fas fa-arrow-trend-up"></i>
            </div>
            <div class="nav-management-stat-number"><t t-esc="state.positiveChanges"/></div>
            <div class="nav-management-stat-label">Tháng tăng trưởng</div>
          </div>
          <div class="nav-management-stat-card">
            <div class="nav-management-stat-icon" style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); color: #991b1b;">
              <i class="fas fa-arrow-trend-down"></i>
            </div>
            <div class="nav-management-stat-number"><t t-esc="state.negativeChanges"/></div>
            <div class="nav-management-stat-label">Tháng giảm</div>
          </div>
          <div class="nav-management-stat-card">
            <div class="nav-management-stat-icon" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #92400e;">
              <i class="fas fa-percent"></i>
            </div>
            <div class="nav-management-stat-number"><t t-esc="this.formatPercentage(state.averageChangePercent)"/></div>
            <div class="nav-management-stat-label">Tăng trưởng TB</div>
          </div>
        </div>

        <!-- Filter Section -->
        <div class="nav-management-content-header mb-4">
          <div class="row g-3 align-items-end">
            <div class="col-12 col-md-4">
              <label class="nav-management-form-label">
                <i class="fas fa-building-columns me-1"></i>Quỹ
              </label>
              <select class="nav-management-form-select" t-on-change="onFundFilterChange">
                <option value="">Tất cả quỹ</option>
                <t t-foreach="state.funds" t-as="fund" t-key="fund.id">
                  <option t-att-value="fund.id" t-att-selected="state.selectedFundId === fund.id">
                    <t t-esc="fund.name"/> (<t t-esc="fund.ticker"/>)
                  </option>
                </t>
              </select>
            </div>
            <div class="col-6 col-md-3">
              <label class="nav-management-form-label">
                <i class="fas fa-calendar me-1"></i>Từ ngày
              </label>
              <input type="date" id="fromDateFilter" class="nav-management-form-control" t-on-change="onDateFilterChange"/>
            </div>
            <div class="col-6 col-md-3">
              <label class="nav-management-form-label">
                <i class="fas fa-calendar-check me-1"></i>Đến ngày
              </label>
              <input type="date" id="toDateFilter" class="nav-management-form-control" t-on-change="onDateFilterChange"/>
            </div>
            <div class="col-12 col-md-2">
              <button class="nav-management-btn-modern nav-management-btn-secondary-modern w-100" t-on-click="applyFilters">
                <i class="fas fa-filter me-2"></i>Lọc
              </button>
            </div>
          </div>
        </div>

        <!-- Data Table -->
        <div class="nav-management-table-container nav-management-fade-in">
          <table class="nav-management-modern-table">
            <thead>
              <tr>
                <th style="width: 60px;">STT</th>
                <th class="sortable" t-on-click="() => this.sortBy('period')">
                  Kỳ
                  <i t-att-class="'fas ms-1 ' + this.getSortIcon('period')"></i>
                </th>
                <th class="sortable" t-on-click="() => this.sortBy('nav_beginning')">
                  NAV đầu kỳ
                  <i t-att-class="'fas ms-1 ' + this.getSortIcon('nav_beginning')"></i>
                </th>
                <th class="sortable" t-on-click="() => this.sortBy('nav_ending')">
                  NAV cuối kỳ
                  <i t-att-class="'fas ms-1 ' + this.getSortIcon('nav_ending')"></i>
                </th>
                <th class="sortable" t-on-click="() => this.sortBy('change_percent')">
                  Thay đổi
                  <i t-att-class="'fas ms-1 ' + this.getSortIcon('change_percent')"></i>
                </th>
                <th class="sortable" t-on-click="() => this.sortBy('upload_date')">
                  Ngày upload
                  <i t-att-class="'fas ms-1 ' + this.getSortIcon('upload_date')"></i>
                </th>
                <th style="width: 100px;">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              <t t-if="state.loading">
                <tr>
                  <td colspan="7" class="text-center py-5">
                    <div class="nav-management-loading-state">
                      <div class="nav-management-spinner-border"></div>
                      <h4 class="nav-management-loading-title mt-3">Đang tải dữ liệu...</h4>
                      <p class="nav-management-loading-description">Vui lòng chờ</p>
                    </div>
                  </td>
                </tr>
              </t>
              <t t-elif="state.error">
                <tr>
                  <td colspan="7" class="text-center py-5">
                    <div class="nav-management-error-state">
                      <i class="fas fa-exclamation-triangle nav-management-error-icon"></i>
                      <h4 class="nav-management-error-title">Lỗi tải dữ liệu</h4>
                      <p class="nav-management-error-description"><t t-esc="state.error"/></p>
                      <button class="nav-management-btn-modern nav-management-btn-primary-modern mt-3" t-on-click="loadData">
                        <i class="fas fa-redo me-2"></i>Thử lại
                      </button>
                    </div>
                  </td>
                </tr>
              </t>
              <t t-elif="state.filteredMonthlyNav and state.filteredMonthlyNav.length > 0">
                <t t-foreach="state.filteredMonthlyNav.slice(state.startIndex, state.endIndex)" t-as="nav" t-key="nav.id">
                  <tr class="nav-management-fade-in">
                    <td><t t-esc="state.startIndex + nav_index + 1"/></td>
                    <td>
                      <span class="fw-semibold"><t t-esc="nav.period"/></span>
                    </td>
                    <td><t t-esc="this.formatCurrency(nav.nav_beginning)"/></td>
                    <td><t t-esc="this.formatCurrency(nav.nav_ending)"/></td>
                    <td>
                      <t t-set="changePercent" t-value="nav.change_percent || 0"/>
                      <span t-att-class="'badge-chip ' + (changePercent >= 0 ? 'badge-pnl-profit' : 'badge-pnl-loss')">
                        <i t-att-class="'fas ' + (changePercent >= 0 ? 'fa-arrow-up' : 'fa-arrow-down') + ' me-1'"></i>
                        <t t-esc="this.formatPercentage(changePercent)"/>
                      </span>
                    </td>
                    <td class="text-muted"><t t-esc="this.formatDate(nav.upload_date)"/></td>
                    <td>
                      <div class="d-flex gap-1 justify-content-center">
                        <button class="nav-management-btn-modern nav-management-btn-secondary-modern" 
                                style="padding: 0.25rem 0.5rem; font-size: 0.75rem;"
                                t-on-click="() => this.editNav(nav)" 
                                title="Sửa">
                          <i class="fas fa-edit"></i>
                        </button>
                        <button class="nav-management-btn-modern" 
                                style="padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #ef4444; color: white;"
                                t-on-click="() => this.deleteNav(nav)" 
                                title="Xóa">
                          <i class="fas fa-trash"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                </t>
              </t>
              <t t-else="">
                <tr>
                  <td colspan="7" class="text-center py-5">
                    <div class="nav-management-empty-state">
                      <i class="fas fa-folder-open nav-management-empty-state-icon"></i>
                      <h4 class="nav-management-empty-state-title">Không có dữ liệu</h4>
                      <p class="nav-management-empty-state-description">Vui lòng chọn quỹ để xem dữ liệu NAV tháng</p>
                    </div>
                  </td>
                </tr>
              </t>
            </tbody>
          </table>

          <!-- Pagination -->
          <div class="nav-management-pagination-modern">
            <div class="nav-management-pagination-info">
              Hiển thị <strong><t t-esc="state.startIndex + 1"/></strong> đến 
              <strong><t t-esc="Math.min(state.endIndex, state.filteredMonthlyNav.length)"/></strong> 
              trong tổng số <strong><t t-esc="state.filteredMonthlyNav.length"/></strong> kết quả
            </div>
            <div class="nav-management-pagination-controls">
              <button class="nav-management-page-btn" t-att-disabled="state.currentPage === 1" t-on-click="() => this.changePage(state.currentPage - 1)">
                <i class="fas fa-chevron-left"></i>
              </button>
              <t t-foreach="state.pageNumbers" t-as="page" t-key="page">
                <button t-att-class="'nav-management-page-btn ' + (page === state.currentPage ? 'active' : '')" t-on-click="() => this.changePage(page)">
                  <t t-esc="page"/>
                </button>
              </t>
              <button class="nav-management-page-btn" t-att-disabled="state.currentPage === state.totalPages" t-on-click="() => this.changePage(state.currentPage + 1)">
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div class="nav-management-modal" t-att-class="state.showModal ? 'show' : ''" id="navMonthlyModal">
      <div class="nav-management-modal-dialog">
        <div class="nav-management-modal-content nav-management-scale-in">
          <div class="nav-management-modal-header nm-modal-success">
            <h5 class="nav-management-modal-title">
              <i t-att-class="'fas ' + (state.isEditing ? 'fa-edit' : 'fa-plus') + ' me-2'"></i>
              <t t-if="state.isEditing">Edit NAV Monthly</t>
              <t t-else="">Add NAV Monthly</t>
            </h5>
            <button type="button" class="nav-management-btn-close" t-on-click="closeModal"></button>
          </div>
          <form t-on-submit.prevent="saveNavMonthly">
            <div class="nav-management-modal-body">
              <div class="mb-3">
                <label class="nav-management-form-label">Fund <span class="nav-management-text-danger">*</span></label>
                <select class="nav-management-form-select" required="required" t-model="state.currentNav.fund_id">
                  <option value="">Select fund</option>
                  <t t-foreach="state.funds" t-as="fund" t-key="fund.id">
                    <option t-att-value="fund.id"><t t-esc="fund.name"/> (<t t-esc="fund.ticker"/>)</option>
                  </t>
                </select>
              </div>
              <div class="mb-3">
                <label class="nav-management-form-label">Period (MM/YYYY) <span class="nav-management-text-danger">*</span></label>
                <input type="text" class="nav-management-form-control" t-model="state.currentNav.period" 
                       pattern="^(0[1-9]|1[0-2])/\\d{4}$" placeholder="12/2024" required="required"/>
              </div>
              <div class="row g-3">
                <div class="col-6">
                  <label class="nav-management-form-label">NAV Start <span class="nav-management-text-danger">*</span></label>
                  <input type="number" step="0.01" class="nav-management-form-control" 
                         t-model="state.currentNav.nav_beginning" required="required" placeholder="0.00"/>
                </div>
                <div class="col-6">
                  <label class="nav-management-form-label">NAV End <span class="nav-management-text-danger">*</span></label>
                  <input type="number" step="0.01" class="nav-management-form-control" 
                         t-model="state.currentNav.nav_ending" required="required" placeholder="0.00"/>
                </div>
              </div>
              <div class="mb-3 mt-3">
                <label class="nav-management-form-label">Notes</label>
                <textarea class="nav-management-form-control" t-model="state.currentNav.notes" rows="2" placeholder="Optional notes"></textarea>
              </div>
            </div>
            <div class="nav-management-modal-footer">
              <button type="button" class="nav-management-btn-modern nav-management-btn-secondary-modern" t-on-click="closeModal">Cancel</button>
              <button type="submit" class="nav-management-btn-modern nav-management-btn-primary-modern" t-att-disabled="state.isSaving">
                <t t-if="state.isSaving">
                  <span class="nav-management-spinner-border nav-management-spinner-border-sm me-2"></span>Saving...
                </t>
                <t t-else="">
                  <i class="fas fa-save me-2"></i>Save
                </t>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

  setup() {
    this.state = useState({
      monthlyNav: [],
      filteredMonthlyNav: [],
      funds: this.props.funds || [],
      currentPage: 1,
      pageSize: 10,
      startIndex: 0,
      endIndex: 10,
      totalPages: 1,
      pageNumbers: [],
      totalMonthlyNav: 0,
      positiveChanges: 0,
      negativeChanges: 0,
      averageChangePercent: 0,
      loading: false,
      error: null,
      selectedFundId: this.props.selectedFundId || null,
      showModal: false,
      isEditing: false,
      currentNav: {
        id: null,
        fund_id: null,
        period: '',
        nav_beginning: 0,
        nav_ending: 0,
        notes: ''
      },
      isSaving: false,
      // Sort state
      sortColumn: 'period',
      sortDirection: 'desc',
    });

    onMounted(() => {
      this.loadData();
    });
  }

  // Filter handlers
  onFundFilterChange(event) {
    const fundId = event.target.value;
    this.state.selectedFundId = fundId ? parseInt(fundId) : null;
    this.applyFilters();
  }

  onDateFilterChange() {
    this.applyFilters();
  }

  applyFilters() {
    this.state.currentPage = 1;
    this.loadData();
  }

  // Sort by column
  sortBy(column) {
    if (this.state.sortColumn === column) {
      this.state.sortDirection = this.state.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.state.sortColumn = column;
      this.state.sortDirection = 'asc';
    }
    this.applySorting();
  }

  getSortIcon(column) {
    if (this.state.sortColumn !== column) return 'fa-sort text-muted';
    return this.state.sortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down';
  }

  applySorting() {
    const col = this.state.sortColumn;
    const dir = this.state.sortDirection;
    this.state.filteredMonthlyNav.sort((a, b) => {
      let valA = a[col], valB = b[col];
      if (valA == null) valA = '';
      if (valB == null) valB = '';
      if (col === 'upload_date' || col === 'period') {
        valA = new Date(valA || 0).getTime();
        valB = new Date(valB || 0).getTime();
      } else if (typeof valA === 'number' || typeof valB === 'number') {
        valA = parseFloat(valA) || 0;
        valB = parseFloat(valB) || 0;
      } else {
        valA = String(valA).toLowerCase();
        valB = String(valB).toLowerCase();
      }
      if (valA < valB) return dir === 'asc' ? -1 : 1;
      if (valA > valB) return dir === 'asc' ? 1 : -1;
      return 0;
    });
    this.updatePagination();
  }

  // Modal handlers
  openAddModal() {
    this.state.isEditing = false;
    this.state.currentNav = {
      id: null,
      fund_id: this.state.selectedFundId || null,
      period: '',
      nav_beginning: 0,
      nav_ending: 0,
      notes: ''
    };
    this.state.showModal = true;
  }

  editNav(nav) {
    this.state.isEditing = true;
    this.state.currentNav = { ...nav };
    this.state.showModal = true;
  }

  closeModal() {
    this.state.showModal = false;
  }

  // CRUD operations
  async saveNavMonthly(event) {
    event.preventDefault();
    
    try {
      this.state.isSaving = true;
      
      const navData = {
        fund_id: this.state.currentNav.fund_id,
        period: this.state.currentNav.period,
        nav_beginning: parseFloat(this.state.currentNav.nav_beginning),
        nav_ending: parseFloat(this.state.currentNav.nav_ending),
        notes: this.state.currentNav.notes || ''
      };

      const periodRegex = /^(0[1-9]|1[0-2])\/\d{4}$/;
      if (!periodRegex.test(navData.period)) {
        alert('Invalid format. Use MM/YYYY (e.g. 12/2024)');
        return;
      }

      const url = this.state.isEditing 
        ? `/nav_management/api/nav_monthly/${this.state.currentNav.id}`
        : '/nav_management/api/nav_monthly/create';

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: navData
        })
      });

      const result = await response.json();
      
      if (result.result && result.result.success) {
        this.closeModal();
        await this.loadData();
        alert(this.state.isEditing ? 'Updated successfully!' : 'Added successfully!');
      } else {
        throw new Error(result.error?.message || 'Error saving data');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Error: ' + error.message);
    } finally {
      this.state.isSaving = false;
    }
  }

  async deleteNav(nav) {
    if (!confirm(`Delete NAV for ${nav.period}?`)) return;

    try {
      const response = await fetch(`/nav_management/api/nav_monthly/${nav.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
      });

      const result = await response.json();
      
      if (result && result.success) {
        alert('Deleted successfully!');
        await this.loadData();
      } else {
        throw new Error(result?.message || 'Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Error: ' + error.message);
    }
  }

  // Data loading
  async loadData() {
    try {
      this.state.loading = true;
      this.state.error = null;
      
      if (this.props.funds?.length > 0) {
        this.state.funds = this.props.funds;
      }
      
      const urlParams = new URLSearchParams(window.location.search);
      const fundId = this.state.selectedFundId || urlParams.get('fund_id');
      
      if (!fundId) {
        this.state.monthlyNav = [];
        this.state.filteredMonthlyNav = [];
        this.calculateStats();
        this.updatePagination();
        this.state.loading = false;
        if (typeof window.hideSpinner === 'function') window.hideSpinner();
        return;
      }

      const response = await fetch('/nav_management/api/nav_monthly/list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {
            fund_id: fundId,
            from_date: document.getElementById('fromDateFilter')?.value,
            to_date: document.getElementById('toDateFilter')?.value
          }
        })
      });

      const result = await response.json();
      
      if (result.result?.nav_monthly) {
        this.state.monthlyNav = result.result.nav_monthly;
        this.state.filteredMonthlyNav = result.result.nav_monthly;
      } else {
        this.state.monthlyNav = [];
        this.state.filteredMonthlyNav = [];
      }
      
      this.calculateStats();
      this.updatePagination();
      this.state.loading = false;
      if (typeof window.hideSpinner === 'function') window.hideSpinner();
    } catch (error) {
      console.error('Load error:', error);
      this.state.error = error.message;
      this.state.loading = false;
      if (typeof window.showError === 'function') window.showError(error.message);
    }
  }

  async refreshData() {
    await this.loadData();
  }

  // Formatting helpers
  formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }

  formatCurrency(value) {
    if (!value) return '0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'VND',
      minimumFractionDigits: 0
    }).format(value);
  }

  formatPercentage(value) {
    if (value === null || value === undefined) return '-';
    return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
  }

  // Stats calculation
  calculateStats() {
    const navs = this.state.filteredMonthlyNav || [];
    this.state.totalMonthlyNav = navs.length;
    
    let positiveChanges = 0;
    let negativeChanges = 0;
    let totalChangePercent = 0;
    
    navs.forEach(nav => {
      const change = nav.change_percent || 0;
      if (change > 0) positiveChanges++;
      else if (change < 0) negativeChanges++;
      totalChangePercent += change;
    });
    
    this.state.positiveChanges = positiveChanges;
    this.state.negativeChanges = negativeChanges;
    this.state.averageChangePercent = navs.length > 0 ? totalChangePercent / navs.length : 0;
  }

  // Pagination
  updatePagination() {
    const totalItems = this.state.filteredMonthlyNav.length;
    this.state.totalPages = Math.ceil(totalItems / this.state.pageSize) || 1;
    this.state.startIndex = (this.state.currentPage - 1) * this.state.pageSize;
    this.state.endIndex = Math.min(this.state.startIndex + this.state.pageSize, totalItems);
    
    const pageNumbers = [];
    const maxVisible = 5;
    let start = Math.max(1, this.state.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.state.totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) pageNumbers.push(i);
    this.state.pageNumbers = pageNumbers;
  }

  changePage(page) {
    if (page >= 1 && page <= this.state.totalPages) {
      this.state.currentPage = page;
      this.updatePagination();
    }
  }

  // Export
  exportData() {
    if (!this.state.filteredMonthlyNav?.length) {
      alert('No data to export');
      return;
    }

    const headers = ['#', 'Period', 'NAV Start', 'NAV End', 'Change %', 'Upload Date'];
    const csv = [
      headers.join(','),
      ...this.state.filteredMonthlyNav.map((nav, i) => [
        i + 1,
        nav.period,
        nav.nav_beginning,
        nav.nav_ending,
        nav.change_percent || 0,
        nav.upload_date
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'nav_monthly_export.csv';
    link.click();
  }
}
