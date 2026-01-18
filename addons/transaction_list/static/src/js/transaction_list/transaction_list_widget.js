/** @odoo-module */

import { Component, xml, useState } from "@odoo/owl";
import { TransactionListTab } from "./transaction_list_tab.js";
import { BetaExportTab } from "./beta_export_tab.js";
import { OrderAllocationTab } from "./order_allocation_tab.js";

// Component chính
export class TransactionListWidget extends Component {
  static template = xml`
    <div class="transaction-list-widget">
      <div class="transaction-list-container">
        <div class="container-fluid">
          <!-- Main Tab Navigation -->
          <div class="main-tab-nav mb-4">
            <nav class="nav nav-tabs">
              <a class="nav-link" t-att-class="state.activeMainTab === 'transaction_list' ? 'active' : ''" href="#" t-on-click="() => this.setActiveMainTab('transaction_list')">
                <i class="fas fa-list me-2"></i>Danh sách giao dịch
              </a>
              <a class="nav-link" t-att-class="state.activeMainTab === 'beta_export' ? 'active' : ''" href="#" t-on-click="() => this.setActiveMainTab('beta_export')">
                <i class="fas fa-file-export me-2"></i>Beta Export
              </a>
              <a class="nav-link" t-att-class="state.activeMainTab === 'order_allocation' ? 'active' : ''" href="#" t-on-click="() => this.setActiveMainTab('order_allocation')">
                <i class="fas fa-chart-pie me-2"></i>Phân bố lệnh (R44)
              </a>
            </nav>
          </div>

          <!-- Tab Content -->
          <t t-if="state.activeMainTab === 'transaction_list'">
            <TransactionListTab />
          </t>
          <t t-if="state.activeMainTab === 'beta_export'">
            <BetaExportTab />
          </t>
          <t t-if="state.activeMainTab === 'order_allocation'">
            <OrderAllocationTab />
          </t>
        </div>
      </div>
    </div>
  `;

  static components = {
    TransactionListTab,
    BetaExportTab,
    OrderAllocationTab
  };

  setup() {
    this.state = useState({
      activeMainTab: 'transaction_list'
    });
  }

  setActiveMainTab(tab) {
    this.state.activeMainTab = tab;
  }
} 