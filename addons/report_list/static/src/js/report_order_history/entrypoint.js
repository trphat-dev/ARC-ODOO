/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportOrderHistoryWidget } from './report_order_history_widget.js';

// Mount OWL widget when DOM is ready
function mountReportOrderHistoryWidget() {
    const container = document.getElementById('reportOrderHistoryWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportOrderHistoryWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportOrderHistoryWidget);
} else {
    // DOM already ready
    mountReportOrderHistoryWidget();
}