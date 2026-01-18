/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportSellContractWidget } from './report_sell_contract_widget.js';

// Mount OWL widget when DOM is ready
function mountReportSellContractWidget() {
    const container = document.getElementById('reportSellContractWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportSellContractWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportSellContractWidget);
} else {
    // DOM already ready
    mountReportSellContractWidget();
}