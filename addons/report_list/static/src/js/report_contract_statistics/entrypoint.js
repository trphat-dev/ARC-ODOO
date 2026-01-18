/** @odoo-module */

import { mount } from "@odoo/owl";
import { ReportContractStatisticsWidget } from './report_contract_statistics_widget.js';

// Mount OWL widget when DOM is ready
function mountReportContractStatisticsWidget() {
    const container = document.getElementById('reportContractStatisticsWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ReportContractStatisticsWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountReportContractStatisticsWidget);
} else {
    // DOM already ready
    mountReportContractStatisticsWidget();
}