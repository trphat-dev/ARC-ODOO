/** @odoo-module */

import { mount } from "@odoo/owl";
import { ListTenorsInterestRatesWidget } from './list_tenors_interest_rates_widget.js';

// Mount OWL widget when DOM is ready
function mountListTenorsInterestRatesWidget() {
    const container = document.getElementById('listTenorsInterestRatesWidget');
    if (!container) {
        return;
    }
    
    try {
        // Mount OWL component using OWL mount function
        mount(ListTenorsInterestRatesWidget, container);
    } catch (error) {
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountListTenorsInterestRatesWidget);
} else {
    // DOM already ready
    mountListTenorsInterestRatesWidget();
}