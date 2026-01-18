/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportTransactionWidget } from './report_transaction_widget.js';

// Mount OWL widget when DOM is ready
function mountReportTransactionWidget() {
    const container = document.getElementById('reportTransactionWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportTransactionWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportTransactionWidget);
} else {
    // DOM already ready
    mountReportTransactionWidget();
}