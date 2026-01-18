// entrypoint.js for SchemeTypeWidget
document.addEventListener('DOMContentLoaded', () => {
    // Call the centralized service to handle mounting.
    if (window.WidgetMountingService) {
        window.WidgetMountingService.mountWhenReady(
            'SchemeWidget',      // The name of the Component Class
            'schemeWidget'       // The ID of the container element in the DOM
        );
    } else {
        console.error('WidgetMountingService is not available. Make sure it is loaded first in your assets.');
    }
});
