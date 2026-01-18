/** @odoo-module */

import { mount } from "@odoo/owl";
import { TransactionListTab } from "./transaction_list_tab.js";

// Mount transaction list widget when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  const widgetContainer = document.getElementById('transaction-list-widget');
  if (widgetContainer) {
    // Hide spinner and show widget
    if (window.hideSpinner) {
      window.hideSpinner();
    }
    
    mount(TransactionListTab, widgetContainer);
  }
});
 