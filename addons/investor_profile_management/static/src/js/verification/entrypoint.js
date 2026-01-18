// entrypoint.js for VerificationWidget

// Wait for OWL to be available and then mount the component
function mountVerificationWidget() {
    if (typeof owl !== 'undefined' && typeof VerificationWidget !== 'undefined') {
        const widgetContainer = document.getElementById('verificationWidget');
        if (widgetContainer) {
            owl.mount(VerificationWidget, widgetContainer);
            // Ẩn spinner, show widget
            const loadingSpinner = document.getElementById('loadingSpinner');
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            widgetContainer.style.display = 'block';
        } else {
            setTimeout(mountVerificationWidget, 100);
        }
    } else {
        setTimeout(mountVerificationWidget, 100);
    }
}

mountVerificationWidget(); 