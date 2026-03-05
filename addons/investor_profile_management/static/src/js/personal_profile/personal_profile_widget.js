// Personal Profile Widget Component


const { Component, xml, useState, onMounted } = owl;

class PersonalProfileWidget extends Component {
    // Configuration constants
    static CONFIG = {
        FACE_API: {
            VERSION: '0.22.2',
            VLADMANDIC_VERSION: '1.7.14',
            CDN_SOURCES: [
                'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js',
                'https://unpkg.com/face-api.js@0.22.2/dist/face-api.min.js',
                'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.js'
            ],
            MODEL_SOURCES: [
                'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.14/model',
                'https://unpkg.com/@vladmandic/face-api@1.7.14/model',
                'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights',
                'https://unpkg.com/face-api.js@0.22.2/weights'
            ],
            LOCAL_PATHS: [
                '/web/static/lib/face-api/face-api.min.js',
                '/static/lib/face-api/face-api.min.js',
                '/face-api.min.js'
            ],
            TIMEOUTS: {
                SCRIPT_LOAD: 8000,
                MODEL_LOAD: 12000,
                INITIALIZATION: 1000
            }
        },
        DETECTION: {
            INPUT_SIZE: 320,
            SCORE_THRESHOLD: 0.3,
            INTERVAL: 1000,
            PERFECT_FACE_THRESHOLD: 3
        },
        CAPTURE: {
            REQUIREMENTS: {
                front: 3,
                left: 2,
                right: 2
            },
            INSTRUCTIONS: {
                front: 'Nhìn thẳng vào camera và giữ nguyên tư thế',
                left: 'Quay mặt sang trái một góc 45 độ',
                right: 'Quay mặt sang phải một góc 45 độ'
            }
        }
    };

    static components = { InvestorSidebar: window.InvestorSidebar };

    static template = xml`
        <div class="investor-page">
            <div class="investor-layout">
                <!-- Sidebar -->
                <InvestorSidebar profile="this.state.profile" statusInfo="this.state.statusInfo" activePage="'personal'" />

                <!-- Main Content -->
                <div class="investor-content">
                    <div class="investor-card">
                        <div class="card-header-styled">
                            <h2>Thông tin cá nhân</h2>
                            <p>Cập nhật thông tin định danh và liên hệ của bạn</p>
                        </div>

                        <form class="investor-form" t-on-submit.prevent="saveProfile">
                            <div class="row">
                                <div class="col-12 mb-4">
                                    <h5 class="text-primary fw-bold mb-3 border-bottom pb-2">1. Thông tin cơ bản</h5>
                                    
                                    <div class="mb-3">
                                        <label for="fullname" class="form-label">Họ &amp; Tên đầy đủ <span class="text-danger">*</span></label>
                                        <input id="fullname" type="text" class="form-control" t-model="state.formData.name" required="required" placeholder="Nhập họ tên đầy đủ" />
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Giới tính <span class="text-danger">*</span></label>
                                        <div class="d-flex gap-3">
                                            <div class="form-check">
                                                <input class="form-check-input" type="radio" name="gender" value="male" t-model="state.formData.gender" id="gender_male" />
                                                <label class="form-check-label" for="gender_male">Nam</label>
                                            </div>
                                            <div class="form-check">
                                                <input class="form-check-input" type="radio" name="gender" value="female" t-model="state.formData.gender" id="gender_female" />
                                                <label class="form-check-label" for="gender_female">Nữ</label>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label for="birth_date" class="form-label">Ngày sinh <span class="text-danger">*</span></label>
                                            <input id="birth_date" type="date" t-model="state.formData.birth_date" required="required" class="form-control" />
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label for="nationality" class="form-label">Quốc tịch <span class="text-danger">*</span></label>
                                            <select id="nationality" t-model="state.formData.nationality" required="required" class="form-select">
                                                <option value="">Chọn quốc tịch</option>
                                                <t t-foreach="state.countries" t-as="country" t-key="country.id">
                                                    <option t-att-value="toString(country.id)"><t t-esc="country.name" /></option>
                                                </t>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label for="email" class="form-label">Email</label>
                                            <input id="email" type="email" t-model="state.formData.email" class="form-control" placeholder="example@email.com" />
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label for="phone" class="form-label">Số điện thoại <span class="text-danger">*</span></label>
                                            <input id="phone" type="tel" t-model="state.formData.phone" 
                                                   pattern="[0-9]{10}" 
                                                   title="Số điện thoại phải có đúng 10 chữ số"
                                                   maxlength="10"
                                                   required="required" 
                                                   t-on-input="onPhoneInput"
                                                   class="form-control" placeholder="09xxxxxxxx" />
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-12">
                                    <h5 class="text-primary fw-bold mb-3 border-bottom pb-2">2. Giấy tờ tùy thân</h5>
                                    
                                    <div class="row">
                                        <div class="col-md-4 mb-3">
                                            <label for="id-type" class="form-label">Loại giấy tờ <span class="text-danger">*</span></label>
                                            <select id="id-type" t-model="state.formData.id_type" required="required" class="form-select">
                                                <option value="id_card">CMND/CCCD</option>
                                                <option value="passport">Hộ chiếu</option>
                                                <option value="other">Khác</option>
                                            </select>
                                        </div>
                                        <div class="col-md-8 mb-3">
                                            <label for="id-number" class="form-label">Số hiệu giấy tờ <span class="text-danger">*</span></label>
                                            <input id="id-number" type="text" t-model="state.formData.id_number" required="required" class="form-control" />
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label for="id_issue_date" class="form-label">Ngày cấp <span class="text-danger">*</span></label>
                                            <input id="id_issue_date" type="date" t-model="state.formData.id_issue_date" required="required" class="form-control" />
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label for="id_issue_place" class="form-label">Nơi cấp <span class="text-danger">*</span></label>
                                            <input id="id_issue_place" type="text" t-model="state.formData.id_issue_place" required="required" class="form-control" />
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Hình ảnh giấy tờ (Mặt trước &amp; Mặt sau) <span class="text-danger">*</span></label>
                                        <div class="row g-3">
                                            <!-- Front Image -->
                                            <div class="col-md-6">
                                                <label class="ekyc-upload-area h-100 d-flex flex-column justify-content-center align-items-center">
                                                    <input type="file" accept="image/*" style="display:none;" t-on-change="onEkycFront" />
                                                    
                                                    <t t-if="!state.ekycFiles.frontPreview and !state.ocrLoading.front">
                                                        <i class="fa fa-id-card upload-icon"></i>
                                                        <h4 class="fs-6 fw-bold">Mặt trước</h4>
                                                        <p class="mb-0">Nhấn để tải ảnh lên</p>
                                                    </t>
                                                    
                                                    <t t-if="state.ocrLoading.front">
                                                        <div class="spinner-border text-primary" role="status"></div>
                                                        <div class="mt-2 text-primary small">Đang xử lý...</div>
                                                    </t>
                                                    
                                                    <t t-if="state.ekycFiles.frontPreview and !state.ocrLoading.front">
                                                        <img t-att-src="state.ekycFiles.frontPreview" class="img-fluid rounded mb-2" style="max-height: 150px;" />
                                                        <button type="button" class="btn btn-sm btn-outline-danger w-auto" t-on-click.stop="removeFrontImage">
                                                            <i class="fa fa-trash"></i> Xóa
                                                        </button>
                                                    </t>
                                                </label>
                                            </div>
                                            
                                            <!-- Back Image -->
                                            <div class="col-md-6">
                                                <label class="ekyc-upload-area h-100 d-flex flex-column justify-content-center align-items-center">
                                                    <input type="file" accept="image/*" style="display:none;" t-on-change="onEkycBack" />
                                                    
                                                    <t t-if="!state.ekycFiles.backPreview and !state.ocrLoading.back">
                                                        <i class="fa fa-id-card upload-icon"></i>
                                                        <h4 class="fs-6 fw-bold">Mặt sau</h4>
                                                        <p class="mb-0">Nhấn để tải ảnh lên</p>
                                                    </t>
                                                    
                                                    <t t-if="state.ocrLoading.back">
                                                        <div class="spinner-border text-primary" role="status"></div>
                                                        <div class="mt-2 text-primary small">Đang xử lý...</div>
                                                    </t>
                                                    
                                                    <t t-if="state.ekycFiles.backPreview and !state.ocrLoading.back">
                                                        <img t-att-src="state.ekycFiles.backPreview" class="img-fluid rounded mb-2" style="max-height: 150px;" />
                                                        <button type="button" class="btn btn-sm btn-outline-danger w-auto" t-on-click.stop="removeBackImage">
                                                            <i class="fa fa-trash"></i> Xóa
                                                        </button>
                                                    </t>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                    
                                     <div class="d-flex align-items-center gap-3 mb-4">
                                        <button type="button" class="btn btn-ekyc" t-att-class="{'is-verified': state.statusInfo.ekyc_verified}" t-on-click="startEkycVerification" t-att-disabled="state.ekycLoading">
                                            <i class="fa fa-camera"></i> Xác thực eKYC
                                        </button>
                                        <div t-if="state.ekycLoading" class="text-primary small"><i class="fa fa-spinner fa-spin"></i> Đang xác thực...</div>
                                        <div t-if="state.ekycError" class="text-danger small"><t t-esc="state.ekycError" /></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-end pt-3 border-top">
                                <button type="submit" class="btn btn-primary-investor px-5">
                                    <i class="fa fa-save me-2"></i> Lưu Thông Tin
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- eKYC Camera Modal -->
        <div t-if="state.showEkycModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(12px); z-index: 9999;">
          <style>
            .ekyc-modal-content {
              background: #f8fafc;
              border-radius: 24px;
              box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
              border: 1px solid rgba(255, 255, 255, 0.1);
              overflow: hidden;
              max-width: 800px;
              margin: auto;
            }
            
            .ekyc-modal-header {
              background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
              border: none;
              padding: 24px 32px;
              color: white;
              display: flex;
              justify-content: space-between;
              align-items: center;
            }
            
            .ekyc-modal-title {
              font-size: 1.25rem;
              font-weight: 800;
              letter-spacing: -0.025em;
              text-transform: uppercase;
              display: flex;
              align-items: center;
              gap: 12px;
              color: #ffffff !important;
              text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .ekyc-modal-title i {
              color: #f97316;
              filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.4));
            }
            
            .ekyc-modal-body {
              padding: 40px;
              position: relative;
            }
            
            .camera-container {
              position: relative;
              border-radius: 20px;
              overflow: hidden;
              background: #000;
              box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
              aspect-ratio: 4/3;
              max-width: 640px;
              margin: 0 auto;
              border: 2px solid #e2e8f0;
            }
            
            #ekycVideoPreview {
              width: 100%;
              height: 100%;
              object-fit: cover;
              transform: scaleX(-1); /* Mirror effect */
            }
            
            .face-overlay-guide {
              position: absolute;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              width: 280px;
              height: 360px;
              border: 3px solid rgba(249, 115, 22, 0.6);
              border-radius: 150px 150px 120px 120px;
              pointer-events: none;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              box-shadow: 0 0 0 2000px rgba(15, 23, 42, 0.4);
            }
            
            .face-overlay-guide.active {
              border-color: #10b981;
              box-shadow: 0 0 0 2000px rgba(6, 78, 59, 0.2);
              transform: translate(-50%, -50%) scale(1.05);
            }

            .capture-steps {
                display: flex;
                justify-content: center;
                gap: 12px;
                margin-top: 32px;
            }

            .step-indicator {
                padding: 10px 20px;
                border-radius: 12px;
                background: #f1f5f9;
                color: #64748b;
                font-size: 0.875rem;
                font-weight: 600;
                transition: all 0.3s ease;
                border: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .step-indicator.active {
                background: #fff;
                color: #f97316;
                border-color: #f97316;
                box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
                transform: translateY(-2px);
            }

            .step-indicator.completed {
                background: #f0fdf4;
                color: #16a34a;
                border-color: #bcfecb;
            }

            .instruction-card {
                position: absolute;
                bottom: 24px;
                left: 24px;
                right: 24px;
                background: rgba(15, 23, 42, 0.8);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                padding: 16px 20px;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                gap: 16px;
                z-index: 30;
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation: fadeInUp 0.5s ease-out;
            }

            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .instruction-icon {
                width: 48px;
                height: 48px;
                background: rgba(249, 115, 22, 0.25);
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #f97316;
                font-size: 1.5rem;
                flex-shrink: 0;
            }

            .instruction-text h4 {
                margin: 0 0 2px 0;
                font-size: 0.8rem;
                font-weight: 700;
                color: rgba(255, 255, 255, 0.5);
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .instruction-text p {
                margin: 0;
                color: #ffffff;
                font-size: 1.1rem;
                font-weight: 600;
                line-height: 1.3;
                text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            }

            .processing-overlay {
                position: absolute;
                inset: 0;
                background: rgba(255, 255, 255, 0.95);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 100;
                backdrop-filter: blur(4px);
            }

            /* Animations */
            @keyframes pulse-ring {
                0% { transform: scale(0.95); opacity: 0.5; }
                50% { transform: scale(1); opacity: 0.3; }
                100% { transform: scale(0.95); opacity: 0.5; }
            }

            .pulse-effect {
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: inherit;
                border: 4px solid #f97316;
                animation: pulse-ring 2s infinite;
            }

            /* Result Overlay */
            .result-overlay {
                position: absolute;
                inset: 0;
                background: rgba(15, 23, 42, 0.4);
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 100;
                padding: 24px;
                animation: fadeIn 0.3s ease;
            }

            .result-content {
                background: white;
                padding: 32px 24px;
                border-radius: 28px;
                text-align: center;
                width: 100%;
                max-width: 320px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255,255,255,0.2);
            }

            .result-content.success {
                border-top: 6px solid #10b981;
            }

            .result-content.error {
                border-top: 6px solid #ef4444;
            }

            .result-icon {
                font-size: 4rem;
                margin-bottom: 20px;
            }

            .result-icon.success { color: #10b981; }
            .result-icon.error { color: #ef4444; }

            .result-content h3 {
                font-size: 1.5rem;
                font-weight: 800;
                color: #1e293b;
                margin-bottom: 8px;
            }

            .result-content p {
                color: #64748b;
                font-size: 0.95rem;
                line-height: 1.5;
                margin-bottom: 24px;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
          </style>
          
          <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content ekyc-modal-content">
              <div class="modal-header ekyc-modal-header">
                <h5 class="ekyc-modal-title">
                  <i class="fas fa-shield-check"></i> 
                  <span>Xác thực danh tính số</span>
                </h5>
                <button type="button" class="btn-close btn-close-white" t-on-click="closeEkycModal"></button>
              </div>
              
              <div class="modal-body ekyc-modal-body">
                <!-- Processing Overlay -->
                <div t-if="state.isProcessing" class="processing-overlay">
                    <div class="spinner-grow text-warning" style="width: 3rem; height: 3rem;" role="status"></div>
                    <h4 class="mt-4 fw-bold text-slate-900">Đang xử lý dữ liệu</h4>
                    <p class="text-slate-500">Hệ thống AI đang so khớp khuôn mặt và trích xuất OCR...</p>
                </div>

                <!-- Camera Work Area -->
                <div class="camera-container">
                  <video id="ekycVideoPreview" autoplay="autoplay" muted="muted" 
                         t-att-class="state.cameraActive ? 'd-block' : 'd-none'">
                  </video>
                  
                  <!-- Face Guide -->
                  <div t-if="state.cameraActive" class="face-overlay-guide" t-att-class="{'active': state.faceStatus and state.faceStatus.status === 'perfect'}">
                      <div t-if="state.faceStatus and state.faceStatus.status === 'perfect'" class="pulse-effect"></div>
                  </div>

                  <!-- Quick Status Tag -->
                  <div t-if="state.cameraActive" class="position-absolute" style="top: 20px; left: 20px; z-index: 10;">
                      <span class="badge rounded-pill px-3 py-2" t-att-class="state.faceStatus and state.faceStatus.status === 'perfect' ? 'bg-success' : 'bg-dark opacity-75'">
                          <i t-att-class="state.faceStatus and state.faceStatus.status === 'perfect' ? 'fas fa-check-circle' : 'fas fa-face-viewfinder'" class="me-2"></i>
                          <t t-esc="state.cameraStatus" />
                      </span>
                  </div>

                  <!-- Guidance Overlay (Moved here for better visibility) -->
                  <div class="instruction-card" t-if="state.cameraActive">
                      <div class="instruction-icon">
                          <i t-att-class="state.currentCapturePhase === 'front' ? 'fas fa-user-check' : (state.currentCapturePhase === 'left' ? 'fas fa-reply' : 'fas fa-share')"></i>
                      </div>
                      <div class="instruction-text">
                          <h4>Bước tiếp theo: <t t-esc="getPhaseName(state.currentCapturePhase)" /></h4>
                          <p><t t-esc="state.cameraInstructions" /></p>
                      </div>
                  </div>

                  <!-- Result Overlay (New centered design) -->
                  <div t-if="state.ekycResult" class="result-overlay">
                    <div class="result-content animate__animated animate__zoomIn" t-att-class="state.ekycResult.success ? 'success' : 'error'">
                        <div class="result-icon" t-att-class="state.ekycResult.success ? 'success' : 'error'">
                            <i t-att-class="state.ekycResult.success ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
                        </div>
                        <h3 t-esc="state.ekycResult.success ? 'Xác thực thành công!' : 'Xác thực thất bại'" />
                        <p t-if="!state.ekycResult.success" t-esc="state.ekycResult.error" />
                        <p t-if="state.ekycResult.success">Thông tin cá nhân đã được tự động cập nhật.</p>
                        
                        <div class="d-grid gap-2">
                            <button t-if="!state.ekycResult.success" type="button" class="btn btn-danger rounded-pill py-2 fw-bold" t-on-click="resetEkycVerification">
                                <i class="fas fa-redo me-2"></i> Thử lại
                            </button>
                            <button type="button" class="btn btn-light border rounded-pill py-2 fw-bold" t-on-click="closeEkycModal">
                                <i class="fas fa-times me-2"></i> Đóng
                            </button>
                        </div>
                    </div>
                  </div>
                </div>

                <!-- Step Indicators -->
                <div class="capture-steps">
                    <div class="step-indicator" t-att-class="getProgressStepClass('front')">
                        <i class="fas fa-user"></i> Nhìn thẳng
                    </div>
                    <div class="step-indicator" t-att-class="getProgressStepClass('left')">
                        <i class="fas fa-arrow-left"></i> Nghiêng trái
                    </div>
                    <div class="step-indicator" t-att-class="getProgressStepClass('right')">
                        <i class="fas fa-arrow-right"></i> Nghiêng phải
                    </div>
                </div>



                <!-- Error Fallback -->
                <div t-if="state.cameraError" class="alert alert-warning mt-4 p-4" style="border-radius: 16px;">
                    <h5 class="fw-bold"><i class="fas fa-video-slash me-2"></i> Lỗi Camera</h5>
                    <p class="mb-3"><t t-esc="state.cameraError" /></p>
                    <button type="button" class="btn btn-warning px-4 py-2" style="border-radius: 10px;" t-on-click="initCamera">
                        <i class="fas fa-sync me-2"></i> Thử lại
                    </button>
                </div>

              </div>
            </div>
          </div>
        </div>

        <!-- Success/Error Modal -->
        <div t-if="state.showModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="border:2px solid #f97316;">
              <div class="modal-header" style="border-bottom:1px solid #f97316;">
                <h5 class="modal-title" style="color:#f97316;"><t t-esc="state.modalTitle" /></h5>
                <button type="button" class="btn-close" t-on-click="closeModal"></button>
              </div>
              <div class="modal-body" t-att-class="state.modalTitle === 'Thành công' ? 'text-center' : ''">
                <t t-if="state.modalTitle === 'Thành công'">
                  <div style="font-size:3rem;color:#43a047;margin-bottom:20px;">
                    <i class="fa fa-check-circle"></i>
                  </div>
                </t>
                <div t-raw="state.modalMessage" class="mt-3"></div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn" style="background-color:#f97316;border-color:#f97316;color:white" t-on-click="closeModal">Đóng</button>
              </div>
            </div>
          </div>
        </div>
    `;

    setup() {


        this.state = useState({
            loading: true,
            profile: {},
            statusInfo: {},
            countries: [],
            formData: {
                name: '',
                gender: '',
                birth_date: '',
                nationality: '',
                email: '',
                phone: '',
                id_type: 'id_card',
                id_number: '',
                id_issue_date: '',
                id_issue_place: ''
            },
            activeTab: 'personal',
            ekycFiles: {
                front: null,
                back: null,
                frontPreview: null,
                backPreview: null
            },
            ekycLoading: false,
            ekycError: '',
            showModal: false,
            modalTitle: '',
            modalMessage: '',
            // eKYC Camera states
            showEkycModal: false,
            cameraActive: false,
            cameraError: '',
            cameraStatus: 'Đang khởi tạo...',
            cameraInstructions: 'Vui lòng đặt khuôn mặt vào đúng vi trí!',
            capturedImages: [],
            capturedImageTypes: [], // Track what type of image was captured
            isProcessing: false,
            _mediaStream: null,
            faceStatus: null,
            autoCaptureEnabled: true,
            autoCaptureInterval: null,
            lastCaptureTime: 0,
            perfectFaceStartTime: 0, // Track when face becomes perfect
            ekycResult: null,
            currentCapturePhase: 'front', // 'front', 'left', 'right'
            captureRequirements: {
                front: 3,  // 3 ảnh chỉnh diện
                left: 2,   // 2 ảnh góc trái
                right: 2   // 2 ảnh góc phải
            },
            // OCR Loading states
            ocrLoading: {
                front: false,
                back: false
            }
        });

        onMounted(async () => {
            // Hide loading spinner
            const loadingSpinner = document.getElementById('loadingSpinner');
            const widgetContainer = document.getElementById('personalProfileWidget');

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
                // Reset formData và preview ảnh/video
                Object.assign(this.state.formData, {
                    name: '',
                    gender: 'male',
                    birth_date: '',
                    nationality: '',
                    email: '',
                    phone: '',
                    id_type: 'id_card',
                    id_number: '',
                    id_issue_date: '',
                    id_issue_place: ''
                });
                this.state.ekycFiles.front = null;
                this.state.ekycFiles.back = null;
                this.state.ekycFiles.frontPreview = null;
                this.state.ekycFiles.backPreview = null;
            }

            // Load countries, profile data and status info
            await Promise.all([
                this.loadCountries(),
                this.loadProfileData()
            ]);
            this.loadInitialFormData(); // Load form data after profile is loaded
            await this.loadStatusInfo();

            this.state.loading = false;
        });
    }

    loadInitialFormData() {
        // Ưu tiên lấy từ sessionStorage
        const storedData = sessionStorage.getItem('personalProfileData');
        if (storedData) {
            const parsedData = JSON.parse(storedData);

            // Check if this is fresh eKYC data (has OCR fields and CCCD images)
            const isEkycData = parsedData.name && parsedData.id_number && (parsedData.frontPreviewBase64 || parsedData.backPreviewBase64);

            if (isEkycData) {


                // Apply OCR data to form
                this.state.formData.name = parsedData.name || '';
                this.state.formData.gender = parsedData.gender || 'male';
                this.state.formData.birth_date = parsedData.birth_date || '';
                this.state.formData.nationality = parsedData.nationality ? String(parsedData.nationality) : '';
                this.state.formData.id_type = parsedData.id_type || 'id_card';
                this.state.formData.id_number = parsedData.id_number || '';
                this.state.formData.id_issue_date = parsedData.id_issue_date || '';
                this.state.formData.id_issue_place = parsedData.id_issue_place || '';

                // Load CCCD images from eKYC và convert thành File objects để lưu thực sự
                if (parsedData.frontPreviewBase64) {
                    this.state.ekycFiles.frontPreview = parsedData.frontPreviewBase64;
                    // Convert base64 thành File object để có thể lưu vào database
                    this.state.ekycFiles.front = this.base64ToFile(parsedData.frontPreviewBase64, 'cccd_front.jpg');
                }
                if (parsedData.backPreviewBase64) {
                    this.state.ekycFiles.backPreview = parsedData.backPreviewBase64;
                    // Convert base64 thành File object để có thể lưu vào database
                    this.state.ekycFiles.back = this.base64ToFile(parsedData.backPreviewBase64, 'cccd_back.jpg');
                }

                // Keep existing email and phone if available, or set defaults
                if (this.state.profile && Object.keys(this.state.profile).length > 0) {
                    this.state.formData.email = this.state.profile.email || parsedData.email || '';
                    this.state.formData.phone = this.state.profile.phone || parsedData.phone || '';
                } else {
                    // Set default values if no existing profile
                    this.state.formData.email = parsedData.email || '';
                    this.state.formData.phone = parsedData.phone || '';
                }

                // Show success message


            } else {
                // Regular session storage data (with preview images)
                if (parsedData.nationality && typeof parsedData.nationality === 'number') {
                    parsedData.nationality = String(parsedData.nationality);
                }
                Object.assign(this.state.formData, parsedData);

                // If có preview base64 thì tạo lại preview
                if (parsedData.frontPreviewBase64) {
                    this.state.ekycFiles.frontPreview = parsedData.frontPreviewBase64;
                }
                if (parsedData.backPreviewBase64) {
                    this.state.ekycFiles.backPreview = parsedData.backPreviewBase64;
                }

            }
        } else if (this.state.profile && Object.keys(this.state.profile).length > 0) {
            this.state.formData.name = this.state.profile.name || '';
            this.state.formData.gender = this.state.profile.gender || 'male';
            this.state.formData.email = this.state.profile.email || '';
            this.state.formData.phone = this.state.profile.phone || '';
            this.state.formData.id_type = this.state.profile.id_type || 'id_card';
            this.state.formData.id_number = this.state.profile.id_number || '';
            this.state.formData.id_issue_date = this.state.profile.id_issue_date || '';
            this.state.formData.id_issue_place = this.state.profile.id_issue_place || '';
            this.state.formData.birth_date = this.state.profile.birth_date || '';
            this.state.formData.nationality = this.state.profile.nationality ? Number(this.state.profile.nationality) : '';

            // Load CCCD images từ database nếu có


            if (this.state.profile.id_front && this.state.profile.id_front !== '') {
                this.state.ekycFiles.frontPreview = this.state.profile.id_front;

                // Convert URL images thành File objects để có thể save lại
                this.loadImageAsFile(this.state.profile.id_front, 'front');
            } else {
                console.log("No front CCCD image found in database");
            }

            if (this.state.profile.id_back && this.state.profile.id_back !== '') {
                this.state.ekycFiles.backPreview = this.state.profile.id_back;

                // Convert URL images thành File objects để có thể save lại
                this.loadImageAsFile(this.state.profile.id_back, 'back');
            } else {
                console.log("No back CCCD image found in database");
            }


        } else {
            console.log("No existing profile data found, using default values");
        }
    }

    showEkycSuccessMessage() {
        // Show success message for eKYC data
        this.state.modalTitle = 'Thành công';
        this.state.modalMessage = 'Thông tin từ CCCD đã được tự động điền vào form thông tin cá nhân và địa chỉ. Vui lòng kiểm tra và lưu thông tin.';
        this.state.showModal = true;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.state.showModal = false;
        }, 5000);
    }

    async loadCountries() {
        try {
            const response = await fetch('/get_countries');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (!Array.isArray(data) || data.length === 0) {
                throw new Error('No countries data received');
            }

            this.state.countries = data;

            // Create a mapping for quick lookup
            this.state.countryMapping = {};
            data.forEach(country => {
                this.state.countryMapping[String(country.id)] = country.name;
                // Also add common variations
                const name = country.name.toLowerCase();
                this.state.countryMapping[name] = String(country.id);
                this.state.countryMapping[country.name] = String(country.id);
            });

        } catch (error) {
            console.error("Error fetching countries:", error);

            // Create fallback countries array
            this.state.countries = [
                { id: '241', name: 'Vietnam', code: 'VN' },
                { id: '233', name: 'USA', code: 'US' },
                { id: '231', name: 'UK', code: 'GB' },
                { id: '113', name: 'Japan', code: 'JP' },
                { id: '48', name: 'China', code: 'CN' },
                { id: '121', name: 'South Korea', code: 'KR' },
                { id: '197', name: 'Singapore', code: 'SG' },
                { id: '217', name: 'Thailand', code: 'TH' },
                { id: '132', name: 'Malaysia', code: 'MY' },
                { id: '103', name: 'Indonesia', code: 'ID' },
                { id: '174', name: 'Philippines', code: 'PH' },
                { id: '14', name: 'Australia', code: 'AU' },
                { id: '39', name: 'Canada', code: 'CA' },
                { id: '82', name: 'Germany', code: 'DE' },
                { id: '75', name: 'France', code: 'FR' },
                { id: '107', name: 'Italy', code: 'IT' },
                { id: '195', name: 'Spain', code: 'ES' },
                { id: '156', name: 'Netherlands', code: 'NL' },
                { id: '207', name: 'Switzerland', code: 'CH' },
                { id: '203', name: 'Sweden', code: 'SE' }
            ];

            // Fallback mapping with common countries
            this.state.countryMapping = {
                // Vietnam
                '241': 'Vietnam', 'vietnam': '241', 'việt nam': '241', 'vn': '241', 'viet nam': '241',
                'cộng hòa xã hội chủ nghĩa việt nam': '241', 'chxhcn việt nam': '241',

                // USA
                '233': 'USA', 'usa': '233', 'united states': '233', 'us': '233', 'hoa kỳ': '233', 'mỹ': '233',
                'united states of america': '233', 'america': '233',

                // UK
                '231': 'UK', 'uk': '231', 'united kingdom': '231', 'england': '231', 'anh': '231',
                'great britain': '231', 'britain': '231',

                // Japan
                '113': 'Japan', 'japan': '113', 'jp': '113', 'nhật bản': '113', 'japanese': '113',

                // China
                '48': 'China', 'china': '48', 'cn': '48', 'trung quốc': '48', 'chinese': '48',

                // Korea
                '121': 'South Korea', 'south korea': '121', 'korea': '121', 'kr': '121', 'hàn quốc': '121',

                // Singapore
                '197': 'Singapore', 'singapore': '197', 'sg': '197',

                // Thailand
                '217': 'Thailand', 'thailand': '217', 'th': '217', 'thái lan': '217',

                // Malaysia
                '132': 'Malaysia', 'malaysia': '132', 'my': '132',

                // Indonesia
                '103': 'Indonesia', 'indonesia': '103', 'id': '103',

                // Philippines
                '174': 'Philippines', 'philippines': '174', 'ph': '174',

                // Australia
                '14': 'Australia', 'australia': '14', 'au': '14',

                // Canada
                '39': 'Canada', 'canada': '39', 'ca': '39',

                // Germany
                '82': 'Germany', 'germany': '82', 'de': '82', 'đức': '82',

                // France
                '75': 'France', 'france': '75', 'fr': '75', 'pháp': '75',

                // Italy
                '107': 'Italy', 'italy': '107', 'it': '107', 'ý': '107',

                // Spain
                '195': 'Spain', 'spain': '195', 'es': '195', 'tây ban nha': '195',

                // Netherlands
                '156': 'Netherlands', 'netherlands': '156', 'nl': '156', 'hà lan': '156',

                // Switzerland
                '207': 'Switzerland', 'switzerland': '207', 'ch': '207', 'thụy sĩ': '207',

                // Sweden
                '203': 'Sweden', 'sweden': '203', 'se': '203', 'thụy điển': '203'
            };
        }
    }

    async loadStatusInfo() {
        try {
            const response = await fetch('/get_status_info');
            const data = await response.json();
            // Status info loaded

            if (data && data.length > 0) {
                this.state.statusInfo = data[0];
            } else {
                console.log("No status info found");
            }
        } catch (error) {
            console.error("Error fetching status info:", error);
        }
    }

    // Thêm hàm chuyển file sang base64
    async fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    // Thêm hàm chuyển base64 thành File object
    base64ToFile(base64String, filename) {
        try {
            // Extract the base64 data and mime type
            const arr = base64String.split(',');
            const mime = arr[0].match(/:(.*?);/)[1];
            const bstr = atob(arr[1]);
            let n = bstr.length;
            const u8arr = new Uint8Array(n);

            while (n--) {
                u8arr[n] = bstr.charCodeAt(n);
            }

            return new File([u8arr], filename, { type: mime });
        } catch (error) {
            console.error('Error converting base64 to file:', error);
            return null;
        }
    }

    // Thêm hàm load image từ URL thành File object  
    async loadImageAsFile(imageUrl, side) {
        try {


            // Kiểm tra URL hợp lệ
            const isWebImage = imageUrl && imageUrl.startsWith('/web/image');
            if (!imageUrl || imageUrl === '' || !isWebImage) {
                console.warn(`Invalid URL for ${side} CCCD image:`, imageUrl);
                return;
            }

            const response = await fetch(imageUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
            }

            const blob = await response.blob();
            if (blob.size === 0) {
                throw new Error('Image blob is empty');
            }

            const filename = `cccd_${side}.jpg`;
            const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });

            if (side === 'front') {
                this.state.ekycFiles.front = file;
            } else if (side === 'back') {
                this.state.ekycFiles.back = file;
            }
        } catch (error) {
            console.error(`Error loading ${side} CCCD image:`, error);
            // Không set file nếu có lỗi, để user có thể upload lại
        }
    }

    // Thêm hàm convert URL thành base64
    async urlToBase64(imageUrl) {
        try {
            const response = await fetch(imageUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.status}`);
            }

            const blob = await response.blob();
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.readAsDataURL(blob);
            });
        } catch (error) {
            console.error('Error converting URL to base64:', error);
            return '';
        }
    }

    async saveProfile() {
        try {
            const profileData = { ...this.state.formData };
            // Đảm bảo nationality là số nguyên ID
            if (!profileData.nationality || isNaN(profileData.nationality) || Number(profileData.nationality) <= 0) {
                this.state.modalTitle = 'Lỗi';
                this.state.modalMessage = 'Bạn chưa chọn quốc tịch!';
                this.state.showModal = true;
                return;
            }

            // Kiểm tra số điện thoại phải có đúng 10 chữ số
            if (profileData.phone) {
                const phoneDigits = profileData.phone.replace(/[^0-9]/g, '');
                if (phoneDigits.length !== 10) {
                    this.state.modalTitle = 'Lỗi';
                    this.state.modalMessage = 'Số điện thoại phải có đúng 10 chữ số!';
                    this.state.showModal = true;
                    return;
                }
                // Cập nhật phone với chỉ số
                profileData.phone = phoneDigits;
            }
            // Ràng buộc phải có ảnh mặt trước, mặt sau CCCD (từ eKYC, upload, hoặc database)
            const hasFrontImage = this.state.ekycFiles.front || this.state.ekycFiles.frontPreview;
            const hasBackImage = this.state.ekycFiles.back || this.state.ekycFiles.backPreview;

            if (!hasFrontImage || !hasBackImage) {
                this.state.modalTitle = 'Lỗi';
                this.state.modalMessage = 'Bạn phải có đủ ảnh mặt trước và mặt sau CCCD! Vui lòng thực hiện eKYC hoặc upload ảnh CCCD.';
                this.state.showModal = true;
                return;
            }
            profileData.nationality = Number(profileData.nationality);
            // Convert images sang base64 cho việc lưu
            if (this.state.ekycFiles.front) {
                profileData.frontPreviewBase64 = await this.fileToBase64(this.state.ekycFiles.front);
            } else if (this.state.ekycFiles.frontPreview && this.state.ekycFiles.frontPreview.startsWith('data:')) {
                profileData.frontPreviewBase64 = this.state.ekycFiles.frontPreview;
            } else if (this.state.ekycFiles.frontPreview && this.state.ekycFiles.frontPreview.startsWith('/web/image')) {
                // Image từ database - convert URL sang base64
                profileData.frontPreviewBase64 = await this.urlToBase64(this.state.ekycFiles.frontPreview);
            } else {
                profileData.frontPreviewBase64 = '';
            }

            if (this.state.ekycFiles.back) {
                profileData.backPreviewBase64 = await this.fileToBase64(this.state.ekycFiles.back);
            } else if (this.state.ekycFiles.backPreview && this.state.ekycFiles.backPreview.startsWith('data:')) {
                profileData.backPreviewBase64 = this.state.ekycFiles.backPreview;
            } else if (this.state.ekycFiles.backPreview && this.state.ekycFiles.backPreview.startsWith('/web/image')) {
                // Image từ database - convert URL sang base64
                profileData.backPreviewBase64 = await this.urlToBase64(this.state.ekycFiles.backPreview);
            } else {
                profileData.backPreviewBase64 = '';
            }



            // Gửi dữ liệu lên Odoo
            const response = await fetch('/save_personal_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            });
            const result = await response.json();
            if (response.ok && result.success) {
                sessionStorage.setItem('personalProfileData', JSON.stringify(profileData));
                sessionStorage.setItem('personalProfileUserId', String(window.currentUserId || ''));

                await this.loadProfileData();
                this.loadInitialFormData();

                this.state.modalTitle = 'Thành công';
                this.state.modalMessage = 'Lưu Thông Tin cá nhân thành công!';
                this.state.showModal = true;
                setTimeout(() => { window.location.href = '/bank_info'; }, 1500);
            } else {
                this.state.modalTitle = 'Lỗi';
                this.state.modalMessage = result.error || 'Có lỗi xảy ra, vui lòng thử lại.';
                this.state.showModal = true;
            }

        } catch (error) {
            this.state.modalTitle = 'Lỗi';
            this.state.modalMessage = error.message || 'Có lỗi xảy ra, vui lòng thử lại.';
            this.state.showModal = true;
        }
    }

    async loadProfileData() {
        try {
            const response = await fetch('/data_personal_profile');
            const data = await response.json();

            if (data && data.length > 0) {
                this.state.profile = data[0];
            } else {
                console.log("No existing profile data found on server");
                this.state.profile = {};
            }
        } catch (error) {
            console.error("Error fetching personal profile data:", error);
            this.state.profile = {};
        }
    }

    onUploadIdFront(ev) {
        const file = ev.target.files[0];
        if (file) {
            this.uploadIdImage(file, 'front');
        }
    }

    onUploadIdBack(ev) {
        const file = ev.target.files[0];
        if (file) {
            this.uploadIdImage(file, 'back');
        }
    }

    onPhoneInput(ev) {
        // Chỉ cho phép nhập số và giới hạn 10 ký tự
        let value = ev.target.value.replace(/[^0-9]/g, '');
        if (value.length > 10) {
            value = value.substring(0, 10);
        }
        this.state.formData.phone = value;
        ev.target.value = value;
    }

    async uploadIdImage(file, side) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('side', side);

            const response = await fetch('/upload_id_image', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                // Successful upload
                // Optionally, refresh profile data to show the new image
                await this.loadProfileData();
            } else {
                const errorData = await response.json();
                console.error(`Failed to upload ${side} ID image:`, errorData.error);
                alert(`Failed to upload ${side} ID image: ${errorData.error}`);
            }
        } catch (error) {
            console.error(`Error uploading ${side} ID image:`, error);
            alert(`Error uploading ${side} ID image.`);
        }
    }

    async onEkycFront(ev) {
        const file = ev.target.files[0];
        if (file) {
            this.state.ekycFiles.front = file;
            if (this.state.ekycFiles.frontPreview && this.state.ekycFiles.frontPreview.startsWith('blob:')) {
                URL.revokeObjectURL(this.state.ekycFiles.frontPreview);
            }
            this.state.ekycFiles.frontPreview = await this.fileToBase64(file);
        }
    }

    async onEkycBack(ev) {
        const file = ev.target.files[0];
        if (file) {
            this.state.ekycFiles.back = file;
            if (this.state.ekycFiles.backPreview && this.state.ekycFiles.backPreview.startsWith('blob:')) {
                URL.revokeObjectURL(this.state.ekycFiles.backPreview);
            }
            this.state.ekycFiles.backPreview = await this.fileToBase64(file);

            // Auto-detect OCR removed - only OCR when eKYC is successful
            console.log('Back CCCD image selected, OCR will run after face matching.');
        }
    }

    async detectOCRFromImage(file, side) {
        try {
            console.log(`Detecting OCR from ${side} CCCD...`);

            // Set loading state
            this.state.ocrLoading[side] = true;

            const formData = new FormData();
            formData.append(side === 'front' ? 'frontID' : 'backID', file);

            const endpoint = side === 'front' ? '/api/ekyc/frontID' : '/api/ekyc/backID';
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Success - update form with OCR data
                // For front OCR: result.data contains the OCR data directly
                // For back OCR: result.data.data contains the OCR data (nested structure)
                const ocrData = side === 'back' && result.data && result.data.data ? result.data.data : result.data;
                this.updateFormWithOCRData(ocrData, side);
                const sideText = side === 'front' ? 'mặt trước' : 'mặt sau';
                this.showModal('Thành công', `Trích xuất thông tin ${sideText} CCCD thành công!`);
            } else {
                // Failed
                const errorMsg = result.error || `Lỗi trích xuất thông tin ${side === 'front' ? 'mặt trước' : 'mặt sau'} CCCD.`;
                this.showModal('Lỗi', errorMsg);
            }
        } catch (error) {
            const errorText = side === 'front' ? 'mặt trước' : 'mặt sau';
            this.showModal('Lỗi', `Có lỗi xảy ra khi trích xuất thông tin từ CCCD ${errorText}. Vui lòng thử lại.`);
            console.error(`Error detecting OCR from ${side} CCCD:`, error);
        } finally {
            // Clear loading state
            this.state.ocrLoading[side] = false;
        }
    }

    updateFormWithOCRData(ocrData, side) {
        const updatedFields = [];

        if (side === 'front') {
            // Update front OCR data
            if (ocrData.idNumber) {
                this.state.formData.id_number = ocrData.idNumber;
                updatedFields.push('Số CCCD');
            }
            if (ocrData.fullName) {
                this.state.formData.name = ocrData.fullName;
                updatedFields.push('Họ và tên');
            }
            if (ocrData.dob) {
                this.state.formData.birth_date = this.formatDateForInput(ocrData.dob);
                updatedFields.push('Ngày sinh');
            }
            if (ocrData.gender) {
                const g = ocrData.gender.toString().toLowerCase();
                if (g.includes('nam') || g.includes('male') || g === 'm') {
                    this.state.formData.gender = 'male';
                } else if (g.includes('nữ') || g.includes('female') || g === 'f') {
                    this.state.formData.gender = 'female';
                }
                updatedFields.push('Giới tính');
            }
            if (ocrData.nationality) {
                const countryId = this.findCountryIdByName(ocrData.nationality);
                if (countryId) {
                    // Convert to string for select dropdown
                    this.state.formData.nationality = String(countryId);
                    updatedFields.push('Quốc tịch');

                    // Force re-render of the select dropdown
                    this.render();
                }
            }

            // Propagate address-related data for AddressInfoWidget via sessionStorage
            try {
                const addressPayload = {};
                if (ocrData.address) {
                    addressPayload.permanent_address = ocrData.address;
                }
                if (ocrData.place_of_birth) {
                    addressPayload.birth_place = ocrData.place_of_birth;
                }
                if (ocrData.place_of_origin || ocrData.hometown) {
                    addressPayload.hometown = ocrData.place_of_origin || ocrData.hometown;
                }
                if (Object.keys(addressPayload).length > 0) {
                    const existingRaw = sessionStorage.getItem('addressInfoData');
                    let merged = {};
                    if (existingRaw) {
                        try { merged = JSON.parse(existingRaw) || {}; } catch (e) { merged = {}; }
                    }
                    const finalData = { ...merged, ...addressPayload };
                    sessionStorage.setItem('addressInfoData', JSON.stringify(finalData));
                    sessionStorage.setItem('addressInfoFromEkyc', 'true');
                }
            } catch (e) {
                console.warn('Failed to store eKYC address data to sessionStorage:', e);
            }
        } else if (side === 'back') {
            // Update back OCR data
            // OCR back returns: {init_date: '...', issue_date: '...', place_of_birth: '...'}
            if (ocrData.init_date) {
                this.state.formData.id_issue_date = this.formatDateForInput(ocrData.init_date);
                updatedFields.push('Ngày cấp');
            } else if (ocrData.issue_date) {
                this.state.formData.id_issue_date = this.formatDateForInput(ocrData.issue_date);
                updatedFields.push('Ngày cấp');
            }
            // Nơi cấp - VNPT uses issue_place or noi_cap. Avoid using place_of_birth which is Nơi sinh.
            const issuePlace = ocrData.issue_place || ocrData.noi_cap || ocrData.place_of_issue || ocrData.co_quan_cap || ocrData.issued_by;
            if (issuePlace && issuePlace !== '-') {
                this.state.formData.id_issue_place = issuePlace;
                updatedFields.push('Nơi cấp');
            } else if (ocrData.place_of_birth) {
                // Fallback for older IDs if issue_place is somehow returned as place_of_birth
                this.state.formData.id_issue_place = ocrData.place_of_birth;
                updatedFields.push('Nơi cấp');
            }

            // Propagate birth place if available (some services return on back side)
            try {
                if (ocrData.place_of_birth) {
                    const existingRaw = sessionStorage.getItem('addressInfoData');
                    let merged = {};
                    if (existingRaw) {
                        try { merged = JSON.parse(existingRaw) || {}; } catch (e) { merged = {}; }
                    }
                    const finalData = { ...merged, birth_place: ocrData.place_of_birth };
                    sessionStorage.setItem('addressInfoData', JSON.stringify(finalData));
                    sessionStorage.setItem('addressInfoFromEkyc', 'true');
                }
            } catch (e) {
                console.warn('Failed to update eKYC birth place in sessionStorage:', e);
            }
        }

        this.render();

        // Show detailed success message
        if (updatedFields.length > 0) {
            const sideText = side === 'front' ? 'mặt trước' : 'mặt sau';
            const fieldsText = updatedFields.join(', ');
            this.showModal('Thành công!', `Đã trích xuất thông tin từ CCCD ${sideText}:\n${fieldsText}`);

            // Auto-close success message after 3 seconds
            setTimeout(() => {
                this.state.showModal = false;
            }, 3000);
        }
    }

    startEkycVerification() {
        // Check if both CCCD images are uploaded
        if (!this.state.ekycFiles.front || !this.state.ekycFiles.back) {
            this.showModal('Lỗi', 'Vui lòng upload đầy đủ ảnh CCCD mặt trước và mặt sau trước khi xác thực eKYC.');
            return;
        }

        // Show eKYC camera modal
        this.state.showEkycModal = true;
        this.state.capturedImages = [];
        this.state.capturedImageTypes = [];
        this.state.isProcessing = false;
        this.state.lastCaptureTime = 0;
        this.state.perfectFaceStartTime = 0; // Reset perfect face timer
        this.state.currentCapturePhase = 'front'; // Start with front-facing
        this.state.cameraStatus = 'Đang khởi tạo camera...';

        // Set initial camera instructions based on current phase
        this.updateCameraInstructionsForPhase('front');

        // Auto-initialize camera
        setTimeout(() => {
            this.initCamera();
        }, 500);
    }

    closeEkycModal() {
        this.state.showEkycModal = false;
        this.stopCamera();

        // Ensure form data is preserved after closing modal
        if (this.state.formData && Object.keys(this.state.formData).length > 0) {
            const profileData = {
                ...this.state.formData,
                // Preserve CCCD images
                frontPreviewBase64: this.state.ekycFiles.frontPreview,
                backPreviewBase64: this.state.ekycFiles.backPreview
            };

            sessionStorage.setItem('personalProfileData', JSON.stringify(profileData));
            sessionStorage.setItem('personalProfileUserId', String(window.currentUserId || ''));

            // Form data preserved after closing eKYC modal

        }

        // Force render to ensure form is visible with updated data
        this.render();
    }

    resetEkycVerification() {
        // Reset all eKYC related states
        this.state.capturedImages = [];
        this.state.capturedImageTypes = [];
        this.state.isProcessing = false;
        this.state.lastCaptureTime = 0;
        this.state.perfectFaceStartTime = 0;
        this.state.ekycResult = null;
        this.state.currentCapturePhase = 'front';
        this.state.cameraStatus = 'Camera đã sẵn sàng';

        // Set initial camera instructions
        this.updateCameraInstructionsForPhase('front');

        // Re-initialize camera
        setTimeout(() => {
            this.initCamera();
        }, 500);

        console.log('eKYC verification reset, ready to start again');
    }

    // Helper methods for new capture logic
    getCapturedCount(phase) {
        return this.state.capturedImageTypes.filter(type => type === phase).length;
    }
    isAllImagesCaptured() {
        const frontCount = this.getCapturedCount('front');
        const leftCount = this.getCapturedCount('left');
        const rightCount = this.getCapturedCount('right');

        return frontCount >= this.state.captureRequirements.front &&
            leftCount >= this.state.captureRequirements.left &&
            rightCount >= this.state.captureRequirements.right;
    }

    getProgressStepClass(phase) {
        const count = this.getCapturedCount(phase);
        const required = this.state.captureRequirements[phase];

        if (count >= required) {
            return 'completed';
        } else if (count > 0) {
            return 'partial';
        } else {
            return 'pending';
        }
    }

    getNextCapturePhase() {
        const frontCount = this.getCapturedCount('front');
        const leftCount = this.getCapturedCount('left');
        const rightCount = this.getCapturedCount('right');

        if (frontCount < this.state.captureRequirements.front) {
            return 'front';
        } else if (leftCount < this.state.captureRequirements.left) {
            return 'left';
        } else if (rightCount < this.state.captureRequirements.right) {
            return 'right';
        }
        return null; // All phases completed
    }

    getPhaseName(phase) {
        const phaseNames = {
            'front': 'Nhìn thẳng',
            'left': 'Quay sang trái',
            'right': 'Quay sang phải'
        };
        return phaseNames[phase] || phase;
    }

    updateCameraInstructionsForPhase(phase) {
        const phaseInstructions = {
            'front': 'Vui lòng nhìn thẳng vào camera và giữ nguyên vị trí',
            'left': 'Vui lòng quay mặt sang trái và giữ nguyên vị trí',
            'right': 'Vui lòng quay mặt sang phải và giữ nguyên vị trí'
        };

        this.updateCameraInstructions(phaseInstructions[phase] || 'Vui lòng điều chỉnh khuôn mặt');
    }

    updateCameraInstructions(message) {
        if (this.state.cameraInstructions !== message) {
            this.state.cameraInstructions = message;

        }
    }


    updateCapturePhase() {
        const nextPhase = this.getNextCapturePhase();
        if (nextPhase && nextPhase !== this.state.currentCapturePhase) {
            this.state.currentCapturePhase = nextPhase;
            this.state.perfectFaceStartTime = 0; // Reset timer for new phase

            // Update camera instructions for new phase
            this.updateCameraInstructionsForPhase(nextPhase);
        }
    }

    showModal(title, message) {
        this.state.modalTitle = title;
        this.state.modalMessage = message;
        this.state.showModal = true;
    }

    async initCamera() {
        this.stopCamera();
        this.state.cameraError = '';
        this.state.cameraStatus = 'Đang khởi tạo camera...';

        try {
            // Check if browser supports getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Trình duyệt không hỗ trợ truy cập camera. Vui lòng sử dụng trình duyệt hiện đại.');
            }

            // Check if running on HTTPS or localhost
            const isSecureContext = window.isSecureContext ||
                location.protocol === 'https:' ||
                location.hostname === 'localhost' ||
                location.hostname === '127.0.0.1';

            if (!isSecureContext) {
                throw new Error('Camera chỉ hoạt động trên HTTPS hoặc localhost. Vui lòng truy cập qua HTTPS.');
            }


            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            });

            this.state._mediaStream = stream;
            const video = document.getElementById('ekycVideoPreview');

            if (video) {
                video.srcObject = stream;
                this.state.cameraActive = true;
                this.state.cameraStatus = 'Camera đã sẵn sàng';
                // Keep existing camera instructions or set default for current phase
                if (!this.state.cameraInstructions) {
                    this.updateCameraInstructionsForPhase(this.state.currentCapturePhase);
                }

                // Start face detection after camera is ready
                video.onloadedmetadata = () => {
                    setTimeout(async () => {
                        // Check if Face API is already loaded from template
                        if (window.faceapi && this.areModelsLoaded()) {
                            this.startFaceDetection();
                            this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt...');
                        } else if (window.faceapi && !this.areModelsLoaded()) {
                            await this.loadFaceAPIModels();
                            this.startFaceDetection();
                            this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt...');
                        } else {
                            // Try to load Face API in background
                            await this.loadFaceAPI();

                            // Check if Face API loaded successfully
                            if (window.faceapi) {
                                this.startFaceDetection();
                                this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt...');
                            } else {
                                console.warn('Face API not available, using fallback detection');
                                this.startFaceDetection();
                                this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt (chế độ cơ bản)...');
                            }
                        }
                    }, 1000); // Small delay to ensure video is fully loaded
                };

                // Backup: Start face detection immediately if video is already loaded
                if (video.readyState >= 2) {
                    setTimeout(async () => {
                        // Check if Face API is already loaded from template
                        if (window.faceapi && this.areModelsLoaded()) {
                            this.startFaceDetection();
                            this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt...');
                        } else if (window.faceapi && !this.areModelsLoaded()) {
                            await this.loadFaceAPIModels();
                            this.startFaceDetection();
                            this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt...');
                        } else {
                            // Try to load Face API in background
                            await this.loadFaceAPI();

                            // Check if Face API loaded successfully
                            if (window.faceapi) {
                                this.startFaceDetection();
                                this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt...');
                            } else {
                                console.warn('Face API not available, using fallback detection');
                                this.startFaceDetection();
                                this.updateFaceStatus('detecting', 'fas fa-search', 'Đang phát hiện khuôn mặt (chế độ cơ bản)...');
                            }
                        }
                    }, 1000);
                }
            } else {
                throw new Error('Video element not found');
            }
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.state.cameraActive = false;
            this.state.cameraStatus = 'Lỗi camera';

            // Provide detailed error messages based on error type
            let errorMessage = 'Không thể truy cập camera. ';

            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMessage += 'Quyền truy cập camera bị từ chối. ';
                errorMessage += 'Vui lòng:\n';
                errorMessage += '1. Click vào biểu tượng camera trên thanh địa chỉ trình duyệt\n';
                errorMessage += '2. Chọn "Cho phép" để cấp quyền truy cập camera\n';
                errorMessage += '3. Làm mới trang và thử lại';
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                errorMessage += 'Không tìm thấy camera. ';
                errorMessage += 'Vui lòng kiểm tra:\n';
                errorMessage += '1. Camera đã được kết nối\n';
                errorMessage += '2. Không có ứng dụng khác đang sử dụng camera\n';
                errorMessage += '3. Thử lại sau khi đóng các ứng dụng khác';
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                errorMessage += 'Camera đang được sử dụng bởi ứng dụng khác. ';
                errorMessage += 'Vui lòng:\n';
                errorMessage += '1. Đóng các ứng dụng đang sử dụng camera (Zoom, Teams, Skype, etc.)\n';
                errorMessage += '2. Làm mới trang và thử lại';
            } else if (error.name === 'OverconstrainedError' || error.name === 'ConstraintNotSatisfiedError') {
                errorMessage += 'Camera không hỗ trợ yêu cầu. ';
                errorMessage += 'Vui lòng thử lại hoặc sử dụng camera khác.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage += 'Trình duyệt không hỗ trợ truy cập camera. ';
                errorMessage += 'Vui lòng sử dụng trình duyệt hiện đại (Chrome, Firefox, Edge, Safari).';
            } else if (error.message && error.message.includes('HTTPS')) {
                errorMessage += 'Camera chỉ hoạt động trên HTTPS hoặc localhost. ';
                errorMessage += 'Vui lòng truy cập qua HTTPS hoặc localhost.';
            } else {
                errorMessage += 'Vui lòng kiểm tra quyền truy cập và thử lại.';
                if (error.message) {
                    errorMessage += `\n\nChi tiết lỗi: ${error.message}`;
                }
            }

            this.state.cameraError = errorMessage;

            // Show error notification
            this.showModal('Lỗi Camera', errorMessage);
        }
    }

    async loadFaceAPI() {
        if (window.faceapi) {
            return;
        }

        try {
            console.log('Face API not found, trying to load...');

            // Check if Face API is already loaded from CDN in template
            if (window.faceapi) {
                console.log('Face API loaded from template CDN');
                return;
            }

            // Try multiple CDN sources for better reliability
            const cdnSources = this.constructor.CONFIG.FACE_API.CDN_SOURCES;

            let loadSuccess = false;
            let lastError = null;

            for (const cdnUrl of cdnSources) {
                try {
                    console.log(`Trying CDN: ${cdnUrl}`);
                    await Promise.race([
                        this.loadScript(cdnUrl),
                        new Promise((_, reject) => setTimeout(() => reject(new Error('Script load timeout')), this.constructor.CONFIG.FACE_API.TIMEOUTS.SCRIPT_LOAD))
                    ]);

                    // Wait for script to initialize
                    await new Promise(resolve => setTimeout(resolve, this.constructor.CONFIG.FACE_API.TIMEOUTS.INITIALIZATION));

                    if (window.faceapi) {
                        loadSuccess = true;
                        console.log(`Face API loaded from: ${cdnUrl}`);
                        break;
                    }
                } catch (error) {
                    console.warn(`Failed to load from ${cdnUrl}:`, error);
                    lastError = error;
                    continue;
                }
            }

            if (!loadSuccess || !window.faceapi) {
                console.warn('All CDNs failed, trying local fallback...');
                await this.loadFaceAPILocal();

                if (!window.faceapi) {
                    throw new Error(`Face API not available after trying all CDNs and local fallback. Last error: ${lastError?.message || 'Unknown'}`);
                }
            }

            // Load models with better error handling
            const modelUrls = this.constructor.CONFIG.FACE_API.MODEL_SOURCES;

            let modelsLoaded = false;
            let modelError = null;

            for (const modelUrl of modelUrls) {
                try {
                    console.log(`Loading models from: ${modelUrl}`);
                    await Promise.race([
                        Promise.all([
                            window.faceapi.nets.tinyFaceDetector.loadFromUri(modelUrl),
                            window.faceapi.nets.faceLandmark68Net.loadFromUri(modelUrl),
                            window.faceapi.nets.faceExpressionNet.loadFromUri(modelUrl)
                        ]),
                        new Promise((_, reject) => setTimeout(() => reject(new Error('Model load timeout')), this.constructor.CONFIG.FACE_API.TIMEOUTS.MODEL_LOAD))
                    ]);
                    modelsLoaded = true;
                    console.log(`Models loaded from: ${modelUrl}`);
                    break;
                } catch (error) {
                    console.warn(`Failed to load models from ${modelUrl}:`, error);
                    modelError = error;
                    continue;
                }
            }

            if (!modelsLoaded) {
                console.warn('All CDN model sources failed, trying local fallback...');
                await this.loadFaceAPIModelsLocal();

                if (!this.areModelsLoaded()) {
                    throw new Error(`Models not loaded from CDN or local. Last error: ${modelError?.message || 'Unknown'}`);
                }
            }

            // Wait for models to be fully initialized
            await new Promise(resolve => setTimeout(resolve, this.constructor.CONFIG.FACE_API.TIMEOUTS.INITIALIZATION));

            // Verify models are ready
            if (!this.areModelsLoaded()) {
                throw new Error('Models not properly loaded');
            }

            console.log('Face API and models loaded successfully');
        } catch (error) {
            console.error('Error loading Face API:', error);
            // Don't throw error, just log it and let fallback methods handle detection
            console.warn('Face API failed to load, will use fallback detection methods');
        }
    }

    async loadFaceAPIModels() {
        try {
            console.log('Loading Face API models...');

            // Load models with better error handling
            const modelUrls = this.constructor.CONFIG.FACE_API.MODEL_SOURCES;

            let modelsLoaded = false;
            let modelError = null;

            for (const modelUrl of modelUrls) {
                try {
                    console.log(`Loading models from: ${modelUrl}`);
                    await Promise.race([
                        Promise.all([
                            window.faceapi.nets.tinyFaceDetector.loadFromUri(modelUrl),
                            window.faceapi.nets.faceLandmark68Net.loadFromUri(modelUrl),
                            window.faceapi.nets.faceExpressionNet.loadFromUri(modelUrl)
                        ]),
                        new Promise((_, reject) => setTimeout(() => reject(new Error('Model load timeout')), this.constructor.CONFIG.FACE_API.TIMEOUTS.MODEL_LOAD))
                    ]);
                    modelsLoaded = true;
                    console.log(`Models loaded from: ${modelUrl}`);
                    break;
                } catch (error) {
                    console.warn(`Failed to load models from ${modelUrl}:`, error);
                    modelError = error;
                    continue;
                }
            }

            if (!modelsLoaded) {
                console.warn('All CDN model sources failed, trying local fallback...');
                await this.loadFaceAPIModelsLocal();

                if (!this.areModelsLoaded()) {
                    throw new Error(`Models not loaded from CDN or local. Last error: ${modelError?.message || 'Unknown'}`);
                }
            }

            // Wait for models to be fully initialized
            await new Promise(resolve => setTimeout(resolve, this.constructor.CONFIG.FACE_API.TIMEOUTS.INITIALIZATION));

            // Verify models are ready
            if (!this.areModelsLoaded()) {
                throw new Error('Models not properly loaded');
            }

            console.log('Face API models loaded successfully');
        } catch (error) {
            console.error('Error loading Face API models:', error);
            throw error;
        }
    }

    async loadFaceAPIModelsLocal() {
        try {
            console.log('Trying to load Face API models from local assets...');

            // Try to load models from local assets
            const localModelPaths = [
                '/web/static/lib/face-api/models',
                '/static/lib/face-api/models',
                '/models'
            ];

            for (const localModelPath of localModelPaths) {
                try {
                    await Promise.all([
                        window.faceapi.nets.tinyFaceDetector.loadFromUri(localModelPath),
                        window.faceapi.nets.faceLandmark68Net.loadFromUri(localModelPath),
                        window.faceapi.nets.faceExpressionNet.loadFromUri(localModelPath)
                    ]);
                    console.log(`Models loaded from local: ${localModelPath}`);
                    return;
                } catch (error) {
                    console.warn(`Failed to load models from local path ${localModelPath}:`, error);
                    continue;
                }
            }

            console.warn('Local models not found, will use fallback detection');
        } catch (error) {
            console.warn('Error loading local models:', error);
        }
    }

    async loadFaceAPILocal() {
        try {
            console.log('Trying to load Face API from local assets...');

            // Try to load from local assets
            const localPaths = this.constructor.CONFIG.FACE_API.LOCAL_PATHS;

            for (const localPath of localPaths) {
                try {
                    await this.loadScript(localPath);
                    if (window.faceapi) {
                        console.log(`Face API loaded from local: ${localPath}`);
                        return;
                    }
                } catch (error) {
                    console.warn(`Failed to load from local path ${localPath}:`, error);
                    continue;
                }
            }

            console.warn('Local Face API not found, will use fallback detection');
        } catch (error) {
            console.warn('Error loading local Face API:', error);
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Check if script already exists
            const existingScript = document.querySelector(`script[src="${src}"]`);
            if (existingScript) {
                console.log(`Script already loaded: ${src}`);
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            script.crossOrigin = 'anonymous';
            script.type = 'text/javascript';

            script.onload = () => {
                console.log(`Script loaded successfully: ${src}`);
                resolve();
            };

            script.onerror = (error) => {
                console.error(`Failed to load script: ${src}`, error);
                // Remove failed script
                if (script.parentNode) {
                    script.parentNode.removeChild(script);
                }
                reject(new Error(`Failed to load script: ${src}`));
            };

            // Add timeout
            const timeoutId = setTimeout(() => {
                console.error(`Script load timeout: ${src}`);
                if (script.parentNode) {
                    script.parentNode.removeChild(script);
                }
                reject(new Error(`Script load timeout: ${src}`));
            }, 8000);

            // Clear timeout on successful load
            const originalOnload = script.onload;
            script.onload = () => {
                clearTimeout(timeoutId);
                originalOnload();
            };

            document.head.appendChild(script);
        });
    }

    stopCamera() {
        this.state.cameraActive = false;
        this.state.cameraError = '';
        this.state.cameraStatus = 'Camera đã tắt';
        this.stopFaceDetection();

        if (this.state._mediaStream) {
            this.state._mediaStream.getTracks().forEach(track => track.stop());
            this.state._mediaStream = null;
        }

        const video = document.getElementById('ekycVideoPreview');
        if (video) {
            video.srcObject = null;
        }

    }

    captureImage(isAutoCapture = false) {
        if (!this.state.cameraActive || this.isAllImagesCaptured()) return;

        try {
            const video = document.getElementById('ekycVideoPreview');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);

            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            this.state.capturedImages.push(imageData);
            this.state.capturedImageTypes.push(this.state.currentCapturePhase);

            // Update last capture time for auto-capture
            this.state.lastCaptureTime = Date.now();

            // Get current phase info
            const currentPhase = this.state.currentCapturePhase;
            const currentCount = this.getCapturedCount(currentPhase);
            const requiredCount = this.state.captureRequirements[currentPhase];

            // Show capture feedback
            this.updateCameraInstructions(`Chụp ${this.getPhaseName(currentPhase)} thành công! (${currentCount}/${requiredCount})`);

            // Check if current phase is completed
            if (currentCount >= requiredCount) {
                this.updateCapturePhase();

                if (this.isAllImagesCaptured()) {
                    this.state.cameraInstructions = 'Hoàn thành chụp ảnh! Đang tự động xác thực eKYC...';
                    this.stopFaceDetection();
                    this.state.cameraStatus = 'Đang tự động xác thực eKYC...';

                    // Auto-verify eKYC after a short delay
                    setTimeout(() => {
                        this.processEkycVerification();
                    }, 2000); // Wait 2 seconds before auto-verification
                } else {
                    // Move to next phase
                    const nextPhase = this.state.currentCapturePhase;
                    this.updateCameraInstructions(`Chuyển sang chụp ${this.getPhaseName(nextPhase)}. Vui lòng điều chỉnh khuôn mặt.`);
                }
            }

            // Reset perfect face timer for next capture
            this.state.perfectFaceStartTime = 0;

        } catch (error) {
            console.error('Error capturing image:', error);
            this.showModal('Lỗi', 'Xác thực thất bại. Vui lòng thử lại.');
        }
    }

    removeCapturedImage(index) {
        const removedType = this.state.capturedImageTypes[index];
        this.state.capturedImages.splice(index, 1);
        this.state.capturedImageTypes.splice(index, 1);

        this.state.lastCaptureTime = 0; // Reset capture time to allow immediate re-capture
        this.state.perfectFaceStartTime = 0; // Reset perfect face timer

        // Update current phase if needed
        this.updateCapturePhase();

        this.updateCameraInstructions(`Đã xóa ảnh ${this.getPhaseName(removedType)}. Vui lòng chụp lại.`);
    }

    async processEkycVerification() {
        if (!this.isAllImagesCaptured()) {
            const frontCount = this.getCapturedCount('front');
            const leftCount = this.getCapturedCount('left');
            const rightCount = this.getCapturedCount('right');

            this.showModal('Thiếu ảnh',
                `Vui lòng chụp đủ ảnh theo yêu cầu:\n` +
                `- Chỉnh diện: ${frontCount}/${this.state.captureRequirements.front}\n` +
                `- Góc trái: ${leftCount}/${this.state.captureRequirements.left}\n` +
                `- Góc phải: ${rightCount}/${this.state.captureRequirements.right}`
            );
            return;
        }

        this.state.isProcessing = true;
        this.state.cameraStatus = 'Đang xử lý xác thực...';

        try {
            const formData = new FormData();

            // Add CCCD front image
            formData.append('frontID', this.state.ekycFiles.front);

            // Add CCCD back image for full OCR (issue_date, issue_place)
            if (this.state.ekycFiles.back) {
                formData.append('backID', this.state.ekycFiles.back);
            }

            // Add 7 portrait images
            for (let i = 0; i < this.state.capturedImages.length; i++) {
                const imageFile = this.dataURLtoFile(this.state.capturedImages[i], `portrait_${i + 1}.jpg`);

                formData.append('portraitImages', imageFile);
            }


            console.log('📁 FormData contents:');
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}:`, value instanceof File ? `${value.name} (${value.type}, ${value.size} bytes)` : value);
            }

            const response = await fetch('/api/ekyc-process', {
                method: 'POST',
                body: formData
            });



            // Check if response is OK before parsing JSON
            if (!response.ok) {
                let errorMessage = `Lỗi server: ${response.status} ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorData.message || errorMessage;
                } catch (e) {
                    const errorText = await response.text();
                    if (errorText) {
                        errorMessage = errorText.substring(0, 500); // Limit error message length
                    }
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();


            if (result.success) {
                // Success - update form with OCR data FIRST

                this.updateFormWithEkycResult(result);

                // Force immediate render to show updated data
                this.render();

                // Wait a bit for render to complete
                await new Promise(resolve => setTimeout(resolve, 100));

                // Set eKYC result state
                this.state.ekycResult = {
                    success: true,
                    message: 'Xác thực eKYC thành công! Thông tin đã được cập nhật tự động.'
                };

                // Get list of updated fields with their values
                const updatedFieldsList = this.getUpdatedFieldsList(result);

                // Build simplified success message
                let successMessage = '<div style="text-align: left;">';
                successMessage += '<p style="margin-bottom: 15px; font-weight: 600;">Xác thực eKYC thành công!</p>';

                if (updatedFieldsList.length > 0) {
                    successMessage += `<p style="margin-bottom: 10px;">Đã tự động điền <strong>${updatedFieldsList.length}</strong> trường thông tin.</p>`;
                    successMessage += '<p style="color: #28a745; font-weight: 600;"><i class="fas fa-check-circle"></i> Vui lòng kiểm tra và hoàn thiện các thông tin còn lại.</p>';
                } else {
                    successMessage += '<p style="color: #ffc107;">Không tìm thấy dữ liệu OCR để điền tự động. Vui lòng nhập thủ công.</p>';
                }

                successMessage += '</div>';

                // this.showModal('Thành công', successMessage);

                // Close eKYC modal after 5 seconds to give user time to see the data
                setTimeout(() => {
                    this.closeEkycModal();
                    // Force render again after closing modal to ensure form data is visible
                    setTimeout(() => {
                        this.render();
                    }, 200);
                }, 5000);

            } else {
                // Failed
                const errorMsg = result.message || result.error || 'Xác thực eKYC thất bại. Vui lòng thử lại.';
                this.state.ekycResult = {
                    success: false,
                    error: errorMsg
                };

                // Show error message for auto-verification
                this.showModal('Lỗi', errorMsg);
            }

        } catch (error) {
            console.error('Error during eKYC verification:', error);

            // Provide detailed error message based on error type
            let errorMessage = 'Lỗi kết nối đến server eKYC. ';

            if (error instanceof TypeError) {
                if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
                    errorMessage = 'Không thể kết nối đến server eKYC. Vui lòng:\n' +
                        '1. Kiểm tra kết nối mạng\n' +
                        '2. Kiểm tra cấu hình eKYC trong Odoo Settings\n' +
                        '3. Thử lại sau vài giây';
                } else {
                    errorMessage = `Lỗi hệ thống: ${error.message}`;
                }
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage += 'Vui lòng thử lại sau.';
            }

            this.state.ekycResult = {
                success: false,
                error: errorMessage
            };

            this.showModal('Lỗi', errorMessage);
        } finally {
            this.state.isProcessing = false;
            this.state.cameraStatus = 'Camera đã sẵn sàng';
        }
    }

    updateFormWithEkycResult(result) {


        // Extract OCR data from result
        // VNPT eKYC returns: { success: true, data: { ocr: {...}, face_compare: {...}, face_liveness: {...} } }
        // OR: { success: true, ocr: {...}, face_compare: {...}, face_liveness: {...} }
        let ocrData = null;

        // Try different paths to find OCR data
        if (result.data && result.data.ocr) {
            // Most common structure: result.data.ocr
            ocrData = result.data.ocr;

        } else if (result.ocr) {
            // Alternative structure: result.ocr
            ocrData = result.ocr;

        } else if (result.data && typeof result.data === 'object') {
            // Check if data itself is OCR data
            const excludedKeys = ['success', 'message', 'error', 'face_compare', 'face_liveness'];
            const hasOcrFields = ['id', 'name', 'birth_day', 'gender', 'nationality'].some(key => key in result.data);
            if (hasOcrFields) {
                ocrData = result.data;

            }
        }

        // Handle nested structure: sometimes OCR data is in result.ocr.object or result.data.ocr.object
        if (ocrData && ocrData.object) {
            ocrData = ocrData.object;
        }

        // VNPT OCR Full (combined) usually returns { front: {...}, back: {...} }
        // Unified handling: merge front/back sub-objects into the main ocrData object
        if (ocrData && (ocrData.front || ocrData.back)) {
            console.log('Merging nested front/back OCR objects...');
            const merged = { ...ocrData };
            if (ocrData.front) Object.assign(merged, ocrData.front);
            if (ocrData.back) Object.assign(merged, ocrData.back);
            ocrData = merged;
        }

        // Log all available OCR fields for debugging
        if (ocrData) {


        } else {
            console.warn('No OCR data found in result. Available keys:', Object.keys(result));
            if (result.data) {
                console.warn('result.data keys:', Object.keys(result.data));
            }
            this.showModal('Cảnh báo', 'Không tìm thấy dữ liệu OCR trong kết quả eKYC. Vui lòng kiểm tra lại.');
            return;
        }

        // Map VNPT eKYC OCR fields to form fields
        // Based on actual VNPT API response structure:
        // - id: "046204003748"
        // - name: "VÕ VĂN NHÂN"
        // - birth_day: "21/02/2004" (format: DD/MM/YYYY)
        // - gender: "Nam" or "Nữ"
        // - nationality: "Việt Nam"
        // - issue_date: "-" or date string
        // - issue_place: "-" or place string
        // - recent_location: address string
        // - origin_location: hometown string
        const ocrFields = {
            // ID number - VNPT uses: id
            idNumber: ocrData.id || ocrData.idNumber || ocrData.id_number || ocrData.cmnd || ocrData.cccd || ocrData.so_cmnd || ocrData.so_cccd,
            // Full name - VNPT uses: name
            fullName: ocrData.name || ocrData.fullName || ocrData.full_name || ocrData.ho_ten || ocrData.ho_va_ten || ocrData.ten,
            // Date of birth - VNPT uses: birth_day (format: DD/MM/YYYY)
            dob: ocrData.birth_day || ocrData.dob || ocrData.date_of_birth || ocrData.birth_date || ocrData.ngay_sinh || ocrData.ngay_thang_nam_sinh || ocrData.birthday,
            // Gender - VNPT uses: gender ("Nam" or "Nữ")
            gender: ocrData.gender || ocrData.gioi_tinh || ocrData.sex || ocrData.gioiTinh,
            // Nationality - VNPT uses: nationality
            nationality: ocrData.nationality || ocrData.quoc_tich || ocrData.country || ocrData.quoc_gia || ocrData.quocTich,
            // Address - VNPT uses: recent_location
            address: ocrData.recent_location || ocrData.address || ocrData.dia_chi || ocrData.permanent_address || ocrData.ho_khau_thuong_tru || ocrData.diaChi,
            // Place of birth - from address or origin_location
            place_of_birth: ocrData.origin_location || ocrData.place_of_birth || ocrData.noi_sinh || ocrData.birth_place || ocrData.noi_sinh_quan_huyen || ocrData.noiSinh,
            // Place of origin / Hometown - VNPT uses: origin_location
            place_of_origin: ocrData.origin_location || ocrData.place_of_origin || ocrData.que_quan || ocrData.hometown || ocrData.nguyen_quan || ocrData.queQuan,
            // Issue date - VNPT uses: issue_date (can be "-" if not available)
            issue_date: (ocrData.issue_date && ocrData.issue_date !== '-') ? ocrData.issue_date : (ocrData.init_date || ocrData.ngay_cap || ocrData.ngay_ky || ocrData.date_of_issue || ocrData.ngayCap),
            // Issue place - VNPT uses: issue_place (can be "-" if not available)
            // Also check post_code for city/district information that might indicate issue place
            issue_place: (() => {
                // First try direct issue_place field (if not "-")
                if (ocrData.issue_place && ocrData.issue_place !== '-') {
                    return ocrData.issue_place;
                }
                // Try alternative field names
                const altFields = [
                    ocrData.noi_cap,
                    ocrData.place_of_issue,
                    ocrData.co_quan_cap,
                    ocrData.issued_by,
                    ocrData.noiCap,
                    ocrData.coQuanCap,
                    ocrData.place_of_birth // Fallback
                ];
                for (const field of altFields) {
                    if (field && field !== '-' && field !== '') {
                        return field;
                    }
                }

                return null;
            })(),
        };

        // Log which fields were found

        const foundFields = Object.keys(ocrFields).filter(key => ocrFields[key]);
        const missingFields = Object.keys(ocrFields).filter(key => !ocrFields[key]);


        // Mark eKYC as verified in status info
        if (this.state.statusInfo) {
            this.state.statusInfo.ekyc_verified = true;
        }

        const updatedFields = [];

        // Update form fields with OCR data
        if (ocrFields.idNumber) {
            this.state.formData.id_number = ocrFields.idNumber;
            updatedFields.push('Số CCCD');
        }

        if (ocrFields.fullName) {
            this.state.formData.name = ocrFields.fullName;
            updatedFields.push('Họ và tên');
        }

        if (ocrFields.dob) {
            this.state.formData.birth_date = this.formatDateForInput(ocrFields.dob);
            updatedFields.push('Ngày sinh');
        }

        if (ocrFields.gender) {
            const genderValue = ocrFields.gender.toString().toLowerCase();
            if (genderValue.includes('nam') || genderValue.includes('male') || genderValue === 'm') {
                this.state.formData.gender = 'male';
            } else if (genderValue.includes('nữ') || genderValue.includes('female') || genderValue === 'f') {
                this.state.formData.gender = 'female';
            }
            updatedFields.push('Giới tính');
        }

        if (ocrFields.nationality) {
            const countryId = this.findCountryIdByName(ocrFields.nationality);
            if (countryId) {
                this.state.formData.nationality = String(countryId);
                updatedFields.push('Quốc tịch');
            }
        }

        if (ocrFields.issue_date) {
            this.state.formData.id_issue_date = this.formatDateForInput(ocrFields.issue_date);
            updatedFields.push('Ngày cấp');
        }

        // Logic for formatting issue place (Nơi cấp)
        // Ensure we don't have leading commas if district is missing
        if (ocrFields.issue_place) {
            let placeObj = ocrFields.issue_place;
            // Handle if issue_place is already a string
            if (typeof placeObj === 'string') {
                this.state.formData.id_issue_place = placeObj.trim();
            } else {
                // If it's undefined or complex object, rely on extracting it
                // Re-use logic for extracting place string from getUpdatedFieldsList if needed
                // But typically it's passed as a string here from the ocrFields mapping
                this.state.formData.id_issue_place = String(placeObj).trim();
            }
            updatedFields.push('Nơi cấp');

        } else {
            // Try to construct from logic similar to getUpdatedFieldsList
            const extractionLogic = () => {
                const data = ocrData;
                if (data.issue_place && data.issue_place !== '-') return data.issue_place;

                const altFields = [data.noi_cap, data.place_of_issue, data.co_quan_cap, data.issued_by, data.noiCap, data.coQuanCap];
                for (const f of altFields) {
                    if (f && f !== '-') return f;
                }

                return null;
            };

            const extractedPlace = extractionLogic();
            if (extractedPlace) {
                this.state.formData.id_issue_place = extractedPlace;
                updatedFields.push('Nơi cấp');

            } else {
                console.warn('issue_place not found even after extraction attempt');
            }
        }

        // Propagate address-related data for AddressInfoWidget via sessionStorage
        try {
            const addressPayload = {};
            if (ocrFields.address) {
                addressPayload.permanent_address = ocrFields.address;
            }
            if (ocrFields.place_of_birth) {
                addressPayload.birth_place = ocrFields.place_of_birth;
            }
            if (ocrFields.place_of_origin) {
                addressPayload.hometown = ocrFields.place_of_origin;
            }
            if (Object.keys(addressPayload).length > 0) {
                const existingRaw = sessionStorage.getItem('addressInfoData');
                let merged = {};
                if (existingRaw) {
                    try { merged = JSON.parse(existingRaw) || {}; } catch (e) { merged = {}; }
                }
                const finalData = { ...merged, ...addressPayload };
                sessionStorage.setItem('addressInfoData', JSON.stringify(finalData));
                sessionStorage.setItem('addressInfoFromEkyc', 'true');

            }
        } catch (e) {
            console.warn('Failed to store eKYC address data to sessionStorage:', e);
        }

        // Save current form data to session storage with CCCD images
        const profileData = {
            ...this.state.formData,
            // Preserve CCCD images
            frontPreviewBase64: this.state.ekycFiles.frontPreview,
            backPreviewBase64: this.state.ekycFiles.backPreview
        };

        sessionStorage.setItem('personalProfileData', JSON.stringify(profileData));
        sessionStorage.setItem('personalProfileUserId', String(window.currentUserId || ''));


        // Force re-render multiple times to ensure data is displayed
        this.render();
        setTimeout(() => this.render(), 100);
        setTimeout(() => this.render(), 300);
    }

    getUpdatedFieldsCount(result) {
        // Helper method to count how many fields were updated
        const fieldsList = this.getUpdatedFieldsList(result);
        return fieldsList.length;
    }

    getUpdatedFieldsList(result) {
        // Helper method to get list of updated fields with their values
        let ocrData = null;

        // Extract OCR data from result
        if (result.data && result.data.ocr) {
            ocrData = result.data.ocr;
        } else if (result.ocr) {
            ocrData = result.ocr;
        } else if (result.data && typeof result.data === 'object') {
            const hasOcrFields = ['id', 'name', 'birth_day', 'gender', 'nationality'].some(key => key in result.data);
            if (hasOcrFields) {
                ocrData = result.data;
            }
        }

        if (ocrData && ocrData.object) {
            ocrData = ocrData.object;
        }

        // VNPT OCR Full (combined) usually returns { front: {...}, back: {...} }
        if (ocrData && (ocrData.front || ocrData.back)) {
            const merged = { ...ocrData };
            if (ocrData.front) Object.assign(merged, ocrData.front);
            if (ocrData.back) Object.assign(merged, ocrData.back);
            ocrData = merged;
        }

        if (!ocrData || Object.keys(ocrData).length === 0) {
            return [];
        }

        const fieldsList = [];

        // Map OCR fields to form fields with labels
        const fieldMappings = [
            {
                key: 'idNumber',
                label: 'Số CCCD',
                value: ocrData.id || ocrData.idNumber || ocrData.id_number || ocrData.cmnd || ocrData.cccd || ocrData.so_cmnd || ocrData.so_cccd
            },
            {
                key: 'fullName',
                label: 'Họ và tên',
                value: ocrData.name || ocrData.fullName || ocrData.full_name || ocrData.ho_ten || ocrData.ho_va_ten || ocrData.ten
            },
            {
                key: 'dob',
                label: 'Ngày sinh',
                value: ocrData.birth_day || ocrData.dob || ocrData.date_of_birth || ocrData.birth_date || ocrData.ngay_sinh || ocrData.ngay_thang_nam_sinh || ocrData.birthday
            },
            {
                key: 'gender',
                label: 'Giới tính',
                value: (() => {
                    const gender = ocrData.gender || ocrData.gioi_tinh || ocrData.sex || ocrData.gioiTinh;
                    if (gender) {
                        const genderValue = gender.toString().toLowerCase();
                        if (genderValue.includes('nam') || genderValue.includes('male') || genderValue === 'm') {
                            return 'Nam';
                        } else if (genderValue.includes('nữ') || genderValue.includes('female') || genderValue === 'f') {
                            return 'Nữ';
                        }
                        return gender;
                    }
                    return null;
                })()
            },
            {
                key: 'nationality',
                label: 'Quốc tịch',
                value: ocrData.nationality || ocrData.quoc_tich || ocrData.country || ocrData.quoc_gia || ocrData.quocTich
            },
            {
                key: 'issue_date',
                label: 'Ngày cấp',
                value: (() => {
                    const date = (ocrData.issue_date && ocrData.issue_date !== '-') ? ocrData.issue_date : (ocrData.init_date || ocrData.ngay_cap || ocrData.ngay_ky || ocrData.date_of_issue || ocrData.ngayCap);
                    return date && date !== '-' ? date : null;
                })()
            },
            {
                key: 'issue_place',
                label: 'Nơi cấp',
                value: (() => {
                    if (ocrData.issue_place && ocrData.issue_place !== '-') {
                        return ocrData.issue_place;
                    }
                    // Try alternative fields
                    const altFields = [ocrData.noi_cap, ocrData.place_of_issue, ocrData.co_quan_cap, ocrData.issued_by, ocrData.noiCap, ocrData.coQuanCap];
                    for (const field of altFields) {
                        if (field && field !== '-') {
                            return field;
                        }
                    }
                    // Try to extract from post_code
                    if (ocrData.post_code && Array.isArray(ocrData.post_code) && ocrData.post_code.length > 0) {
                        const addressInfo = ocrData.post_code[0];
                        if (addressInfo && addressInfo.city && Array.isArray(addressInfo.city) && addressInfo.city.length > 1) {
                            const cityName = addressInfo.city[1];
                            if (addressInfo.district && Array.isArray(addressInfo.district) && addressInfo.district.length > 1) {
                                const districtName = addressInfo.district[1];
                                if (districtName && typeof districtName === 'string' && districtName.trim() !== '') {
                                    return `${districtName.trim()}, ${cityName}`;
                                }
                            }
                            return cityName;
                        }
                    }
                    // Try new_post_code as fallback
                    if (ocrData.new_post_code && Array.isArray(ocrData.new_post_code) && ocrData.new_post_code.length > 0) {
                        const addressInfo = ocrData.new_post_code[0];
                        if (addressInfo && addressInfo.city && Array.isArray(addressInfo.city) && addressInfo.city.length > 1) {
                            const cityName = addressInfo.city[1];
                            if (addressInfo.district && Array.isArray(addressInfo.district) && addressInfo.district.length > 1) {
                                const districtName = addressInfo.district[1];
                                if (districtName && typeof districtName === 'string' && districtName.trim() !== '') {
                                    return `${districtName.trim()}, ${cityName}`;
                                }
                            }
                            return cityName;
                        }
                    }
                    return null;
                })()
            }
        ];

        // Only include fields that have values
        fieldMappings.forEach(field => {
            if (field.value && field.value !== '-' && field.value.toString().trim() !== '') {
                fieldsList.push({
                    label: field.label,
                    value: field.value.toString().trim()
                });
            }
        });

        return fieldsList;
    }

    dataURLtoFile(dataURL, filename) {
        const arr = dataURL.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }

        // Ensure correct mimetype for images
        const fileType = mime || 'image/jpeg';


        return new File([u8arr], filename, { type: fileType });
    }

    formatDateForInput(dateStr) {
        if (!dateStr || dateStr === '-') return '';

        const cleanDateStr = dateStr.toString().trim();


        // Handle simple DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
        // Also handles YYYY-MM-DD (ISO)
        const ddmmyyyy = /^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$/;
        const yyyymmdd = /^(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})$/;

        let day, month, year;
        let match = cleanDateStr.match(ddmmyyyy);

        if (match) {
            day = parseInt(match[1], 10);
            month = parseInt(match[2], 10);
            year = parseInt(match[3], 10);
        } else {
            match = cleanDateStr.match(yyyymmdd);
            if (match) {
                year = parseInt(match[1], 10);
                month = parseInt(match[2], 10);
                day = parseInt(match[3], 10);
            }
        }

        if (day && month && year) {
            // Validate ranges
            if (month < 1 || month > 12 || day < 1 || day > 31) {
                console.warn(`Invalid date values: ${day}/${month}/${year}`);
                return '';
            }

            const formattedDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            return formattedDate;
        }

        console.log(`Date format not recognized: "${cleanDateStr}"`);
        return '';
    }

    findCountryIdByName(countryName) {
        if (!countryName) {
            return '';
        }

        const normalizedName = countryName.trim().toLowerCase();

        // First, try to map Vietnamese names to English names
        const vietnameseToEnglish = {
            'việt nam': 'vietnam',
            'viet nam': 'vietnam',
            'cộng hòa xã hội chủ nghĩa việt nam': 'vietnam',
            'chxhcn việt nam': 'vietnam',
            'chxhcnvn': 'vietnam',
            'hoa kỳ': 'united states',
            'mỹ': 'united states',
            'anh': 'united kingdom',
            'nhật bản': 'japan',
            'nhật': 'japan',
            'trung quốc': 'china',
            'hàn quốc': 'south korea',
            'hàn': 'south korea',
            'thái lan': 'thailand',
            'thái': 'thailand',
            'đức': 'germany',
            'pháp': 'france',
            'ý': 'italy',
            'tây ban nha': 'spain',
            'hà lan': 'netherlands',
            'thụy sĩ': 'switzerland',
            'thụy điển': 'sweden'
        };

        // Convert Vietnamese to English if possible
        let searchName = normalizedName;
        if (vietnameseToEnglish[normalizedName]) {
            searchName = vietnameseToEnglish[normalizedName];
        }

        // Use mapping from database if available
        if (this.state.countryMapping) {
            // Try exact match first
            let countryId = this.state.countryMapping[searchName];
            if (countryId) {
                return countryId;
            }

            // Try original name
            countryId = this.state.countryMapping[countryName];
            if (countryId) {
                return countryId;
            }

            // Try partial matches
            for (const [key, id] of Object.entries(this.state.countryMapping)) {
                if (typeof key === 'string' && (searchName.includes(key) || key.includes(searchName))) {
                    return id;
                }
            }
        }

        // Fallback to hardcoded mapping if database mapping fails
        const fallbackMap = {
            // Vietnam variations
            'việt nam': '241', 'vietnam': '241', 'vn': '241', 'viet nam': '241', 'việt': '241', 'viet': '241',
            'cộng hòa xã hội chủ nghĩa việt nam': '241', 'chxhcn việt nam': '241', 'chxhcnvn': '241',

            // USA variations
            'hoa kỳ': '233', 'usa': '233', 'united states': '233', 'us': '233', 'mỹ': '233', 'america': '233',
            'united states of america': '233', 'u.s.a': '233', 'u.s': '233',

            // UK variations
            'anh': '231', 'uk': '231', 'united kingdom': '231', 'england': '231', 'great britain': '231',
            'britain': '231', 'gb': '231', 'u.k': '231',

            // Japan variations
            'nhật bản': '113', 'japan': '113', 'jp': '113', 'japanese': '113', 'nhật': '113',

            // China variations
            'trung quốc': '48', 'china': '48', 'cn': '48', 'chinese': '48',
            'people\'s republic of china': '48', 'prc': '48',

            // Korea variations
            'hàn quốc': '121', 'south korea': '121', 'korea': '121', 'kr': '121', 'republic of korea': '121',
            'rok': '121', 'hàn': '121',

            // Other common countries
            'singapore': '197', 'sg': '197',
            'thailand': '217', 'th': '217', 'thái lan': '217', 'thái': '217',
            'malaysia': '132', 'my': '132',
            'indonesia': '103', 'id': '103',
            'philippines': '174', 'ph': '174',
            'australia': '14', 'au': '14',
            'canada': '39', 'ca': '39',
            'germany': '82', 'de': '82', 'đức': '82',
            'france': '75', 'fr': '75', 'pháp': '75',
            'italy': '107', 'it': '107', 'ý': '107',
            'spain': '195', 'es': '195', 'tây ban nha': '195',
            'netherlands': '156', 'nl': '156', 'hà lan': '156',
            'switzerland': '207', 'ch': '207', 'thụy sĩ': '207',
            'sweden': '203', 'se': '203', 'thụy điển': '203'
        };

        // Try fallback exact match
        const fallbackId = fallbackMap[normalizedName];
        if (fallbackId) {
            return fallbackId;
        }

        // Try fallback partial matches
        for (const [key, id] of Object.entries(fallbackMap)) {
            if (normalizedName.includes(key) || key.includes(normalizedName)) {
                return id;
            }
        }

        // Special case for Vietnam (most common)
        if (normalizedName.includes('việt') || normalizedName.includes('viet')) {
            return '241';
        }

        return '';
    }



    removeFrontImage = () => {
        if (this.state.ekycFiles.frontPreview && this.state.ekycFiles.frontPreview.startsWith('blob:')) {
            URL.revokeObjectURL(this.state.ekycFiles.frontPreview);
        }
        this.state.ekycFiles.front = null;
        this.state.ekycFiles.frontPreview = null;
        this.updatePersonalProfileDataSession('frontPreviewBase64', '');
    }

    removeBackImage = () => {
        if (this.state.ekycFiles.backPreview && this.state.ekycFiles.backPreview.startsWith('blob:')) {
            URL.revokeObjectURL(this.state.ekycFiles.backPreview);
        }
        this.state.ekycFiles.back = null;
        this.state.ekycFiles.backPreview = null;
        this.updatePersonalProfileDataSession('backPreviewBase64', '');
    }



    // Hàm tiện ích cập nhật sessionStorage
    updatePersonalProfileDataSession(key, value) {
        let data = {};
        try {
            data = JSON.parse(sessionStorage.getItem('personalProfileData')) || {};
        } catch (e) { data = {}; }
        data[key] = value;
        sessionStorage.setItem('personalProfileData', JSON.stringify(data));
    }

    closeModal = () => {
        this.state.showModal = false;
    };

    // Face Detection Methods
    startFaceDetection() {
        if (this.state.faceDetectionInterval) {
            clearInterval(this.state.faceDetectionInterval);
        }
        // Do not start detection if already captured all required images
        if (this.isAllImagesCaptured()) {

            return;
        }

        // Ensure camera instructions are set for current phase when starting detection
        this.updateCameraInstructionsForPhase(this.state.currentCapturePhase);

        // Determine detection method based on available APIs
        const detectionMethod = this.getBestDetectionMethod();


        this.state.faceDetectionInterval = setInterval(() => {
            this.detectFace();
        }, this.constructor.CONFIG.DETECTION.INTERVAL); // Check every 1 second for better responsiveness
    }

    getBestDetectionMethod() {
        if (window.faceapi && this.areModelsLoaded()) {
            return 'Face API';
        } else {
            return 'Fallback (eKYC + Canvas)';
        }
    }

    areModelsLoaded() {
        if (!window.faceapi) {
            return false;
        }

        try {
            return window.faceapi.nets.tinyFaceDetector.isLoaded &&
                window.faceapi.nets.faceLandmark68Net.isLoaded &&
                window.faceapi.nets.faceExpressionNet.isLoaded;
        } catch (error) {
            console.warn('Error checking model status:', error);
            return false;
        }
    }

    stopFaceDetection() {
        if (this.state.faceDetectionInterval) {
            clearInterval(this.state.faceDetectionInterval);
            this.state.faceDetectionInterval = null;
        }
        this.state.faceStatus = null;

    }

    async detectFace() {
        const video = document.getElementById('ekycVideoPreview');
        if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) {
            // Set waiting status if video not ready
            this.updateFaceStatus('waiting', 'fas fa-clock', 'Chờ camera khởi động...');
            // Ensure camera instructions are set for current phase
            if (!this.state.cameraInstructions) {
                this.updateCameraInstructionsForPhase(this.state.currentCapturePhase);
            }
            return;
        }

        // If already captured all required images, stop further detection to speed up flow
        if (this.isAllImagesCaptured()) {
            this.stopFaceDetection();
            this.updateCameraInstructions('Đã chụp đủ ảnh theo yêu cầu. Sẵn sàng xác thực.');
            return;
        }

        try {
            // Create canvas to analyze video frame
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);

            // Try Face API first, fallback to eKYC API, then canvas detection
            if (window.faceapi) {
                try {
                    await this.detectFaceWithFaceAPI(canvas);
                } catch (faceApiError) {
                    console.warn('Face API detection failed, trying eKYC fallback:', faceApiError);
                    try {
                        await this.detectFaceWithEkycAPI(canvas);
                    } catch (ekycError) {
                        console.warn('eKYC API failed, using enhanced canvas detection:', ekycError);
                        this.detectFaceWithCanvas(canvas);
                    }
                }
            } else {
                // Face API not available, try eKYC API first
                try {
                    await this.detectFaceWithEkycAPI(canvas);
                } catch (ekycError) {
                    console.warn('eKYC API failed, using enhanced canvas detection:', ekycError);
                    this.detectFaceWithCanvas(canvas);
                }
            }
        } catch (error) {
            console.error('Error in face detection:', error);
            // Show helpful error message to user
            this.updateFaceStatus('error', 'fas fa-exclamation-triangle',
                'Lỗi phát hiện khuôn mặt - Vui lòng thử lại hoặc kiểm tra camera');
            // Final fallback to basic detection
            this.detectFaceWithCanvas(canvas);
        }
    }

    async detectFaceWithFaceAPI(canvas) {
        try {
            // Check if models are loaded before using
            if (!this.areModelsLoaded()) {
                console.warn('Face API models not loaded, using fallback detection');
                this.detectFaceWithCanvas(canvas);
                return;
            }

            // Use more lenient detection options
            const options = new window.faceapi.TinyFaceDetectorOptions({
                inputSize: this.constructor.CONFIG.DETECTION.INPUT_SIZE,
                scoreThreshold: this.constructor.CONFIG.DETECTION.SCORE_THRESHOLD
            });

            const detections = await window.faceapi.detectAllFaces(canvas, options)
                .withFaceLandmarks()
                .withFaceExpressions();



            if (detections.length === 0) {
                this.updateFaceStatus('no_face', 'fas fa-user-slash', 'Không tìm thấy khuôn mặt - Hãy di chuyển gần camera hơn và đảm bảo ánh sáng tốt');
                return;
            }

            if (detections.length > 1) {
                this.updateFaceStatus('multiple_faces', 'fas fa-users', 'Phát hiện nhiều khuôn mặt - Chỉ một người trong khung hình');
                return;
            }

            const detection = detections[0];
            const landmarks = detection.landmarks;

            // Check face position and orientation
            const isCentered = this.checkFaceCentered(landmarks, canvas);
            const orientation = this.checkFaceOrientation(landmarks);
            const isGoodSize = this.checkFaceSize(detection, canvas);

            const currentPhase = this.state.currentCapturePhase;
            const isCorrectOrientation = (orientation === currentPhase);



            // Only capture if orientation matches the required phase
            if (isGoodSize && isCentered && isCorrectOrientation) {
                const currentPhase = this.state.currentCapturePhase;
                const currentCount = this.getCapturedCount(currentPhase);
                const requiredCount = this.state.captureRequirements[currentPhase];

                // Track when face becomes perfect
                if (this.state.perfectFaceStartTime === 0) {
                    this.state.perfectFaceStartTime = Date.now();
                    console.log(`Face position perfect for ${currentPhase}, starting auto-capture timer...`);
                }

                const timeInPerfectPosition = Date.now() - this.state.perfectFaceStartTime;
                const remainingTime = Math.max(0, 2000 - timeInPerfectPosition);

                if (remainingTime > 0) {
                    this.updateFaceStatus('perfect', 'fas fa-check-circle',
                        `Giữ nguyên vị trí ${this.getPhaseName(currentPhase)} ${Math.ceil(remainingTime / 500)}s (${currentCount}/${requiredCount})`);
                } else {
                    this.updateFaceStatus('perfect', 'fas fa-check-circle',
                        `Đang chụp ${this.getPhaseName(currentPhase)}... (${currentCount}/${requiredCount})`);
                }

                // Auto-capture logic for eKYC API
                if (this.state.autoCaptureEnabled &&
                    currentCount < requiredCount &&
                    timeInPerfectPosition >= 500 &&
                    (!this.state.lastCaptureTime || Date.now() - this.state.lastCaptureTime > 500)) {

                    this.captureImage(true);
                    this.state.perfectFaceStartTime = 0; // Reset timer for next capture
                }
            } else {
                // Face not in perfect position, reset timer
                if (this.state.perfectFaceStartTime > 0) {
                    this.state.perfectFaceStartTime = 0;
                    console.log('Face moved out of perfect position (eKYC API), resetting timer');
                }

                let message = 'Điều chỉnh khuôn mặt: ';
                let detailedMessage = '';

                if (!isCentered) {
                    message += 'Căn giữa, ';
                    detailedMessage += '• Di chuyển khuôn mặt vào giữa khung\n';
                }
                if (!isCorrectOrientation) {
                    const instruction = this.getPhaseName(currentPhase);
                    message += instruction + ', ';
                    detailedMessage += `• Vui lòng ${instruction}\n`;
                }
                if (!isGoodSize) {
                    message += 'Tiến gần hơn';
                    detailedMessage += '• Di chuyển gần hơn';
                }

                this.updateFaceStatus('adjusting', 'fas fa-arrows-alt', message, detailedMessage);
            }

        } catch (error) {
            console.error('Face API detection error:', error);
            throw error;
        }
    }

    checkFaceCentered(landmarks, canvas) {
        const nose = landmarks.getNose()[3]; // Bottom of nose
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        const distanceFromCenter = Math.sqrt(
            Math.pow(nose.x - centerX, 2) + Math.pow(nose.y - centerY, 2)
        );

        // More lenient - allow face to be further from center
        const maxDistance = Math.min(canvas.width, canvas.height) * 0.25;
        return distanceFromCenter < maxDistance;
    }

    checkFaceOrientation(landmarks) {
        const nose = landmarks.getNose();
        const leftEye = landmarks.getLeftEye();
        const rightEye = landmarks.getRightEye();

        // Use nose tip (index 6 or 3)
        const noseTip = nose[6] || nose[3];

        // Use outer eye corners
        const leftEyeOuter = leftEye[0];
        const rightEyeOuter = rightEye[3];

        if (!noseTip || !leftEyeOuter || !rightEyeOuter) return 'unknown';

        const leftDist = Math.abs(noseTip._x - leftEyeOuter._x);
        const rightDist = Math.abs(noseTip._x - rightEyeOuter._x);

        if (rightDist === 0) return 'left';
        const ratio = leftDist / rightDist;



        // Ratios based on empirical testing with face-api.js
        if (ratio > 1.6) return 'right'; // Looking right = left side visible/larger distance
        if (ratio < 0.6) return 'left';  // Looking left = right side visible/larger distance

        // Also check if eyes are horizontal for 'front'
        const leftEyeY = leftEye.reduce((sum, p) => sum + p._y, 0) / leftEye.length;
        const rightEyeY = rightEye.reduce((sum, p) => sum + p._y, 0) / rightEye.length;
        if (Math.abs(leftEyeY - rightEyeY) > 25) return 'tilted';

        return 'front';
    }

    checkFaceSize(detection, canvas) {
        const faceArea = detection.detection.box.area;
        const canvasArea = canvas.width * canvas.height;
        const faceRatio = faceArea / canvasArea;

        // More lenient size requirements - face should be between 5% and 50% of canvas area
        return faceRatio >= 0.05 && faceRatio <= 0.5;
    }

    async detectFaceWithEkycAPI(canvas) {
        try {
            // Skip calling detection API if already captured all required images
            if (this.isAllImagesCaptured()) {
                console.log('⏭️ Skipping eKYC detection API: already have all required images');
                return;
            }
            // Convert canvas to blob
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
            const file = new File([blob], 'face_frame.jpg', { type: 'image/jpeg' });

            // Create form data
            const formData = new FormData();
            formData.append('frame', file);
            formData.append('expected', this.state.currentCapturePhase); // Expect current phase orientation

            // Call eKYC detection API
            const response = await fetch('/api/ekyc/detection', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();


                // Process detection result
                const currentPhase = this.state.currentCapturePhase;
                const currentCount = this.getCapturedCount(currentPhase);
                const requiredCount = this.state.captureRequirements[currentPhase];

                if (result.orientation === currentPhase && result.match) {
                    // Track when face becomes perfect
                    if (this.state.perfectFaceStartTime === 0) {
                        this.state.perfectFaceStartTime = Date.now();
                        console.log(`Face position perfect for ${currentPhase} (eKYC API), starting auto-capture timer...`);
                    }

                    const timeInPerfectPosition = Date.now() - this.state.perfectFaceStartTime;
                    const remainingTime = Math.max(0, 1000 - timeInPerfectPosition);

                    if (remainingTime > 0) {
                        this.updateFaceStatus('perfect', 'fas fa-check-circle',
                            `Bắt đầu chụp ${this.getPhaseName(currentPhase)} sau ${Math.ceil(remainingTime / 500)}s (${currentCount}/${requiredCount})`);
                    } else {
                        this.updateFaceStatus('perfect', 'fas fa-check-circle',
                            `Đang chụp ${this.getPhaseName(currentPhase)}... (${currentCount}/${requiredCount})`);
                    }

                    // Auto-capture logic for eKYC API
                    if (this.state.autoCaptureEnabled &&
                        currentCount < requiredCount &&
                        timeInPerfectPosition >= 1000 &&
                        (!this.state.lastCaptureTime || Date.now() - this.state.lastCaptureTime > 1000)) {

                        console.log(`Auto-capturing ${currentPhase} image due to perfect face position (eKYC API)`);
                        this.captureImage(true);
                        this.state.perfectFaceStartTime = 0; // Reset timer for next capture
                    }
                } else {
                    // Face not in perfect position, reset timer
                    if (this.state.perfectFaceStartTime > 0) {
                        this.state.perfectFaceStartTime = 0;
                        console.log(`Face moved out of perfect position for ${currentPhase} (eKYC API), resetting timer`);
                    }

                    // Set common instruction for all cases
                    this.updateCameraInstructions(`Đang chụp ${this.getPhaseName(currentPhase)}. Vui lòng điều chỉnh khuôn mặt.`);

                    if (result.orientation === 'left') {
                        this.updateFaceStatus('turn_right', 'fas fa-arrow-right', 'Quay sang phải', '• Quay mặt sang phải\n• Giữ nguyên vị trí khi quay');
                    } else if (result.orientation === 'right') {
                        this.updateFaceStatus('turn_left', 'fas fa-arrow-left', 'Quay sang trái', '• Quay mặt sang trái\n• Giữ nguyên vị trí khi quay');
                    } else {
                        this.updateFaceStatus('no_face', 'fas fa-user-slash', 'Không phát hiện khuôn mặt', '• Đặt khuôn mặt vào đúng vị trí\n• Đảm bảo ánh sáng đủ sáng');
                    }
                }
            } else {
                // Fallback to basic detection
                this.detectFaceWithCanvas(canvas);
            }
        } catch (error) {
            console.error('Error calling eKYC detection API:', error);
            // Fallback to basic detection
            this.detectFaceWithCanvas(canvas);
        }
    }

    detectFaceWithCanvas(canvas) {
        // Basic face detection using canvas analysis
        if (!canvas) {
            canvas = document.createElement('canvas');
            const video = document.getElementById('ekycVideoPreview');
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
        }

        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        // Simple skin tone detection
        let skinPixels = 0;
        let totalPixels = data.length / 4;

        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];

            // Basic skin tone detection
            if (r > 95 && g > 40 && b > 20 &&
                Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
                Math.abs(r - g) > 15 && r > g && r > b) {
                skinPixels++;
            }
        }

        const skinRatio = skinPixels / totalPixels;

        // Determine status based on skin tone ratio
        let status, icon, message, instructions;

        if (skinRatio < 0.1) {
            // Reset timer if face not detected
            if (this.state.perfectFaceStartTime > 0) {
                this.state.perfectFaceStartTime = 0;
                console.log('No face detected (Canvas), resetting timer');
            }
            status = 'no_face';
            icon = 'fas fa-user-slash';
            message = 'Không phát hiện khuôn mặt';
            instructions = '';
        } else if (skinRatio < 0.2) {
            // Reset timer if face too far
            if (this.state.perfectFaceStartTime > 0) {
                this.state.perfectFaceStartTime = 0;
                console.log('Face too far (Canvas), resetting timer');
            }
            status = 'too_far';
            icon = 'fas fa-arrows-alt-v';
            message = 'Khuôn mặt quá xa';
            instructions = 'Vui lòng tiến lại gần hơn';
        } else if (skinRatio > 0.6) {
            // Reset timer if face too close
            if (this.state.perfectFaceStartTime > 0) {
                this.state.perfectFaceStartTime = 0;
                console.log('Face too close (Canvas), resetting timer');
            }
            status = 'too_close';
            icon = 'fas fa-arrows-alt-v';
            message = 'Khuôn mặt quá gần';
            instructions = 'Vui lòng lùi ra xa hơn';
        } else {
            const currentPhase = this.state.currentCapturePhase;
            const currentCount = this.getCapturedCount(currentPhase);
            const requiredCount = this.state.captureRequirements[currentPhase];

            // Track when face becomes perfect
            if (this.state.perfectFaceStartTime === 0) {
                this.state.perfectFaceStartTime = Date.now();
                console.log(`Face position perfect for ${currentPhase} (Canvas), starting auto-capture timer...`);
            }

            const timeInPerfectPosition = Date.now() - this.state.perfectFaceStartTime;
            const remainingTime = Math.max(0, 2000 - timeInPerfectPosition);

            if (remainingTime > 0) {
                status = 'perfect';
                icon = 'fas fa-check-circle';
                message = `Giữ nguyên vị trí ${this.getPhaseName(currentPhase)}! Bắt đầu chụp sau ${Math.ceil(remainingTime / 1000)}s (${currentCount}/${requiredCount})`;
                instructions = `Giữ nguyên vị trí ${this.getPhaseName(currentPhase)}!`;
            } else {
                status = 'perfect';
                icon = 'fas fa-check-circle';
                message = `Đang chụp ${this.getPhaseName(currentPhase)}... (${currentCount}/${requiredCount})`;
                instructions = `Đang chụp ${this.getPhaseName(currentPhase)}...`;
            }

            // Auto-capture logic for canvas detection
            if (this.state.autoCaptureEnabled &&
                currentCount < requiredCount &&
                timeInPerfectPosition >= 2000 &&
                (!this.state.lastCaptureTime || Date.now() - this.state.lastCaptureTime > 2000)) {

                console.log(`Auto-capturing ${currentPhase} image due to perfect face position (Canvas)`);
                this.captureImage(true);
                this.state.perfectFaceStartTime = 0; // Reset timer for next capture
            }
        }

        // Only update if status changed
        if (!this.state.faceStatus || this.state.faceStatus.status !== status) {
            this.updateFaceStatus(status, icon, message);
            this.updateCameraInstructions(instructions);
        }
    }

    updateFaceStatus(status, icon, message, detailedMessage = '') {
        this.state.faceStatus = {
            status: status,
            icon: icon,
            message: message,
            detailedMessage: detailedMessage
        };
        console.log('👤 Face status updated:', status, message);
        if (detailedMessage) {

        }
    }

    getFaceFrameStyle() {
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const borderColor = isPerfect ? '#28a745' : '#ffffff';
        const backgroundColor = isPerfect ? 'rgba(40, 167, 69, 0.05)' : 'rgba(255, 255, 255, 0.05)';
        return `width: 100%; height: 100%; border: 2px solid ${borderColor}; border-radius: 50%; position: relative; transition: all 0.3s ease; background: ${backgroundColor}; box-shadow: 0 0 20px ${isPerfect ? 'rgba(40, 167, 69, 0.2)' : 'rgba(255, 255, 255, 0.2)'}; opacity: 0.8;`;
    }

    getCornerStyle(position) {
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const color = isPerfect ? '#28a745' : '#d32f2f';
        const size = '20px';
        const thickness = '3px';

        let style = `position: absolute; width: ${size}; height: ${size}; border: ${thickness} solid ${color}; transition: all 0.3s ease; opacity: 0.7;`;

        switch (position) {
            case 'top-left':
                style += 'top: -2px; left: -2px; border-right: none; border-bottom: none; border-radius: 20px 0 0 0;';
                break;
            case 'top-right':
                style += 'top: -2px; right: -2px; border-left: none; border-bottom: none; border-radius: 0 20px 0 0;';
                break;
            case 'bottom-left':
                style += 'bottom: -2px; left: -2px; border-right: none; border-top: none; border-radius: 0 0 0 20px;';
                break;
            case 'bottom-right':
                style += 'bottom: -2px; right: -2px; border-left: none; border-top: none; border-radius: 0 0 20px 0;';
                break;
        }

        return style;
    }

    getGuideLineStyle(type) {
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const color = isPerfect ? 'rgba(40, 167, 69, 0.6)' : 'rgba(211, 47, 47, 0.4)';

        if (type === 'horizontal') {
            return `position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: ${color}; transform: translateY(-50%); transition: all 0.3s ease;`;
        } else {
            return `position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: ${color}; transform: translateX(-50%); transition: all 0.3s ease;`;
        }
    }

    getFacePositionIndicatorStyle() {
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const color = isPerfect ? '#28a745' : '#d32f2f';
        return `position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 120px; height: 160px; border: 2px dashed ${color}; border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%; transition: all 0.3s ease; opacity: ${isPerfect ? '1' : '0.7'};`;
    }

    getProgressRingStyle() {
        return `position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;`;
    }

    getProgressRingFillStyle() {
        const progress = (this.state.capturedImages.length / 7) * 100;
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const color = isPerfect ? '#28a745' : '#ffffff';
        const circumference = 2 * Math.PI * 140;
        const strokeDasharray = circumference;
        const strokeDashoffset = circumference - (progress / 100) * circumference;

        return `stroke: ${color}; stroke-dasharray: ${strokeDasharray}; stroke-dashoffset: ${strokeDashoffset}; transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 0.5s ease;`;
    }

    getFacePositionIndicatorStyle() {
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const color = isPerfect ? '#28a745' : '#d32f2f';
        return `position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 200px; height: 200px; border: 2px dashed ${color}; border-radius: 50%; transition: all 0.3s ease; opacity: ${isPerfect ? '1' : '0.7'}; z-index: 2;`;
    }

    getCenterCrosshairStyle() {
        return `position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 20px; height: 20px; z-index: 3;`;
    }

    getFaceInstructionsStyle() {
        const isPerfect = this.state.faceStatus && this.state.faceStatus.status === 'perfect';
        const color = isPerfect ? '#28a745' : '#d32f2f';
        return `position: absolute; bottom: -40px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.8); color: white; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 500; border: 1px solid ${color}; transition: all 0.3s ease;`;
    }

    toString(value) {
        return String(value);
    }

    // Cleanup method
    willUnmount() {
        this.stopCamera();
        this.stopFaceDetection();
        if (this.state.ekycFiles.frontPreview && this.state.ekycFiles.frontPreview.startsWith('blob:')) {
            URL.revokeObjectURL(this.state.ekycFiles.frontPreview);
        }
        if (this.state.ekycFiles.backPreview && this.state.ekycFiles.backPreview.startsWith('blob:')) {
            URL.revokeObjectURL(this.state.ekycFiles.backPreview);
        }
    }
}

// Expose the component globally for the entrypoint to mount
Object.assign(window, { PersonalProfileWidget });

// Auto-mount when script is loaded
if (typeof owl !== 'undefined') {
    const widgetContainer = document.getElementById('personalProfileWidget');
    if (widgetContainer) {
        owl.mount(PersonalProfileWidget, widgetContainer);
    }
} 
