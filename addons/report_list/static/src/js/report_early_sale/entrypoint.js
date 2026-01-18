/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportEarlySaleWidget } from './report_early_sale_widget.js';

// Mount OWL widget when DOM is ready
function mountReportEarlySaleWidget() {
    const container = document.getElementById('reportEarlySaleWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportEarlySaleWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportEarlySaleWidget);
} else {
    // DOM already ready
    mountReportEarlySaleWidget();
}