// Personal Profile Entrypoint
document.addEventListener('DOMContentLoaded', function() {
    // Check if OWL is available
    if (typeof owl === 'undefined') {
        return;
    }
    
    const widgetContainer = document.getElementById('personalProfileWidget');
    if (!widgetContainer) {
        return;
    }
    
    // Wait a bit for the component to be loaded
    setTimeout(() => {
        if (typeof window.PersonalProfileWidget !== 'undefined') {
            owl.mount(window.PersonalProfileWidget, widgetContainer);
            // Ẩn spinner, show widget
            const loadingSpinner = document.getElementById('loadingSpinner');
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            widgetContainer.style.display = 'block';
        }
    }, 500);
}); 