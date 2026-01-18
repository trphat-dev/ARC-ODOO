console.log("Loading SipSettingsWidget component...");

const { Component, xml, useState, onMounted } = window.owl;

class SipSettingsWidget extends Component {
    static template = xml`
    <div class="sip-settings-container slide-in-bottom">
        <!-- Header Section -->
        <div class="page-header d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div>
                <h1 class="h3 mb-1">Cài đặt SIP</h1>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="#"><i class="fas fa-home me-1"></i>Trang chủ</a></li>
                        <li class="breadcrumb-item active" aria-current="page">Danh mục cấu hình SIP</li>
                    </ol>
                </nav>
            </div>
            <button t-on-click="createNew" class="btn btn-fmc-primary d-flex align-items-center gap-2">
                <i class="fas fa-plus"></i>
                <span>Tạo cấu hình</span>
            </button>
        </div>

        <!-- Search and Filter Section -->
        <div class="card-fmc">
            <div class="card-body">
                <div class="row g-3 align-items-center">
                    <div class="col-lg-6 col-md-8">
                        <div class="position-relative">
                            <i class="fas fa-search position-absolute top-50 start-0 translate-middle-y ms-3 text-muted"></i>
                            <input type="text" 
                                placeholder="Nhập tên chương trình SIP để tìm kiếm..." 
                                class="form-control fmc-search-input ps-5"
                                t-on-input="onSearchInput" 
                                t-on-keyup="onSearchKeyup" 
                                t-model="state.searchTerm"
                            />
                        </div>
                    </div>
                    <div class="col-lg-6 col-md-4 text-end">
                        <div class="d-flex align-items-center justify-content-end gap-2">
                             <span class="text-muted small">
                                Tổng <strong class="text-primary" t-esc="state.totalRecords"/> bản ghi
                            </span>
                             <button t-on-click="performSearch" class="btn btn-light border fw-semibold">
                                <i class="fas fa-sync-alt me-1"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- SIP Settings Table Section -->
        <div class="card-fmc">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-fmc table-hover align-middle">
                        <thead>
                            <tr>
                                <th>Chương trình của SIP</th>
                                <th class="text-center">Số kỳ bỏ lỡ tối đa</th>
                                <th>Số tiền tối thiểu/kỳ</th>
                                <th class="text-center">Số kỳ duy trì tối thiểu</th>
                                <th>Mã chu kỳ</th>
                                <th class="text-center">Đầu tư nhiều lần</th>
                                <th class="text-center">Kích hoạt</th>
                                <th class="text-center" style="width: 120px;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-if="state.loading">
                                <tr>
                                    <td colspan="8" class="text-center py-5">
                                        <div class="d-flex flex-column justify-content-center align-items-center">
                                            <div class="spinner-border text-primary mb-3" role="status"></div>
                                            <p class="text-muted mb-0">Đang tải dữ liệu...</p>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                            <t t-if="!state.loading and state.settings.length === 0">
                                <tr>
                                    <td colspan="8" class="text-center py-5">
                                        <div class="d-flex flex-column align-items-center">
                                             <div class="bg-light rounded-circle p-4 mb-3">
                                                 <i class="fas fa-cogs fa-3x text-secondary opacity-50"></i>
                                            </div>
                                            <h5 class="text-muted mb-3">Chưa có cấu hình SIP nào</h5>
                                            <p class="text-muted mb-4">Bắt đầu bằng cách tạo cấu hình SIP đầu tiên của bạn.</p>
                                            <button class="btn btn-fmc-primary" t-on-click="createNew">
                                                <i class="fas fa-plus me-2"></i>Tạo cấu hình SIP
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                            <t t-foreach="state.settings" t-as="setting" t-key="setting.id">
                                <tr>
                                    <td>
                                        <div class="fw-bold text-dark" t-esc="setting.sip_scheme_name"/>
                                    </td>
                                    <td class="text-center">
                                         <span class="badge bg-light text-dark border fw-bold" t-esc="setting.max_non_consecutive_periods"/>
                                    </td>
                                    <td>
                                        <span class="fw-bold text-success" t-esc="formatCurrency(setting.min_monthly_amount)"/> <small>VND</small>
                                    </td>
                                    <td class="text-center">
                                         <span class="badge bg-light text-dark border fw-bold" t-esc="setting.min_maintenance_periods"/>
                                    </td>
                                    <td>
                                        <span class="badge-fmc badge-info" t-esc="setting.cycle_code"/>
                                    </td>
                                    <td class="text-center">
                                        <i t-if="setting.allow_multiple_investments" class="fas fa-check-circle text-success fa-lg"/>
                                        <i t-else="" class="fas fa-times-circle text-muted fa-lg"/>
                                    </td>
                                    <td class="text-center">
                                        <span t-if="setting.active" class="badge-fmc badge-success">Active</span>
                                        <span t-else="" class="badge-fmc badge-danger">Inactive</span>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group">
                                            <button t-on-click="() => this.handleEdit(setting.id)" class="btn btn-sm btn-light border text-secondary">
                                                <i class="fas fa-pen"></i>
                                            </button>
                                            <button t-on-click="() => this.confirmDelete(setting.id, setting.sip_scheme_name)" class="btn btn-sm btn-light border text-danger">
                                                <i class="fas fa-trash-alt"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </div>

                <!-- Mobile Cards -->
                <div class="d-lg-none mt-3">
                    <t t-if="state.loading">
                        <div class="text-center py-5">
                            <div class="spinner-border text-primary mb-3" role="status"></div>
                             <p class="text-muted mb-0">Đang tải dữ liệu...</p>
                        </div>
                    </t>
                    <t t-if="!state.loading and state.settings.length === 0">
                         <div class="text-center py-5">
                            <h5 class="text-muted">Chưa có dữ liệu</h5>
                        </div>
                    </t>
                    <t t-foreach="state.settings" t-as="setting" t-key="setting.id">
                        <div class="card-fmc mb-3">
                            <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <div>
                                        <h6 class="fw-bold mb-0 text-dark" t-esc="setting.sip_scheme_name"/>
                                        <small class="text-muted" t-esc="setting.cycle_code"/>
                                    </div>
                                    <span t-if="setting.active" class="badge-fmc badge-success">Active</span>
                                    <span t-else="" class="badge-fmc badge-danger">Inactive</span>
                                </div>
                                <div class="row g-2 small mb-3">
                                     <div class="col-6">
                                        <div class="text-muted">Tối thiều/kỳ:</div>
                                        <div class="fw-bold text-success" t-esc="formatCurrency(setting.min_monthly_amount)"/> <small>VND</small>
                                    </div>
                                    <div class="col-6">
                                         <div class="text-muted">Đầu tư nhiều lần:</div>
                                         <span t-if="setting.allow_multiple_investments" class="text-success"><i class="fas fa-check me-1"></i>Có</span>
                                         <span t-else="" class="text-muted"><i class="fas fa-times me-1"></i>Không</span>
                                    </div>
                                </div>
                                <div class="d-flex justify-content-end gap-2">
                                     <button t-on-click="() => this.handleEdit(setting.id)" class="btn btn-sm btn-light border">
                                        <i class="fas fa-edit"></i> Sửa
                                    </button>
                                    <button t-on-click="() => this.confirmDelete(setting.id, setting.sip_scheme_name)" class="btn btn-sm btn-light border text-danger">
                                        <i class="fas fa-trash"></i> Xóa
                                    </button>
                                </div>
                            </div>
                        </div>
                    </t>
                </div>
            </div>
            
            <!-- Pagination Controls -->
            <t t-if="totalPages > 1">
                <div class="card-footer border-0 pt-3">
                    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
                        <div class="d-flex align-items-center gap-2">
                            <span class="text-muted small">Hiển thị</span>
                            <select class="form-select form-select-sm" style="width: 70px;" t-model="state.limit" t-on-change="() => { state.currentPage = 1; loadData(); }">
                                <option value="10">10</option><option value="25">25</option><option value="50">50</option>
                            </select>
                             <span class="text-muted small">mỗi trang</span>
                        </div>
                        <nav aria-label="Page navigation">
                            <ul class="pagination pagination-sm mb-0">
                                <li t-attf-class="page-item #{state.currentPage === 1 ? 'disabled' : ''}">
                                    <a class="page-link" href="#" t-on-click.prevent="() => this.changePage(state.currentPage - 1)">«</a>
                                </li>
                                <t t-foreach="getPaginationRange()" t-as="page" t-key="page">
                                    <li t-if="page === '...'" class="page-item disabled"><span class="page-link">...</span></li>
                                    <li t-else="" t-attf-class="page-item #{page === state.currentPage ? 'active' : ''}">
                                        <a class="page-link" href="#" t-on-click.prevent="() => this.changePage(page)" t-esc="page"/>
                                    </li>
                                </t>
                                <li t-attf-class="page-item #{state.currentPage === totalPages ? 'disabled' : ''}">
                                    <a class="page-link" href="#" t-on-click.prevent="() => this.changePage(state.currentPage + 1)">»</a>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            </t>
        </div>

        <!-- Delete Confirmation Modal -->
        <div class="modal fade" id="deleteSipSettingModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0 pb-0"><h5 class="modal-title text-danger" id="deleteModalLabel"><i class="fas fa-exclamation-triangle me-2"></i>Xác nhận xóa</h5><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div>
                    <div class="modal-body pt-2">
                        <p class="mb-3">Bạn có chắc chắn muốn xóa cài đặt SIP cho chương trình:</p>
                        <div class="bg-light p-3 rounded"><strong t-esc="state.deleteTarget.name"></strong></div>
                        <p class="mt-3 text-muted small">Hành động này không thể hoàn tác.</p>
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal"><i class="fas fa-times me-1"></i>Hủy</button>
                        <button type="button" class="btn btn-danger" t-on-click="handleDelete"><i class="fas fa-trash me-1"></i>Xác nhận xóa</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Toast Notification -->
        <div class="position-fixed top-0 end-0 p-3" style="z-index: 1100">
            <div id="sipSettingToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header"><i class="fas fa-check-circle text-success me-2"></i><strong class="me-auto">Thông báo</strong><button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button></div>
                <div class="toast-body" t-esc="state.toastMessage"></div>
            </div>
        </div>
    </div>
    `;

    setup() {
        this.state = useState({
            settings: [],
            searchTerm: "",
            loading: true,
            currentPage: 1,
            totalRecords: 0,
            limit: 10,
            deleteTarget: { id: null, name: '' },
            toastMessage: ''
        });

        this.searchTimeout = null;

        onMounted(() => {
            this.loadData();
        });
    }

    get totalPages() {
        return Math.ceil(this.state.totalRecords / this.state.limit);
    }

    getPaginationRange() {
        const current = this.state.currentPage;
        const total = this.totalPages;
        const range = [];
        if (total <= 7) {
            for (let i = 1; i <= total; i++) range.push(i);
        } else {
            if (current < 5) {
                range.push(1, 2, 3, 4, 5, '...', total);
            } else if (current > total - 4) {
                range.push(1, '...', total - 4, total - 3, total - 2, total - 1, total);
            } else {
                range.push(1, '...', current - 1, current, current + 1, '...', total);
            }
        }
        return range;
    }

    async loadData() {
        this.state.loading = true;
        const params = new URLSearchParams({
            page: this.state.currentPage,
            limit: this.state.limit,
            search: this.state.searchTerm.trim(),
        });
        try {
            const response = await fetch(`/get_sip_settings_data?${params.toString()}`);
            if (!response.ok) throw new Error(`Network response was not ok`);
            const result = await response.json();
            if (result.error) throw new Error(result.error);
            this.state.settings = result.records || [];
            this.state.totalRecords = result.total_records || 0;
        } catch (error) {
            console.error("Error fetching SIP settings:", error);
            this.state.settings = [];
            this.state.totalRecords = 0;
        } finally {
            this.state.loading = false;
        }
    }

    changePage(newPage) {
        if (newPage > 0 && newPage <= this.totalPages && newPage !== this.state.currentPage) {
            this.state.currentPage = newPage;
            this.loadData();
        }
    }
    
    onSearchInput(ev) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.performSearch();
        }, 300);
    }

    onSearchKeyup(ev) {
        if (ev.key === 'Enter') {
            clearTimeout(this.searchTimeout); // Hủy debounce nếu người dùng nhấn Enter
            this.performSearch();
        }
    }

    performSearch() {
        this.state.currentPage = 1;
        this.loadData();
    }
    
    handleEdit(id) {
        window.location.href = `/sip_settings/edit/${id}`;
    }

    confirmDelete(id, name) {
        this.state.deleteTarget = { id, name };
        const modal = new bootstrap.Modal(document.getElementById('deleteSipSettingModal'));
        modal.show();
    }

    async handleDelete() {
        if (!this.state.deleteTarget.id) return;

        const modalElement = document.getElementById('deleteSipSettingModal');
        const modal = bootstrap.Modal.getInstance(modalElement);

        try {
            const response = await fetch('/sip_settings/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: this.state.deleteTarget.id })
            });

            if (modal) modal.hide();

            const result = await response.json();

            if (response.ok && result.success) {
                this.state.toastMessage = result.message;
                this.showToast();
                // Nếu trang hiện tại trống sau khi xóa, hãy quay lại trang trước đó
                if (this.state.settings.length === 1 && this.state.currentPage > 1) {
                    this.state.currentPage--;
                }
                await this.loadData();
            } else {
                alert(`Lỗi khi xóa: ${result.error || 'Lỗi không xác định'}`);
            }
        } catch (error) {
            if (modal) modal.hide();
            console.error('Error during delete operation:', error);
            alert(`Có lỗi xảy ra: ${error.message}`);
        } finally {
            this.state.deleteTarget = { id: null, name: '' };
        }
    }

    showToast() {
        const toastElement = document.getElementById('sipSettingToast');
        if (toastElement) {
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
        }
    }
    
    createNew() {
        window.location.href = '/sip_settings/new';
    }
    
    formatCurrency(value) {
        if (typeof value !== 'number') return value;
        return new Intl.NumberFormat('vi-VN', { style: 'decimal' }).format(value);
    }
}

if (!window.SipSettingsWidget) {
    window.SipSettingsWidget = SipSettingsWidget;
    console.log("SipSettingsWidget component updated and loaded successfully.");
} else {
    console.log("SipSettingsWidget already exists, skipping registration.");
}
