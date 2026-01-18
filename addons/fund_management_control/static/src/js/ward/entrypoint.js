/** @odoo-module **/
import WardWidget from './ward_widget';
window.WardWidget = WardWidget;
// entrypoint.js cho ward
// Bạn có thể import ward_widget.js ở đây nếu cần
console.log('Ward JS loaded');
console.log('WardWidget entrypoint.js loaded');
let mountAttempts = 0;
const maxAttempts = 50;
function mountWardWidget() {
    mountAttempts++;
    if (typeof owl !== 'undefined' && typeof window.WardWidget !== 'undefined') {
        const widgetContainer = document.getElementById('wardWidget');
        if (widgetContainer) {
            try {
                widgetContainer.innerHTML = '';
                const app = new owl.App(window.WardWidget);
                app.mount(widgetContainer);
                return;
            } catch (error) {
                try {
                    widgetContainer.innerHTML = '';
                    owl.mount(window.WardWidget, widgetContainer);
                    return;
                } catch (fallbackError) {}
            }
        }
    }
    if (mountAttempts < maxAttempts) setTimeout(mountWardWidget, 100);
}
document.addEventListener('DOMContentLoaded', mountWardWidget);
window.addEventListener('load', () => { if (mountAttempts === 0) mountWardWidget(); });
if (document.readyState !== 'loading') setTimeout(mountWardWidget, 50); 
