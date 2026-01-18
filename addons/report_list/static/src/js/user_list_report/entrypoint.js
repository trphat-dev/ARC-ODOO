/** @odoo-module */

import { mount } from "@odoo/owl";
import { UserListReportWidget } from './user_list_report_widget.js';

// Mount OWL widget when DOM is ready
function mountUserListReportWidget() {
    const container = document.getElementById('userListReportWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(UserListReportWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountUserListReportWidget);
} else {
    // DOM already ready
    mountUserListReportWidget();
}