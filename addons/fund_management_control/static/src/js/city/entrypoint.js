/** @odoo-module **/
import CityWidget from './city_widget';
window.CityWidget = CityWidget;
// entrypoint.js cho city
// Bạn có thể import city_widget.js ở đây nếu cần
console.log('City JS loaded');
console.log('CityWidget entrypoint.js loaded');
let mountAttempts = 0;
const maxAttempts = 50;
function mountCityWidget() {
    mountAttempts++;
    if (typeof owl !== 'undefined' && typeof window.CityWidget !== 'undefined') {
        const widgetContainer = document.getElementById('cityWidget');
        if (widgetContainer) {
            try {
                widgetContainer.innerHTML = '';
                const app = new owl.App(window.CityWidget);
                app.mount(widgetContainer);
                return;
            } catch (error) {
                try {
                    widgetContainer.innerHTML = '';
                    owl.mount(window.CityWidget, widgetContainer);
                    return;
                } catch (fallbackError) {}
            }
        }
    }
    if (mountAttempts < maxAttempts) setTimeout(mountCityWidget, 100);
}
document.addEventListener('DOMContentLoaded', mountCityWidget);
window.addEventListener('load', () => { if (mountAttempts === 0) mountCityWidget(); });
if (document.readyState !== 'loading') setTimeout(mountCityWidget, 50); 
