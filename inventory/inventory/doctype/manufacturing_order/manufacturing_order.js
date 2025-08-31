frappe.ui.form.on('Manufacturing Order', {
	refresh: function(frm) {
		// Add custom buttons based on document status
		if (frm.doc.docstatus === 1) {  // Submitted
			if (frm.doc.status === "In Process") {
				// Add button to complete production
				frm.add_custom_button(__('Complete Production'), function() {
					frappe.confirm(
						__('Are you sure you want to complete production for this order?'),
						function() {
							frappe.call({
								method: 'complete_production',
								doc: frm.doc,
								callback: function(r) {
									if (!r.exc) {
										frm.refresh();
										frappe.show_alert({
											message: __('Production completed successfully'),
											indicator: 'green'
										});
									}
								}
							});
						}
					);
				}).addClass('btn-primary');
			} else {
				// Add button to start production (for any submitted status other than "In Process" or "Completed")
				if (frm.doc.status !== "Completed" && frm.doc.status !== "Cancelled") {
					frm.add_custom_button(__('Start Production'), function() {
						frappe.confirm(
							__('Are you sure you want to start production for this order?'),
							function() {
								frappe.call({
									method: 'start_production',
									doc: frm.doc,
									callback: function(r) {
										if (!r.exc) {
											frm.refresh();
											frappe.show_alert({
												message: __('Production started successfully'),
												indicator: 'green'
											});
										}
									}
								});
							}
						);
					}).addClass('btn-primary');
				}
			}
		}

		// Add a dashboard to show related stock entries
		frm.dashboard.add_transactions([
			{
				'label': 'Stock',
				'items': ['Stock Entry']
			}
		]);
	},

	setup: function(frm) {
		// Set query filters for BOM Reference field
		frm.set_query("bom_reference", function() {
			return {
				filters: {
					"item": frm.doc.item_to_manufacture
				}
			};
		});
	},

	item_to_manufacture: function(frm) {
		// When item changes, clear the BOM reference
		if (frm.doc.item_to_manufacture) {
			frm.set_value('bom_reference', '');
		}
	},

	planned_start_date: function(frm) {
		// Auto-set planned end date to 1 day later if not already set
		if (frm.doc.planned_start_date && !frm.doc.planned_end_date) {
			let end_date = frappe.datetime.add_days(frm.doc.planned_start_date, 1);
			frm.set_value('planned_end_date', end_date);
		}
	},

	quantity: function(frm) {
		// Validate quantity is greater than zero
		if (frm.doc.quantity <= 0) {
			frappe.msgprint(__('Quantity must be greater than zero'));
			frm.set_value('quantity', 1);
		}
	},

	validate: function(frm) {
		// Additional client-side validation if needed
		if (frm.doc.planned_end_date && frappe.datetime.get_diff(frm.doc.planned_end_date, frm.doc.planned_start_date) < 0) {
			frappe.msgprint(__('Planned End Date cannot be before Planned Start Date'));
			frappe.validated = false;
		}
	}
}); 