/** @odoo-module */

import { mount } from "@odoo/owl";
import { OrderBookComponent } from "./order_book_component.js";
import { CompletedOrdersComponent } from "./completed_orders_component.js";
import { NegotiatedOrdersComponent } from "./negotiated_orders_component.js";
import { NormalOrdersComponent } from "./normal_orders_component.js";

// Dùng chung một entrypoint để mount đúng component theo container hiện diện
document.addEventListener('DOMContentLoaded', function () {
  const orderBookEl = document.querySelector('.order-book-widget');
  const completedEl = document.getElementById('completed-orders-widget');
  const negotiatedEl = document.getElementById('negotiated-orders-widget');
  const normalOrdersEl = document.getElementById('normal-orders-widget');

  const hide = () => { if (window.hideSpinner) window.hideSpinner(); };

  if (orderBookEl) {
    hide();
    mount(OrderBookComponent, orderBookEl);
    return;
  }
  if (completedEl) {
    hide();
    mount(CompletedOrdersComponent, completedEl);
    return;
  }
  if (negotiatedEl) {
    hide();
    mount(NegotiatedOrdersComponent, negotiatedEl);
    return;
  }
  if (normalOrdersEl) {
    hide();
    mount(NormalOrdersComponent, normalOrdersEl);
  }
});
