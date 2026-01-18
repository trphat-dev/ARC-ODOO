/** @odoo-module **/
// ward_widget.js cho ward
console.log("Loading WardWidget...");

const { Component, xml, useState, onMounted } = window.owl;

class WardWidget extends Component {
    static template = xml`
    <div class="fund-management-widget slide-in-bottom">
        <!-- Header Section -->
        <div class="page-header d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div>
                <h1 class="h3 mb-1">Danh mục Phường (Xã)</h1>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="#"><i class="fas fa-home me-1"></i>Trang chủ</a></li>
                        <li class="breadcrumb-item active" aria-current="page">Danh mục Phường (Xã)</li>
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
                <div class="row g-3 align-items-center">
                    <div class="col-lg-5 col-md-12">
                        <div class="position-relative">
                            <i class="fas fa-search position-absolute top-50 start-0 translate-middle-y ms-3 text-muted"></i>
                            <input type="text" 
                                placeholder="Tìm theo tên hoặc mã phường..."
                                class="form-control fmc-search-input ps-5"
                                t-on-keyup="onSearchKeyup"
                                t-model="state.searchTerm"
                            />
                        </div>
                    </div>
                     <div class="col-lg-7 col-md-12 text-end">
                        <div class="d-flex align-items-center justify-content-end gap-2">
                             <span class="text-muted small">
                                Tổng <strong class="text-primary" t-esc="state.totalRecords"/> kết quả
                            </span>
                            <button t-on-click="performSearch" class="btn btn-light border fw-semibold">
                                <i class="fas fa-sync-alt me-1"></i> Tìm kiếm
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
                                <th>Tên phường/xã</th>
                                <th>Mã phường/xã</th>
                                <th>Thành phố</th>
                                <th class="text-center">Trạng thái</th>
                                <th class="text-center" style="width: 120px;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-if="state.loading">
                                <tr><td colspan="5" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Đang tải dữ liệu...</p></td></tr>
                            </t>
                            <t t-if="!state.loading and state.wards.length === 0">
                                <tr>
                                    <td colspan="5" class="text-center py-5">
                                        <div class="d-flex flex-column align-items-center">
                                             <div class="bg-light rounded-circle p-4 mb-3">
                                                 <i class="fas fa-map-marker-alt fa-3x text-secondary opacity-50"></i>
                                            </div>
                                            <h5 class="text-dark fw-bold">Chưa có dữ liệu</h5>
                                            <p class="text-muted mb-3">Không tìm thấy phường/xã nào.</p>
                                            <button class="btn btn-fmc-primary" t-on-click="createNew">
                                                <i class="fas fa-plus me-2"></i>Tạo mới ngay
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                            <t t-foreach="state.wards" t-as="ward" t-key="ward.id">
                                <tr>
                                    <td>
                                        <div class="fw-bold text-dark" t-esc="ward.name"/>
                                    </td>
                                    <td>
                                        <span class="badge bg-light text-dark border fw-bold" t-esc="ward.code"/>
                                    </td>
                                    <td>
                                        <span class="text-muted" t-esc="ward.city_name"/>
                                    </td>
                                    <td class="text-center">
                                        <span t-if="ward.active" class="badge-fmc badge-success">Kích hoạt</span>
                                        <span t-else="" class="badge-fmc badge-danger">Không kích hoạt</span>
                                    </td>
                                    <td class="text-center">
                                        <div class="d-flex justify-content-center gap-2">
                                            <button t-on-click.prevent="() => this.handleEdit(ward.id)" class="btn btn-sm btn-light border" title="Chỉnh sửa">
                                                <i class="fas fa-edit text-primary"></i>
                                            </button>
                                            <button t-on-click.prevent="() => this.handleDelete(ward.id)" class="btn btn-sm btn-light border" title="Xóa">
                                                <i class="fas fa-trash text-danger"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                </div>
            </div>
            <!-- Pagination Controls -->
            <div t-if="totalPages > 1" class="card-footer d-flex justify-content-end bg-white border-top-0 py-3">
                <nav aria-label="Page navigation">
                    <ul class="pagination mb-0">
                         <li t-attf-class="page-item #{state.currentPage === 1 ? 'disabled' : ''}">
                            <a class="page-link shadow-none" href="#" t-on-click.prevent="() => this.changePage(state.currentPage - 1)">
                                <i class="fas fa-chevron-left"></i>
                            </a>
                        </li>
                        <t t-foreach="Array.from({ length: totalPages }, (_, i) => i + 1)" t-as="page" t-key="page">
                             <li t-attf-class="page-item #{page === state.currentPage ? 'active' : ''}">
                                <a class="page-link shadow-none" href="#" t-on-click.prevent="() => this.changePage(page)" t-esc="page"/>
                            </li>
                        </t>
                         <li t-attf-class="page-item #{state.currentPage === totalPages ? 'disabled' : ''}">
                            <a class="page-link shadow-none" href="#" t-on-click.prevent="() => this.changePage(state.currentPage + 1)">
                                <i class="fas fa-chevron-right"></i>
                            </a>
                        </li>
                    </ul>
                </nav>
            </div>
        </div>
    </div>
    `;
    setup() {
        this.state = useState({ wards: [], searchTerm: "", loading: true, currentPage: 1, totalRecords: 0, limit: 10 });
        onMounted(() => this.loadData());
    }
    get totalPages() { return Math.ceil(this.state.totalRecords / this.state.limit); }
    async loadData() {
        this.state.loading = true;
        const url = `/get_ward_data?page=${this.state.currentPage}&limit=${this.state.limit}&search=${encodeURIComponent(this.state.searchTerm.trim())}`;
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error("Tải dữ liệu thất bại");
            const data = await res.json();
            this.state.wards = data.records;
            this.state.totalRecords = data.total_records;
        } catch (e) { console.error(e); } finally { this.state.loading = false; }
    }
    changePage(page) { if (page > 0 && page <= this.totalPages) { this.state.currentPage = page; this.loadData(); } }
    onSearchKeyup(ev) { if (ev.key === 'Enter') this.performSearch(); }
    performSearch() { this.state.currentPage = 1; this.loadData(); }
    handleEdit(id) { window.location.href = `/ward/edit/${id}`; }
    createNew() { window.location.href = '/ward/new'; }
}
window.WardWidget = WardWidget;
export default WardWidget; 
