    /** @odoo-module */

    import { FundCertificateWidget } from './fund_certificate_widget';
    import { SidebarPanel } from "@fund_management_dashboard/js/dashboard/sidebar_panel";
    import { mount } from "@odoo/owl";

    document.addEventListener('DOMContentLoaded', async () => {
        // Mount Sidebar
        const sidebarContainer = document.getElementById("sidebarWidget");
        if (sidebarContainer) {
            try {
                await mount(SidebarPanel, sidebarContainer);
            } catch (e) {
                console.error("Failed to mount SidebarPanel", e);
            }
        }

        // Mount FundCertificateWidget
        const widgetContainer = document.getElementById("fundCertificateWidget");
        if (widgetContainer) {
            // Clear loading spinner
            widgetContainer.innerHTML = ''; 
            try {
                await mount(FundCertificateWidget, widgetContainer);
                console.log("FundCertificateWidget mounted successfully.");
            } catch (e) {
                console.error("Failed to mount FundCertificateWidget", e);
                widgetContainer.innerHTML = `<div class="alert alert-danger">Error loading component: ${e.message}</div>`;
            }
        }
    });
