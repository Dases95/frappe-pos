// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["POS Profit Analysis"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "pos_session",
			"label": __("POS Session"),
			"fieldtype": "Link",
			"options": "POS Session"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Data"
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight negative profit in red
		if (column.fieldname === "profit_amount" && data && data.profit_amount < 0) {
			value = `<span style="color: red">${value}</span>`;
		}
		
		// Highlight low profit margin in orange
		if (column.fieldname === "profit_margin_percent" && data && data.profit_margin_percent < 10) {
			value = `<span style="color: orange">${value}</span>`;
		}
		
		// Highlight high profit margin in green
		if (column.fieldname === "profit_margin_percent" && data && data.profit_margin_percent > 30) {
			value = `<span style="color: green">${value}</span>`;
		}
		
		return value;
	},
	
	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Export to Excel"), function() {
			frappe.utils.make_event_emitter(frappe.query_report);
			return frappe.query_report.export_report();
		});
		
		report.page.add_inner_button(__("Item Wise Summary"), function() {
			show_item_wise_summary(report);
		});
		
		report.page.add_inner_button(__("Session Wise Summary"), function() {
			show_session_wise_summary(report);
		});
	}
};

function show_item_wise_summary(report) {
	let data = report.data;
	if (!data || data.length === 0) {
		frappe.msgprint(__("No data to summarize"));
		return;
	}
	
	// Group by item
	let item_summary = {};
	data.forEach(row => {
		if (!item_summary[row.item_code]) {
			item_summary[row.item_code] = {
				item_name: row.item_name,
				total_qty: 0,
				total_sales: 0,
				total_cost: 0,
				total_profit: 0
			};
		}
		
		item_summary[row.item_code].total_qty += row.qty;
		item_summary[row.item_code].total_sales += row.amount;
		item_summary[row.item_code].total_cost += row.total_cost;
		item_summary[row.item_code].total_profit += row.profit_amount;
	});
	
	// Create summary table
	let summary_html = `
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Item Code</th>
					<th>Item Name</th>
					<th>Total Qty</th>
					<th>Total Sales</th>
					<th>Total Cost</th>
					<th>Total Profit</th>
					<th>Profit %</th>
				</tr>
			</thead>
			<tbody>
	`;
	
	Object.keys(item_summary).forEach(item_code => {
		let item = item_summary[item_code];
		let profit_percent = item.total_sales > 0 ? (item.total_profit / item.total_sales * 100).toFixed(2) : 0;
		
		summary_html += `
			<tr>
				<td>${item_code}</td>
				<td>${item.item_name}</td>
				<td>${item.total_qty.toFixed(2)}</td>
				<td>${format_currency(item.total_sales)}</td>
				<td>${format_currency(item.total_cost)}</td>
				<td>${format_currency(item.total_profit)}</td>
				<td>${profit_percent}%</td>
			</tr>
		`;
	});
	
	summary_html += `
			</tbody>
		</table>
	`;
	
	frappe.msgprint({
		title: __("Item Wise Profit Summary"),
		message: summary_html,
		wide: true
	});
}

function show_session_wise_summary(report) {
	let data = report.data;
	if (!data || data.length === 0) {
		frappe.msgprint(__("No data to summarize"));
		return;
	}
	
	// Group by session
	let session_summary = {};
	data.forEach(row => {
		if (!session_summary[row.pos_session]) {
			session_summary[row.pos_session] = {
				date: row.posting_date,
				total_qty: 0,
				total_sales: 0,
				total_cost: 0,
				total_profit: 0,
				invoice_count: new Set()
			};
		}
		
		session_summary[row.pos_session].total_qty += row.qty;
		session_summary[row.pos_session].total_sales += row.amount;
		session_summary[row.pos_session].total_cost += row.total_cost;
		session_summary[row.pos_session].total_profit += row.profit_amount;
		session_summary[row.pos_session].invoice_count.add(row.invoice_name);
	});
	
	// Create summary table
	let summary_html = `
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Session</th>
					<th>Date</th>
					<th>Invoices</th>
					<th>Total Qty</th>
					<th>Total Sales</th>
					<th>Total Cost</th>
					<th>Total Profit</th>
					<th>Profit %</th>
				</tr>
			</thead>
			<tbody>
	`;
	
	Object.keys(session_summary).forEach(session => {
		let sess = session_summary[session];
		let profit_percent = sess.total_sales > 0 ? (sess.total_profit / sess.total_sales * 100).toFixed(2) : 0;
		
		summary_html += `
			<tr>
				<td>${session}</td>
				<td>${frappe.datetime.str_to_user(sess.date)}</td>
				<td>${sess.invoice_count.size}</td>
				<td>${sess.total_qty.toFixed(2)}</td>
				<td>${format_currency(sess.total_sales)}</td>
				<td>${format_currency(sess.total_cost)}</td>
				<td>${format_currency(sess.total_profit)}</td>
				<td>${profit_percent}%</td>
			</tr>
		`;
	});
	
	summary_html += `
			</tbody>
		</table>
	`;
	
	frappe.msgprint({
		title: __("Session Wise Profit Summary"),
		message: summary_html,
		wide: true
	});
}