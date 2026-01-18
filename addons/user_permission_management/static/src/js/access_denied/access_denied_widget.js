/** @odoo-module */

import { Component, xml, useState, onMounted } from "@odoo/owl";

export class AccessDeniedWidget extends Component {
    static props = {
        errorTitle: { type: String, optional: true },
        errorMessage: { type: String, optional: true },
        allowedTypes: { type: Array, optional: true },
    };
    
    setup() {
        this.state = useState({
            errorTitle: this.props.errorTitle || 'Không có quyền truy cập',
            errorMessage: this.props.errorMessage || 'Bạn không có quyền truy cập trang này.',
            allowedTypes: this.props.allowedTypes || [],
        });
    }

    goToDashboard() {
        window.location.href = '/fund-management-dashboard';
    }

    goBack() {
        window.history.back();
    }

    static template = xml`
        <div class="access-denied-container">
            <div class="access-denied-content">         
                <!-- Error Content -->
                <div class="error-content">
                    <div class="error-icon-wrapper">
                        <i class="fas fa-shield-alt error-icon"></i>
                    </div>
                    
                    <h1 class="error-title" t-esc="state.errorTitle"/>
                    
                    <p class="error-description" t-esc="state.errorMessage"/>
                    
                    <!-- Action Buttons -->
                    <div class="action-buttons">
                        <button 
                            type="button" 
                            class="btn-secondary-action" 
                            t-on-click="goBack">
                            <i class="fas fa-arrow-left me-2"></i>
                            <span>Quay Lại</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

