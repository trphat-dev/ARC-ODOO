/** @odoo-module **/

import { mount } from "@odoo/owl";
import { NormalOrderFormComponent } from "./normal_order_form";

let isMounted = false;
let app = null;

function validateElement(element) {
    if (!element) return false;
    if (!(element instanceof Element)) return false;
    if (!element.isConnected) return false;
    return true;
}

/**
 * Mount NormalOrderFormComponent to target container
 * Called when user switches to "Normal Order" tab
 */
export function mountNormalOrderForm(targetId = 'normal-order-form-container') {
    if (isMounted) {
        console.log('[NormalOrderForm] Already mounted');
        return Promise.resolve();
    }

    const target = document.getElementById(targetId);
    if (!validateElement(target)) {
        console.warn('[NormalOrderForm] Target not found:', targetId);
        return Promise.reject(new Error('Target not found'));
    }

    // Check if already has component
    if (target.querySelector('.normal-order-form-container')) {
        isMounted = true;
        return Promise.resolve();
    }

    // Clear target
    target.innerHTML = '';

    // Get props from page context
    const fundSelect = document.getElementById('fund-select');
    const fundId = fundSelect?.options[fundSelect.selectedIndex]?.dataset?.id;

    const props = {
        fundId: fundId ? parseInt(fundId) : null,
        transactionType: 'buy',
        onOrderCreated: (result) => {
            console.log('[NormalOrderForm] Order created:', result);
        }
    };

    try {
        app = new owl.App(NormalOrderFormComponent, { props });
        return app.mount(target)
            .then(() => {
                isMounted = true;
                console.log('[NormalOrderForm] Mounted successfully');
            })
            .catch(error => {
                console.error('[NormalOrderForm] Mount error:', error);
                // Fallback mount
                return mount(NormalOrderFormComponent, { target, props });
            })
            .then(() => {
                isMounted = true;
            });
    } catch (error) {
        console.error('[NormalOrderForm] Sync error:', error);
        return Promise.reject(error);
    }
}

/**
 * Unmount NormalOrderFormComponent
 * Called when user switches away from "Normal Order" tab
 */
export function unmountNormalOrderForm() {
    if (app) {
        app.destroy();
        app = null;
        isMounted = false;
        console.log('[NormalOrderForm] Unmounted');
    }
}

/**
 * Check if component is mounted
 */
export function isNormalOrderFormMounted() {
    return isMounted;
}

// Export for global access
window.NormalOrderFormMount = {
    mount: mountNormalOrderForm,
    unmount: unmountNormalOrderForm,
    isMounted: isNormalOrderFormMounted
};
