/** @odoo-module **/

/**
 * Maturity Notification Bus Service
 * 
 * Service để lắng nghe thông báo đáo hạn qua Odoo Bus (WebSocket)
 * Chỉ hiển thị thông báo cho user hiện tại đang đăng nhập
 */

import { registry } from '@web/core/registry';

const serviceRegistry = registry.category('services');

serviceRegistry.add('maturity_notification_service', {
    dependencies: ['bus_service'],
    start(env, { bus_service }) {
        // Subscribe to maturity notification channel
        try {
            bus_service.addChannel('transaction.maturity.notifications');
        } catch (error) {
            // Chỉ log lỗi nghiêm trọng
            if (error.message && !error.message.includes('Network')) {
                console.warn('[MATURITY NOTIFICATION] Failed to add channel:', error);
            }
        }

        // Listen for notifications
        bus_service.addEventListener('notification', ({ detail: notifications }) => {
            for (const notif of notifications) {
                try {
                    // Odoo bus notification format: [channel_name, payload]
                    const payload = Array.isArray(notif) ? notif[1] : (notif.payload || notif);
                    if (!payload || typeof payload !== 'object') continue;
                    
                    // Lấy user_id hiện tại từ session để filter
                    const currentUserId = env.services.user?.userId || null;
                    
                    // Handle maturity notification - chỉ xử lý nếu là notification của user hiện tại
                    if (payload.type === 'maturity_notification') {
                        // Kiểm tra xem notification có phải của user hiện tại không
                        if (payload.user_id && currentUserId && payload.user_id !== currentUserId) {
                            continue; // Bỏ qua notification của user khác
                        }
                        
                        // Trigger custom event để header có thể lắng nghe
                        const event = new CustomEvent('maturity-notification-received', {
                            detail: payload
                        });
                        window.dispatchEvent(event);
                    }
                    
                    // Handle confirmation notification
                    if (payload.type === 'maturity_confirmation') {
                        // Kiểm tra xem notification có phải của user hiện tại không
                        if (payload.user_id && currentUserId && payload.user_id !== currentUserId) {
                            continue; // Bỏ qua notification của user khác
                        }
                        
                        const event = new CustomEvent('maturity-confirmation-received', {
                            detail: payload
                        });
                        window.dispatchEvent(event);
                    }
                } catch (error) {
                    // Chỉ log lỗi nghiêm trọng
                    if (error.message && !error.message.includes('Network')) {
                        console.error('[MATURITY NOTIFICATION] Error processing notification:', error);
                    }
                }
            }
        });
    },
});

