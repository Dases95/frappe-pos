// Copyright (c) 2023, Your Name and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Add the customer-form class to the form for CSS styling
        frm.page.wrapper.addClass('customer-form');
        
        // Add visual indicators for customer status
        if(frm.doc.status === "Active") {
            frm.set_indicator("Active", "green");
        } else if(frm.doc.status === "Inactive") {
            frm.set_indicator("Inactive", "red");
        }
        
        // Add custom buttons in a more organized way
        if(!frm.is_new()) {
            // Add a button group for related documents
            frm.add_custom_button(__('Sales Orders'), function() {
                frappe.set_route('List', 'Sales Order', {customer: frm.doc.name});
            }, __('View'));
            
            frm.add_custom_button(__('Delivery Notes'), function() {
                frappe.set_route('List', 'Delivery Note', {customer: frm.doc.name});
            }, __('View'));
            
            // Add a button group for communication
            if(frm.doc.contact_number) {
                frm.add_custom_button(__('Send SMS'), function() {
                    send_sms(frm);
                }, __('Contact'));
            }
            
            if(frm.doc.email) {
                frm.add_custom_button(__('Send Email'), function() {
                    frappe.email.send({
                        recipients: [frm.doc.email],
                        subject: __('Message from {0}', [frappe.boot.company]),
                        message: __('Dear {0},', [frm.doc.customer_name])
                    });
                }, __('Contact'));
            }
            
            // Add Map button if coordinates are available
            if(frm.doc.latitude) {
                frm.add_custom_button(__('View on Map'), function() {
                    view_on_map(frm.doc);
                }, __('Actions'));
            }
            
            // Add Copy Address button
            frm.add_custom_button(__('Copy Address'), function() {
                navigator.clipboard.writeText(frm.doc.full_address || "")
                    .then(() => {
                        frappe.show_alert({
                            message: __('Address copied to clipboard'),
                            indicator: 'green'
                        });
                    })
                    .catch(err => {
                        console.error('Error copying address: ', err);
                        frappe.show_alert({
                            message: __('Failed to copy address'),
                            indicator: 'red'
                        });
                    });
            }, __('Actions'));
        }
        
        // Render the address display when the form is refreshed
        render_address_display(frm);
    },
    
    setup: function(frm) {
        // Set up custom queries for wilaya/commune fields
        frm.set_query('wilaya', function() {
            return {
                filters: {
                    'disabled': 0
                }
            };
        });
        
        frm.set_query('commune', function() {
            return {
                filters: {
                    'wilaya': frm.doc.wilaya || '',
                    'disabled': 0
                }
            };
        });
    },
    
    wilaya: function(frm) {
        // Clear commune when wilaya changes
        if(frm.doc.wilaya) {
            if(frm.doc.commune) {
                frappe.db.get_value('Commune', frm.doc.commune, 'wilaya', function(r) {
                    if(r && r.wilaya !== frm.doc.wilaya) {
                        frm.set_value('commune', '');
                        frappe.show_alert({
                            message:__('Commune has been reset as the Wilaya was changed'),
                            indicator:'blue'
                        });
                    }
                });
            }
        } else {
            frm.set_value('commune', '');
        }
        
        // Update address display
        frm.trigger('address');
    },
    
    commune: function(frm) {
        // Update address display
        frm.trigger('address');
    },
    
    address: function(frm) {
        // Update address display
        render_address_display(frm);
    },
    
    latitude: function(frm) {
        // Enable/disable map button based on coordinates
        frm.toggle_display('show_on_map', frm.doc.latitude ? true : false);
    },
    
    customer_name: function(frm) {
        // Capitalize customer name
        if(frm.doc.customer_name) {
            frm.set_value('customer_name', frm.doc.customer_name.charAt(0).toUpperCase() + frm.doc.customer_name.slice(1));
        }
    },
    
    contact_person: function(frm) {
        // Capitalize contact person name
        if(frm.doc.contact_person) {
            frm.set_value('contact_person', frm.doc.contact_person.charAt(0).toUpperCase() + frm.doc.contact_person.slice(1));
        }
    },
    
    customer_type: function(frm) {
        // Apply different styling based on customer type
        frm.trigger('refresh');
    },
    
    status: function(frm) {
        // Update indicator when status changes
        if(frm.doc.status === "Active") {
            frm.set_indicator("Active", "green");
        } else if(frm.doc.status === "Inactive") {
            frm.set_indicator("Inactive", "red");
        }
    }
});

// Function to render the address display
function render_address_display(frm) {
    if(!frm.doc.address && !frm.doc.commune && !frm.doc.wilaya) {
        frm.set_df_property('full_address_display', 'options', '');
        return;
    }
    
    var parts = [];
    
    if(frm.doc.address) {
        parts.push('<div>' + frm.doc.address + '</div>');
    }
    
    if(frm.doc.commune) {
        frappe.db.get_value('Commune', frm.doc.commune, ['commune_name'], function(r) {
            if(r && r.commune_name) {
                parts.push('<div><strong>Commune:</strong> ' + r.commune_name + '</div>');
            } else {
                parts.push('<div><strong>Commune:</strong> ' + frm.doc.commune + '</div>');
            }
            
            if(frm.doc.wilaya) {
                frappe.db.get_value('Wilaya', frm.doc.wilaya, ['wilaya_name'], function(r2) {
                    if(r2 && r2.wilaya_name) {
                        parts.push('<div><strong>Wilaya:</strong> ' + r2.wilaya_name + '</div>');
                    } else {
                        parts.push('<div><strong>Wilaya:</strong> ' + frm.doc.wilaya + '</div>');
                    }
                    
                    // Create the full address HTML with styling
                    var html = '<div class="address-display" style="padding: 10px; border-left: 3px solid #5e64ff; background-color: #f8f8f8; border-radius: 0 4px 4px 0; margin-top: 5px;">';
                    html += parts.join('');
                    
                    if(frm.doc.latitude) {
                        var coords = frm.doc.latitude.split(',');
                        if(coords.length === 2) {
                            html += '<div style="margin-top: 5px;"><strong>GPS:</strong> <span style="font-family: monospace;">' + 
                                coords[0].trim() + ', ' + coords[1].trim() + '</span></div>';
                        }
                    }
                    
                    html += '</div>';
                    
                    frm.set_df_property('full_address_display', 'options', html);
                });
            } else {
                // No wilaya, just show the commune
                var html = '<div class="address-display" style="padding: 10px; border-left: 3px solid #5e64ff; background-color: #f8f8f8; border-radius: 0 4px 4px 0; margin-top: 5px;">';
                html += parts.join('');
                html += '</div>';
                
                frm.set_df_property('full_address_display', 'options', html);
            }
        });
    } else if(frm.doc.wilaya) {
        // No commune, just wilaya
        frappe.db.get_value('Wilaya', frm.doc.wilaya, ['wilaya_name'], function(r) {
            if(r && r.wilaya_name) {
                parts.push('<div><strong>Wilaya:</strong> ' + r.wilaya_name + '</div>');
            } else {
                parts.push('<div><strong>Wilaya:</strong> ' + frm.doc.wilaya + '</div>');
            }
            
            var html = '<div class="address-display" style="padding: 10px; border-left: 3px solid #5e64ff; background-color: #f8f8f8; border-radius: 0 4px 4px 0; margin-top: 5px;">';
            html += parts.join('');
            html += '</div>';
            
            frm.set_df_property('full_address_display', 'options', html);
        });
    } else {
        // Just plain address
        var html = '<div class="address-display" style="padding: 10px; border-left: 3px solid #5e64ff; background-color: #f8f8f8; border-radius: 0 4px 4px 0; margin-top: 5px;">';
        html += parts.join('');
        html += '</div>';
        
        frm.set_df_property('full_address_display', 'options', html);
    }
}

// Function to open map with coordinates
function view_on_map(doc) {
    if(!doc.latitude) {
        frappe.msgprint(__('No coordinates available for this customer.'));
        return;
    }
    
    var coords = doc.latitude.split(',');
    if(coords.length !== 2) {
        frappe.msgprint(__('Invalid coordinates format. Expected format: latitude, longitude'));
        return;
    }
    
    var lat = coords[0].trim();
    var lng = coords[1].trim();
    
    var url = 'https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lng;
    window.open(url, '_blank');
}

// Function to send SMS
function send_sms(frm) {
    if(!frm.doc.contact_number) {
        frappe.msgprint(__('No contact number available for this customer.'));
        return;
    }
    
    var d = new frappe.ui.Dialog({
        title: __('Send SMS to {0}', [frm.doc.customer_name]),
        fields: [
            {
                label: __('To'),
                fieldname: 'phone',
                fieldtype: 'Data',
                default: frm.doc.contact_number,
                read_only: 1
            },
            {
                label: __('Message'),
                fieldname: 'message',
                fieldtype: 'Text Editor',
                reqd: 1
            }
        ],
        primary_action_label: __('Send'),
        primary_action: function() {
            var values = d.get_values();
            
            // Here you would integrate with your SMS provider
            frappe.msgprint(__('SMS feature will be available when configured with an SMS provider.'));
            
            d.hide();
            
            // Show confirmation
            frappe.show_alert({
                message: __('SMS would be sent to {0}', [frm.doc.contact_number]),
                indicator: 'green'
            });
        }
    });
    
    d.show();
}

// Add custom formatters and helpers
frappe.provide('inventory.customer');

inventory.customer = {
    // Function to format address with wilaya and commune
    format_full_address: function(doc) {
        let address_parts = [];
        if (doc.address) address_parts.push(doc.address);
        if (doc.commune) address_parts.push(doc.commune);
        if (doc.wilaya) address_parts.push(doc.wilaya);
        
        return address_parts.join(', ');
    },
    
    // Function to get coordinates from address using geocoding service
    // This would require additional setup for actual geocoding integration
    get_coordinates: function(doc, callback) {
        // Placeholder for geocoding implementation
        // In a real implementation, you would call a geocoding API
        frappe.msgprint(__('Geocoding functionality would be implemented here.'));
        if (callback) callback(null);
    }
}; 