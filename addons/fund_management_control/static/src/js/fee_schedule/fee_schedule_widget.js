console.log("Loading FeeScheduleWidget component...");

const { Component, xml, useState, onMounted } = window.owl;

class FeeScheduleWidget extends Component {
    static template = xml`
    <div class="fee-schedule-container slide-in-bottom">
        <!-- Header Section -->
        <div class="page-header d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div>
                <h1 class="h3 mb-1">Biểu phí</h1>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="#"><i class="fas fa-home me-1"></i>Trang chủ</a></li>
                        <li class="breadcrumb-item active" aria-current="page">Danh sách biểu phí</li>
                    </ol>
                </nav>
            </div>
            <button t-on-click="createNew" class="btn btn-fmc-primary d-flex align-items-center gap-2">
                <i class="fas fa-plus"></i>
                <span>Tạo mới</span>
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
                                placeholder="Nhập từ khóa để tìm kiếm..." 
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

        <!-- Fee Schedule Table Section -->
        <div class="card-fmc">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-fmc table-hover align-middle">
                        <thead>
                            <tr>
                                <th>Tên biểu phí</th>
                                <th>Mã VSD</th>
                                <th>Chương trình</th>
                                <th>Loại phí</th>
                                <th>Tỉ lệ (%)</th>
                                <th class="text-center">Trạng thái</th>
                                <th class="text-center" style="width: 120px;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-if="state.loading">
                                <tr>
                                    <td colspan="7" class="text-center py-5">
                                        <div class="d-flex flex-column justify-content-center align-items-center">
                                            <div class="spinner-border text-primary mb-3" role="status">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <p class="text-muted mb-0">Đang tải dữ liệu...</p>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                            <t t-if="!state.loading and state.fees.length === 0">
                                <tr>
                                    <td colspan="7" class="text-center py-5">
                                        <div class="d-flex flex-column align-items-center">
                                            <div class="bg-light rounded-circle p-4 mb-3">
                                                 <i class="fas fa-percentage fa-3x text-secondary opacity-50"></i>
                                            </div>
                                            <h5 class="text-dark fw-bold">Chưa có dữ liệu</h5>
                                            <p class="text-muted mb-3">Chưa có biểu phí nào được tạo.</p>
                                            <button class="btn btn-fmc-primary" t-on-click="createNew">
                                                <i class="fas fa-plus me-2"></i>Tạo mới ngay
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                            <t t-foreach="state.fees" t-as="fee" t-key="fee.id">
                                <tr>
                                    <td>
                                        <div class="fw-bold text-dark" t-esc="fee.fee_name"/>
                                    </td>
                                    <td>
                                        <span class="badge bg-light text-dark border fw-bold" t-esc="fee.fee_code"/>
                                    </td>
                                    <td>
                                        <span class="text-muted" t-esc="fee.scheme_name"/>
                                    </td>
                                    <td>
                                        <span class="badge-fmc badge-info" t-esc="fee.fee_type"/>
                                    </td>
                                    <td>
                                        <span class="fw-bold text-primary" t-esc="fee.fee_rate"/>%
                                    </td>
                                    <td class="text-center">
                                        <span t-if="fee.activate" class="badge-fmc badge-success">Active</span>
                                        <span t-else="" class="badge-fmc badge-danger">Inactive</span>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group">
                                             <a t-on-click.prevent="() => this.handleEdit(fee.id)" href="#" class="btn btn-sm btn-light border text-secondary">
                                                <i class="fas fa-pen"></i>
                                            </a>
                                            <a t-on-click.prevent="() => this.handleDelete(fee.id, fee.fee_name)" href="#" class="btn btn-sm btn-light border text-danger">
                                                <i class="fas fa-trash-alt"></i>
                                            </a>
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
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="text-muted mb-0">Đang tải dữ liệu...</p>
                        </div>
                    </t>
                    <t t-if="!state.loading and state.fees.length === 0">
                        <div class="text-center py-5 px-3">
                             <div class="mb-4">
                                <i class="fas fa-percentage fa-4x text-muted opacity-50"></i>
                            </div>
                            <h5 class="text-muted mb-3">Chưa có biểu phí nào</h5>
                        </div>
                    </t>
                    <t t-foreach="state.fees" t-as="fee" t-key="fee.id">
                        <div class="card-fmc mb-3">
                            <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                     <div>
                                        <h6 class="fw-bold mb-0 text-dark" t-esc="fee.fee_name"/>
                                        <small class="text-muted" t-esc="fee.fee_code"/>
                                    </div>
                                    <span t-if="fee.activate" class="badge-fmc badge-success">Active</span>
                                    <span t-else="" class="badge-fmc badge-danger">Inactive</span>
                                </div>
                                <div class="row g-2 small mb-3">
                                    <div class="col-6">
                                        <div class="text-muted">Tỉ lệ:</div>
                                        <div class="fw-bold text-primary" t-esc="fee.fee_rate"/>%
                                    </div>
                                    <div class="col-6">
                                        <div class="text-muted">Loại phí:</div>
                                        <span class="badge bg-info-subtle text-info" t-esc="fee.fee_type"/>
                                    </div>
                                    <div class="col-12">
                                         <div class="text-muted">Chương trình:</div>
                                         <span t-esc="fee.scheme_name"/>
                                    </div>
                                </div>
                                <div class="d-flex justify-content-end gap-2">
                                     <a t-on-click.prevent="() => this.handleEdit(fee.id)" href="#" class="btn btn-sm btn-light border">
                                        <i class="fas fa-edit me-1"></i>Sửa
                                    </a>
                                    <a t-on-click.prevent="() => this.handleDelete(fee.id, fee.fee_name)" href="#" class="btn btn-sm btn-light border text-danger">
                                        <i class="fas fa-trash-alt me-1"></i>Xóa
                                    </a>
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
    </div>
    `;

    setup() {
        this.state = useState({
            fees: [],
            searchTerm: "",
            loading: true,
            currentPage: 1,
            totalRecords: 0,
            limit: 10,
        });

        onMounted(() => {
            console.log("FeeScheduleWidget mounted, loading data...");
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
            for (let i = 1; i <= total; i++) {
                range.push(i);
            }
        } else {
            if (current <= 4) {
                for (let i = 1; i <= 5; i++) {
                    range.push(i);
                }
                range.push('...');
                range.push(total);
            } else if (current >= total - 3) {
                range.push(1);
                range.push('...');
                for (let i = total - 4; i <= total; i++) {
                    range.push(i);
                }
            } else {
                range.push(1);
                range.push('...');
                for (let i = current - 1; i <= current + 1; i++) {
                    range.push(i);
                }
                range.push('...');
                range.push(total);
            }
        }
        
        return range;
    }

    async loadData() {
        console.log("Loading fee schedule data...");
        this.state.loading = true;
        const searchTerm = encodeURIComponent(this.state.searchTerm.trim());
        try {
            const url = `/get_fee_schedule_data?page=${this.state.currentPage}&limit=${this.state.limit}&search=${searchTerm}`;
            console.log("Fetching from URL:", url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            this.state.fees = result.records || [];
            this.state.totalRecords = result.total_records || 0;
            
        } catch (error) {
            console.error("Error fetching fee schedules:", error);
            this.state.fees = [];
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
        this.state.searchTerm = ev.target.value;
    }
    
    onSearchKeyup(ev) {
        if (ev.key === 'Enter') {
            this.performSearch();
        }
    }

    performSearch() {
        this.state.currentPage = 1;
        this.loadData();
    }
    
    handleEdit(feeId) { 
        window.location.href = `/fee_schedule/edit/${feeId}`;
    }

    async handleDelete(feeId, feeName) {
        if (confirm(`Bạn có chắc chắn muốn xóa biểu phí "${feeName}" không?`)) {
            try {
                const response = await fetch('/fee_schedule/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: feeId }),
                });

                const result = await response.json();
                if (result.success) {
                    alert(result.message || 'Đã xóa thành công!');
                    this.loadData();
                } else {
                    alert(`Lỗi: ${result.error}`);
                }
            } catch (error) {
                console.error('Error deleting fee schedule:', error);
                alert('Đã xảy ra lỗi khi cố gắng xóa biểu phí.');
            }
        }
    }
    
    createNew() { 
        window.location.href = '/fee_schedule/new';
    }
    
    formatCurrency(value) {
        if (typeof value !== 'number') return value;
        return new Intl.NumberFormat('vi-VN', { style: 'decimal' }).format(value);
    }
}

if (!window.FeeScheduleWidget) {
    window.FeeScheduleWidget = FeeScheduleWidget;
    console.log("FeeScheduleWidget component loaded successfully.");
} else {
    console.log("FeeScheduleWidget already exists, skipping registration.");
}
