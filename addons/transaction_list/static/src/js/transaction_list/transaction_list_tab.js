/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class TransactionListTab extends Component {
  static template = xml`
    <div class="tl-container">
      <!-- Sub Tab Navigation -->
      <div class="tl-sub-tabs">
        <button class="tl-sub-tab" t-att-class="{'tl-sub-tab--active': state.activeSubTab === 'pending'}" t-on-click="() => this.setActiveSubTab('pending')">
          <i class="fas fa-clock"></i>Pending
        </button>
        <button class="tl-sub-tab" t-att-class="{'tl-sub-tab--active': state.activeSubTab === 'approved'}" t-on-click="() => this.setActiveSubTab('approved')">
          <i class="fas fa-check-circle"></i>Approved
        </button>
      </div>

      <!-- Content Header -->
      <div class="tl-header">
        <div class="tl-header__info">
          <h2 class="tl-header__title">
            <i class="fas fa-list"></i>Danh sách lệnh giao dịch
          </h2>
          <p class="tl-header__subtitle">
            Hiển thị <strong><t t-esc="state.displayedTransactions ? state.displayedTransactions.length : 0"/></strong> trong tổng số <strong><t t-esc="state.totalTransactions"/></strong> lệnh giao dịch
          </p>
        </div>
        <div class="tl-header__actions">
          <button class="tl-btn tl-btn--primary" t-on-click="exportData">
            <i class="fas fa-download"></i>Xuất file
          </button>
          <button class="tl-btn tl-btn--icon" t-on-click="() => this.state.showColumnModal = true" title="Chọn cột hiển thị">
            <i class="fas fa-cog"></i>
          </button>
        </div>
      </div>
      
      <!-- Filters Section -->
      <div class="tl-filters">
        <div class="tl-filters__header">
          <h6><i class="fas fa-filter"></i>Bộ lọc</h6>
        </div>
        <div class="tl-filters__body">
          <div class="tl-filters__row">
            <div class="tl-filters__group">
              <label>Quỹ:</label>
              <select t-on-change="onFundFilterChange" t-att-value="state.selectedFundId">
                <option value="">Tất cả quỹ</option>
                <t t-foreach="state.fundOptions" t-as="fund" t-key="fund.value">
                  <option t-att-value="fund.value" t-att-selected="state.selectedFundId == fund.value">
                    <t t-esc="fund.label"/>
                  </option>
                </t>
              </select>
            </div>
            <div class="tl-filters__group">
              <label>Ngày giao dịch:</label>
              <input type="date" t-on-change="onDateFilterChange" t-att-value="state.selectedDate"/>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Table Container -->
      <div class="tl-table-wrapper">
        <table class="tl-table">
          <thead class="tl-table__head">
            <tr>
              <th t-if="state.visibleColumns.transaction_date" class="tl-table__th--sortable" t-on-click="() => this.sortTable('transaction_date')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Phiên GD
                    <i t-att-class="this.getSortIcon('transaction_date')"></i>
                  </div>
                  <input type="date" class="tl-table__column-filter" t-on-click.stop="" t-on-change="(ev) => this.filterTable('transaction_date', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.account_number" class="tl-table__th--sortable" t-on-click="() => this.sortTable('account_number')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    STK
                    <i t-att-class="this.getSortIcon('account_number')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('account_number', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.investor_name" class="tl-table__th--sortable" t-on-click="() => this.sortTable('investor_name')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Nhà đầu tư
                    <i t-att-class="this.getSortIcon('investor_name')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('investor_name', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.investor_phone" class="tl-table__th--sortable" t-on-click="() => this.sortTable('investor_phone')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    ĐKSH
                    <i t-att-class="this.getSortIcon('investor_phone')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('investor_phone', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.fund_name" class="tl-table__th--sortable" t-on-click="() => this.sortTable('fund_name')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Quỹ
                    <i t-att-class="this.getSortIcon('fund_name')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('fund_name', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.fund_ticker" class="tl-table__th--sortable" t-on-click="() => this.sortTable('fund_ticker')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    CT
                    <i t-att-class="this.getSortIcon('fund_ticker')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('fund_ticker', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.transaction_code" class="tl-table__th--sortable" t-on-click="() => this.sortTable('transaction_code')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Mã GD
                    <i t-att-class="this.getSortIcon('transaction_code')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('transaction_code', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.transaction_type" class="tl-table__th--sortable" t-on-click="() => this.sortTable('transaction_type')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Loại
                    <i t-att-class="this.getSortIcon('transaction_type')"></i>
                  </div>
                  <select class="tl-table__column-filter" t-on-click.stop="" t-on-change="(ev) => this.filterTable('transaction_type', ev.target.value)">
                    <option value="">Tất cả</option>
                    <option value="buy">Mua</option>
                    <option value="sell">Bán</option>
                    <option value="exchange">Chuyển đổi</option>
                  </select>
                </div>
              </th>
              <th t-if="state.visibleColumns.target_fund">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">Quỹ Mục Tiêu</div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-input="(ev) => this.filterTable('target_fund', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.units" class="tl-table__th--sortable" t-on-click="() => this.sortTable('units')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Số CCQ
                    <i t-att-class="this.getSortIcon('units')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('units', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.unit_price" class="tl-table__th--sortable" t-on-click="() => this.sortTable('unit_price')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Giá
                    <i t-att-class="this.getSortIcon('unit_price')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('unit_price', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.amount" class="tl-table__th--sortable" t-on-click="() => this.sortTable('amount')">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">
                    Tổng tiền
                    <i t-att-class="this.getSortIcon('amount')"></i>
                  </div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-click.stop="" t-on-input="(ev) => this.filterTable('amount', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.matched_units and state.activeSubTab === 'approved'">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">Số lượng khớp</div>
                  <input type="text" class="tl-table__column-filter" placeholder="Tìm..." t-on-input="(ev) => this.filterTable('matched_units', ev.target.value)"/>
                </div>
              </th>
              <th t-if="state.visibleColumns.actions">
                <div class="tl-table__column-header">
                  <div class="tl-table__column-title">Thao tác</div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="tl-table__body">
            <t t-if="state.loading">
              <tr>
                <td t-att-colspan="this.getVisibleColumnsCount()">
                  <div class="tl-loading">
                    <i class="fas fa-spinner fa-spin tl-loading__icon"></i>
                    <h3 class="tl-loading__title">Đang tải dữ liệu...</h3>
                    <p class="tl-loading__description">Vui lòng chờ trong giây lát.</p>
                  </div>
                </td>
              </tr>
            </t>
            <t t-elif="state.error">
              <tr>
                <td t-att-colspan="this.getVisibleColumnsCount()">
                  <div class="tl-error">
                    <i class="fas fa-exclamation-triangle tl-error__icon"></i>
                    <h3 class="tl-error__title">Lỗi tải dữ liệu</h3>
                    <p class="tl-error__description"><t t-esc="state.error"/></p>
                    <button class="tl-btn tl-btn--primary" t-on-click="() => this.loadData()">
                      <i class="fas fa-refresh"></i>Thử lại
                    </button>
                  </div>
                </td>
              </tr>
            </t>
            <t t-elif="state.displayedTransactions and state.displayedTransactions.length > 0">
              <t t-foreach="state.displayedTransactions" t-as="transaction" t-key="transaction.id">
                <tr>
                  <td t-if="state.visibleColumns.transaction_date" class="tl-table__cell--center">
                    <div class="tl-time-info">
                      <div class="tl-time-entry">
                        <span class="tl-time-label">In:</span>
                        <span class="tl-time-value--in">
                          <t t-esc="this.formatDateTime(transaction.first_in_time || transaction.in_time || transaction.created_at)"/>
                        </span>
                      </div>
                      <t t-if="transaction.out_time">
                        <div class="tl-time-entry">
                          <span class="tl-time-label">Out:</span>
                          <span class="tl-time-value--out">
                            <t t-esc="this.formatDateTime(transaction.out_time)"/>
                          </span>
                        </div>
                      </t>
                    </div>
                  </td>
                  <td t-if="state.visibleColumns.account_number"><t t-esc="transaction.account_number or '-'"/></td>
                  <td t-if="state.visibleColumns.investor_name"><t t-esc="transaction.investor_name or '-'"/></td>
                  <td t-if="state.visibleColumns.investor_phone"><t t-esc="transaction.investor_phone or '-'"/></td>
                  <td t-if="state.visibleColumns.fund_name"><t t-esc="transaction.fund_name or '-'"/></td>
                  <td t-if="state.visibleColumns.fund_ticker" class="tl-table__cell--center"><t t-esc="transaction.fund_ticker or '-'"/></td>
                  <td t-if="state.visibleColumns.transaction_code" class="tl-table__cell--center"><t t-esc="transaction.transaction_code or '-'"/></td>
                  <td t-if="state.visibleColumns.transaction_type" class="tl-table__cell--center">
                    <span class="tl-badge" t-att-class="'tl-badge--' + transaction.transaction_type">
                      <t t-esc="this.getTransactionTypeDisplay(transaction.transaction_type)"/>
                    </span>
                  </td>
                  <td t-if="state.visibleColumns.target_fund"><t t-esc="transaction.target_fund or '-'"/></td>
                  <td t-if="state.visibleColumns.units" class="tl-table__cell--right"><t t-esc="this.formatNumber(transaction.units)"/></td>
                  <td t-if="state.visibleColumns.unit_price" class="tl-table__cell--right"><t t-esc="this.formatUnitPrice(transaction)"/></td>
                  <td t-if="state.visibleColumns.amount" class="tl-table__cell--right"><t t-esc="this.formatAmount(transaction.amount, transaction.currency)"/></td>
                  <td t-if="state.visibleColumns.matched_units and state.activeSubTab === 'approved'" class="tl-table__cell--center">
                    <span class="tl-badge tl-badge--success">
                      <t t-esc="this.formatNumber(transaction.matched_units || 0)"/>
                    </span>
                  </td>
                  <td t-if="state.visibleColumns.actions" class="tl-table__cell--center">
                    <div class="tl-actions">
                      <t t-if="transaction.has_contract">
                        <button class="tl-action-btn tl-action-btn--view" title="Xem hợp đồng" t-on-click="() => this.viewContract(transaction)">
                          <i class="fas fa-eye"></i>
                        </button>
                      </t>
                      <button class="tl-action-btn tl-action-btn--delete" t-on-click="() => this.deleteTransaction(transaction.id)" title="Xóa">
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </t>
            </t>
            <t t-else="">
              <tr>
                <td t-att-colspan="this.getVisibleColumnsCount()">
                  <div class="tl-empty-state">
                    <div class="tl-empty-state__icon">
                      <i class="fas fa-inbox"></i>
                    </div>
                    <div class="tl-empty-state__title">Không có dữ liệu</div>
                    <div class="tl-empty-state__message">Không tìm thấy lệnh giao dịch nào</div>
                  </div>
                </td>
              </tr>
            </t>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <t t-if="state.displayedTransactions.length > 0">
        <div class="tl-pagination">
          <div class="tl-pagination__info">
            Hiển thị <strong><t t-esc="this.getRegularPaginationStart()"/></strong> - <strong><t t-esc="this.getRegularPaginationEnd()"/></strong> 
            trong tổng số <strong><t t-esc="state.regularPagination.totalItems"/></strong> giao dịch
          </div>
          <div class="tl-pagination__controls">
            <button class="tl-page-btn" t-att-disabled="state.regularPagination.currentPage === 1" t-on-click="() => this.changeRegularPage(state.regularPagination.currentPage - 1)">
              <i class="fas fa-chevron-left"></i>
            </button>
            
            <t t-foreach="Array.from({length: this.getRegularTotalPages()}, (_, i) => i + 1)" t-as="page" t-key="page">
              <button class="tl-page-btn" t-att-class="{'tl-page-btn--active': page === state.regularPagination.currentPage}" t-on-click="() => this.changeRegularPage(page)">
                <t t-esc="page"/>
              </button>
            </t>
            
            <button class="tl-page-btn" t-att-disabled="state.regularPagination.currentPage === this.getRegularTotalPages()" t-on-click="() => this.changeRegularPage(state.regularPagination.currentPage + 1)">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
      </t>
      
      <!-- Contract Modal -->
      <t t-if="state.showContractModal">
        <div class="tl-modal-backdrop" t-on-click="() => this.closeContractModal()"></div>
        <div class="tl-modal tl-modal--xl">
          <div class="tl-modal__content">
            <div class="tl-modal__header">
              <h5 class="tl-modal__title">
                <i class="fas fa-file-contract"></i>
                Hợp đồng giao dịch - <t t-esc="state.selectedContract?.name || 'N/A'"/>
              </h5>
              <button class="tl-modal__close" t-on-click="() => this.closeContractModal()">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="tl-modal__body" style="padding: 0; max-height: none;">
              <div class="tl-contract-info">
                <div>
                  <strong>Mã giao dịch:</strong> <t t-esc="state.selectedContract?.transaction_code || 'N/A'"/><br/>
                  <strong>Nhà đầu tư:</strong> <t t-esc="state.selectedContract?.investor_name || 'N/A'"/><br/>
                  <strong>Số tài khoản:</strong> <t t-esc="state.selectedContract?.account_number || 'N/A'"/>
                </div>
                <div>
                  <strong>Quỹ:</strong> <t t-esc="state.selectedContract?.fund_name || 'N/A'"/><br/>
                  <strong>Loại lệnh:</strong> <t t-esc="this.getTransactionTypeDisplay(state.selectedContract?.transaction_type) || 'N/A'"/><br/>
                  <strong>Số tiền:</strong> <t t-esc="this.formatAmount(state.selectedContract?.amount, state.selectedContract?.currency)"/>
                </div>
              </div>
              <div class="tl-contract-viewer">
                <iframe t-att-src="state.selectedContract?.contract_url" title="Contract Viewer"/>
              </div>
            </div>
            <div class="tl-modal__footer">
              <a t-att-href="state.selectedContract?.contract_download_url" class="tl-btn tl-btn--primary">
                <i class="fas fa-download"></i>Tải về
              </a>
              <button class="tl-btn tl-btn--secondary" t-on-click="() => this.closeContractModal()">
                <i class="fas fa-times"></i>Đóng
              </button>
            </div>
          </div>
        </div>
      </t>
      
      <!-- Column Selector Modal -->
      <t t-if="state.showColumnModal">
        <div class="tl-modal-backdrop" t-on-click="() => this.state.showColumnModal = false"></div>
        <div class="tl-modal">
          <div class="tl-modal__content">
            <div class="tl-modal__header">
              <h5 class="tl-modal__title">Chọn cột hiển thị</h5>
              <button class="tl-modal__close" t-on-click="() => this.state.showColumnModal = false">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="tl-modal__body">
              <div class="tl-column-selector">
                <div class="tl-column-selector__item tl-column-selector__all">
                  <input type="checkbox" id="selectAll" t-on-change="(ev) => this.toggleAllColumns(ev)"/>
                  <label for="selectAll">Chọn tất cả</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_transaction_date" t-model="state.visibleColumns.transaction_date"/>
                  <label for="col_transaction_date">Phiên giao dịch</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_account_number" t-model="state.visibleColumns.account_number"/>
                  <label for="col_account_number">Số tài khoản</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_investor_name" t-model="state.visibleColumns.investor_name"/>
                  <label for="col_investor_name">Nhà đầu tư</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_investor_phone" t-model="state.visibleColumns.investor_phone"/>
                  <label for="col_investor_phone">ĐKSH</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_fund_name" t-model="state.visibleColumns.fund_name"/>
                  <label for="col_fund_name">Quỹ</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_fund_ticker" t-model="state.visibleColumns.fund_ticker"/>
                  <label for="col_fund_ticker">Chương trình</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_transaction_code" t-model="state.visibleColumns.transaction_code"/>
                  <label for="col_transaction_code">Mã GD</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_transaction_type" t-model="state.visibleColumns.transaction_type"/>
                  <label for="col_transaction_type">Loại lệnh</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_target_fund" t-model="state.visibleColumns.target_fund"/>
                  <label for="col_target_fund">Quỹ mục tiêu</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_units" t-model="state.visibleColumns.units"/>
                  <label for="col_units">Số CCQ</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_unit_price" t-model="state.visibleColumns.unit_price"/>
                  <label for="col_unit_price">Giá</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_amount" t-model="state.visibleColumns.amount"/>
                  <label for="col_amount">Tổng số tiền</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_matched_units" t-model="state.visibleColumns.matched_units"/>
                  <label for="col_matched_units">Số lượng khớp</label>
                </div>
                <div class="tl-column-selector__item">
                  <input type="checkbox" id="col_actions" t-model="state.visibleColumns.actions"/>
                  <label for="col_actions">Thao tác</label>
                </div>
              </div>
            </div>
            <div class="tl-modal__footer">
              <button class="tl-btn tl-btn--secondary" t-on-click="() => this.state.showColumnModal = false">Đóng</button>
            </div>
          </div>
        </div>
      </t>
    </div>
  `;

  setup() {
    const todayStr = new Date().toISOString().split('T')[0];
    this.state = useState({
      activeSubTab: 'pending',
      transactions: [],
      filteredTransactions: [],
      displayedTransactions: [],
      totalTransactions: 0,
      loading: false,
      error: null,
      showContractModal: false,
      selectedContract: null,
      showColumnModal: false,
      // Phân trang cho regular transactions (pending/approved)
      regularPagination: {
        currentPage: 1,
        itemsPerPage: 10,
        totalItems: 0
      },
      // Filter state
      fundOptions: [],
      selectedFundId: '',
      selectedDate: todayStr,
      selectedQuickDate: 'today',
      visibleColumns: {
        transaction_date: true,
        account_number: true,
        investor_name: true,
        investor_phone: true,
        fund_name: true,
        fund_ticker: true,
        transaction_code: true,
        transaction_type: true,
        target_fund: true,
        units: true,
        unit_price: true,
        amount: true,
        matched_units: true,
        actions: true
      },
      filters: {
        account_number: '',
        investor_name: '',
        investor_phone: '',
        fund_name: '',
        fund_ticker: '',
        transaction_code: '',
        transaction_type: '',
        target_fund: '',
        units: '',
        unit_price: '',
        amount: '',
        matched_units: '',
        transaction_date: ''
      },
      // Sort state
      sortField: '',
      sortOrder: 'asc' // 'asc' or 'desc'
    });

    onMounted(async () => {
      await this.loadData();
      await this.loadFundOptions();
    });
  }

  setActiveSubTab(tab) {
    this.state.activeSubTab = tab;
    // Reset filters khi chuyển tab
    Object.keys(this.state.filters).forEach(key => {
      this.state.filters[key] = '';
    });
    
    // Reset pagination khi chuyển tab
    this.state.regularPagination.currentPage = 1;
    
    this.loadTransactions();
  }

  async loadData() {
    try {
      this.state.loading = true;
      this.state.error = null;
      
      // Load initial data based on active tab
      if (this.state.activeSubTab === 'pending' || this.state.activeSubTab === 'approved') {
        await this.loadTransactions();
      }
      
      // Extract fund options from loaded data
      this.extractFundOptionsFromTransactions();
      
      this.state.loading = false;
    } catch (error) {
      console.error('Error loading data:', error);
      this.state.error = error.message;
      this.state.loading = false;
    }
  }

  async loadTransactions() {
    try {
      this.state.loading = true;
      this.state.error = null;
      
      // Map tab to correct status filter
      let statusFilter;
      if (this.state.activeSubTab === 'pending') {
        statusFilter = 'pending';
      } else if (this.state.activeSubTab === 'approved') {
        statusFilter = 'approved'; // This will be mapped to 'completed' in backend
      }
      
      const params = {
        status_filter: statusFilter
      };
      
      const response = await this.rpc('/api/transaction-list/data', params);
      
      // Nếu không có dữ liệu với status_filter, thử lấy tất cả dữ liệu
      if (response && response.success && (!response.data || response.data.length === 0) && statusFilter) {
        const allDataResponse = await this.rpc('/api/transaction-list/data', {});
        if (allDataResponse && allDataResponse.success && allDataResponse.data) {
          response.data = allDataResponse.data;
        }
      }

      if (response && response.success) {
        // Lọc dữ liệu theo status ngay tại đây để đảm bảo đúng
        let filteredData = response.data || [];
        
        // Nếu API không lọc đúng, lọc lại ở frontend
        if (statusFilter) {
          const expectedStatus = statusFilter === 'approved' ? 'completed' : statusFilter; // Map approved -> completed
          filteredData = filteredData.filter(transaction => {
            return transaction.status === expectedStatus;
          });
        }
        
        this.state.transactions = filteredData;
        this.state.totalTransactions = this.state.transactions.length;
        
        // Áp dụng các filter từ form nếu có
        this.applyAllFilters();
        
        // Cập nhật phân trang
        this.state.regularPagination.totalItems = this.state.filteredTransactions.length;
        this.state.regularPagination.currentPage = 1;
        this.updateRegularDisplay();
      } else {
        console.error('Error loading transactions:', response ? response.message : 'No response');
        this.state.transactions = [];
        this.state.totalTransactions = 0;
        this.state.filteredTransactions = [];
        this.state.displayedTransactions = [];
      }
      
      this.state.loading = false;
    } catch (error) {
      console.error('Error loading transactions:', error);
      this.state.error = error.message;
      this.state.transactions = [];
      this.state.totalTransactions = 0;
      this.state.filteredTransactions = [];
      this.state.displayedTransactions = [];
      this.state.loading = false;
    }
  }

  filterTable(field, value) {
    this.state.filters[field] = value;
    this.applyFilters();
  }

  // Sort table by column
  sortTable(field) {
    if (this.state.sortField === field) {
      // Toggle sort order if same field
      this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      // New field, start with ascending
      this.state.sortField = field;
      this.state.sortOrder = 'asc';
    }
    this.applySorting();
  }

  // Get sort icon class for column header
  getSortIcon(field) {
    if (this.state.sortField !== field) {
      return 'fas fa-sort tl-sort-icon';
    }
    return this.state.sortOrder === 'asc' 
      ? 'fas fa-sort-up tl-sort-icon tl-sort-icon--active' 
      : 'fas fa-sort-down tl-sort-icon tl-sort-icon--active';
  }

  // Apply sorting to filtered transactions
  applySorting() {
    if (!this.state.sortField) return;
    
    const field = this.state.sortField;
    const order = this.state.sortOrder;
    
    this.state.filteredTransactions.sort((a, b) => {
      let valA = a[field];
      let valB = b[field];
      
      // Handle null/undefined
      if (valA == null) valA = '';
      if (valB == null) valB = '';
      
      // Handle numeric fields
      if (['units', 'unit_price', 'amount', 'matched_units'].includes(field)) {
        valA = parseFloat(valA) || 0;
        valB = parseFloat(valB) || 0;
      } else if (typeof valA === 'string') {
        // Handle string fields
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
      
      let comparison = 0;
      if (valA < valB) comparison = -1;
      else if (valA > valB) comparison = 1;
      
      return order === 'asc' ? comparison : -comparison;
    });
    
    this.updateRegularDisplay();
  }

  applyFilters() {
    // Kết hợp cả filter cũ (text filters) và filter mới (dropdown filters)
    this.applyAllFilters();
  }

  applyAllFilters() {
    let filtered = [...this.state.transactions];

    // 1. Apply dropdown filters first (fund, date)
    if (this.state.selectedFundId) {
      filtered = filtered.filter(tx => {
        return Number(tx.fund_id) === Number(this.state.selectedFundId);
      });
    }

    // Filter by specific date
    if (this.state.selectedDate) {
      filtered = filtered.filter(tx => {
        const txDate = new Date(tx.date_end || tx.created_at || tx.create_date);
        if (!txDate) return false;
        
        // So sánh ngày không tính timezone
        const txDateStr = txDate.getFullYear() + '-' + 
          String(txDate.getMonth() + 1).padStart(2, '0') + '-' + 
          String(txDate.getDate()).padStart(2, '0');
        
        return txDateStr === this.state.selectedDate;
      });
    }

    // Filter by quick date
    if (this.state.selectedQuickDate) {
      const today = new Date();
      let fromTime, toTime;

      switch (this.state.selectedQuickDate) {
        case 'today':
          fromTime = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
          toTime = fromTime + (24 * 60 * 60 * 1000) - 1;
          break;
        case 'yesterday':
          const yesterday = new Date(today);
          yesterday.setDate(today.getDate() - 1);
          fromTime = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate()).getTime();
          toTime = fromTime + (24 * 60 * 60 * 1000) - 1;
          break;
        case 'last7days':
          const sevenDaysAgo = new Date(today);
          sevenDaysAgo.setDate(today.getDate() - 7);
          fromTime = new Date(sevenDaysAgo.getFullYear(), sevenDaysAgo.getMonth(), sevenDaysAgo.getDate()).getTime();
          toTime = today.getTime() + (24 * 60 * 60 * 1000) - 1;
          break;
      }

      if (fromTime && toTime) {
        filtered = filtered.filter(tx => {
          const txDate = new Date(tx.date_end || tx.created_at || tx.create_date);
          const txTime = txDate.getTime();
          return txTime >= fromTime && txTime <= toTime;
        });
      }
    }

    // 2. Apply text filters from form (existing logic)
    Object.keys(this.state.filters).forEach(field => {
      const value = this.state.filters[field];
      if (value && value.trim() !== '') {
        filtered = filtered.filter(item => {
          const itemValue = String(item[field] || '').toLowerCase();
          
          // Special handling for date filter
          if (field === 'transaction_date' && value) {
            // Ưu tiên date_end, sau đó created_at, cuối cùng create_date
            const itemDateValue = item.date_end || item.created_at || item.create_date || item[field];
            const itemDate = itemDateValue ? new Date(itemDateValue) : null;
            if (!itemDate || isNaN(itemDate.getTime())) return false;
            // So sánh ngày không tính timezone
            const itemDateStr = itemDate.getFullYear() + '-' + 
              String(itemDate.getMonth() + 1).padStart(2, '0') + '-' + 
              String(itemDate.getDate()).padStart(2, '0');
            return itemDateStr === value;
          }
          
          return itemValue.includes(value.toLowerCase());
        });
      }
    });

    this.state.filteredTransactions = filtered;
    this.state.regularPagination.totalItems = filtered.length;
    this.state.regularPagination.currentPage = 1;
    this.updateRegularDisplay();
  }

  // Phân trang cho Regular Transactions
  getRegularTotalPages() {
    return Math.ceil(this.state.regularPagination.totalItems / this.state.regularPagination.itemsPerPage);
  }

  getRegularPaginationStart() {
    return (this.state.regularPagination.currentPage - 1) * this.state.regularPagination.itemsPerPage + 1;
  }

  getRegularPaginationEnd() {
    const end = this.state.regularPagination.currentPage * this.state.regularPagination.itemsPerPage;
    return Math.min(end, this.state.regularPagination.totalItems);
  }

  changeRegularPage(page) {
    const totalPages = this.getRegularTotalPages();
    if (page < 1 || page > totalPages) return;
    this.state.regularPagination.currentPage = page;
    this.updateRegularDisplay();
  }

  updateRegularDisplay() {
    const { currentPage, itemsPerPage } = this.state.regularPagination;
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    
    this.state.displayedTransactions = this.state.filteredTransactions.slice(startIndex, endIndex);
  }

  showNotification(message, type = 'info') {
    // Tạo notification element
    if (!document || !document.body) {
      console.warn('[DEBUG] document.body not available for notification');
      return;
    }
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Tự động ẩn sau 3 giây
    setTimeout(() => {
      if (notification && notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  getTransactionTypeDisplay(type) {
    const types = {
      'buy': 'Lệnh mua',
      'sell': 'Lệnh bán',
      'exchange': 'Lệnh chuyển đổi'
    };
    return types[type] || type;
  }

  getTransactionTypeClass(type) {
    const classes = {
      'buy': 'status-buy',
      'sell': 'status-sell',
      'exchange': 'status-pending'
    };
    return classes[type] || 'status-pending';
  }

  async deleteTransaction(transactionId) {
    if (!confirm('Bạn có chắc chắn muốn xóa giao dịch này? Hành động này không thể hoàn tác.')) {
      return;
    }

    try {
      // Đảm bảo transactionId là số
      const numericId = parseInt(transactionId);
      
      // Thử phương thức đơn giản trước
      const formData = new FormData();
      formData.append('transaction_id', numericId);
      
      const response = await fetch('/api/transaction-list/delete-simple', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();

      if (result.success) {
        alert('Giao dịch đã được xóa thành công!');
        this.loadTransactions(); // Reload data
      } else {
        const errorMessage = result.message || 'Không thể xóa giao dịch';
        console.error('Delete failed:', errorMessage);
        alert('Lỗi: ' + errorMessage);
      }
    } catch (error) {
      console.error('Error deleting transaction:', error);
      
      // Fallback to original method if simple method fails
      try {
        const params = {
          transaction_id: parseInt(transactionId)
        };
        
        const response = await this.rpc('/api/transaction-list/delete', params);
        
        if (response && response.success) {
          alert('Giao dịch đã được xóa thành công!');
          this.loadTransactions();
        } else {
          const errorMessage = response?.message || 'Không thể xóa giao dịch';
          alert('Lỗi: ' + errorMessage);
        }
      } catch (fallbackError) {
        console.error('Fallback method also failed:', fallbackError);
        alert('Có lỗi xảy ra khi xóa giao dịch: ' + error.message);
      }
    }
  }

  async exportData() {
    try {
      const statusFilter = this.state.activeSubTab === 'pending' ? 'pending' : 'approved';
      const response = await this.rpc('/api/transaction-list/export', {
        status_filter: statusFilter
      });

      if (response.success) {
        this.downloadCSV(response.data, response.filename);
      } else {
        alert('Lỗi: ' + response.message);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Có lỗi xảy ra khi xuất dữ liệu');
    }
  }

  downloadCSV(content, fileName) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', fileName);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  refreshData() {
    this.loadData();
  }

  formatNumber(number) {
    if (number === null || number === undefined || number === '' || isNaN(Number(number))) {
      return '-';
    }
    const value = Number(number);
    return new Intl.NumberFormat('vi-VN').format(value);
  }

  formatDate(dateString) {
    if (!dateString) {
      return '-';
    }
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return '-';
      }
      return date.toLocaleDateString('vi-VN');
    } catch (e) {
      return '-';
    }
  }

  formatDateTime(dateString) {
    if (!dateString) {
      return '-';
    }
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return '-';
      }
      return date.toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    } catch (e) {
      return '-';
    }
  }

  formatUnitPrice(transaction) {
    // Ưu tiên unit_price, sau đó current_nav, cuối cùng tính từ amount/units
    let unitPrice = transaction.unit_price || transaction.current_nav;
    
    // Nếu không có unit_price và current_nav, tính từ amount/units
    if (!unitPrice && transaction.amount && transaction.units && transaction.units > 0) {
      unitPrice = transaction.amount / transaction.units;
    }
    
    if (!unitPrice || unitPrice === 0 || isNaN(Number(unitPrice))) {
      return '-';
    }
    
    return this.formatPriceWithDot(unitPrice, transaction.currency);
  }

  formatPriceWithDot(price, currency) {
    if (price === null || price === undefined || price === '' || isNaN(Number(price))) {
      return '-';
    }
    const value = Number(price);
    const cur = (currency || '').toString().trim().toUpperCase();
    
    try {
      if (cur === 'USD' || cur === '$' || cur === 'US$' || cur === 'US DOLLAR') {
        // Format USD với dấu chấm phân cách hàng nghìn
        return '$' + value.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        });
      }
      if (cur === 'VND' || cur === '₫' || cur === 'VND₫' || cur === '') {
        // Format VND với dấu chấm phân cách hàng nghìn, không có số thập phân
        return value.toLocaleString('vi-VN', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }) + ' VND';
      }
      // Mặc định: hiển thị theo mã tiền tệ với dấu chấm
      try {
        return value.toLocaleString('vi-VN', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        }) + ' ' + cur;
      } catch (e) {
        return value.toLocaleString('vi-VN', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }) + ' VND';
      }
    } catch (e) {
      return value.toLocaleString('vi-VN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }) + ' VND';
    }
  }

  formatAmount(amount, currency) {
    if (amount === null || amount === undefined || amount === '' || isNaN(Number(amount))) {
      return '-';
    }
    const value = Number(amount);
    const cur = (currency || '').toString().trim().toUpperCase();
    try {
      if (cur === 'USD' || cur === '$' || cur === 'US$' || cur === 'US DOLLAR') {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(value);
      }
      if (cur === 'VND' || cur === '₫' || cur === 'VND₫' || cur === '') {
        return new Intl.NumberFormat('vi-VN').format(value) + ' VND';
      }
      // Mặc định: hiển thị theo mã tiền tệ nếu hợp lệ, fallback VND style
      try {
        return new Intl.NumberFormat(undefined, { style: 'currency', currency: cur }).format(value);
      } catch (_) {
        return new Intl.NumberFormat('vi-VN').format(value) + (cur ? ' ' + cur : ' VND');
      }
    } catch (e) {
      return value + (cur ? ' ' + cur : ' VND');
    }
  }

  viewContract(transaction) {
    this.state.selectedContract = transaction;
    this.state.showContractModal = true;
  }

  closeContractModal() {
    this.state.showContractModal = false;
    this.state.selectedContract = null;
  }

  getVisibleColumnsCount() {
    let count = 0;
    Object.keys(this.state.visibleColumns).forEach(key => {
      if (this.state.visibleColumns[key]) {
        // Cột "Số lượng khớp" chỉ hiển thị ở tab "Approved"
        if (key === 'matched_units' && this.state.activeSubTab !== 'approved') {
          return; // Bỏ qua cột này nếu không ở tab approved
        }
        count++;
      }
    });
    return count;
  }

  toggleAllColumns(ev) {
    const checked = ev.target.checked;
    Object.keys(this.state.visibleColumns).forEach(key => {
      this.state.visibleColumns[key] = checked;
    });
  }

  // Filter functions
  async loadFundOptions() {
    try {
      // First try the funds API
      const response = await fetch('/api/transaction-list/funds', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({})
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data && data.success && data.data && data.data.length > 0) {
          this.state.fundOptions = data.data.map(fund => ({
            value: fund.id,
            label: `${fund.name} (${fund.ticker || fund.symbol || ''})`
          }));
          return;
        }
      }
      
      // Fallback: extract from transactions
      this.extractFundOptionsFromTransactions();
      
    } catch (error) {
      console.error('Error loading fund options:', error);
      this.extractFundOptionsFromTransactions();
    }
  }

  extractFundOptionsFromTransactions() {
    const funds = new Map();
    
    // Extract from regular transactions
    this.state.transactions.forEach(tx => {
      if (tx.fund_id && tx.fund_name) {
        funds.set(tx.fund_id, {
          value: tx.fund_id,
          label: tx.fund_name + (tx.fund_ticker ? ` (${tx.fund_ticker})` : '')
        });
      }
    });
    
    this.state.fundOptions = Array.from(funds.values());
  }

  onFundFilterChange(ev) {
    this.state.selectedFundId = ev.target.value;
    this.applyFilters();
  }

  onDateFilterChange(ev) {
    this.state.selectedDate = ev.target.value;
    this.state.selectedQuickDate = '';
    this.applyFilters();
  }

  onQuickDateFilterChange(ev) {
    this.state.selectedQuickDate = ev.target.value;
    this.state.selectedDate = '';
    this.applyFilters();
  }

  async rpc(route, params) {
    try {
      const response = await fetch(route, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(params)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Handle JSON-RPC format
      if (data && data.jsonrpc && data.result) {
        return data.result;
      }
      
      // Handle direct response format
      if (data && typeof data === 'object') {
        return data;
      }
      
      return data;
    } catch (error) {
      console.error('RPC Error:', error);
      throw error;
    }
  }
}