/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportContractSummaryWidget } from './report_contract_summary_widget.js';

// Mount OWL widget when DOM is ready
function mountReportContractSummaryWidget() {
    const container = document.getElementById('reportContractSummaryWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportContractSummaryWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportContractSummaryWidget);
} else {
    // DOM already ready
    mountReportContractSummaryWidget();
}