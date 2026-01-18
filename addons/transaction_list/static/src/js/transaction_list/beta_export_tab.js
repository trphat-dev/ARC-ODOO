/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class BetaExportTab extends Component {
  static template = xml`
    <div class="tab-content">
      <div class="row">
        <div class="col-12">
          <h3 class="mb-4">
            <i class="fas fa-file-export me-2"></i>Beta Export - Xem trước file R44 VSD
          </h3>
          <div class="card">
            <div class="card-body">
              <!-- Bước 1: Chọn phiên giao dịch và nhập NAV -->
              <div class="row mb-4">
                <div class="col-md-6">
                  <label class="form-label fw-bold">
                    <i class="fas fa-calendar me-2"></i>Phiên giao dịch:
                  </label>
                  <div class="input-group">
                    <input 
                      type="date" 
                      id="trading-session"
                      name="trading-session"
                      class="form-control" 
                      t-model="state.tradingSession"
                      t-on-change="onTradingSessionChange"
                    />
                    <span class="input-group-text">
                      <i class="fas fa-calendar"></i>
                    </span>
                  </div>
                </div>
                <div class="col-md-6">
                  <label class="form-label fw-bold">
                    <i class="fas fa-chart-line me-2"></i>NAV (Net Asset Value):
                  </label>
                  <div class="input-group">
                    <input 
                      type="number" 
                      id="nav-value"
                      name="nav-value"
                      class="form-control" 
                      placeholder="Nhập NAV..."
                      t-model="state.navValue"
                      t-on-change="onNavChange"
                      step="0.01"
                      min="0"
                    />
                    <span class="input-group-text">VND</span>
                  </div>
                </div>
              </div>
              
              <!-- Bước 2: Upload file R44 -->
              <div class="row mb-4">
                <div class="col-md-8">
                  <label class="form-label fw-bold">
                    <i class="fas fa-upload me-2"></i>Upload file R44 từ VSD:
                  </label>
                  <div class="upload-area" t-on-click="triggerFileUpload" t-att-class="state.isDragOver ? 'drag-over' : ''">
                    <div class="upload-content">
                      <i class="fas fa-file-upload fa-3x mb-3"></i>
                      <h5>UPLOAD FILE R44 VSD</h5>
                      <p>Kéo &amp; thả file R44 vào đây hoặc <a href="#" t-on-click.prevent="triggerFileUpload">chọn file</a></p>
                      <small class="text-muted">Hỗ trợ file Excel (.xlsx, .xls)</small>
                      
                      <t t-if="state.uploadedFile">
                        <div class="uploaded-file mt-3">
                          <i class="fas fa-file-excel me-2 text-success"></i>
                          <span t-esc="state.uploadedFile.name"/>
                          <button class="btn btn-sm btn-outline-danger ms-2" t-on-click="removeFile">
                            <i class="fas fa-trash"></i>
                          </button>
                        </div>
                      </t>
                    </div>
                  </div>
                  <input 
                    type="file" 
                    ref="fileInput" 
                    accept=".xlsx,.xls" 
                    style="display: none;"
                    t-on-change="onFileSelected"
                  />
                </div>
                <div class="col-md-4 d-flex align-items-end">
                  <button 
                    class="btn btn-lg w-100 btn-orange" 
                    title="Xác nhận upload file R44"
                    t-on-click="confirmUpload"
                    t-att-disabled="!state.canConfirm"
                  >
                    <i class="fas fa-check me-2"></i>XÁC NHẬN
                  </button>
                </div>
              </div>

              <!-- Bước 3: Bảng đối soát lệnh giao dịch -->
              <div class="mt-4" t-if="state.transactions.length > 0">
                <h5>
                  <i class="fas fa-table me-2"></i>Bảng đối soát lệnh giao dịch
                </h5>
                <p class="text-muted">
                  <i class="fas fa-info-circle me-1"></i>
                  Tổng số lệnh giao dịch: <strong t-esc="state.transactions.length"></strong>
                </p>
                
                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead class="table-dark">
                      <tr>
                        <th>Account No</th>
                        <th>Investor</th>
                        <th>Fund</th>
                        <th>Trade Code</th>
                        <th>Order Type</th>
                        <th>Gross Amount</th>
                        <th>Net Amount</th>
                        <th>NAV</th>
                        <th>Total CCQ</th>
                        <th>FEEAMC</th>
                        <th>FEEDXX</th>
                        <th>FEEFUND</th>
                        <th>FEETO</th>
                      </tr>
                    </thead>
                    <tbody>
                      <t t-foreach="state.transactions" t-as="transaction" t-key="transaction.id">
                        <tr>
                          <td><t t-esc="transaction.accountNo"/></td>
                          <td><t t-esc="transaction.investor"/></td>
                          <td><t t-esc="transaction.fund"/></td>
                          <td><t t-esc="transaction.tradeCode"/></td>
                          <td>
                            <span class="badge" t-att-class="transaction.orderType === 'Lệnh mua' ? 'bg-success' : 'bg-orange'">
                              <t t-esc="transaction.orderType"/>
                            </span>
                          </td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.grossAmount)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.netAmount)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.nav)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.totalCCQ)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.feeAMC)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.feeDXX)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.feeFund)"/></td>
                          <td class="text-end"><t t-esc="this.formatNumber(transaction.feeTO)"/></td>
                        </tr>
                      </t>
                    </tbody>
                  </table>
                </div>
                
                <!-- Tổng kết -->
                <div class="row mt-3">
                  <div class="col-md-6">
                    <div class="card bg-light">
                      <div class="card-body">
                        <h6 class="card-title">Tổng kết</h6>
                        <div class="row">
                          <div class="col-6">
                            <small class="text-muted">Tổng Gross Amount:</small>
                            <div class="fw-bold"><t t-esc="this.formatNumber(state.totalGrossAmount)"/></div>
                          </div>
                          <div class="col-6">
                            <small class="text-muted">Tổng Net Amount:</small>
                            <div class="fw-bold"><t t-esc="this.formatNumber(state.totalNetAmount)"/></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="card bg-light">
                      <div class="card-body">
                        <h6 class="card-title">Phí</h6>
                        <div class="row">
                          <div class="col-6">
                            <small class="text-muted">Tổng phí:</small>
                            <div class="fw-bold"><t t-esc="this.formatNumber(state.totalFees)"/></div>
                          </div>
                          <div class="col-6">
                            <small class="text-muted">Tổng CCQ:</small>
                            <div class="fw-bold"><t t-esc="this.formatNumber(state.totalCCQ)"/></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Thông báo khi chưa có dữ liệu -->
              <div class="mt-4" t-if="state.transactions.length === 0 and state.hasConfirmed">
                <div class="alert alert-info text-center">
                  <i class="fas fa-info-circle fa-2x mb-3"></i>
                  <h5>Chưa có dữ liệu</h5>
                  <p>Vui lòng upload file R44 và xác nhận để xem dữ liệu đối soát.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  setup() {
    this.state = useState({
      tradingSession: '',
      navValue: '',
      uploadedFile: null,
      isDragOver: false,
      canConfirm: false,
      hasConfirmed: false,
      transactions: [],
      totalGrossAmount: 0,
      totalNetAmount: 0,
      totalFees: 0,
      totalCCQ: 0
    });

    onMounted(() => {
      // Đảm bảo refs đã được khởi tạo
('BetaExportTab mounted, refs:', this.refs);
    });
  }

  onTradingSessionChange(ev) {
    this.state.tradingSession = ev.target.value;
    this.checkCanConfirm();
  }

  onNavChange(ev) {
    this.state.navValue = ev.target.value;
    this.checkCanConfirm();
  }

  checkCanConfirm() {
    this.state.canConfirm = this.state.tradingSession && 
                           this.state.navValue && 
                           this.state.uploadedFile;
  }

  triggerFileUpload() {
    if (this.refs && this.refs.fileInput) {
      this.refs.fileInput.click();
    } else {
      console.warn('fileInput ref not available yet');
      // Fallback: tạo input file tạm thời
      const tempInput = document.createElement('input');
      tempInput.type = 'file';
      tempInput.accept = '.xlsx,.xls';
      tempInput.style.display = 'none';
      tempInput.onchange = (ev) => this.onFileSelected(ev);
      document.body.appendChild(tempInput);
      tempInput.click();
      document.body.removeChild(tempInput);
    }
  }

  onFileSelected(ev) {
    const file = ev.target.files[0];
    if (file) {
      this.state.uploadedFile = file;
      this.checkCanConfirm();
    }
  }

  removeFile() {
    this.state.uploadedFile = null;
    if (this.refs && this.refs.fileInput) {
      this.refs.fileInput.value = '';
    }
    this.checkCanConfirm();
  }

  async confirmUpload() {
    if (!this.state.canConfirm) {
      alert('Vui lòng điền đầy đủ thông tin và upload file R44');
      return;
    }

    try {
      // Simulate processing file R44
      this.state.hasConfirmed = true;
      
      // Mock data - trong thực tế sẽ parse file Excel
      this.state.transactions = [
        {
          id: 1,
          accountNo: '911CL39541',
          investor: 'TRẦN ĐÌNH B',
          fund: 'FFC1TEST-FFC1N003',
          tradeCode: '220413228484',
          orderType: 'Lệnh mua',
          grossAmount: 2000000,
          netAmount: 1994000,
          nav: parseFloat(this.state.navValue) || 15678.87,
          totalCCQ: 127.17,
          feeAMC: 3000,
          feeDXX: 0,
          feeFund: 3000,
          feeTO: 6000
        },
        {
          id: 2,
          accountNo: '911CL39541',
          investor: 'TRẦN ĐÌNH B',
          fund: 'FFC1TEST-FFC1N003',
          tradeCode: '220413493361',
          orderType: 'Lệnh bán',
          grossAmount: 156789,
          netAmount: 153496,
          nav: parseFloat(this.state.navValue) || 15678.87,
          totalCCQ: 10,
          feeAMC: 1568,
          feeDXX: 0,
          feeFund: 1568,
          feeTO: 3136
        }
      ];

      this.calculateTotals();
      
      alert('File R44 đã được xử lý thành công!');
      
    } catch (error) {
      console.error('Error processing file:', error);
      alert('Có lỗi xảy ra khi xử lý file R44');
    }
  }

  calculateTotals() {
    this.state.totalGrossAmount = this.state.transactions.reduce((sum, t) => sum + t.grossAmount, 0);
    this.state.totalNetAmount = this.state.transactions.reduce((sum, t) => sum + t.netAmount, 0);
    this.state.totalFees = this.state.transactions.reduce((sum, t) => sum + t.feeAMC + t.feeDXX + t.feeFund + t.feeTO, 0);
    this.state.totalCCQ = this.state.transactions.reduce((sum, t) => sum + t.totalCCQ, 0);
  }

  formatNumber(value) {
    if (typeof value === 'number') {
      return value.toLocaleString('vi-VN');
    }
    return value || '0';
  }
} 