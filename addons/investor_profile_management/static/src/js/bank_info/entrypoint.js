// entrypoint.js for BankInfoWidget

// Wait for OWL to be available and then mount the component
function mountBankInfoWidget() {
    if (typeof owl !== 'undefined' && typeof BankInfoWidget !== 'undefined') {
        const widgetContainer = document.getElementById('bankInfoWidget');
        if (widgetContainer) {
            owl.mount(BankInfoWidget, widgetContainer);
            // Ẩn spinner, show widget
            const loadingSpinner = document.getElementById('loadingSpinner');
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            widgetContainer.style.display = 'block';
        } else {
            setTimeout(mountBankInfoWidget, 100);
        }
    } else {
        setTimeout(mountBankInfoWidget, 100);
    }
}

mountBankInfoWidget(); 