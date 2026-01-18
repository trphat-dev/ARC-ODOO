/** @odoo-module */

import { Component, xml } from "@odoo/owl";

export class OrderAllocationTab extends Component {
  static template = xml`
    <div class="tab-content">
      <div class="row">
        <div class="col-12">
          <h3 class="mb-4">Phân bố lệnh (R44)</h3>
          <div class="card">
            <div class="card-body">
              <p class="text-muted mb-3">Vui lòng chọn phiên giao dịch để có thể tiếp tục.</p>
              
              <div class="row mb-4">
                <div class="col-md-3">
                  <label class="form-label">Phiên giao dịch: 15/04/2022</label>
                  <div class="input-group">
                    <input type="date" class="form-control" value="2022-04-15"/>
                    <span class="input-group-text"><i class="fas fa-calendar"></i></span>
                  </div>
                </div>
                <div class="col-md-3">
                  <label class="form-label">FFC5:</label>
                  <input type="text" class="form-control" value="d"/>
                </div>
                <div class="col-md-3">
                  <label class="form-label">FFC1TEST:</label>
                  <input type="text" class="form-control" value="15,678.87"/>
                </div>
                <div class="col-md-3">
                  <label class="form-label">QUY-TEST:</label>
                  <input type="text" class="form-control" value="d"/>
                </div>
              </div>

              <div class="row mb-4">
                <div class="col-md-8">
                  <div class="d-flex align-items-start">
                    <div class="step-circle me-3">1</div>
                    <div class="flex-grow-1">
                      <h6>Update final NAV/CCQ</h6>
                      <p class="text-muted">Vui lòng update NAV/CCQ của phiên giao dịch mới nhất.</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-4 d-flex align-items-center">
                  <button class="btn btn-lg w-100" style="background-color:#f97316;border-color:#f97316;color:white">
                    <i class="fas fa-save me-2"></i>LƯU &amp; TIẾP TỤC
                  </button>
                </div>
              </div>

              <div class="row mb-4">
                <div class="col-md-8">
                  <div class="d-flex align-items-start">
                    <div class="step-circle me-3">2</div>
                    <div class="flex-grow-1">
                      <h6>Upload final R44</h6>
                      <p class="text-muted">Vui lòng upload file R44 của VSD.</p>
                      <div class="upload-area">
                        <div class="upload-content">
                          <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i>
                          <h6>UPLOAD FINAL R44</h6>
                          <p>Kéo &amp; thả tệp vào đây hoặc <a href="#" class="text-primary">chọn file</a></p>
                        </div>
                      </div>
                      <div class="mt-2">
                        <a href="#" class="text-primary">
                          <i class="fas fa-download me-1"></i>Tải file mẫu R44
                        </a>
                        <span class="ms-2">Export_R44_Template (1).xlsx</span>
                        <button class="btn btn-sm btn-outline-danger ms-2">
                          <i class="fas fa-trash"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="col-md-4 d-flex align-items-center">
                  <button class="btn btn-lg w-100" style="background-color:#f97316;border-color:#f97316;color:white">
                    <i class="fas fa-eye me-2"></i>XEM TRƯỚC ĐỐI SOÁT
                  </button>
                </div>
              </div>

              <div class="mt-4">
                <p class="text-muted">tổng số danh sách: 2</p>
                <div class="table-responsive">
                  <table class="table table-striped">
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
                        <th>FEEDIXK</th>
                        <th>FEEFUND</th>
                        <th>FEET</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td rowspan="2">911CL39541</td>
                        <td rowspan="2">TRẦN ĐÌNH B</td>
                        <td rowspan="2">FFC1TEST - FFC1N003</td>
                        <td rowspan="2">220413228484</td>
                        <td rowspan="2">Lệnh mua</td>
                        <td>2,000,000</td>
                        <td>1,994,000</td>
                        <td>15,678.87</td>
                        <td>127.17</td>
                        <td>3,000</td>
                        <td>0</td>
                        <td>3,000</td>
                        <td>6,000</td>
                      </tr>
                      <tr class="table-light">
                        <td>2,000,000</td>
                        <td>1,994,000</td>
                        <td>15,678.87</td>
                        <td>127.17</td>
                        <td>3,000</td>
                        <td>0</td>
                        <td>3,000</td>
                        <td>6,000</td>
                      </tr>
                      <tr>
                        <td rowspan="2">911CL39541</td>
                        <td rowspan="2">TRẦN ĐÌNH B</td>
                        <td rowspan="2">FFC1TEST - FFC1N003</td>
                        <td rowspan="2">220413493361</td>
                        <td rowspan="2">Lệnh bán</td>
                        <td>156,789</td>
                        <td>153,496</td>
                        <td>15,678.87</td>
                        <td>10</td>
                        <td>1,568</td>
                        <td>0</td>
                        <td>1,568</td>
                        <td>3,136</td>
                      </tr>
                      <tr class="table-light">
                        <td>156,789</td>
                        <td>153,496</td>
                        <td>15,678.87</td>
                        <td>10</td>
                        <td>1,568</td>
                        <td>0</td>
                        <td>1,568</td>
                        <td>3,136</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
} 