console.log("Loading SchemeWidget...");

const { Component, xml, useState, onMounted } = window.owl;

class SchemeWidget extends Component {
static template = xml`
    <div class="scheme-container slide-in-bottom">
        <!-- Header Section -->
        <div class="page-header d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div>
                <h1 class="h3 mb-1">Chương trình đầu tư</h1>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="#"><i class="fas fa-home me-1"></i>Trang chủ</a></li>
                        <li class="breadcrumb-item active" aria-current="page">Danh mục chương trình</li>
                    </ol>
                </nav>
            </div>
            <button t-on-click="createNew" class="btn btn-fmc-primary d-flex align-items-center gap-2">
                <i class="fas fa-plus"></i>
                <span>Tạo mới</span>
            </button>
        </div>

        <!-- Filter and Search Section -->
        <div class="card-fmc">
            <div class="card-body">
                <div class="row g-2 align-items-center">
                    <div class="col-lg-6 col-md-8">
                        <div class="position-relative">
                             <i class="fas fa-search position-absolute top-50 start-0 translate-middle-y ms-3 text-muted"></i>
                            <input type="text" 
                                placeholder="Tìm theo tên hoặc mã giao dịch..."
                                class="form-control fmc-search-input ps-5"
                                t-on-input="onSearchInput"
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

        <!-- Data Table Section -->
        <div class="card-fmc">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-fmc table-hover align-middle">
                        <thead>
                            <tr>
                                <th>Tên chương trình</th>
                                <th>Mã giao dịch</th>
                                <th>Giá trị mua tối thiểu</th>
                                <th>Quyền hạn</th>
                                <th class="text-center">Trạng thái</th>
                                <th class="text-center" style="width: 120px;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-if="state.loading">
                                <tr><td colspan="6" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Đang tải dữ liệu...</p></td></tr>
                            </t>
                            <t t-if="!state.loading and state.schemes.length === 0">
                                <tr>
                                    <td colspan="6" class="text-center py-5">
                                        <div class="d-flex flex-column align-items-center">
                                            <div class="bg-light rounded-circle p-4 mb-3">
                                                 <i class="fas fa-tasks fa-3x text-secondary opacity-50"></i>
                                            </div>
                                            <h5 class="text-dark fw-bold">Chưa có dữ liệu</h5>
                                            <p class="text-muted mb-3">Chưa có chương trình nào được tạo.</p>
                                            <button class="btn btn-fmc-primary" t-on-click="createNew">
                                                <i class="fas fa-plus me-2"></i>Tạo mới ngay
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                            <t t-foreach="state.schemes" t-as="s" t-key="s.id">
                                <tr>
                                    <td>
                                        <div class="fw-bold text-dark" t-esc="s.name"/>
                                    </td>
                                    <td>
                                        <span class="badge bg-light text-dark border fw-bold" t-esc="s.transaction_code"/>
                                    </td>
                                    <td>
                                        <span class="fw-bold text-success" t-esc="formatCurrency(s.min_purchase_value)"/>
                                        <small class="text-muted"> VND</small>
                                    </td>
                                    <td>
                                        <span t-if="s.can_purchase" class="badge-fmc badge-primary me-1">Mua</span>
                                        <span t-if="s.can_sell" class="badge-fmc badge-success me-1">Bán</span>
                                        <span t-if="s.can_convert" class="badge-fmc badge-info me-1">Chuyển đổi</span>
                                    </td>
                                    <td class="text-center">
                                        <span t-if="s.active_status === 'Kích hoạt'" class="badge-fmc badge-success">
                                            Active
                                        </span>
                                        <span t-else="" class="badge-fmc badge-danger">
                                            Inactive
                                        </span>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group">
                                            <button t-on-click="() => this.handleEdit(s.id)" class="btn btn-sm btn-light border text-secondary">
                                                <i class="fas fa-pen"></i>
                                            </button>
                                            <button t-on-click="() => this.confirmDelete(s.id, s.name)" class="btn btn-sm btn-light border text-danger">
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
                        <div class="text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">Đang tải...</p></div>
                    </t>
                    <t t-if="!state.loading and state.schemes.length === 0">
                         <div class="text-center py-5">
                            <h5 class="text-muted">Chưa có dữ liệu</h5>
                        </div>
                    </t>
                    <t t-foreach="state.schemes" t-as="s" t-key="s.id">
                        <div class="card-fmc mb-3">
                             <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                     <div>
                                        <h6 class="fw-bold mb-0 text-dark" t-esc="s.name"/>
                                        <small class="text-muted" t-esc="s.transaction_code"/>
                                    </div>
                                    <span t-if="s.active_status === 'Kích hoạt'" class="badge-fmc badge-success">Active</span>
                                    <span t-else="" class="badge-fmc badge-danger">Inactive</span>
                                </div>
                                <div class="mb-2">
                                     <span class="text-muted small">Tối thiểu: </span>
                                     <span class="fw-bold text-success" t-esc="formatCurrency(s.min_purchase_value)"/> <small>VND</small>
                                </div>
                                <div class="mb-3">
                                    <span t-if="s.can_purchase" class="badge bg-primary-subtle text-primary me-1">Mua</span>
                                    <span t-if="s.can_sell" class="badge bg-success-subtle text-success me-1">Bán</span>
                                    <span t-if="s.can_convert" class="badge bg-info-subtle text-info me-1">Chuyển đổi</span>
                                </div>
                                <div class="d-flex justify-content-end gap-2">
                                    <button t-on-click="() => this.handleEdit(s.id)" class="btn btn-sm btn-light border">
                                        <i class="fas fa-edit"></i> Sửa
                                    </button>
                                    <button t-on-click="() => this.confirmDelete(s.id, s.name)" class="btn btn-sm btn-light border text-danger">
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
                                <option value="10">10</option>
                                <option value="25">25</option>
                                <option value="50">50</option>
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
    <div class="modal fade" id="deleteSchemeModal" tabindex="-1" aria-labelledby="deleteSchemeModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0 pb-0">
                    <h5 class="modal-title text-danger" id="deleteSchemeModalLabel">
                        <i class="fas fa-exclamation-triangle me-2"></i>Xác nhận xóa
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body pt-2">
                    <p>Bạn có chắc chắn muốn xóa vĩnh viễn chương trình này?</p>
                    <div class="bg-light p-3 rounded">
                        <strong t-esc="state.deleteTarget.name"></strong>
                    </div>
                </div>
                <div class="modal-footer border-0 pt-0">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Hủy</button>
                    <button type="button" class="btn btn-danger" t-on-click="handleDelete">Xác nhận xóa</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="position-fixed top-0 end-0 p-3" style="z-index: 1100">
        <div id="schemeToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas fa-check-circle text-success me-2"></i>
                <strong class="me-auto">Thông báo</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body" t-esc="state.toastMessage"></div>
        </div>
    </div>
</div>
`;

    setup() {
        this.state = useState({ 
            schemes: [], 
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
            // Initialize the modal but don't show it
            this.deleteModal = new bootstrap.Modal(document.getElementById('deleteSchemeModal'));
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
        const { currentPage, limit, searchTerm } = this.state;
        const url = `/get_scheme_data?page=${currentPage}&limit=${limit}&search=${encodeURIComponent(searchTerm.trim())}`;
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error("Tải dữ liệu thất bại");
            const data = await res.json();
            this.state.schemes = data.records || [];
            this.state.totalRecords = data.total_records || 0;
        } catch (e) { 
            console.error(e); 
            this.state.schemes = [];
            this.state.totalRecords = 0;
        } finally { 
            this.state.loading = false; 
        }
    }

    changePage(page) {
        if (page > 0 && page <= this.totalPages && page !== this.state.currentPage) {
            this.state.currentPage = page;
            this.loadData();
        }
    }

    onSearchInput() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.performSearch();
        }, 300);
    }

    performSearch() { 
        this.state.currentPage = 1; 
        this.loadData(); 
    }

    handleEdit(id) { 
        window.location.href = `/scheme/edit/${id}`; 
    }

    confirmDelete(id, name) {
        this.state.deleteTarget.id = id;
        this.state.deleteTarget.name = name;
        this.deleteModal.show();
    }

    async handleDelete() {
        if (!this.state.deleteTarget.id) return;

        this.deleteModal.hide();

        try {
            const response = await fetch('/scheme/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ id: this.state.deleteTarget.id })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.state.toastMessage = result.message || 'Xóa thành công!';
                this.showToast();
                // Reset page to 1 if it's the last item on a page > 1
                if (this.state.schemes.length === 1 && this.state.currentPage > 1) {
                    this.state.currentPage -= 1;
                }
                await this.loadData();
            } else {
                alert(`Lỗi khi xóa: ${result.error || 'Lỗi không xác định từ máy chủ.'}`);
            }

        } catch (error) {
            console.error('Error during delete operation:', error);
            alert(`Có lỗi xảy ra: ${error.message}`);
        } finally {
            this.state.deleteTarget.id = null;
            this.state.deleteTarget.name = '';
        }
    }

    showToast() {
        const toastEl = document.getElementById('schemeToast');
        if (toastEl) {
            const toast = bootstrap.Toast.getOrCreateInstance(toastEl);
            toast.show();
        }
    }

    createNew() { 
        window.location.href = '/scheme/new';   
    }

    formatCurrency(val) { 
        if (typeof val !== 'number') return val;
        return new Intl.NumberFormat('vi-VN').format(val); 
    }
}

if (!window.SchemeWidget) {
    window.SchemeWidget = SchemeWidget;
    console.log("SchemeWidget component loaded successfully.");
} else {
    console.log("SchemeWidget already exists, skipping registration.");
}
