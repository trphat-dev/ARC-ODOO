/** @odoo-module */

import { mount } from "@odoo/owl";
import { AOCReportWidget } from './aoc_report_widget.js';

// Mount OWL widget when DOM is ready
function mountAOCReportWidget() {
    const container = document.getElementById('aocReportWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(AOCReportWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountAOCReportWidget);
} else {
    // DOM already ready
    mountAOCReportWidget();
}