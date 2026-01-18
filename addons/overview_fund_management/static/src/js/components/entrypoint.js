/** @odoo-module **/

import { Header } from './header';
import { Footer } from './footer';
import { mountGlobalLoader } from './loader';
import { mount } from '@odoo/owl';

// Export components for other modules to import
export { Header, Footer };

// Hàm mount Header component
let headerRetries = 0;
function mountHeader() {
    const headerContainer = document.getElementById('header-container');
    if (headerContainer) {

        mount(Header, headerContainer, {
            props: {
                userName: window.userName || "TRẦN NGUYÊN TRƯỜNG PHÁT",
                accountNo: window.accountNo || "N/A"
            }
        });
    } else if (headerRetries < 50) {
        headerRetries++;
        setTimeout(mountHeader, 100);
    }
}

// Hàm mount Footer component
let footerRetries = 0;
function mountFooter() {
    const footerContainer = document.getElementById('footer-container');

    if (footerContainer) {

        mount(Footer, footerContainer, { props: {} });

    } else if (footerRetries < 50) {
        footerRetries++;
        setTimeout(mountFooter, 100);
    }

}

// Đợi DOM load xong
document.addEventListener('DOMContentLoaded', () => {

    mountGlobalLoader(); // Khởi tạo Global Loader ngay lập tức
    mountHeader();
    mountFooter();
}); 