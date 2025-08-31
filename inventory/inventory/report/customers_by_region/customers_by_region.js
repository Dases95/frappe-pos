// Copyright (c) 2023, Your Company and contributors
// For license information, please see license.txt

frappe.query_reports["Customers by Region"] = {
	"filters": [
		{
			"fieldname": "wilaya",
			"label": __("Wilaya"),
			"fieldtype": "Link",
			"options": "Wilaya",
			"get_query": function() {
				return {
					"filters": [
						["Wilaya", "disabled", "=", 0]
					],
					"order_by": "wilaya_name"
				};
			},
			"on_change": function() {
				var wilaya = frappe.query_report.get_filter_value('wilaya');
				if (wilaya) {
					frappe.query_report.set_filter_value('commune', "");
					frappe.db.get_list('Commune', {
						filters: {
							'wilaya': wilaya,
							'disabled': 0
						},
						fields: ['name']
					}).then(data => {
						// Update the commune filter options
						var commune_filter = frappe.query_report.get_filter('commune');
						commune_filter.df.get_query = () => {
							return {
								"filters": [
									["Commune", "wilaya", "=", wilaya],
									["Commune", "disabled", "=", 0]
								],
								"order_by": "commune_name"
							};
						};
						commune_filter.refresh();
					});
				}
			}
		},
		{
			"fieldname": "commune",
			"label": __("Commune"),
			"fieldtype": "Link",
			"options": "Commune",
			"depends_on": "wilaya",
			"get_query": function() {
				var wilaya = frappe.query_report.get_filter_value('wilaya');
				return {
					"filters": [
						["Commune", "wilaya", "=", wilaya],
						["Commune", "disabled", "=", 0]
					],
					"order_by": "commune_name"
				};
			}
		},
		{
			"fieldname": "customer_type",
			"label": __("Customer Type"),
			"fieldtype": "Select",
			"options": "\nRetailer\nWholesaler\nDistributor\nOther"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive",
			"default": "Active"
		},
		{
			"fieldname": "with_contact",
			"label": __("With Contact Number"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "with_email",
			"label": __("With Email"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "view_type",
			"label": __("View Type"),
			"fieldtype": "Select",
			"options": "Detailed\nSummary",
			"default": "Detailed",
			"on_change": function() {
				let viewType = frappe.query_report.get_filter_value('view_type');
				
				if (viewType === "Summary") {
					frappe.query_report.toggle_summary();
				}
			}
		}
	],
	
	"initial_depth": 0,
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "status") {
			if (data.status == "Active") {
				value = '<span style="color: green; font-weight: bold;">' + value + '</span>';
			} else if (data.status == "Inactive") {
				value = '<span style="color: red; font-weight: bold;">' + value + '</span>';
			}
		}
		
		if (column.fieldname == "customer_type") {
			let colors = {
				"Retailer": "#5e64ff",
				"Wholesaler": "#743ee2",
				"Distributor": "#ff5858",
				"Other": "#7578f6"
			};
			let color = colors[data.customer_type] || "#7578f6";
			
			value = '<span class="indicator-pill" style="background-color: ' + color + 
				'; color: white; font-weight: 500; padding: 2px 8px; border-radius: 10px;">' + 
				value + '</span>';
		}
		
		if (column.fieldname == "contact_number" && data.contact_number) {
			value = '<a href="tel:' + data.contact_number + '" title="' + __('Call') + 
				'" style="text-decoration: none;"><i class="fa fa-phone" style="margin-right: 5px; color: #5e64ff;"></i>' + 
				data.contact_number + '</a>';
		}
		
		if (column.fieldname == "email" && data.email) {
			value = '<a href="mailto:' + data.email + '" title="' + __('Send Email') + 
				'" style="text-decoration: none;"><i class="fa fa-envelope" style="margin-right: 5px; color: #5e64ff;"></i>' + 
				data.email + '</a>';
		}
		
		if (column.fieldname == "customer") {
			value = '<a href="/app/customer/' + data.customer + '" style="font-weight: bold; color: #5e64ff;">' + 
				data.customer + '</a>';
		}
		
		return value;
	},
	
	"onload": function(report) {
		// Add toggle button for chart view
		report.page.add_inner_button(__('Toggle Chart View'), function() {
			let $chart = report.page.main.find('.chart-container');
			if ($chart.length && $chart.is(':visible')) {
				$chart.hide();
			} else if ($chart.length) {
				$chart.show();
			}
		}, __('View'));
		
		// Add button to toggle summary view
		report.page.add_inner_button(__('Toggle Summary View'), function() {
			toggle_summary_view(report);
		}, __('View'));
		
		// Add export button
		report.page.add_inner_button(__('Export Data'), function() {
			var filters = report.get_values();
			frappe.set_route('query-report', 'Customers by Region',
				{
					'wilaya': filters.wilaya,
					'commune': filters.commune,
					'customer_type': filters.customer_type,
					'status': filters.status,
					'with_contact': filters.with_contact,
					'with_email': filters.with_email,
					'export': 1
				}
			);
		}, __('Actions'));
		
		// Add print button
		report.page.add_inner_button(__('Print Report'), function() {
			print_report(report);
		}, __('Actions'));
		
		// Add Map View button
		report.page.add_inner_button(__('Map View'), function() {
			show_map_view(report);
		}, __('View'));
		
		// Initial setup for summary view if selected
		if (frappe.query_report.get_filter_value('view_type') === "Summary") {
			setTimeout(function() {
				toggle_summary_view(report);
			}, 1000);
		}
	},
	
	"print_report": function(report) {
		print_report(report);
	},
	
	"toggle_summary": function() {
		toggle_summary_view(frappe.query_report);
	}
};

// Function to print the report
function print_report(report) {
	var filters = report.get_values();
	
	frappe.call({
		method: "frappe.desk.query_report.run",
		args: {
			report_name: "Customers by Region",
			filters: filters
		},
		callback: function(r) {
			if (r.message.data) {
				frappe.ui.get_print_settings(false, function(print_settings) {
					var title = __("Customers by Region"),
						subtitle = [];
					
					if (filters.wilaya) {
						subtitle.push(__("Wilaya") + ": " + filters.wilaya);
					}
					if (filters.commune) {
						subtitle.push(__("Commune") + ": " + filters.commune);
					}
					if (filters.customer_type) {
						subtitle.push(__("Customer Type") + ": " + filters.customer_type);
					}
					if (filters.status) {
						subtitle.push(__("Status") + ": " + filters.status);
					}
					
					frappe.render_grid({
						title: title,
						subtitle: subtitle.join(", "),
						report: "Customers by Region",
						data: r.message.data,
						columns: r.message.columns,
						print_settings: print_settings
					});
				});
			}
		}
	});
}

// Function to toggle summary view
function toggle_summary_view(report) {
	var data = report.data;
	var columns = report.columns;
	
	if (!data || !data.length) return;
	
	var $results = report.page.main.find('.results');
	var $summary = report.page.main.find('.summary-section');
	
	if ($summary.length) {
		$summary.remove();
		$results.show();
		return;
	}
	
	// Group data by wilaya
	var groups = {};
	var total = 0;
	
	data.forEach(function(row) {
		var wilaya = row.wilaya || 'Not Specified';
		if (!groups[wilaya]) {
			groups[wilaya] = {
				count: 0,
				active: 0,
				inactive: 0,
				types: {}
			};
		}
		
		groups[wilaya].count++;
		total++;
		
		if (row.status === 'Active') {
			groups[wilaya].active++;
		} else if (row.status === 'Inactive') {
			groups[wilaya].inactive++;
		}
		
		var type = row.customer_type || 'Not Specified';
		if (!groups[wilaya].types[type]) {
			groups[wilaya].types[type] = 0;
		}
		groups[wilaya].types[type]++;
	});
	
	// Create summary HTML
	var html = '<div class="summary-section" style="margin-top: 15px;">';
	
	// Summary header
	html += '<div class="summary-header" style="margin-bottom: 15px;">';
	html += '<h3>' + __('Customer Summary') + '</h3>';
	html += '<div class="text-muted">' + __('Total Customers') + ': ' + total + '</div>';
	html += '</div>';
	
	// Summary cards grid
	html += '<div class="summary-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;">';
	
	// Create a card for each wilaya
	Object.keys(groups).sort().forEach(function(wilaya) {
		var group = groups[wilaya];
		
		html += '<div class="summary-card" style="border: 1px solid #d1d8dd; border-radius: 4px; overflow: hidden;">';
		html += '<div class="card-header" style="background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #d1d8dd;">';
		html += '<h4 style="margin: 0;">' + wilaya + '</h4>';
		html += '</div>';
		html += '<div class="card-body" style="padding: 10px;">';
		
		// Customer count
		html += '<div class="count-line" style="margin-bottom: 8px;">';
		html += '<strong>' + __('Total') + ':</strong> ' + group.count;
		html += '</div>';
		
		// Status breakdown
		html += '<div class="status-line" style="margin-bottom: 8px;">';
		html += '<strong>' + __('Active') + ':</strong> <span style="color: green">' + group.active + '</span> | ';
		html += '<strong>' + __('Inactive') + ':</strong> <span style="color: red">' + group.inactive + '</span>';
		html += '</div>';
		
		// Customer type breakdown
		html += '<div class="types-section">';
		html += '<strong>' + __('Types') + ':</strong> ';
		html += '<ul style="margin: 5px 0 0 20px; padding: 0;">';
		
		Object.keys(group.types).forEach(function(type) {
			html += '<li>' + type + ': ' + group.types[type] + '</li>';
		});
		
		html += '</ul>';
		html += '</div>';
		
		html += '</div>'; // End card-body
		html += '</div>'; // End summary-card
	});
	
	html += '</div>'; // End summary-grid
	html += '</div>'; // End summary-section
	
	$results.hide();
	$results.after(html);
}

// Function to show customers on a map
function show_map_view(report) {
	var data = report.data;
	
	if (!data || !data.length) {
		frappe.msgprint(__('No customer data available'));
		return;
	}
	
	// Since geolocation field has been removed, show a message about map functionality
	frappe.msgprint({
		title: __('Map View Not Available'),
		message: __('Map view requires geolocation coordinates which are not currently available for customers. To enable map view, add geolocation data to your customer records.'),
		indicator: 'yellow'
	});
	
	return;
} 