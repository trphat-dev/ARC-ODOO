/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportBalanceWidget } from './report_balance_widget.js';

// Mount OWL widget when DOM is ready
function mountReportBalanceWidget() {
    const container = document.getElementById('reportBalanceWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportBalanceWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportBalanceWidget);
} else {
    // DOM already ready
    mountReportBalanceWidget();
}