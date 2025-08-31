frappe.pages['point-of-sale'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Point of Sale'),
		single_column: true
	});

	// Create the POS application
	new POSApp(page);
};

// Cleanup when leaving the page
frappe.pages['point-of-sale'].on_page_unload = function() {
	// Remove POS page class from body
	document.body.classList.remove('pos-page');
};

class POSApp {
	constructor(page) {
		this.page = page;
		this.wrapper = page.main;
		this.language = frappe.boot.lang || 'en';
		this.currentSession = null;
		this.posProfiles = [];
		this.products = [];
		this.cart = [];
		this.paymentMethods = [];
		this.selectedPaymentMethod = 'Cash';
		this.paidAmount = 0;
		this.productSearch = '';
		this.selectedCustomer = null;
		this.selectedPOSClient = null;
		this.posClients = [];
		
		this.setup_page();
		this.load_initial_data();
	}

	setup_page() {
		// Set up the main interface
		this.render_interface();
		this.bind_events();
	}

	render_interface() {
		// Add Tailwind CSS (scoped to POS only)
		if (!document.querySelector('link[href*="tailwindcss"]')) {
			const tailwindCSS = document.createElement('link');
			tailwindCSS.rel = 'stylesheet';
			tailwindCSS.href = 'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css';
			document.head.appendChild(tailwindCSS);
		}

		// Add POS page class to body for scoping
		document.body.classList.add('pos-page');
		
		const html = `
			<div class="pos-tailwind-container max-w-full p-6">
				<!-- Header -->
				<div class="bg-blue-600 text-white rounded-lg p-4 mb-4">
					<div class="flex justify-between items-center">
						<div class="flex-1">
							<h3 class="text-xl font-bold m-0">${__('Point of Sale')}</h3>
						</div>
						<div class="flex items-center space-x-2">
							<button class="bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm hover:bg-gray-300" id="toggle-language">
								${this.language === 'ar' ? 'English' : 'العربية'}
							</button>
							<span id="session-indicator" class="bg-green-500 text-white px-2 py-1 rounded text-sm ml-2" style="display: none;">
								${__('Session')}: <span id="session-name"></span>
							</span>
						</div>
					</div>
				</div>

				<!-- Session Start Modal -->
				<div id="session-start-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
					<div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
						<button class="absolute top-4 right-4 text-gray-500 hover:text-gray-700" type="button" onclick="document.getElementById('session-start-modal').style.display='none'">
							<span class="text-xl">&times;</span>
						</button>
						<div class="bg-white">
							<div class="border-b pb-4 mb-4">
								<h3 class="text-lg font-semibold">${__('Start POS Session')}</h3>
							</div>
							<div>
								<form id="start-session-form" class="space-y-4">
									<div>
										<label class="block text-sm font-medium text-gray-700 mb-1">${__('POS Profile')}</label>
										<div>
											<select id="pos-profile-select" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
												<option value="">${__('Select POS Profile')}</option>
											</select>
										</div>
									</div>
									<div>
										<label class="block text-sm font-medium text-gray-700 mb-1">${__('Opening Amount')} (${__('DZD')})</label>
										<div>
											<input id="opening-amount" type="number" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" min="0" value="0">
										</div>
									</div>
									<button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
										${__('Start Session')}
									</button>
								</form>
							</div>
						</div>
					</div>
				</div>

				<!-- Main POS Interface -->
				<div id="pos-interface" class="py-4" style="display: none;">
					<div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
					<!-- Products Section -->
				<div class="lg:col-span-3">
						<!-- Products Grid -->
						<div class="bg-white border border-gray-200 rounded-lg mb-4">
							<div class="border-b border-gray-200 p-4">
								<div class="flex items-center gap-4">
									<div class="flex-shrink-0">
										<h3 class="text-lg font-semibold text-gray-900 m-0">${__('Products')}</h3>
									</div>
									<div class="flex-1">
										<input id="product-search" type="text" placeholder="${__('Search by name, code, or barcode...')}" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
									</div>
									<div class="flex-shrink-0 flex gap-2">
								<button id="refresh-prices" class="bg-gray-100 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500" title="${__('Refresh Prices')}">
									💰
								</button>
								<button id="refresh-stock" class="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500" title="${__('Refresh Stock')}">
									📦
								</button>
							</div>
								</div>
							</div>
							<div class="p-4" style="max-height: 500px; overflow-y: auto;">
								<div id="products-grid" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
									<!-- Products will be loaded here -->
								</div>
							</div>
						</div>

						<!-- Shortcuts Section -->
						<div class="bg-white border border-gray-200 rounded-lg">
							<div class="border-b border-gray-200 p-4">
								<h3 class="text-lg font-semibold text-gray-900 m-0">${__('Quick Shortcuts')}</h3>
							</div>
							<div class="p-4">
								<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
									<!-- Function Shortcuts -->
									<div>
										<h4 class="text-gray-600 text-sm font-medium mb-2">${__('Functions')}</h4>
										<div id="function-shortcuts" class="space-y-2">
											<!-- Function shortcuts will be loaded here -->
										</div>
									</div>
									<!-- Payment Shortcuts -->
									<div>
										<h4 class="text-gray-600 text-sm font-medium mb-2">${__('Payments')}</h4>
										<div id="payment-shortcuts" class="space-y-2">
											<!-- Payment shortcuts will be loaded here -->
										</div>
									</div>
									<!-- Product Shortcuts -->
									<div>
										<h4 class="text-gray-600 text-sm font-medium mb-2">${__('Products')}</h4>
										<div id="product-shortcuts" class="space-y-2">
											<!-- Product shortcuts will be loaded here -->
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>

						<!-- Cart and Payment Section -->
						<div class="lg:col-span-2">
							<!-- Cart -->
							<div class="bg-white border border-gray-200 rounded-lg mb-4">
								<div class="border-b border-gray-200 p-4">
									<div class="flex items-center justify-between">
										<div>
											<h3 class="text-lg font-semibold text-gray-900 m-0">${__('Cart')}</h3>
										</div>
										<div class="flex-1 ml-4">
								<div class="relative">
									<input id="customer-search" type="text" placeholder="${__('Search customer or use Walk-in Customer...')}" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" value="${__('Walk-in Customer')}">
									<div id="customer-dropdown" class="absolute w-full" style="display: none; position: absolute; z-index: 1000; background: white; border: 1px solid #e5e5e5; max-height: 200px; overflow-y: auto; border-radius: 6px; margin-top: 2px;">
										<!-- Customer search results will appear here -->
									</div>
								</div>
							</div>
									</div>
								</div>
								<div class="p-4" style="max-height: 400px; overflow-y: auto; min-height: 250px;">
									<div id="cart-items">
										<!-- Cart items will be loaded here -->
									</div>
								</div>
								<div class="border-t border-gray-200 p-4">
									<div class="flex items-center justify-between">
										<div><strong>${__('Total')}:</strong></div>
										<div>
											<strong id="cart-total" class="text-lg text-blue-600">0.00 ${__('DZD')}</strong>
										</div>
									</div>
								</div>
							</div>

							<!-- Payment -->
							<div class="bg-white border border-gray-200 rounded-lg">
								<div class="border-b border-gray-200 p-4">
									<h3 class="text-lg font-semibold text-gray-900 m-0">${__('Payment')}</h3>
								</div>
								<div class="p-4 space-y-4">
									<!-- POS Client Selection -->
									<div>
										<label class="block text-sm font-medium text-gray-700 mb-1">${__('POS Client')}</label>
										<div class="relative">
											<input id="pos-client-search" type="text" placeholder="${__('Search client by name...')}" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
											<div id="pos-client-dropdown" class="absolute w-full" style="display: none; position: absolute; z-index: 1000; background: white; border: 1px solid #e5e5e5; max-height: 200px; overflow-y: auto; border-radius: 6px; margin-top: 2px;">
												<!-- Client search results will appear here -->
											</div>
										</div>
									</div>
									<div>
										<label class="block text-sm font-medium text-gray-700 mb-1">${__('Payment Method')}</label>
										<div>
											<select id="payment-method" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
												<option value="Cash">${__('Cash')}</option>
												<option value="Card">${__('Card')}</option>
												<option value="Bank Transfer">${__('Bank Transfer')}</option>
												<option value="Credit">${__('Credit')}</option>
											</select>
										</div>
									</div>
									<div>
										<label class="block text-sm font-medium text-gray-700 mb-1">${__('Amount Paid')} (${__('DZD')})</label>
										<div>
											<input id="paid-amount" type="number" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" min="0">
										</div>
									</div>
									<div id="change-display" class="bg-green-50 border border-green-200 rounded-md p-3" style="display: none;">
										<p class="text-sm text-green-800 m-0"><strong>${__('Change')}: <span id="change-amount">0.00 ${__('DZD')}</span></strong></p>
									</div>
									<button id="complete-sale" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed" disabled>
										${__('Complete Sale')}
									</button>
									<button id="clear-cart" class="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 mt-2">
									${__('Clear Cart')}
								</button>
								<button id="modify-invoice" class="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 mt-2">
										${__('Modify Existing Sale')}
									</button>
								</div>
							</div>
						</div>
					</div>

					<!-- Session Controls -->
					<div class="text-center mt-6">
						<button id="close-session" class="bg-gray-600 text-white py-2 px-6 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500">
							${__('Close Session')}
						</button>
					</div>
				</div>

				<!-- Invoice Selection Modal -->
				<div id="invoice-selection-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" style="display: none;">
					<div class="bg-white rounded-lg w-full max-w-4xl mx-4 max-h-screen overflow-hidden">
						<button class="absolute top-4 right-4 text-gray-500 hover:text-gray-700" type="button" onclick="document.getElementById('invoice-selection-modal').style.display='none'">
							<span class="text-xl">&times;</span>
						</button>
						<div class="bg-white">
							<div class="border-b pb-4 mb-4 p-6">
								<h3 class="text-lg font-semibold">${__('Select Invoice to Modify')}</h3>
							</div>
							<div class="p-6">
								<div class="mb-4">
									<input id="invoice-search" type="text" placeholder="${__('Search by invoice number or customer...')}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4">
								</div>
								<div id="invoice-list" style="max-height: 400px; overflow-y: auto;">
									<!-- Invoice list will be loaded here -->
								</div>
							</div>
							<div class="border-t pt-4 p-6">
								<button type="button" class="bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500" onclick="document.getElementById('invoice-selection-modal').style.display='none'">${__('Cancel')}</button>
							</div>
						</div>
					</div>
				</div>

				<!-- Receipt Modal -->
				<div id="receipt-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" style="display: none;">
					<div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
						<button class="absolute top-4 right-4 text-gray-500 hover:text-gray-700" type="button" onclick="document.getElementById('receipt-modal').style.display='none'">
							<span class="text-xl">&times;</span>
						</button>
						<div class="bg-white">
							<div class="border-b pb-4 mb-4">
								<h3 class="text-lg font-semibold">${__('Sales Receipt')}</h3>
							</div>
							<div class="mb-4">
								<div id="receipt-content">
									<!-- Receipt content will be generated here -->
								</div>
							</div>
							<div class="border-t pt-4">
								<button id="print-receipt" class="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 mr-2">${__('Print')}</button>
								<button type="button" class="bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500" onclick="document.getElementById('receipt-modal').style.display='none'">${__('Close')}</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		$(this.wrapper).html(html);
	}

	bind_events() {
		const self = this;

		// Toggle language
		$('#toggle-language').on('click', function() {
			self.toggle_language();
		});

		// Start session form
		$('#start-session-form').on('submit', function(e) {
			e.preventDefault();
			self.start_session();
		});

		// Product search
		$('#product-search').on('input', function() {
			self.productSearch = $(this).val();
			self.render_products();
		});

		// Customer search
		$('#customer-search').on('input', function() {
			const query = $(this).val();
			if (query.length >= 2 && query !== __('Walk-in Customer')) {
				self.search_customers(query);
			} else {
				$('#customer-dropdown').hide();
			}
		});

		// Hide dropdowns when clicking outside
		$(document).on('click', function(e) {
			if (!$(e.target).closest('#customer-search, #customer-dropdown').length) {
				$('#customer-dropdown').hide();
			}
			if (!$(e.target).closest('#pos-client-search, #pos-client-dropdown').length) {
				$('#pos-client-dropdown').hide();
			}
		});

		// POS Client search
		$('#pos-client-search').on('input', function() {
			const query = $(this).val();
			if (query.length >= 2) {
				self.search_pos_clients(query);
			} else {
				$('#pos-client-dropdown').hide();
			}
		});

		// Payment amount input
		$('#paid-amount').on('input', function() {
			self.paidAmount = parseFloat($(this).val()) || 0;
			self.update_change_display();
			self.update_complete_sale_button();
		});

		// Complete sale
		$('#complete-sale').on('click', function() {
			self.complete_sale();
		});

		// Clear cart
		$('#clear-cart').on('click', function() {
			self.clear_cart();
		});

		// Close session
		$('#close-session').on('click', function() {
			self.close_session();
		});

		// Print receipt
		$('#print-receipt').on('click', function() {
			self.print_receipt();
		});

		// Refresh prices
		$('#refresh-prices').on('click', function() {
			self.refresh_product_prices();
		});

		// Refresh stock
		$('#refresh-stock').on('click', function() {
			self.refresh_product_stock(true);
		});

		// Customer selection
		$('#customer-select').on('change', function() {
			self.selectedCustomer = $(this).val() || null;
			self.refresh_product_prices(); // Refresh prices when customer changes
		});

		// Payment method selection
		$('#payment-method').on('change', function() {
			self.selectedPaymentMethod = $(this).val();
			self.handle_payment_method_change();
		});

		// POS Client search
		$('#pos-client-search').on('input', function() {
			self.search_pos_clients($(this).val());
		});

		// Hide client dropdown when clicking outside
		$(document).on('click', function(e) {
			if (!$(e.target).closest('#pos-client-search, #pos-client-dropdown').length) {
				$('#pos-client-dropdown').hide();
			}
		});

		// Modify invoice
		$('#modify-invoice').on('click', function() {
			self.show_invoice_selection_modal();
		});

		// Invoice search
		$('#invoice-search').on('input', function() {
			self.filter_invoice_list($(this).val());
		});
	}

	async load_initial_data() {
		try {
			// Load POS profiles
			const profiles = await frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'POS Profile',
					fields: ['name', 'profile_name', 'currency', 'company_name', 'warehouse_name'],
					limit_page_length: 0
				}
			});

			this.posProfiles = profiles.message || [];
			this.populate_pos_profiles();

			// Check for existing open session
			await this.check_existing_session();

		} catch (error) {
			frappe.msgprint(__('Error loading initial data: ') + error.message);
		}
	}

	populate_pos_profiles() {
		const select = $('#pos-profile-select');
		select.empty().append('<option value="">' + __('Select POS Profile') + '</option>');
		
		this.posProfiles.forEach(profile => {
			select.append(`<option value="${profile.name}">${profile.profile_name}</option>`);
		});
	}

	async check_existing_session() {
		try {
			const response = await frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'POS Session',
					fields: ['name', 'pos_profile', 'status'],
					filters: [
						['user', '=', frappe.session.user],
						['status', '=', 'Open']
					],
					limit_page_length: 1
				}
			});

			if (response.message && response.message.length > 0) {
				this.currentSession = response.message[0];
				this.show_pos_interface();
				await this.load_pos_data();
			}
		} catch (error) {
			console.error('Error checking existing session:', error);
		}
	}

	async start_session() {
		const profileName = $('#pos-profile-select').val();
		const openingAmount = parseFloat($('#opening-amount').val()) || 0;

		if (!profileName) {
			frappe.msgprint(__('Please select a POS Profile'));
			return;
		}

		try {
			const response = await frappe.call({
				method: 'inventory.pos.doctype.pos_session.pos_session.create_opening_entry',
				args: {
					pos_profile: profileName,
					opening_amount: openingAmount
				}
			});

			if (response.message) {
				this.currentSession = response.message;
				this.show_toast(__('Session started successfully!'), 'success');
				this.show_pos_interface();
				await this.load_pos_data();
			}
		} catch (error) {
			this.show_toast(__('Error starting session: ') + error.message, 'error');
		}
	}

	show_pos_interface() {
		// Hide session modal
		document.getElementById('session-start-modal').style.display = 'none';
		$('#pos-interface').show();
		$('#session-indicator').show();
		$('#session-name').text(this.currentSession.name);
		
		// Set payment method to default (Cash)
		$('#payment-method').val(this.selectedPaymentMethod);
	}

	async load_pos_data() {
		try {
			// Get current warehouse from session
			const warehouse = this.currentSession?.warehouse || null;
			
			// Load products with stock information using the dedicated POS API
			const products = await frappe.call({
				method: 'inventory.pos.api.get_pos_items',
				args: {
					warehouse: warehouse,
					search_term: ''
				}
			});

			// Map the products to include available_qty from stock_qty
			this.products = (products.message || []).map(item => ({
				...item,
				available_qty: item.stock_qty || 0
			}));

			this.render_products();

		} catch (error) {
			frappe.msgprint(__('Error loading products: ') + error.message);
		}
		
		// Load customers
		await this.load_customers();
		
		// Load POS clients
		await this.load_pos_clients();
		
		// Load shortcuts
		await this.load_shortcuts();
	}

	async load_customers() {
		// This method is no longer needed as we use search-based customer selection
		// Keeping it for backward compatibility but it doesn't populate any dropdown
	}

	async search_customers(query, page = 1) {
		if (!query || query.length < 2) {
			$('#customer-dropdown').hide();
			return;
		}

		try {
			const response = await frappe.call({
				method: 'inventory.pos.api.search_customers',
				args: {
					search_term: query
				}
			});

			const allCustomers = response.message || [];
			this.currentCustomerSearch = {
				query: query,
				allResults: allCustomers,
				currentPage: page,
				itemsPerPage: 5
			};
			this.render_customer_dropdown();
		} catch (error) {
			console.error('Error searching customers:', error);
			$('#customer-dropdown').hide();
		}
	}

	render_customer_dropdown() {
		const dropdown = $('#customer-dropdown');
		dropdown.empty();

		if (!this.currentCustomerSearch || this.currentCustomerSearch.allResults.length === 0) {
			dropdown.append('<div class="p-3 text-gray-500">' + __('No customers found') + '</div>');
			dropdown.show();
			return;
		}

		const { allResults, currentPage, itemsPerPage } = this.currentCustomerSearch;
		const totalPages = Math.ceil(allResults.length / itemsPerPage);
		const startIndex = (currentPage - 1) * itemsPerPage;
		const endIndex = startIndex + itemsPerPage;
		const currentPageResults = allResults.slice(startIndex, endIndex);

		// Add pagination header
		const header = $(`
			<div class="p-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center text-sm">
				<span class="text-gray-600">${__('Page')} ${currentPage} ${__('of')} ${totalPages} (${allResults.length} ${__('total')})</span>
				<div class="flex gap-1">
					<button class="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 ${currentPage === 1 ? 'opacity-50 cursor-not-allowed' : ''}" id="customer-prev-page" ${currentPage === 1 ? 'disabled' : ''}>
						<i class="fa fa-chevron-left"></i>
					</button>
					<button class="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 ${currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : ''}" id="customer-next-page" ${currentPage === totalPages ? 'disabled' : ''}>
						<i class="fa fa-chevron-right"></i>
					</button>
				</div>
			</div>
		`);
		dropdown.append(header);

		// Add pagination event handlers
		header.find('#customer-prev-page').on('click', (e) => {
			e.preventDefault();
			if (currentPage > 1) {
				this.search_customers(this.currentCustomerSearch.query, currentPage - 1);
			}
		});

		header.find('#customer-next-page').on('click', (e) => {
			e.preventDefault();
			if (currentPage < totalPages) {
				this.search_customers(this.currentCustomerSearch.query, currentPage + 1);
			}
		});

		// Add current page results
		currentPageResults.forEach(customer => {
			const item = $(`
				<div class="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100" data-customer="${customer.name}">
					<div><strong class="text-gray-900">${customer.customer_name}</strong></div>
					<small class="text-gray-500">${customer.customer_type || ''}</small>
				</div>
			`);
			
			item.on('click', () => {
				this.select_customer(customer);
			});
			
			dropdown.append(item);
		});

		dropdown.show();
	}

	select_customer(customer) {
		this.selectedCustomer = customer.name;
		$('#customer-search').val(customer.customer_name);
		$('#customer-dropdown').hide();
	}

	async load_pos_clients() {
		try {
			const clients = await frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'POS Client',
					fields: ['name', 'full_name', 'first_name', 'last_name', 'allow_credit', 'credit_limit', 'current_balance'],
					filters: [['status', '=', 'Active']],
					limit_page_length: 0,
					order_by: 'full_name'
				}
			});

			this.posClients = clients.message || [];
		} catch (error) {
			console.error('Error loading POS clients:', error);
			this.posClients = [];
		}
	}

	async search_pos_clients(query, page = 1) {
		if (!query || query.length < 2) {
			$('#pos-client-dropdown').hide();
			return;
		}

		try {
			const response = await frappe.call({
				method: 'inventory.pos.doctype.pos_client.pos_client.search_pos_clients',
				args: {
					search_term: query,
					limit: 50 // Get more results for pagination
				}
			});

			const allClients = response.message || [];
			this.currentClientSearch = {
				query: query,
				allResults: allClients,
				currentPage: page,
				itemsPerPage: 5
			};
			this.render_client_dropdown();
		} catch (error) {
			console.error('Error searching POS clients:', error);
			$('#pos-client-dropdown').hide();
		}
	}

	render_client_dropdown() {
		const dropdown = $('#pos-client-dropdown');
		dropdown.empty();

		if (!this.currentClientSearch || this.currentClientSearch.allResults.length === 0) {
			dropdown.append('<div class="p-3 text-gray-500">' + __('No clients found') + '</div>');
			dropdown.show();
			return;
		}

		const { allResults, currentPage, itemsPerPage } = this.currentClientSearch;
		const totalPages = Math.ceil(allResults.length / itemsPerPage);
		const startIndex = (currentPage - 1) * itemsPerPage;
		const endIndex = startIndex + itemsPerPage;
		const currentPageResults = allResults.slice(startIndex, endIndex);

		// Add pagination header
		const header = $(`
			<div class="p-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center text-sm">
				<span class="text-gray-600">${__('Page')} ${currentPage} ${__('of')} ${totalPages} (${allResults.length} ${__('total')})</span>
				<div class="flex gap-1">
					<button class="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 ${currentPage === 1 ? 'opacity-50 cursor-not-allowed' : ''}" id="prev-page" ${currentPage === 1 ? 'disabled' : ''}>
						<i class="fa fa-chevron-left"></i>
					</button>
					<button class="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 ${currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : ''}" id="next-page" ${currentPage === totalPages ? 'disabled' : ''}>
						<i class="fa fa-chevron-right"></i>
					</button>
				</div>
			</div>
		`);
		dropdown.append(header);

		// Add pagination event handlers
		header.find('#prev-page').on('click', (e) => {
			e.preventDefault();
			if (currentPage > 1) {
				this.search_pos_clients(this.currentClientSearch.query, currentPage - 1);
			}
		});

		header.find('#next-page').on('click', (e) => {
			e.preventDefault();
			if (currentPage < totalPages) {
				this.search_pos_clients(this.currentClientSearch.query, currentPage + 1);
			}
		});

		// Add current page results
		currentPageResults.forEach(client => {
			const creditInfo = client.allow_credit ? 
				`<small class="text-gray-500 block">Credit: ${this.format_currency(client.credit_limit - client.current_balance)} available</small>` : '';
			
			const item = $(`
				<div class="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100" data-client="${client.name}">
					<div><strong class="text-gray-900">${client.full_name}</strong></div>
					${creditInfo}
				</div>
			`);
			
			item.on('click', () => {
				this.select_pos_client(client);
			});
			
			dropdown.append(item);
		});

		dropdown.show();
	}

	select_pos_client(client) {
		this.selectedPOSClient = client;
		$('#pos-client-search').val(client.full_name);
		$('#pos-client-dropdown').hide();
		
		// Enable credit payment if client allows it
		if (client.allow_credit) {
			$('#payment-method option[value="Credit"]').prop('disabled', false);
		} else {
			$('#payment-method option[value="Credit"]').prop('disabled', true);
			if (this.selectedPaymentMethod === 'Credit') {
				this.selectedPaymentMethod = 'Cash';
				$('#payment-method').val('Cash');
			}
		}
	}

	handle_payment_method_change() {
		if (this.selectedPaymentMethod === 'Credit') {
			if (!this.selectedPOSClient) {
				frappe.msgprint(__('Please select a POS client for credit payment'));
				this.selectedPaymentMethod = 'Cash';
				$('#payment-method').val('Cash');
				return;
			}
			
			if (!this.selectedPOSClient.allow_credit) {
				frappe.msgprint(__('Selected client is not allowed for credit payments'));
				this.selectedPaymentMethod = 'Cash';
				$('#payment-method').val('Cash');
				return;
			}
			
			// For credit payment, set paid amount to 0
			$('#paid-amount').val(0).prop('disabled', true);
			this.paidAmount = 0;
		} else {
			// Enable paid amount input for other payment methods
			$('#paid-amount').prop('disabled', false);
		}
		
		this.update_change_display();
		this.update_complete_sale_button();
	}

	async get_item_prices(itemCodes) {
		try {
			// Use the new dedicated API for POS price fetching
			const response = await frappe.call({
				method: 'inventory.inventory.doctype.item_price.item_price.get_item_prices_for_pos',
				args: {
					item_codes: itemCodes,
					customer: this.selectedCustomer || null
				}
			});

			return response.message || {};
		} catch (error) {
			console.error('Error fetching item prices:', error);
			// Show a warning to the user if prices couldn't be loaded
			if (itemCodes.length > 0) {
				this.show_toast(__('Warning: Could not load item prices. Using fallback pricing.'), 'warning');
			}
			return {};
		}
	}

	async refresh_product_prices() {
		try {
			// Show loading state
			const refreshBtn = $('#refresh-prices');
			const originalContent = refreshBtn.html();
			refreshBtn.html('<i class="fa fa-spinner fa-spin"></i>').prop('disabled', true);
			
			// Get current item codes
			const itemCodes = this.products.map(item => item.item_code);
			
			// Fetch updated prices
			const prices = await this.get_item_prices(itemCodes);
			
			// Update product prices
			this.products.forEach(product => {
				product.standard_rate = prices[product.item_code] || 0;
			});
			
			// Re-render products
			this.render_products();
			
			this.show_toast(__('Product prices refreshed'), 'success');
		} catch (error) {
			console.error('Error refreshing product prices:', error);
			this.show_toast(__('Error refreshing prices'), 'error');
		} finally {
			// Restore button state
			const refreshBtn = $('#refresh-prices');
			refreshBtn.html('<i class="fa fa-refresh"></i>').prop('disabled', false);
		}
	}

	async refresh_product_stock(showLoadingState = false) {
		try {
			// Show loading state if manually triggered
			if (showLoadingState) {
				const refreshBtn = $('#refresh-stock');
				const originalContent = refreshBtn.html();
				refreshBtn.html('⏳').prop('disabled', true);
			}
			
			// Add a delay to ensure stock updates are committed to database
			const delay = showLoadingState ? 200 : 1000; // Shorter delay for manual refresh
			await new Promise(resolve => setTimeout(resolve, delay));
			
			// Get current warehouse from session
			const warehouse = this.currentSession?.warehouse || null;
			
			// Reload products with updated stock information
			const products = await frappe.call({
				method: 'inventory.pos.api.get_pos_items',
				args: {
					warehouse: warehouse,
					search_term: ''
				}
			});

			// Update products with fresh stock data
			const oldProducts = [...this.products];
			this.products = (products.message || []).map(item => ({
				...item,
				available_qty: item.stock_qty || 0
			}));

			// Check if stock actually changed and show feedback
			let stockChanged = false;
			for (let i = 0; i < this.products.length; i++) {
				const oldProduct = oldProducts.find(p => p.item_code === this.products[i].item_code);
				if (oldProduct && oldProduct.available_qty !== this.products[i].available_qty) {
					stockChanged = true;
					break;
				}
			}

			// Re-render products to show updated stock
			this.render_products();
			
			// Show feedback based on context
			if (showLoadingState) {
				if (stockChanged) {
					this.show_toast(__('Stock levels refreshed successfully'), 'success');
				} else {
					this.show_toast(__('Stock levels are up to date'), 'info');
				}
			} else if (stockChanged) {
				this.show_toast(__('Stock levels updated'), 'info');
			}
			
		} catch (error) {
			console.error('Error refreshing product stock:', error);
			// Show error if stock refresh fails
			this.show_toast(__('Failed to refresh stock levels'), 'warning');
		} finally {
			// Restore button state if manually triggered
			if (showLoadingState) {
				const refreshBtn = $('#refresh-stock');
				refreshBtn.html('📦').prop('disabled', false);
			}
		}
	}

	async load_shortcuts() {
		try {
					const shortcuts_response = await frappe.call({
			method: 'inventory.doctype.pos_shortcut.pos_shortcut.get_all_shortcuts'
		});

			this.shortcuts = shortcuts_response.message || {};
			this.render_shortcuts();
			this.bind_shortcut_events();
		} catch (error) {
			console.log('Error loading shortcuts:', error);
		}
	}

	render_shortcuts() {
		// Render function shortcuts
		const functionContainer = $('#function-shortcuts');
		functionContainer.empty();
		
		this.shortcuts.functions?.forEach(shortcut => {
			const shortcutBtn = $(`
				<button class="bg-blue-50 border border-blue-200 text-blue-700 px-3 py-2 rounded-md text-sm hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 shortcut-btn w-full" 
						data-shortcut-key="${shortcut.shortcut_key}" 
						data-shortcut-type="function" 
						data-action="${shortcut.action_type}"
						title="${shortcut.shortcut_name} (${shortcut.shortcut_key})">
					<strong>${shortcut.shortcut_key}</strong><br>
					<small>${shortcut.shortcut_name}</small>
				</button>
			`);
			functionContainer.append(shortcutBtn);
		});

		// Render payment shortcuts
		const paymentContainer = $('#payment-shortcuts');
		paymentContainer.empty();
		
		this.shortcuts.payments?.forEach(shortcut => {
			const shortcutBtn = $(`
				<button class="bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded-md text-sm hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500 shortcut-btn w-full" 
						data-shortcut-key="${shortcut.shortcut_key}" 
						data-shortcut-type="payment" 
						data-method="${shortcut.shortcut_name}"
						title="${shortcut.shortcut_name} (${shortcut.shortcut_key})">
					<strong>${shortcut.shortcut_key}</strong><br>
					<small>${shortcut.shortcut_name}</small>
				</button>
			`);
			paymentContainer.append(shortcutBtn);
		});

		// Render product shortcuts
		const productContainer = $('#product-shortcuts');
		productContainer.empty();
		
		this.shortcuts.products?.forEach(shortcut => {
			const shortcutBtn = $(`
				<button class="bg-cyan-50 border border-cyan-200 text-cyan-700 px-3 py-2 rounded-md text-sm hover:bg-cyan-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 shortcut-btn w-full" 
						data-shortcut-key="${shortcut.shortcut_key}" 
						data-shortcut-type="product" 
						data-item-code="${shortcut.item_code}"
						data-item-name="${shortcut.item_name}"
						title="${shortcut.item_name} (${shortcut.shortcut_key})">
					<strong>${shortcut.shortcut_key}</strong><br>
					<small>${shortcut.item_name}</small>
				</button>
			`);
			productContainer.append(shortcutBtn);
		});
	}

	bind_shortcut_events() {
		const self = this;

		// Bind click events for shortcut buttons
		$('.shortcut-btn').on('click', function() {
			const shortcutType = $(this).data('shortcut-type');
			const shortcutKey = $(this).data('shortcut-key');

			if (shortcutType === 'function') {
				const action = $(this).data('action');
				self.execute_function_shortcut(action);
			} else if (shortcutType === 'payment') {
				const method = $(this).data('method');
				self.execute_payment_shortcut(method);
			} else if (shortcutType === 'product') {
				const itemCode = $(this).data('item-code');
				const itemName = $(this).data('item-name');
				self.execute_product_shortcut(itemCode, itemName);
			}
		});

		// Bind keyboard events
		$(document).on('keydown', function(e) {
			const key = e.key;
			const functionKey = e.key.startsWith('F') ? e.key : null;
			
			// Check if any shortcut matches the pressed key
			const allShortcuts = [
				...(self.shortcuts.functions || []),
				...(self.shortcuts.payments || []),
				...(self.shortcuts.products || [])
			];

			const matchingShortcut = allShortcuts.find(s => s.shortcut_key === key || s.shortcut_key === functionKey);
			
			if (matchingShortcut) {
				e.preventDefault();
				self.execute_shortcut_by_key(matchingShortcut);
			}
		});
	}

	execute_shortcut_by_key(shortcut) {
		if (shortcut.shortcut_type === 'Function') {
			this.execute_function_shortcut(shortcut.action_type);
		} else if (shortcut.shortcut_type === 'Payment') {
			this.execute_payment_shortcut(shortcut.shortcut_name);
		} else if (shortcut.shortcut_type === 'Product') {
			this.execute_product_shortcut(shortcut.item_code, shortcut.item_name);
		}
	}

	execute_function_shortcut(action) {
		switch (action) {
			case 'New Sale':
				this.clear_cart();
				break;
			case 'Clear Cart':
				this.clear_cart();
				break;
			case 'Print Receipt':
				this.print_receipt();
				break;
			case 'Close Session':
				this.close_session();
				break;
			case 'Toggle Language':
				this.toggle_language();
				break;
		}
		this.show_toast(__('Function executed: ') + action, 'info');
	}

	execute_payment_shortcut(method) {
		$('#payment-method').val(method);
		this.selectedPaymentMethod = method;
		this.show_toast(__('Payment method set to: ') + method, 'info');
	}

	execute_product_shortcut(itemCode, itemName) {
		// Find the product in the products list
		const product = this.products.find(p => p.item_code === itemCode);
		if (product) {
			this.add_to_cart(product);
		} else {
			// Create a temporary product object with price lookup
			this.add_product_with_price_lookup(itemCode, itemName);
		}
	}

	async add_product_with_price_lookup(itemCode, itemName) {
		try {
			// Fetch price for this specific item
			const prices = await this.get_item_prices([itemCode]);
			const price = prices[itemCode] || 0;
			
			const tempProduct = {
				item_code: itemCode,
				item_name: itemName,
				standard_rate: price
			};
			this.add_to_cart(tempProduct);
		} catch (error) {
			console.error('Error fetching price for product shortcut:', error);
			// Add with zero price if price lookup fails
			const tempProduct = {
				item_code: itemCode,
				item_name: itemName,
				standard_rate: 0
			};
			this.add_to_cart(tempProduct);
		}
	}

	render_products() {
		const grid = $('#products-grid');
		grid.empty();

		const filteredProducts = this.products.filter(product => {
			if (!this.productSearch) return true;
			const search = this.productSearch.toLowerCase();
			return product.item_name.toLowerCase().includes(search) ||
				   product.item_code.toLowerCase().includes(search) ||
				   (product.barcode && product.barcode.toLowerCase().includes(search));
		});

		const self = this; // Store reference to this

		filteredProducts.forEach(product => {
			const price = product.standard_rate || 0;
			const hasPrice = price > 0;
			const stockQty = product.available_qty || 0;
			const isOutOfStock = stockQty <= 0;
			const isLowStock = stockQty > 0 && stockQty <= 5;
			
			const productCard = $(`
				<div class="bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow product-card ${isOutOfStock ? 'out-of-stock opacity-50' : ''}" style="cursor: pointer;" tabindex="0">
					<div class="p-3">
						<h3 class="text-sm font-semibold text-gray-900 mb-1 line-clamp-2">${product.item_name}</h3>
						<p class="text-xs text-gray-500 mb-1">${product.item_code}</p>
						${product.barcode ? `<p class="text-xs text-gray-500 mb-2"><i class="fa fa-barcode"></i> ${product.barcode}</p>` : ''}
						<div class="product-price text-sm font-medium ${hasPrice ? 'text-blue-600' : 'text-gray-400'} mb-1">${hasPrice ? self.format_currency(price) : __('No Price Set')}</div>
						<div class="product-stock text-xs ${isOutOfStock ? 'text-red-600' : isLowStock ? 'text-yellow-600' : 'text-gray-500'}">
							${__('Stock')}: ${stockQty}
							${isOutOfStock ? ' - ' + __('Out of Stock') : isLowStock ? ' - ' + __('Low Stock') : ''}
						</div>
					</div>
				</div>
			`);

			// Handle click and keyboard events
			productCard.on('click keypress', function(e) {
				if (e.type === 'keypress' && e.which !== 13) return;
				
				// Prevent adding out-of-stock items
				if (isOutOfStock) {
					self.show_toast(__('Item is out of stock'), 'warning');
					return;
				}
				
				// Add click animation
				$(this).addClass('product-clicked');
				setTimeout(() => $(this).removeClass('product-clicked'), 200);
				self.add_to_cart(product);
			});
			
			// Add hover effect for low stock warning
			if (isLowStock) {
				productCard.on('mouseenter', function() {
					self.show_toast(__('Low stock warning: Only {0} items remaining').replace('{0}', stockQty), 'warning');
				});
			}

			grid.append(productCard);
		});
	}

	add_to_cart(product) {
		const existingItem = this.cart.find(item => item.item_code === product.item_code);
		
		if (existingItem) {
			existingItem.qty += 1;
			existingItem.amount = existingItem.qty * existingItem.rate;
		} else {
			this.cart.push({
				item_code: product.item_code,
				item_name: product.item_name,
				qty: 1,
				rate: product.standard_rate || 0,
				amount: product.standard_rate || 0
			});
		}

		this.render_cart();
		this.update_cart_total();
		this.update_complete_sale_button();
		
		// Show success feedback
		this.show_toast(__('Added to cart: ') + product.item_name, 'success');
		
		// Add cart animation
		$('#cart-total').addClass('number-change');
		setTimeout(() => $('#cart-total').removeClass('number-change'), 300);
	}

	render_cart() {
		const cartContainer = $('#cart-items');
		cartContainer.empty();

		if (this.cart.length === 0) {
			cartContainer.html(`
				<div class="text-center py-5">
					<div class="mb-3" style="font-size: 48px; color: var(--text-light);">🛒</div>
					<h6 class="text-muted">${__('Cart is empty')}</h6>
					<small class="text-muted">${__('Add products to get started')}</small>
				</div>
			`);
			return;
		}

		this.cart.forEach((item, index) => {
			const cartItem = $(`
				<div class="cart-item mb-3">
					<div class="row align-items-start">
						<div class="col-12">
							<div class="d-flex justify-content-between align-items-start mb-2">
								<div>
									<div class="font-weight-bold text-dark">${item.item_name}</div>
									<small class="text-muted">${item.item_code}</small>
								</div>
								<button class="btn btn-sm btn-link text-danger p-0 remove-item" style="font-size: 18px; line-height: 1;">×</button>
							</div>
						</div>
						<div class="col-12">
							<div class="row align-items-center">
								<div class="col-6">
									<div class="input-group input-group-sm">
										<div class="input-group-prepend">
											<button class="btn btn-outline-secondary qty-minus" type="button">-</button>
										</div>
										<input type="text" class="form-control text-center" value="${item.qty}" readonly>
										<div class="input-group-append">
											<button class="btn btn-outline-secondary qty-plus" type="button">+</button>
										</div>
									</div>
								</div>
								<div class="col-6 text-right">
									<div class="font-weight-bold text-primary" style="font-size: 16px;">${this.format_currency(item.amount)}</div>
									<small class="text-muted">${this.format_currency(item.rate)} ${__('each')}</small>
								</div>
							</div>
						</div>
					</div>
				</div>
			`);

			cartItem.find('.qty-minus').on('click', () => {
				this.update_quantity(index, -1);
			});

			cartItem.find('.qty-plus').on('click', () => {
				this.update_quantity(index, 1);
			});

			cartItem.find('.remove-item').on('click', () => {
				this.remove_from_cart(index);
			});

			cartContainer.append(cartItem);
		});
	}

	update_quantity(index, change) {
		const item = this.cart[index];
		item.qty = Math.max(1, item.qty + change);
		item.amount = item.qty * item.rate;
		
		this.render_cart();
		this.update_cart_total();
		this.update_complete_sale_button();
	}

	remove_from_cart(index) {
		this.cart.splice(index, 1);
		this.render_cart();
		this.update_cart_total();
		this.update_complete_sale_button();
	}

	clear_cart() {
		this.cart = [];
		this.paidAmount = 0;
		this.modifyingInvoice = null;
		this.selectedCustomer = null;
		this.selectedPOSClient = null;
		$('#paid-amount').val('').prop('disabled', false);
		$('#customer-select').val('');
		$('#pos-client-search').val('');
		$('#pos-client-dropdown').hide();
		$('#payment-method').val('Cash');
		this.selectedPaymentMethod = 'Cash';
		$('#complete-sale').text(__('Complete Sale'));
		this.render_cart();
		this.update_cart_total();
		this.update_complete_sale_button();
		this.update_change_display();
	}

	update_cart_total() {
		const total = this.cart.reduce((sum, item) => sum + item.amount, 0);
		$('#cart-total').text(this.format_currency(total));
		
		// Update paid amount minimum
		$('#paid-amount').attr('min', total);
		
		// Only auto-update paid amount if not modifying an existing invoice
		if (!this.modifyingInvoice && this.paidAmount < total) {
			$('#paid-amount').val(total);
			this.paidAmount = total;
		}
		
		this.update_change_display();
	}

	update_change_display() {
		const total = this.cart.reduce((sum, item) => sum + item.amount, 0);
		const change = Math.max(0, this.paidAmount - total);
		
		if (change > 0) {
			$('#change-amount').text(this.format_currency(change));
			$('#change-display').show();
		} else {
			$('#change-display').hide();
		}
	}

	update_complete_sale_button() {
		const total = this.cart.reduce((sum, item) => sum + item.amount, 0);
		let canComplete = false;
		
		if (this.cart.length > 0) {
			if (this.selectedPaymentMethod === 'Credit') {
				// For credit payment, check if client is selected and has sufficient credit
				if (this.selectedPOSClient && this.selectedPOSClient.allow_credit) {
					const availableCredit = this.selectedPOSClient.credit_limit - this.selectedPOSClient.current_balance;
					canComplete = total <= availableCredit;
				}
			} else {
				// For other payment methods, check if paid amount is sufficient
				canComplete = this.paidAmount >= total;
			}
		}
		
		$('#complete-sale').prop('disabled', !canComplete);
	}

	async complete_sale() {
		if (this.cart.length === 0) {
			frappe.msgprint(__('Cart is empty'));
			return;
		}

		if (!this.currentSession || !this.currentSession.name) {
			frappe.msgprint(__('No active session found. Please start a session first.'));
			return;
		}

		const total = this.cart.reduce((sum, item) => sum + item.amount, 0);
		
		// Validate payment based on method
		if (this.selectedPaymentMethod === 'Credit') {
			if (!this.selectedPOSClient) {
				frappe.msgprint(__('Please select a POS client for credit payment'));
				return;
			}
			
			// Validate credit limit
			const availableCredit = this.selectedPOSClient.credit_limit - this.selectedPOSClient.current_balance;
			if (total > availableCredit) {
				frappe.msgprint(__(`Insufficient credit limit. Available: ${availableCredit}, Required: ${total}`));
				return;
			}
		} else {
			if (this.paidAmount < total) {
				frappe.msgprint(__('Insufficient payment amount'));
				return;
			}
		}

		try {
			let response;
			
			if (this.modifyingInvoice) {
				// Update existing invoice
				response = await frappe.call({
					method: 'inventory.pos.api.update_pos_invoice',
					args: {
						invoice_name: this.modifyingInvoice,
						items: this.cart,
						payments: [{
							payment_method: $('#payment-method').val(),
							amount: this.paidAmount
						}],
						customer: this.selectedCustomer || 'Walk-in Customer',
						pos_client: this.selectedPOSClient ? this.selectedPOSClient.name : null
					}
				});
				
				if (response.message && response.message.success) {
					this.show_toast(__('Invoice updated successfully!'), 'success');
					this.show_receipt({
						name: response.message.new_invoice,
						cancelled_invoice: response.message.cancelled_invoice
					});
					this.clear_cart();
					this.modifyingInvoice = null;
					$('#complete-sale').text(__('Complete Sale'));
					// Refresh product stock after successful invoice update
					await this.refresh_product_stock();
				}
			} else {
				// Create new invoice
				response = await frappe.call({
					method: 'inventory.pos.doctype.pos_invoice.pos_invoice.create_pos_invoice',
					args: {
						pos_profile: this.currentSession.pos_profile,
						pos_session: this.currentSession.name,
						items: this.cart,
						payments: [{
							payment_method: $('#payment-method').val(),
							amount: this.paidAmount
						}],
						customer: this.selectedCustomer || 'Walk-in Customer',
						pos_client: this.selectedPOSClient ? this.selectedPOSClient.name : null
					}
				});

				if (response.message) {
					this.show_toast(__('Sale completed successfully!'), 'success');
					this.show_receipt(response.message);
					this.clear_cart();
					// Refresh product stock after successful sale
					await this.refresh_product_stock();
				}
			}

		} catch (error) {
			frappe.msgprint(__('Error completing sale: ') + error.message);
		}
	}

	show_receipt(invoice) {
		const total = this.cart.reduce((sum, item) => sum + item.amount, 0);
		const change = Math.max(0, this.paidAmount - total);

		let receiptHtml = `
			<div class="text-center mb-3">
				<h6>${__('Sales Receipt')}</h6>
				<small>${__('Invoice')}: ${invoice.name}</small>
			</div>
		`;

		this.cart.forEach(item => {
			receiptHtml += `
				<div class="row mb-1">
					<div class="col-8">${item.item_name} (${item.qty})</div>
					<div class="col-4 text-right">${this.format_currency(item.amount)}</div>
				</div>
			`;
		});

		receiptHtml += `
			<hr>
			<div class="row font-weight-bold">
				<div class="col-6">${__('Total')}:</div>
				<div class="col-6 text-right">${this.format_currency(total)}</div>
			</div>
			<div class="row">
				<div class="col-6">${__('Paid')}:</div>
				<div class="col-6 text-right">${this.format_currency(this.paidAmount)}</div>
			</div>
		`;

		if (change > 0) {
			receiptHtml += `
				<div class="row">
					<div class="col-6">${__('Change')}:</div>
					<div class="col-6 text-right">${this.format_currency(change)}</div>
				</div>
			`;
		}

		$('#receipt-content').html(receiptHtml);
		
		// Show modal using standard JavaScript
		document.getElementById('receipt-modal').style.display = 'flex';
	}

	print_receipt() {
		const printContent = $('#receipt-content').html();
		const printWindow = window.open('', '_blank');
		printWindow.document.write(`
			<html>
				<head>
					<title>${__('Receipt')}</title>
					<style>
						body { font-family: Arial, sans-serif; margin: 20px; }
						.row { display: flex; justify-content: space-between; margin-bottom: 5px; }
						hr { margin: 10px 0; }
						.text-center { text-align: center; }
						.font-weight-bold { font-weight: bold; }
					</style>
				</head>
				<body>
					${printContent}
				</body>
			</html>
		`);
		printWindow.document.close();
		printWindow.print();
	}

	async close_session() {
		if (!this.currentSession) return;

		const confirmed = await frappe.confirm(__('Are you sure you want to close the current session?'));
		if (!confirmed) return;

		try {
			await frappe.call({
				method: 'inventory.pos.doctype.pos_session.pos_session.close_session',
				args: {
					session_name: this.currentSession.name
				}
			});

			frappe.msgprint(__('Session closed successfully'));
			this.currentSession = null;
			$('#pos-interface').hide();
			// Show session modal using standard JavaScript
			document.getElementById('session-start-modal').style.display = 'flex';
			$('#session-indicator').hide();

		} catch (error) {
			frappe.msgprint(__('Error closing session: ') + error.message);
		}
	}

	toggle_language() {
		// Simple language toggle - in a real implementation, 
		// this would reload the page with the new language
		frappe.msgprint(__('Language toggle feature will be implemented with proper translation system'));
	}

	format_currency(amount) {
		return new Intl.NumberFormat('ar-DZ', {
			style: 'currency',
			currency: 'DZD',
			minimumFractionDigits: 2
		}).format(amount || 0);
	}

	show_toast(message, type = 'success') {
		// Remove existing toast
		$('.pos-toast').remove();
		
		// Create new toast
		const toast = $(`
			<div class="pos-toast ${type}">
				<i class="fa fa-check-circle" style="margin-right: 8px;"></i>
				${message}
			</div>
		`);
		
		// Add to DOM
		$('body').append(toast);
		
		// Show with animation
		setTimeout(() => toast.addClass('show'), 100);
		
		// Hide after 3 seconds
		setTimeout(() => {
			toast.removeClass('show');
			setTimeout(() => toast.remove(), 300);
		}, 3000);
	}

	async show_invoice_selection_modal() {
		try {
			// Load recent invoices
			const response = await frappe.call({
				method: 'inventory.pos.api.get_pos_invoices_for_modification',
				args: {
					limit: 20
				}
			});

			this.availableInvoices = response.message || [];
			this.render_invoice_list();
			
			// Show invoice selection modal
			document.getElementById('invoice-selection-modal').style.display = 'flex';

		} catch (error) {
			frappe.msgprint(__('Error loading invoices: ') + error.message);
		}
	}

	render_invoice_list(filteredInvoices = null) {
		const invoices = filteredInvoices || this.availableInvoices;
		const listContainer = $('#invoice-list');
		
		if (!invoices || invoices.length === 0) {
			listContainer.html(`
				<div class="text-center text-muted py-4">
					<i class="fa fa-file-text-o fa-3x mb-3"></i>
					<p>${__('No recent invoices found')}</p>
				</div>
			`);
			return;
		}

		let html = '';
		invoices.forEach(invoice => {
			html += `
				<div class="invoice-item card mb-2" data-invoice="${invoice.name}" style="cursor: pointer;">
					<div class="card-body py-2">
						<div class="row">
							<div class="col-md-3">
								<strong>${invoice.name}</strong>
								<br><small class="text-muted">${invoice.posting_date} ${invoice.posting_time}</small>
							</div>
							<div class="col-md-4">
								<span class="text-muted">${__('Customer')}:</span>
								<br>${invoice.customer || 'Walk-in Customer'}
							</div>
							<div class="col-md-3">
								<span class="text-muted">${__('Total')}:</span>
								<br><strong>${this.format_currency(invoice.grand_total)}</strong>
							</div>
							<div class="col-md-2">
								<span class="badge badge-${invoice.status === 'Paid' ? 'success' : 'warning'}">
									${invoice.status}
								</span>
							</div>
						</div>
					</div>
				</div>
			`;
		});

		listContainer.html(html);

		// Bind click events
		$('.invoice-item').on('click', (e) => {
			const invoiceName = $(e.currentTarget).data('invoice');
			this.load_invoice_for_modification(invoiceName);
		});
	}

	filter_invoice_list(searchTerm) {
		if (!searchTerm) {
			this.render_invoice_list();
			return;
		}

		const filtered = this.availableInvoices.filter(invoice => 
			invoice.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
			(invoice.customer && invoice.customer.toLowerCase().includes(searchTerm.toLowerCase()))
		);

		this.render_invoice_list(filtered);
	}

	async load_invoice_for_modification(invoiceName) {
		try {
			// Close the modal first
			document.getElementById('invoice-selection-modal').style.display = 'none';

			// Load invoice details
			const response = await frappe.call({
				method: 'inventory.pos.api.get_pos_invoice_details',
				args: {
					invoice_name: invoiceName
				}
			});

			if (response.message) {
				const invoiceData = response.message;
				
				// Store original invoice name for updating
				this.modifyingInvoice = invoiceName;
				
				// Clear current cart and reset payment amount
				this.cart = [];
				this.paidAmount = 0;
				$('#paid-amount').val('');
				
				// Load invoice items into cart
				invoiceData.items.forEach(item => {
					this.cart.push({
						item_code: item.item_code,
						item_name: item.item_name,
						qty: parseFloat(item.qty) || 1,
						rate: parseFloat(item.rate) || 0,
						amount: parseFloat(item.amount) || 0
					});
				});
				
				// Set customer
				if (invoiceData.invoice.customer && invoiceData.invoice.customer !== 'Walk-in Customer') {
					$('#customer-select').val(invoiceData.invoice.customer);
					this.selectedCustomer = invoiceData.invoice.customer;
				}
				
				// Set payment amount
				if (invoiceData.payments && invoiceData.payments.length > 0) {
					const totalPaid = invoiceData.payments.reduce((sum, payment) => sum + payment.amount, 0);
					$('#paid-amount').val(totalPaid);
					this.paidAmount = totalPaid;
					
					// Set payment method from first payment
					$('#payment-method').val(invoiceData.payments[0].payment_method);
				}
				
				// Update UI
				this.render_cart();
				this.update_cart_total();
				this.update_change_display();
				this.update_complete_sale_button();
				
				// Change button text to indicate modification
				$('#complete-sale').text(__('Update Sale'));
				
				this.show_toast(__('Invoice loaded for modification'), 'info');
			}

		} catch (error) {
			frappe.msgprint(__('Error loading invoice: ') + error.message);
		}
	}

}