/** @odoo-module */

import { mount } from "@odoo/owl";
import { InvestorReportWidget } from './investor_report_widget.js';

// Mount OWL widget when DOM is ready
function mountInvestorReportWidget() {
    const container = document.getElementById('investorReportWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(InvestorReportWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountInvestorReportWidget);
} else {
    // DOM already ready
    mountInvestorReportWidget();
}