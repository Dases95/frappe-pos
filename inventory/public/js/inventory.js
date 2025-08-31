// Inventory App - Global JS Utilities

// Add the module CSS class to all Inventory app pages
$(document).on('page-change', function() {
    // Get the current route to determine if we're in the inventory module
    var route = frappe.get_route();
    if (route && route.length > 0 && route[0] === 'inventory') {
        $('.page-container').addClass('inventory-module');
    }
});

// Add a custom dropdown to the navbar for quick access to key Inventory features
frappe.provide("inventory.navbar");
inventory.navbar.setup = function() {
    if ($('#inventory-menu').length) return;
    
    // Wait for navbar to be available
    if (!$('.navbar').length) {
        setTimeout(inventory.navbar.setup, 500);
        return;
    }
    
    // Create the inventory menu item
    var $dropdown = $('<li class="nav-item dropdown" id="inventory-menu">\
        <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" \
            role="button" aria-haspopup="true" aria-expanded="false">\
            <span>'+__('Inventory')+'</span>\
        </a>\
        <div class="dropdown-menu">\
            <a class="dropdown-item" href="#List/Customer/List">'+__('Customers')+'</a>\
            <a class="dropdown-item" href="#List/Sales Order/List">'+__('Sales Orders')+'</a>\
            <a class="dropdown-item" href="#List/Delivery Note/List">'+__('Delivery Notes')+'</a>\
            <div class="dropdown-divider"></div>\
            <a class="dropdown-item" href="#query-report/Customers by Region">'+__('Customer Analysis')+'</a>\
            <div class="dropdown-divider"></div>\
            <a class="dropdown-item" href="#List/Wilaya/List">'+__('Geographic Data')+'</a>\
        </div>\
    </li>');
    
    // Add to navbar
    $('.navbar .nav').append($dropdown);
};

// Initialize once the DOM is ready
$(document).ready(function() {
    // Set up navbar items
    inventory.navbar.setup();
    
    // Add extra class to customer lists
    $(document).on('page-change', function() {
        var route = frappe.get_route();
        if (route && route.length >= 3 && route[0] === 'List' && route[1] === 'Customer' && route[2] === 'List') {
            $('.result-list').addClass('customer-list');
        }
    });
});

// Utility functions for geography
inventory.utils = {
    // Format coordinates for display
    formatCoordinates: function(coordinates) {
        if (!coordinates) return '';
        
        var parts = coordinates.split(',');
        if (parts.length !== 2) return coordinates;
        
        return parts[0].trim() + '°, ' + parts[1].trim() + '°';
    },
    
    // Show location on map
    showOnMap: function(coordinates) {
        if (!coordinates) return;
        
        var parts = coordinates.split(',');
        if (parts.length !== 2) {
            frappe.msgprint(__('Invalid coordinates. Format should be "latitude, longitude"'));
            return;
        }
        
        var lat = parts[0].trim();
        var lng = parts[1].trim();
        
        window.open('https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lng, '_blank');
    },
    
    // Get wilaya name
    getWilayaName: function(wilaya_code, callback) {
        frappe.db.get_value('Wilaya', {'wilaya_code': wilaya_code}, 'wilaya_name', callback);
    },
    
    // Get commune name
    getCommuneName: function(commune_code, callback) {
        frappe.db.get_value('Commune', {'commune_code': commune_code}, 'commune_name', callback);
    }
};

// Register a custom keyboard shortcut for the inventory menu
$(document).on('keydown', function(e) {
    // Alt+I for Inventory menu
    if (e.altKey && e.keyCode === 73) {
        if ($('#inventory-menu .dropdown-menu').hasClass('show')) {
            $('#inventory-menu .dropdown-menu').removeClass('show');
        } else {
            $('#inventory-menu .dropdown-menu').addClass('show');
        }
        e.preventDefault();
    }
}); 