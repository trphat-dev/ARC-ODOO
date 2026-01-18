/** @odoo-module **/
import { Component, xml } from "@odoo/owl";

export class Footer extends Component {
    static template = xml`
    <div>
        <!-- Spacer to create distance from body content -->
        <div class="footer-spacer"></div>
        
        <footer class="hd-footer">
            <div class="footer-main">
                <div class="container-fluid">
                    <div class="row">
                        <!-- Company Info -->
                        <div class="col-lg-3 col-md-6 mb-4 mb-lg-0">
                            <div class="footer-brand">
                                <img src="/overview_fund_management/static/src/img/hdcapital_logo.png" alt="HDCapital" class="footer-logo"/>
                            </div>
                            <div class="footer-company-info">
                                <h6 class="fw-bold">Công ty Cổ phần Quản lý Quỹ HD</h6>
                                <p class="mb-2">Lầu 7, số 58 Nguyễn Đình Chiểu, phường Tân Định,<br/>thành phố Hồ Chí Minh</p>
                                <div class="footer-contact">
                                    <p class="fw-bold text-primary mb-1">Chăm sóc khách hàng</p>
                                    <p class="mb-1"><strong>Tel:</strong> 028 3915 1818</p>
                                    <p class="mb-0"><strong>Email:</strong> <a href="mailto:info@hdcap.vn">info@hdcap.vn</a></p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Products & Services -->
                        <div class="col-lg-3 col-md-6 mb-4 mb-lg-0">
                            <h5 class="footer-heading">Sản phẩm &amp; Dịch vụ</h5>
                            <ul class="footer-links">
                                <li><a href="https://hdcap.vn/#">Tư vấn đầu tư</a></li>
                                <li><a href="https://hdcap.vn/#">Uỷ thác đầu tư</a></li>
                                <li><a href="https://hdcap.vn/#">Quỹ HDBOND</a></li>
                                <li><a href="https://hdcap.vn/#">Quỹ GDEGF</a></li>
                            </ul>
                        </div>
                        
                        <!-- Links -->
                        <div class="col-lg-3 col-md-6 mb-4 mb-lg-0">
                            <h5 class="footer-heading">Liên kết</h5>
                            <ul class="footer-links">
                                <li><a href="https://hdcap.vn/#">Về chúng tôi</a></li>
                                <li><a href="https://hdcap.vn/#">Quan hệ nhà đầu tư</a></li>
                                <li><a href="https://hdcap.vn/#">Cơ hội nghề nghiệp</a></li>
                                <li><a href="https://hdcap.vn/#">Tin tức</a></li>
                            </ul>
                        </div>
                        
                        <!-- Support -->
                        <div class="col-lg-3 col-md-6 mb-4 mb-lg-0">
                            <h5 class="footer-heading">Hỗ trợ</h5>
                            <ul class="footer-links">
                                <li><a href="https://hdcap.vn/#">Kiến thức đầu tư</a></li>
                                <li><a href="https://hdcap.vn/#">Liên hệ</a></li>
                            </ul>
                            <div class="footer-social">
                                <a href="https://www.facebook.com/hdcapitaljsc" target="_blank" class="social-icon facebook">
                                    <i class="fab fa-facebook-f"></i>
                                </a>
                                <a href="https://www.youtube.com/@hdcapitaljsc" target="_blank" class="social-icon youtube">
                                    <i class="fab fa-youtube"></i>
                                </a>
                                <a href="https://hdcap.vn/#" target="_blank" class="social-icon zalo">
                                    <span>Zalo</span>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer Bottom -->
            <div class="footer-bottom">
                <div class="container-fluid">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <p class="mb-0">© 2025 HDCapital.</p>
                        </div>
                        <div class="col-md-4 text-center">
                            <a href="https://hdcap.vn/wp-content/uploads/2025/12/CS06-HDCAP-CHINH-SACH-CHIA-SE-THONG-TIN.pdf" target="_blank" class="footer-policy-link">Chính sách chia sẻ thông tin</a>
                        </div>
                        <div class="col-md-4 text-end">
                            <a href="https://hdcap.vn/wp-content/uploads/2025/12/CS07-HDCAP-CHINH-SACH-BAO-VE-DU-LIEU-CA-NHAN.pdf" target="_blank" class="footer-policy-link">Chính sách bảo vệ dữ liệu cá nhân</a>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    </div>
    `;
}

// Export for other modules to import
Footer.props = {};
