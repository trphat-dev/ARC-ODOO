/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportPurchaseContractWidget } from './report_purchase_contract_widget.js';

// Mount OWL widget when DOM is ready
function mountReportPurchaseContractWidget() {
    const container = document.getElementById('reportPurchaseContractWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportPurchaseContractWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportPurchaseContractWidget);
} else {
    // DOM already ready
    mountReportPurchaseContractWidget();
}