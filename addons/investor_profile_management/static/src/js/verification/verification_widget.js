// Verification Completion Widget Component
console.log('Loading VerificationWidget component...');

const { Component, xml, useState, onMounted } = owl;

class VerificationWidget extends Component {
    static template = xml`
        <div class="investor-page">
            <div class="investor-layout">
                <!-- Sidebar -->
                <aside class="investor-sidebar">
                    <div class="sidebar-header">
                        <div class="logo-container">
                            <i class="fa fa-user-circle"></i>
                        </div>
                        <h3><t t-esc="state.profile.name || 'Investor'" /></h3>
                        <div class="mt-2">
                             <span t-if="state.statusInfo.account_status == 'approved'" class="status-badge status-complete">Đã duyệt</span>
                             <span t-elif="state.statusInfo.account_status == 'pending'" class="status-badge status-incomplete">Chờ duyệt</span>
                             <span t-elif="state.statusInfo.account_status == 'rejected'" class="status-badge status-incomplete">Từ chối</span>
                             <span t-else="" class="status-badge status-incomplete">Chưa có</span>
                        </div>
                        
                        <div class="mt-4 px-2">
                            <div class="d-flex justify-content-between mb-2 small">
                                <span class="text-muted">Số TK:</span>
                                <span class="fw-bold text-dark"><t t-esc="state.statusInfo.account_number || '---'" /></span>
                            </div>
                            <div class="d-flex justify-content-between mb-2 small">
                                <span class="text-muted">Mã GT:</span>
                                <span class="fw-bold text-dark"><t t-esc="state.statusInfo.referral_code || '---'" /></span>
                            </div>
                            <div class="d-flex justify-content-between mb-2 small">
                                <span class="text-muted">Hồ sơ:</span>
                                
                                <span t-if="state.statusInfo.profile_status == 'complete'" class="text-success fw-bold">Đã hoàn tất</span>
                                <span t-else="" class="text-warning fw-bold">Chưa hoàn tất</span>
                            </div>
                        </div>

                        <t t-if="state.statusInfo.rm_name">
                            <div class="mt-3 pt-3 border-top small text-center text-muted">
                                <i class="fa fa-id-card-o me-1"></i> RM: <t t-esc="state.statusInfo.rm_name"/>
                            </div>
                        </t>
                    </div>
                    
                    <nav class="sidebar-nav mt-3">
                        <a href="/personal_profile" class="nav-item">
                            <i class="fa fa-user"></i> Thông tin cá nhân
                        </a>
                        <a href="/bank_info" class="nav-item">
                            <i class="fa fa-university"></i> TK Ngân hàng
                        </a>
                        <a href="/address_info" class="nav-item">
                            <i class="fa fa-map-marker"></i> Thông tin địa chỉ
                        </a>
                        <a href="/verification" class="nav-item active">
                            <i class="fa fa-shield"></i> Xác thực &amp; eKYC
                        </a>
                    </nav>
                </aside>
                
                <!-- Main Content -->
                <div class="investor-content">
                    <div class="investor-card">
                        <div class="card-header-styled">
                            <h2>Xác thực hoàn tất</h2>
                            <p>Xác nhận thông tin và hoàn tất hồ sơ đăng ký</p>
                        </div>
                        
                        <form class="investor-form" t-on-submit.prevent="completeVerification">
                             <div class="row">
                                <div class="col-12 mb-4">
                                     <h5 class="text-primary fw-bold mb-3 border-bottom pb-2">Xác nhận thông tin</h5>
                                     
                                     <div class="p-3 bg-light rounded mb-4 border">
                                         <p class="mb-3">
                                          Để bắt đầu thực hiện giao dịch, Quý khách cần phải xác nhận thông tin và đồng ý các điều khoản, điều kiện dưới đây:
                                         </p>
                                         <p class="mb-3">
                                          Sau khi hoàn tất bước xác nhận này thông tin <span class="fw-bold text-primary">Hợp đồng mở tài khoản</span> của Quý khách sẽ được gửi tới email <span class="fw-bold text-highlight"><t t-esc="state.contractEmail" /></span>.
                                         </p>
                                         <p class="mb-0">
                                          Quý khách vui lòng in, ký xác nhận và gửi thư về địa chỉ của công ty trong phần liên hệ!
                                         </p>
                                     </div>
                                     
                                     <div class="terms-box p-3 border rounded mb-3 bg-white" style="max-height: 200px; overflow-y: auto;">
                                          <p class="mb-2 small"><i class="fa fa-check text-success me-2"></i> Tôi cam kết các thông tin đã cung cấp là chính xác và trung thực.</p>
                                          <p class="mb-2 small"><i class="fa fa-check text-success me-2"></i> Tôi đồng ý tuân thủ các quy định giao dịch của công ty quản lý quỹ.</p>
                                          <p class="mb-2 small"><i class="fa fa-check text-success me-2"></i> Tôi đã đọc, hiểu và đồng ý với các điều khoản trong hợp đồng mở tài khoản.</p>
                                          <p class="mb-2 small"><i class="fa fa-check text-success me-2"></i> Tôi cam kết sẽ thông báo cho công ty khi có thay đổi về thông tin cá nhân.</p>
                                     </div>
                                     
                                     <div class="form-check p-3 border border-warning bg-warning bg-opacity-10 rounded">
                                          <input type="checkbox" id="agree_terms" t-model="state.agreedToTerms" required="required" class="form-check-input mt-1" />
                                          <label for="agree_terms" class="form-check-label fw-bold">
                                              Tôi đồng ý với các điều khoản và điều kiện trên <span class="text-danger">*</span>
                                          </label>
                                     </div>
                                </div>
                             </div>
                             
                             <div class="d-flex justify-content-end pt-3 border-top gap-2">
                                 <button type="button" class="btn btn-outline-secondary px-4 rounded-pill" t-on-click="onBack">
                                     <i class="fa fa-arrow-left me-2"></i> Quay lại
                                 </button>
                                 <button type="submit" class="btn btn-primary-investor px-5">
                                      <i class="fa fa-check-circle me-2"></i> Hoàn tất
                                 </button>
                             </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <div t-if="state.showModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);">
              <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg rounded-4">
                  <div class="modal-header border-0 bg-light rounded-top-4">
                    <h5 class="modal-title fw-bold text-primary"><t t-esc="state.modalTitle" /></h5>
                    <button type="button" class="btn-close" t-on-click="closeModal"></button>
                  </div>
                  <div class="modal-body text-center p-4">
                    <t t-if="state.modalTitle === 'Thành công' || state.modalTitle === 'Xác nhận thành công'">
                      <div class="mb-3 text-success" style="font-size: 3rem;">
                        <i class="fa fa-check-circle"></i>
                      </div>
                    </t>
                    <p class="fs-5 text-secondary"><t t-esc="state.modalMessage" /></p>
                  </div>
                  <div class="modal-footer border-0 justify-content-center pb-4">
                    <button type="button" class="btn btn-primary-investor px-4 rounded-pill" t-on-click="closeModal">Đóng</button>
                  </div>
                </div>
              </div>
            </div>
        </div>
    `;


    setup() {
        console.log("🎯 VerificationWidget - setup called!");

        this.state = useState({
            loading: true,
            profile: {},
            statusInfo: {},
            agreedToTerms: false,
            contractEmail: 'nhaltp7397@gmail.com', // Hardcoded for now, will fetch dynamically later
            companyAddress: '123 Fincorp St, Financial City, Country', // Hardcoded for now
            showModal: false,
            modalTitle: '',
            modalMessage: '',
        });

        onMounted(async () => {
            // Hide loading spinner
            const loadingSpinner = document.getElementById('loadingSpinner');
            const widgetContainer = document.getElementById('verificationWidget');
            
            if (loadingSpinner && widgetContainer) {
                loadingSpinner.style.display = 'none';
                widgetContainer.style.display = 'block';
            }
            // Reset storage nếu user đổi
            const currentUserId = window.currentUserId || (window.odoo && window.odoo.session_info && window.odoo.session_info.uid);
            const storedUserId = sessionStorage.getItem('personalProfileUserId');
            if (storedUserId && String(storedUserId) !== String(currentUserId)) {
                sessionStorage.removeItem('personalProfileData');
                sessionStorage.removeItem('personalProfileUserId');
                sessionStorage.removeItem('bankInfoData');
                sessionStorage.removeItem('bankInfoUserId');
                sessionStorage.removeItem('addressInfoData');
                sessionStorage.removeItem('addressInfoUserId');
            }
            // Load profile data and status info
            await this.loadProfileData();
            this.loadInitialFormData(); // Load form data from sessionStorage
            await this.loadStatusInfo();
            await this.checkAllInfoCompleted();
            
            this.state.loading = false;
        });
    }

    loadInitialFormData() {
        // Load data from sessionStorage if available
        const storedPersonalData = sessionStorage.getItem('personalProfileData');
        const storedBankData = sessionStorage.getItem('bankInfoData');
        const storedAddressData = sessionStorage.getItem('addressInfoData');

        if (storedPersonalData) {
            console.log("✅ Loaded personalProfileData from sessionStorage:", JSON.parse(storedPersonalData));
        } else {
            console.log("ℹ️ No personal profile data in sessionStorage");
        }
        if (storedBankData) {
            console.log("✅ Loaded bankInfoData from sessionStorage:", JSON.parse(storedBankData));
        } else {
            console.log("ℹ️ No bank info data in sessionStorage");
        }
        if (storedAddressData) {
            console.log("✅ Loaded addressInfoData from sessionStorage:", JSON.parse(storedAddressData));
        } else {
            console.log("ℹ️ No address info data in sessionStorage");
        }
    }

    async loadStatusInfo() {
        try {
            const response = await fetch('/get_status_info');
            const data = await response.json();
            if (data && data.length > 0) {
                this.state.statusInfo = data[0];
            } else {
                this.state.statusInfo = {};
            }
            // Luôn lấy tên user từ profile
            const profileRes = await fetch('/data_personal_profile');
            const profileData = await profileRes.json();
            if (profileData && profileData.length > 0 && profileData[0].name) {
                this.state.profile.name = profileData[0].name;
            } else {
                this.state.profile.name = (window.odoo && window.odoo.session_info && window.odoo.session_info.name) || 'Chưa có thông tin';
            }
        } catch (error) {
            this.state.statusInfo = {};
            this.state.profile.name = (window.odoo && window.odoo.session_info && window.odoo.session_info.name) || 'Chưa có thông tin';
        }
    }

    async checkAllInfoCompleted() {
        // Gọi API kiểm tra đủ thông tin 3 phần
        try {
            const [personal, bank, address] = await Promise.all([
                fetch('/data_personal_profile').then(r => r.json()),
                fetch('/data_bank_info').then(r => r.json()),
                fetch('/data_address_info').then(r => r.json()),
            ]);
            if (!personal.length) {
                this.state.modalTitle = 'Thiếu thông tin';
                this.state.modalMessage = 'Bạn cần nhập đầy đủ thông tin cá nhân trước khi xác thực.';
                this.state.showModal = true;
                setTimeout(() => { window.location.href = '/personal_profile'; }, 1800);
                return;
            }
            if (!bank.length) {
                this.state.modalTitle = 'Thiếu thông tin';
                this.state.modalMessage = 'Bạn cần nhập đầy đủ thông tin ngân hàng trước khi xác thực.';
                this.state.showModal = true;
                setTimeout(() => { window.location.href = '/bank_info'; }, 1800);
                return;
            }
            if (!address.length) {
                this.state.modalTitle = 'Thiếu thông tin';
                this.state.modalMessage = 'Bạn cần nhập đầy đủ thông tin địa chỉ trước khi xác thực.';
                this.state.showModal = true;
                setTimeout(() => { window.location.href = '/address_info'; }, 1800);
                return;
            }
        } catch (error) {
            this.state.modalTitle = 'Lỗi';
            this.state.modalMessage = 'Không kiểm tra được thông tin hồ sơ. Vui lòng thử lại.';
            this.state.showModal = true;
        }
    }

    async completeVerification() {
        // Kiểm tra xác nhận điều khoản
        if (!this.state.agreedToTerms) {
            this.state.modalTitle = 'Thiếu xác nhận';
            this.state.modalMessage = 'Vui lòng đồng ý với các điều khoản và điều kiện để hoàn tất.';
            this.state.showModal = true;
            return;
        }

        try {
            // Kiểm tra thông tin từ các bước trước
            const personalData = JSON.parse(sessionStorage.getItem('personalProfileData') || '{}');
            const bankData = JSON.parse(sessionStorage.getItem('bankInfoData') || '{}');
            const addressData = JSON.parse(sessionStorage.getItem('addressInfoData') || '{}');

            // Kiểm tra thông tin cá nhân
            const requiredPersonalFields = ['name', 'birth_date', 'gender', 'nationality', 'id_type', 'id_number', 'id_issue_date', 'id_issue_place'];
            const missingPersonalFields = requiredPersonalFields.filter(field => !personalData[field]);
            
            // Kiểm tra thông tin ngân hàng
            const requiredBankFields = ['bank_name', 'account_number', 'account_holder', 'branch'];
            const missingBankFields = requiredBankFields.filter(field => !bankData[field]);
            
            // Kiểm tra thông tin địa chỉ (chỉ yêu cầu các trường bắt buộc)
            const requiredAddressFields = ['city', 'district', 'ward'];
            const missingAddressFields = requiredAddressFields.filter(field => !addressData[field]);

            // Tạo thông báo lỗi nếu có trường bắt buộc bị thiếu
            let errorMessage = '';
            
            if (missingPersonalFields.length > 0) {
                errorMessage += 'Thiếu thông tin cá nhân: ' + missingPersonalFields.join(', ') + '\n';
            }
            
            if (missingBankFields.length > 0) {
                errorMessage += 'Thiếu thông tin ngân hàng: ' + missingBankFields.join(', ') + '\n';
            }
            
            if (missingAddressFields.length > 0) {
                errorMessage += 'Thiếu thông tin địa chỉ: ' + missingAddressFields.join(', ');
            }

            // Nếu có lỗi thiếu thông tin, hiển thị thông báo
            if (errorMessage) {
                this.state.modalTitle = 'Thiếu thông tin';
                this.state.modalMessage = 'Vui lòng điền đầy đủ thông tin trước khi xác thực.\n\n' + errorMessage;
                this.state.showModal = true;
                return;
            }

            // Nếu đã đủ thông tin, hiển thị thông báo hoàn tất
            this.state.modalTitle = 'Xác nhận hoàn tất';
            this.state.modalMessage = 'Bạn đã hoàn tất việc xác thực thông tin. Vui lòng đợi hệ thống xử lý.';
            this.state.showModal = true;
            
            // Chuyển hướng về trang chủ sau 3 giây
            setTimeout(() => { 
                window.location.href = '/my/home'; 
            }, 3000);
            
        } catch (error) {
            console.error('Lỗi khi xác thực:', error);
            this.state.modalTitle = 'Lỗi';
            this.state.modalMessage = 'Có lỗi xảy ra khi xác thực: ' + error.message;
            this.state.showModal = true;
        }
    }

    onBack() {
        window.location.href = '/address_info';
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        return csrfToken ? csrfToken.getAttribute('content') : '';
    }

    async loadProfileData() {
        try {
            console.log("🔄 Loading verification profile data from server...");
            const response = await fetch('/data_verification');
            const data = await response.json();
            console.log("📥 Verification profile data received:", data);
            
            if (data && data.length > 0) {
                this.state.profile = data[0];
                console.log("✅ Verification profile data loaded successfully:", this.state.profile);
            } else {
                console.log("ℹ️ No existing verification profile data found on server");
                this.state.profile = {};
            }
        } catch (error) {
            console.error("❌ Error fetching verification profiles:", error);
            this.state.profile = {};
        }
    }

    closeModal = () => {
        this.state.showModal = false;
    };
}

// Make component globally available
window.VerificationWidget = VerificationWidget;
console.log('VerificationWidget component loaded and available globally');

// Auto-mount when script is loaded
if (typeof owl !== 'undefined') {
    const widgetContainer = document.getElementById('verificationWidget');
    if (widgetContainer) {
        console.log('Mounting VerificationWidget');
        owl.mount(VerificationWidget, widgetContainer);
    }
} 