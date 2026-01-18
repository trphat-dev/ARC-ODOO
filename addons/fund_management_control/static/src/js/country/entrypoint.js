import './country_widget';
// entrypoint.js cho country
// Bạn có thể import country_widget.js ở đây nếu cần
console.log('Country JS loaded');
console.log('CountryWidget entrypoint.js loaded');
let mountAttempts = 0;
const maxAttempts = 50;
function mountCountryWidget() {
    mountAttempts++;
    if (typeof owl !== 'undefined' && typeof window.CountryWidget !== 'undefined') {
        const widgetContainer = document.getElementById('countryWidget');
        if (widgetContainer) {
            try {
                widgetContainer.innerHTML = '';
                const app = new owl.App(window.CountryWidget);
                app.mount(widgetContainer);
                return;
            } catch (error) {
                try {
                    widgetContainer.innerHTML = '';
                    owl.mount(window.CountryWidget, widgetContainer);
                    return;
                } catch (fallbackError) {}
            }
        }
    }
    if (mountAttempts < maxAttempts) setTimeout(mountCountryWidget, 100);
}
document.addEventListener('DOMContentLoaded', mountCountryWidget);
window.addEventListener('load', () => { if (mountAttempts === 0) mountCountryWidget(); });
if (document.readyState !== 'loading') setTimeout(mountCountryWidget, 50); 
