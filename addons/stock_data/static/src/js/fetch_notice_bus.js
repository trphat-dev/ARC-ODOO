/** @odoo-module **/

import { registry } from '@web/core/registry';

const serviceRegistry = registry.category('services');

serviceRegistry.add('ssi_fetch_notice_service', {
    dependencies: ['bus_service', 'notification'],
    start(env, { bus_service, notification }) {
        // Subscribe to custom channel
        try {
            bus_service.addChannel('ssi.marketdata');
        } catch (e) {
            // ignore
        }

        bus_service.addEventListener('notification', ({ detail: notifications }) => {
            for (const notif of notifications) {
                try {
                    const { payload } = notif;
                    if (!payload || typeof payload !== 'object') continue;
                    if (payload.type !== 'fetch_notice') continue;

                    const title = payload.title || 'Auto Fetch';
                    const message = payload.message || '';
                    const level = (payload.level || 'info');
                    const typeMap = { info: 'info', success: 'success', warning: 'warning', error: 'danger' };
                    const type = typeMap[level] || 'info';

                    notification.add(message, { title, type, sticky: false });
                } catch (e) {
                    // ignore
                }
            }
        });
    },
});


