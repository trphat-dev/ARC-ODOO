// entrypoint.js for AddressInfoWidget

// Wait for OWL to be available and then mount the component
function mountAddressInfoWidget() {
    if (typeof owl !== 'undefined' && typeof AddressInfoWidget !== 'undefined') {
        const widgetContainer = document.getElementById('addressInfoWidget');
        if (widgetContainer) {
            owl.mount(AddressInfoWidget, widgetContainer);
            // Ẩn spinner, show widget
            const loadingSpinner = document.getElementById('loadingSpinner');
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            widgetContainer.style.display = 'block';
        } else {
            setTimeout(mountAddressInfoWidget, 100);
        }
    } else {
        setTimeout(mountAddressInfoWidget, 100);
    }
}

mountAddressInfoWidget(); 