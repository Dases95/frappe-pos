frappe.pages['point-of-sale'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Point of Sale'),
		single_column: true
	});

	// Load Vue and Vuetify from CDN, then initialize the app
	loadVuetifyDependencies().then(() => {
		new POSApp(page);
	});
};

async function loadVuetifyDependencies() {
	// Load Vue 3
	if (!window.Vue) {
		await loadScript('https://unpkg.com/vue@3.4.21/dist/vue.global.prod.js');
	}
	
	// Load Vuetify CSS (scoped version) - only if not already loaded
	if (!document.getElementById('pos-vuetify-css')) {
		const vuetifyCSS = document.createElement('link');
		vuetifyCSS.id = 'pos-vuetify-css';
		vuetifyCSS.rel = 'stylesheet';
		vuetifyCSS.href = 'https://unpkg.com/vuetify@3.5.1/dist/vuetify.min.css';
		document.head.appendChild(vuetifyCSS);
	}
	
	// Load Material Design Icons - only if not already loaded
	if (!document.getElementById('pos-mdi-css')) {
		const mdiCSS = document.createElement('link');
		mdiCSS.id = 'pos-mdi-css';
		mdiCSS.rel = 'stylesheet';
		mdiCSS.href = 'https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/css/materialdesignicons.min.css';
		document.head.appendChild(mdiCSS);
	}
	
	// Load Vuetify JS
	if (!window.Vuetify) {
		await loadScript('https://unpkg.com/vuetify@3.5.1/dist/vuetify.min.js');
	}
	
	// Enable Vuetify CSS
	enablePOSStyles();
	
	// Small delay to ensure everything is loaded
	await new Promise(resolve => setTimeout(resolve, 100));
}

function loadScript(src) {
	return new Promise((resolve, reject) => {
		const script = document.createElement('script');
		script.src = src;
		script.onload = resolve;
		script.onerror = reject;
		document.head.appendChild(script);
	});
}

function enablePOSStyles() {
	const vuetifyCSS = document.getElementById('pos-vuetify-css');
	const mdiCSS = document.getElementById('pos-mdi-css');
	if (vuetifyCSS) vuetifyCSS.disabled = false;
	if (mdiCSS) mdiCSS.disabled = false;
}

function disablePOSStyles() {
	const vuetifyCSS = document.getElementById('pos-vuetify-css');
	const mdiCSS = document.getElementById('pos-mdi-css');
	if (vuetifyCSS) vuetifyCSS.disabled = true;
	if (mdiCSS) mdiCSS.disabled = true;
}

// Cleanup when leaving the page
frappe.pages['point-of-sale'].on_page_unload = function() {
	document.body.classList.remove('pos-page');
	disablePOSStyles();
};

// Also listen to Frappe route changes for cleanup
$(document).on('page-change', function() {
	if (!frappe.get_route_str().includes('point-of-sale')) {
		document.body.classList.remove('pos-page');
		disablePOSStyles();
	}
});

// Cleanup on hashchange as backup
window.addEventListener('hashchange', function() {
	if (!window.location.hash.includes('point-of-sale')) {
		document.body.classList.remove('pos-page');
		disablePOSStyles();
	}
});

class POSApp {
	constructor(page) {
		this.page = page;
		this.wrapper = page.main;
		document.body.classList.add('pos-page');
		enablePOSStyles();
		this.initVueApp();
	}

	initVueApp() {
		const { createApp, ref, computed, reactive, onMounted, watch } = Vue;
		const { createVuetify } = Vuetify;

		const vuetify = createVuetify({
			theme: {
				defaultTheme: 'posTheme',
				themes: {
					posTheme: {
						dark: false,
						colors: {
							primary: '#1565C0',
							secondary: '#424242',
							accent: '#00ACC1',
							error: '#D32F2F',
							warning: '#FFA000',
							info: '#1976D2',
							success: '#388E3C',
							surface: '#FAFAFA',
							background: '#F5F5F5',
						}
					}
				}
			}
		});

		const appTemplate = `
<v-app>
	<v-main class="pos-main">
		<!-- Session Start Dialog -->
		<v-dialog v-model="showSessionDialog" persistent max-width="500" class="session-dialog">
			<v-card class="session-card elevation-12">
				<v-card-title class="text-h5 primary white--text pa-6" style="background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%);">
					<v-icon class="mr-3" color="white">mdi-store</v-icon>
					<span style="color: white;">{{ __('Start POS Session') }}</span>
				</v-card-title>
				<v-card-text class="pa-6">
					<v-form @submit.prevent="startSession">
						<v-select
							v-model="selectedProfile"
							:items="posProfiles"
							item-title="profile_name"
							item-value="name"
							:label="__('POS Profile')"
							variant="outlined"
							prepend-inner-icon="mdi-account-tie"
							class="mb-4"
							:rules="[v => !!v || __('Please select a POS Profile')]"
							required
						></v-select>
						<v-text-field
							v-model.number="openingAmount"
							:label="__('Opening Amount (DZD)')"
							type="number"
							variant="outlined"
							prepend-inner-icon="mdi-cash"
							min="0"
							step="0.01"
						></v-text-field>
					</v-form>
				</v-card-text>
				<v-card-actions class="pa-6 pt-0">
					<v-spacer></v-spacer>
					<v-btn
						color="primary"
						size="large"
						variant="elevated"
						@click="startSession"
						:loading="loading"
						block
					>
						<v-icon left class="mr-2">mdi-play-circle</v-icon>
						{{ __('Start Session') }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Main POS Interface -->
		<v-container fluid v-if="currentSession" class="pos-container pa-4">
			<!-- Header -->
			<v-card class="mb-4 header-card" elevation="4">
				<v-toolbar color="primary" dark dense>
					<v-icon class="mr-3">mdi-point-of-sale</v-icon>
					<v-toolbar-title class="font-weight-bold">{{ __('Point of Sale') }}</v-toolbar-title>
					<v-spacer></v-spacer>
					<v-chip color="success" class="mr-3" variant="elevated">
						<v-icon start size="small">mdi-check-circle</v-icon>
						{{ currentSession.name }}
					</v-chip>
					<v-btn 
						color="white" 
						variant="outlined" 
						size="small" 
						class="mr-2"
						@click="showInvoiceModal = true"
					>
						<v-icon start size="small">mdi-history</v-icon>
						{{ __('Previous Invoices') }}
					</v-btn>
					<v-btn icon variant="text" @click="closeSession" :title="__('Close Session')">
						<v-icon>mdi-power</v-icon>
					</v-btn>
				</v-toolbar>
			</v-card>

			<v-row>
				<!-- Products Section -->
				<v-col cols="12" lg="7">
					<v-card class="products-card" elevation="3">
						<v-card-title class="d-flex align-center pa-4 products-header">
							<v-icon class="mr-2" color="primary">mdi-package-variant</v-icon>
							<span class="text-h6">{{ __('Products') }}</span>
							<v-spacer></v-spacer>
							<v-text-field
								v-model="productSearch"
								:placeholder="__('Search products...')"
								prepend-inner-icon="mdi-magnify"
								variant="outlined"
								density="compact"
								hide-details
								clearable
								style="max-width: 300px;"
								class="search-field"
							></v-text-field>
							<v-btn icon variant="text" color="primary" @click="refreshStock" :loading="refreshingStock" class="ml-2">
								<v-icon>mdi-refresh</v-icon>
							</v-btn>
						</v-card-title>
						<v-divider></v-divider>
						<v-card-text class="products-grid-container pa-4" style="max-height: 500px; overflow-y: auto;">
							<v-row dense>
								<v-col v-for="product in filteredProducts" :key="product.item_code" cols="6" sm="4" md="3">
									<v-card
										:class="['product-card', { 'out-of-stock': product.available_qty <= 0 }]"
										@click="addToCart(product)"
										:disabled="product.available_qty <= 0"
										elevation="2"
										hover
									>
										<v-card-text class="pa-3 text-center position-relative">
											<!-- Info Button - click.stop prevents adding to cart -->
											<v-btn
												icon
												size="x-small"
												variant="text"
												color="primary"
												class="product-info-btn"
												@click.stop="showProductDetails(product)"
												:title="__('View Details')"
											>
												<v-icon size="small">mdi-information-outline</v-icon>
											</v-btn>
											
											<div class="product-icon mb-2">
												<v-icon size="40" :color="product.available_qty > 0 ? 'primary' : 'grey'">mdi-cube-outline</v-icon>
											</div>
											<div class="product-name text-body-2 font-weight-medium text-truncate" :title="product.item_name">
												{{ product.item_name }}
											</div>
											<div class="product-code text-caption text-grey text-truncate">{{ product.item_code }}</div>
											<div class="product-price text-h6 font-weight-bold mt-2" :class="product.standard_rate > 0 ? 'text-primary' : 'text-grey'">
												{{ product.standard_rate > 0 ? formatCurrency(product.standard_rate) : __('No Price') }}
											</div>
											<v-chip
												:color="getStockColor(product.available_qty)"
												size="x-small"
												class="mt-2"
												variant="tonal"
											>
												{{ __('Stock') }}: {{ product.available_qty || 0 }}
											</v-chip>
										</v-card-text>
									</v-card>
								</v-col>
							</v-row>
							<div v-if="filteredProducts.length === 0" class="text-center pa-8">
								<v-icon size="64" color="grey-lighten-1">mdi-package-variant-remove</v-icon>
								<div class="text-h6 text-grey mt-4">{{ __('No products found') }}</div>
							</div>
						</v-card-text>
					</v-card>

					<!-- Shortcuts Section -->
					<v-card class="mt-4 shortcuts-card" elevation="3" v-if="hasShortcuts">
						<v-card-title class="pa-4">
							<v-icon class="mr-2" color="accent">mdi-keyboard</v-icon>
							<span class="text-h6">{{ __('Quick Shortcuts') }}</span>
						</v-card-title>
						<v-divider></v-divider>
						<v-card-text class="pa-4">
							<v-row>
								<v-col cols="12" md="4" v-if="shortcuts.functions && shortcuts.functions.length">
									<div class="text-subtitle-2 text-grey mb-2">{{ __('Functions') }}</div>
									<v-chip-group>
										<v-chip
											v-for="shortcut in shortcuts.functions"
											:key="shortcut.shortcut_key"
											color="primary"
											variant="outlined"
											@click="executeShortcut(shortcut)"
											class="ma-1"
										>
											<strong>{{ shortcut.shortcut_key }}</strong>
											<span class="ml-1">{{ shortcut.shortcut_name }}</span>
										</v-chip>
									</v-chip-group>
								</v-col>
								<v-col cols="12" md="4" v-if="shortcuts.payments && shortcuts.payments.length">
									<div class="text-subtitle-2 text-grey mb-2">{{ __('Payments') }}</div>
									<v-chip-group>
										<v-chip
											v-for="shortcut in shortcuts.payments"
											:key="shortcut.shortcut_key"
											color="success"
											variant="outlined"
											@click="executePaymentShortcut(shortcut)"
											class="ma-1"
										>
											<strong>{{ shortcut.shortcut_key }}</strong>
											<span class="ml-1">{{ shortcut.shortcut_name }}</span>
										</v-chip>
									</v-chip-group>
								</v-col>
								<v-col cols="12" md="4" v-if="shortcuts.products && shortcuts.products.length">
									<div class="text-subtitle-2 text-grey mb-2">{{ __('Products') }}</div>
									<v-chip-group>
										<v-chip
											v-for="shortcut in shortcuts.products"
											:key="shortcut.shortcut_key"
											color="info"
											variant="outlined"
											@click="executeProductShortcut(shortcut)"
											class="ma-1"
										>
											<strong>{{ shortcut.shortcut_key }}</strong>
											<span class="ml-1">{{ shortcut.item_name }}</span>
										</v-chip>
									</v-chip-group>
								</v-col>
							</v-row>
						</v-card-text>
					</v-card>
				</v-col>

				<!-- Cart & Payment Section -->
				<v-col cols="12" lg="5">
						<!-- Cart -->
						<v-card class="cart-card mb-4" elevation="3" :class="{ 'modifying-invoice': modifyingInvoice }">
							<v-card-title class="d-flex align-center pa-4 cart-header">
								<v-icon class="mr-2" :color="modifyingInvoice ? 'warning' : 'success'">
									{{ modifyingInvoice ? 'mdi-file-document-edit' : 'mdi-cart' }}
								</v-icon>
								<span class="text-h6">
									{{ modifyingInvoice ? __('Modifying Invoice') : __('Cart') }}
								</span>
								<v-chip v-if="modifyingInvoice" color="warning" size="small" class="ml-2">
									{{ modifyingInvoice }}
								</v-chip>
								<v-badge
									v-else
									:content="cart.length"
									:model-value="cart.length > 0"
									color="error"
									class="ml-2"
								>
								</v-badge>
								<v-spacer></v-spacer>
							<v-autocomplete
								v-model="selectedCustomer"
								:items="customers"
								item-title="customer_name"
								item-value="name"
								:label="__('Customer')"
								variant="outlined"
								density="compact"
								hide-details
								clearable
								:placeholder="__('Walk-in Customer')"
								style="max-width: 200px;"
								prepend-inner-icon="mdi-account"
								@update:search="searchCustomers"
							></v-autocomplete>
						</v-card-title>
						<v-divider></v-divider>
						<v-card-text class="cart-items pa-0" style="max-height: 350px; min-height: 200px; overflow-y: auto;">
							<v-list v-if="cart.length > 0" lines="two">
								<v-list-item v-for="(item, index) in cart" :key="item.item_code" class="cart-item">
									<template v-slot:prepend>
										<v-avatar color="primary" size="40" class="mr-3">
											<v-icon color="white">mdi-cube</v-icon>
										</v-avatar>
									</template>
									<v-list-item-title class="font-weight-medium">{{ item.item_name }}</v-list-item-title>
									<v-list-item-subtitle>
										{{ formatCurrency(item.rate) }} × {{ item.qty }}
									</v-list-item-subtitle>
									<template v-slot:append>
										<div class="d-flex align-center">
											<v-btn icon size="small" variant="text" @click="updateQuantity(index, -1)">
												<v-icon>mdi-minus</v-icon>
											</v-btn>
											<span class="mx-2 font-weight-bold">{{ item.qty }}</span>
											<v-btn icon size="small" variant="text" @click="updateQuantity(index, 1)">
												<v-icon>mdi-plus</v-icon>
											</v-btn>
											<div class="text-right ml-4" style="min-width: 100px;">
												<div class="text-primary font-weight-bold">{{ formatCurrency(item.amount) }}</div>
											</div>
											<v-btn icon size="small" color="error" variant="text" @click="removeFromCart(index)" class="ml-2">
												<v-icon>mdi-delete</v-icon>
											</v-btn>
										</div>
									</template>
								</v-list-item>
							</v-list>
							<div v-else class="text-center pa-8">
								<v-icon size="80" color="grey-lighten-2">mdi-cart-outline</v-icon>
								<div class="text-h6 text-grey mt-4">{{ __('Cart is empty') }}</div>
								<div class="text-body-2 text-grey">{{ __('Add products to get started') }}</div>
							</div>
						</v-card-text>
						<v-divider></v-divider>
						<v-card-actions class="pa-4 cart-total">
							<span class="text-h6">{{ __('Total') }}:</span>
							<v-spacer></v-spacer>
							<span class="text-h5 font-weight-bold text-primary">{{ formatCurrency(cartTotal) }}</span>
						</v-card-actions>
					</v-card>

					<!-- Payment -->
					<v-card class="payment-card" elevation="3">
						<v-card-title class="pa-4 payment-header">
							<v-icon class="mr-2" color="warning">mdi-credit-card</v-icon>
							<span class="text-h6">{{ __('Payment') }}</span>
						</v-card-title>
						<v-divider></v-divider>
						<v-card-text class="pa-4">
							<!-- POS Client -->
							<v-autocomplete
								v-model="selectedPOSClient"
								:items="posClients"
								item-title="full_name"
								item-value="name"
								:label="__('POS Client (Optional)')"
								variant="outlined"
								density="comfortable"
								clearable
								prepend-inner-icon="mdi-account-circle"
								class="mb-4"
								@update:search="searchPOSClients"
								return-object
							>
								<template v-slot:item="{ props, item }">
									<v-list-item v-bind="props">
										<template v-slot:subtitle>
											<span v-if="item.raw.allow_credit">
												{{ __('Credit Available') }}: {{ formatCurrency(item.raw.credit_limit - item.raw.current_balance) }}
											</span>
										</template>
									</v-list-item>
								</template>
							</v-autocomplete>

							<!-- Payment Method -->
							<v-select
								v-model="paymentMethod"
								:items="paymentMethods"
								:label="__('Payment Method')"
								variant="outlined"
								density="comfortable"
								prepend-inner-icon="mdi-cash-register"
								class="mb-4"
							></v-select>

							<!-- Paid Amount -->
							<v-text-field
								v-model.number="paidAmount"
								:label="__('Amount Paid (DZD)')"
								type="number"
								variant="outlined"
								density="comfortable"
								prepend-inner-icon="mdi-cash"
								:disabled="paymentMethod === 'Credit'"
								class="mb-4"
								min="0"
								step="0.01"
							></v-text-field>

							<!-- Change Display -->
							<v-alert
								v-if="changeAmount > 0"
								type="success"
								variant="tonal"
								class="mb-4"
								density="compact"
							>
								<strong>{{ __('Change') }}:</strong> {{ formatCurrency(changeAmount) }}
							</v-alert>

							<!-- Action Buttons -->
							<v-btn
								color="success"
								size="large"
								block
								:disabled="!canCompleteSale"
								@click="completeSale"
								:loading="completingSale"
								class="mb-3"
							>
								<v-icon left class="mr-2">mdi-check-circle</v-icon>
								{{ modifyingInvoice ? __('Update Sale') : __('Complete Sale') }}
							</v-btn>

							<v-row dense>
								<v-col cols="6">
									<v-btn
										color="error"
										variant="outlined"
										block
										@click="clearCart"
									>
										<v-icon left class="mr-1">mdi-cart-remove</v-icon>
										{{ __('Clear') }}
									</v-btn>
								</v-col>
								<v-col cols="6">
									<v-btn
										color="secondary"
										variant="outlined"
										block
										@click="showInvoiceModal = true"
									>
										<v-icon left class="mr-1">mdi-pencil</v-icon>
										{{ __('Modify') }}
									</v-btn>
								</v-col>
							</v-row>
						</v-card-text>
					</v-card>
				</v-col>
			</v-row>
		</v-container>

		<!-- Invoice Selection Dialog -->
		<v-dialog v-model="showInvoiceModal" max-width="1000" scrollable>
			<v-card>
				<v-card-title class="pa-4 d-flex align-center">
					<v-icon class="mr-2" color="primary">mdi-history</v-icon>
					<span class="text-h6">{{ __('Previous Invoices') }}</span>
					<v-spacer></v-spacer>
					<v-btn icon variant="text" @click="showInvoiceModal = false">
						<v-icon>mdi-close</v-icon>
					</v-btn>
				</v-card-title>
				<v-divider></v-divider>
				<v-card-text class="pa-4">
					<v-row class="mb-4">
						<v-col cols="12" md="6">
							<v-text-field
								v-model="invoiceSearch"
								:placeholder="__('Search by invoice number or customer...')"
								prepend-inner-icon="mdi-magnify"
								variant="outlined"
								density="compact"
								hide-details
								clearable
							></v-text-field>
						</v-col>
						<v-col cols="12" md="3">
							<v-text-field
								v-model="invoiceFromDate"
								type="date"
								:label="__('From Date')"
								variant="outlined"
								density="compact"
								hide-details
							></v-text-field>
						</v-col>
						<v-col cols="12" md="3">
							<v-text-field
								v-model="invoiceToDate"
								type="date"
								:label="__('To Date')"
								variant="outlined"
								density="compact"
								hide-details
							></v-text-field>
						</v-col>
					</v-row>
					
					<v-alert v-if="availableInvoices.length === 0 && !loadingInvoices" type="info" variant="tonal" class="mb-4">
						{{ __('No invoices found') }}
					</v-alert>
					
					<v-progress-linear v-if="loadingInvoices" indeterminate color="primary" class="mb-4"></v-progress-linear>
					
					<v-list style="max-height: 500px; overflow-y: auto;" v-if="filteredInvoices.length > 0">
						<v-list-item
							v-for="invoice in filteredInvoices"
							:key="invoice.name"
							@click="loadInvoiceForModification(invoice.name)"
							class="invoice-item"
							:class="{ 'invoice-item-selected': modifyingInvoice === invoice.name }"
						>
							<template v-slot:prepend>
								<v-avatar color="primary" size="40">
									<v-icon color="white">mdi-file-document</v-icon>
								</v-avatar>
							</template>
							<v-list-item-title class="font-weight-medium">{{ invoice.name }}</v-list-item-title>
							<v-list-item-subtitle>
								<div class="d-flex align-center mt-1">
									<v-icon size="small" class="mr-1">mdi-account</v-icon>
									<span>{{ invoice.customer || __('Walk-in Customer') }}</span>
									<span class="mx-2">•</span>
									<v-icon size="small" class="mr-1">mdi-calendar</v-icon>
									<span>{{ invoice.posting_date }} {{ invoice.posting_time || '' }}</span>
									<span v-if="invoice.item_count" class="mx-2">•</span>
									<span v-if="invoice.item_count">
										<v-icon size="small" class="mr-1">mdi-package-variant</v-icon>
										{{ invoice.item_count }} {{ __('items') }}
									</span>
								</div>
							</v-list-item-subtitle>
							<template v-slot:append>
								<div class="d-flex flex-column align-end">
									<v-chip 
										:color="invoice.status === 'Paid' ? 'success' : 'warning'" 
										size="small"
										class="mb-2"
									>
										{{ invoice.status }}
									</v-chip>
									<span class="text-h6 font-weight-bold text-primary">
										{{ formatCurrency(invoice.grand_total) }}
									</span>
								</div>
							</template>
						</v-list-item>
					</v-list>
				</v-card-text>
				<v-card-actions class="pa-4">
					<v-spacer></v-spacer>
					<v-btn color="secondary" variant="text" @click="showInvoiceModal = false">
						{{ __('Close') }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Product Details Dialog -->
		<v-dialog v-model="showProductDetailsModal" max-width="800" scrollable>
			<v-card v-if="selectedProductDetails">
				<v-card-title class="pa-4 d-flex align-center">
					<v-icon class="mr-2" color="primary">mdi-information</v-icon>
					<span class="text-h6">{{ __('Product Details') }}</span>
					<v-spacer></v-spacer>
					<v-btn icon variant="text" @click="showProductDetailsModal = false">
						<v-icon>mdi-close</v-icon>
					</v-btn>
				</v-card-title>
				<v-divider></v-divider>
				<v-card-text class="pa-4">
					<v-row v-if="loadingProductDetails">
						<v-col cols="12" class="text-center py-8">
							<v-progress-circular indeterminate color="primary"></v-progress-circular>
							<div class="mt-4">{{ __('Loading product details...') }}</div>
						</v-col>
					</v-row>
					<v-row v-else>
						<!-- Product Info -->
						<v-col cols="12">
							<v-card variant="outlined" class="mb-4">
								<v-card-title class="text-h6 pa-3">
									{{ selectedProductDetails.item_name }}
								</v-card-title>
								<v-card-text class="pa-3">
									<v-row>
										<v-col cols="6">
											<div class="text-caption text-grey">{{ __('Item Code') }}</div>
											<div class="text-body-1 font-weight-medium">{{ selectedProductDetails.item_code }}</div>
										</v-col>
										<v-col cols="6">
											<div class="text-caption text-grey">{{ __('Category') }}</div>
											<div class="text-body-1">{{ selectedProductDetails.item_category || __('N/A') }}</div>
										</v-col>
										<v-col cols="6">
											<div class="text-caption text-grey">{{ __('Unit of Measurement') }}</div>
											<div class="text-body-1">{{ selectedProductDetails.unit_of_measurement || __('N/A') }}</div>
										</v-col>
										<v-col cols="6">
											<div class="text-caption text-grey">{{ __('Stock Available') }}</div>
											<div class="text-body-1">
												<v-chip :color="getStockColor(selectedProductDetails.stock_qty)" size="small">
													{{ selectedProductDetails.stock_qty || 0 }}
												</v-chip>
											</div>
										</v-col>
										<v-col cols="12" v-if="selectedProductDetails.description">
											<div class="text-caption text-grey">{{ __('Description') }}</div>
											<div class="text-body-2">{{ selectedProductDetails.description }}</div>
										</v-col>
									</v-row>
								</v-card-text>
							</v-card>
						</v-col>

						<!-- Selling Prices -->
						<v-col cols="12" md="6">
							<v-card variant="outlined" class="h-100">
								<v-card-title class="pa-3 text-subtitle-1 bg-success-lighten-5">
									<v-icon class="mr-2" color="success">mdi-arrow-up</v-icon>
									{{ __('Selling Prices') }}
								</v-card-title>
								<v-card-text class="pa-3">
									<div class="mb-3">
										<div class="text-caption text-grey">{{ __('Current Selling Price') }}</div>
										<div class="text-h6 text-success font-weight-bold">
											{{ formatCurrency(selectedProductDetails.current_selling_price) }}
										</div>
									</div>
									<div class="mb-2">
										<div class="text-caption text-grey">{{ __('Standard Rate') }}</div>
										<div class="text-body-1">{{ formatCurrency(selectedProductDetails.standard_rate) }}</div>
									</div>
									<v-divider class="my-3"></v-divider>
									<div v-if="selectedProductDetails.selling_prices && selectedProductDetails.selling_prices.length > 0">
										<div class="text-caption text-grey mb-2">{{ __('All Selling Prices') }}</div>
										<v-list density="compact" style="max-height: 200px; overflow-y: auto;">
											<v-list-item
												v-for="(price, idx) in selectedProductDetails.selling_prices"
												:key="idx"
												class="pa-1"
											>
												<v-list-item-title class="text-body-2">
													{{ formatCurrency(price.price_list_rate) }}
													<v-chip v-if="price.is_default_price" size="x-small" color="primary" class="ml-2">
														{{ __('Default') }}
													</v-chip>
													<v-chip v-if="price.customer" size="x-small" color="info" class="ml-1">
														{{ price.customer }}
													</v-chip>
												</v-list-item-title>
												<v-list-item-subtitle class="text-caption">
													{{ price.valid_from || __('No start date') }} - {{ price.valid_upto || __('No end date') }}
												</v-list-item-subtitle>
											</v-list-item>
										</v-list>
									</div>
									<div v-else class="text-caption text-grey text-center py-2">
										{{ __('No selling prices found') }}
									</div>
								</v-card-text>
							</v-card>
						</v-col>

						<!-- Buying Prices -->
						<v-col cols="12" md="6">
							<v-card variant="outlined" class="h-100">
								<v-card-title class="pa-3 text-subtitle-1 bg-error-lighten-5">
									<v-icon class="mr-2" color="error">mdi-arrow-down</v-icon>
									{{ __('Buying Prices') }}
								</v-card-title>
								<v-card-text class="pa-3">
									<div class="mb-3">
										<div class="text-caption text-grey">{{ __('Current Buying Price') }}</div>
										<div class="text-h6 text-error font-weight-bold">
											{{ formatCurrency(selectedProductDetails.current_buying_price) }}
										</div>
									</div>
									<div class="mb-2">
										<div class="text-caption text-grey">{{ __('Valuation Rate') }}</div>
										<div class="text-body-1">{{ formatCurrency(selectedProductDetails.valuation_rate) }}</div>
									</div>
									<div class="mb-2">
										<div class="text-caption text-grey">{{ __('Last Purchase Rate') }}</div>
										<div class="text-body-1">{{ formatCurrency(selectedProductDetails.last_purchase_rate) }}</div>
									</div>
									<v-divider class="my-3"></v-divider>
									<div v-if="selectedProductDetails.buying_prices && selectedProductDetails.buying_prices.length > 0">
										<div class="text-caption text-grey mb-2">{{ __('All Buying Prices') }}</div>
										<v-list density="compact" style="max-height: 200px; overflow-y: auto;">
											<v-list-item
												v-for="(price, idx) in selectedProductDetails.buying_prices"
												:key="idx"
												class="pa-1"
											>
												<v-list-item-title class="text-body-2">
													{{ formatCurrency(price.price_list_rate) }}
													<v-chip v-if="price.is_default_price" size="x-small" color="primary" class="ml-2">
														{{ __('Default') }}
													</v-chip>
													<v-chip v-if="price.supplier" size="x-small" color="warning" class="ml-1">
														{{ price.supplier }}
													</v-chip>
												</v-list-item-title>
												<v-list-item-subtitle class="text-caption">
													{{ price.valid_from || __('No start date') }} - {{ price.valid_upto || __('No end date') }}
												</v-list-item-subtitle>
											</v-list-item>
										</v-list>
									</div>
									<div v-else class="text-caption text-grey text-center py-2">
										{{ __('No buying prices found') }}
									</div>
								</v-card-text>
							</v-card>
						</v-col>

						<!-- Stock Information -->
						<v-col cols="12" v-if="selectedProductDetails.minimum_stock_level || selectedProductDetails.reorder_level">
							<v-card variant="outlined">
								<v-card-title class="pa-3 text-subtitle-1">
									<v-icon class="mr-2">mdi-package-variant</v-icon>
									{{ __('Stock Management') }}
								</v-card-title>
								<v-card-text class="pa-3">
									<v-row>
										<v-col cols="4">
											<div class="text-caption text-grey">{{ __('Available Stock') }}</div>
											<div class="text-h6">{{ selectedProductDetails.stock_qty || 0 }}</div>
										</v-col>
										<v-col cols="4">
											<div class="text-caption text-grey">{{ __('Minimum Stock Level') }}</div>
											<div class="text-body-1">{{ selectedProductDetails.minimum_stock_level || 0 }}</div>
										</v-col>
										<v-col cols="4">
											<div class="text-caption text-grey">{{ __('Reorder Level') }}</div>
											<div class="text-body-1">{{ selectedProductDetails.reorder_level || 0 }}</div>
										</v-col>
									</v-row>
								</v-card-text>
							</v-card>
						</v-col>
					</v-row>
				</v-card-text>
				<v-card-actions class="pa-4">
					<v-spacer></v-spacer>
					<v-btn
						color="secondary"
						variant="text"
						@click="showProductDetailsModal = false"
						class="mr-2"
					>
						{{ __('Close') }}
					</v-btn>
					<v-btn
						color="primary"
						variant="elevated"
						@click="addToCartFromDetails"
						:disabled="!selectedProductDetails || selectedProductDetails.stock_qty <= 0"
					>
						<v-icon left class="mr-1">mdi-cart-plus</v-icon>
						{{ __('Add to Cart') }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Receipt Dialog -->
		<v-dialog v-model="showReceiptModal" max-width="450">
			<v-card class="receipt-card">
				<v-card-title class="pa-4 text-center">
					<v-icon class="mr-2" color="success">mdi-receipt</v-icon>
					{{ __('Sales Receipt') }}
				</v-card-title>
				<v-divider></v-divider>
				<v-card-text class="pa-4" id="receipt-content">
					<div class="text-center mb-4">
						<div class="text-h6 mb-1">{{ __('Invoice') }}: {{ lastInvoice?.name }}</div>
						<div class="text-caption text-grey">{{ new Date().toLocaleString() }}</div>
					</div>
					<v-table density="compact">
						<tbody>
							<tr v-for="item in receiptItems" :key="item.item_code">
								<td>{{ item.item_name }} ({{ item.qty }})</td>
								<td class="text-right">{{ formatCurrency(item.amount) }}</td>
							</tr>
						</tbody>
					</v-table>
					<v-divider class="my-3"></v-divider>
					<div class="d-flex justify-space-between text-h6">
						<span>{{ __('Total') }}:</span>
						<span class="font-weight-bold">{{ formatCurrency(receiptTotal) }}</span>
					</div>
					<div class="d-flex justify-space-between">
						<span>{{ __('Paid') }}:</span>
						<span>{{ formatCurrency(receiptPaid) }}</span>
					</div>
					<div v-if="receiptChange > 0" class="d-flex justify-space-between text-success">
						<span>{{ __('Change') }}:</span>
						<span>{{ formatCurrency(receiptChange) }}</span>
					</div>
				</v-card-text>
				<v-card-actions class="pa-4">
					<v-btn color="primary" variant="outlined" @click="printReceipt">
						<v-icon left class="mr-1">mdi-printer</v-icon>
						{{ __('Print') }}
					</v-btn>
					<v-spacer></v-spacer>
					<v-btn color="secondary" variant="text" @click="showReceiptModal = false">
						{{ __('Close') }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Snackbar for notifications - no overlay -->
		<v-snackbar
			v-model="snackbar.show"
			:color="snackbar.color"
			:timeout="2000"
			location="top right"
			:contained="true"
			:multi-line="false"
			class="pos-snackbar"
		>
			<div class="d-flex align-center">
				<v-icon size="small" class="mr-2">{{ snackbar.color === 'success' ? 'mdi-check-circle' : snackbar.color === 'error' ? 'mdi-alert-circle' : 'mdi-information' }}</v-icon>
				{{ snackbar.message }}
			</div>
			<template v-slot:actions>
				<v-btn icon size="x-small" variant="text" @click="snackbar.show = false">
					<v-icon size="small">mdi-close</v-icon>
				</v-btn>
			</template>
		</v-snackbar>
	</v-main>
</v-app>
		`;

		const app = createApp({
			template: appTemplate,
			setup() {
				// State
				const loading = ref(false);
				const showSessionDialog = ref(true);
				const posProfiles = ref([]);
				const selectedProfile = ref(null);
				const openingAmount = ref(0);
				const currentSession = ref(null);
				const products = ref([]);
				const productSearch = ref('');
				const cart = ref([]);
				const customers = ref([]);
				const selectedCustomer = ref(null);
				const posClients = ref([]);
				const selectedPOSClient = ref(null);
				const paymentMethod = ref('Cash');
				const paidAmount = ref(0);
				const refreshingStock = ref(false);
				const completingSale = ref(false);
				const modifyingInvoice = ref(null);
				const showInvoiceModal = ref(false);
				const availableInvoices = ref([]);
				const invoiceSearch = ref('');
				const invoiceFromDate = ref(null);
				const invoiceToDate = ref(null);
				const loadingInvoices = ref(false);
				const showReceiptModal = ref(false);
				const showProductDetailsModal = ref(false);
				const selectedProductDetails = ref(null);
				const loadingProductDetails = ref(false);
				const lastInvoice = ref(null);
				const receiptItems = ref([]);
				const receiptTotal = ref(0);
				const receiptPaid = ref(0);
				const receiptChange = ref(0);
				const shortcuts = ref({ functions: [], payments: [], products: [] });
				
				const snackbar = reactive({
					show: false,
					message: '',
					color: 'success'
				});

				const paymentMethods = ref([
					{ title: __('Cash'), value: 'Cash' },
					{ title: __('Card'), value: 'Card' },
					{ title: __('Bank Transfer'), value: 'Bank Transfer' },
					{ title: __('Credit'), value: 'Credit' }
				]);

				// Computed
				const filteredProducts = computed(() => {
					if (!productSearch.value) return products.value;
					const search = productSearch.value.toLowerCase();
					return products.value.filter(p => 
						p.item_name.toLowerCase().includes(search) ||
						p.item_code.toLowerCase().includes(search) ||
						(p.barcode && p.barcode.toLowerCase().includes(search))
					);
				});

				const cartTotal = computed(() => {
					return cart.value.reduce((sum, item) => sum + item.amount, 0);
				});

				const changeAmount = computed(() => {
					return Math.max(0, paidAmount.value - cartTotal.value);
				});

				const canCompleteSale = computed(() => {
					if (cart.value.length === 0) return false;
					if (paymentMethod.value === 'Credit') {
						if (!selectedPOSClient.value) return false;
						const available = selectedPOSClient.value.credit_limit - selectedPOSClient.value.current_balance;
						return cartTotal.value <= available;
					}
					return paidAmount.value >= cartTotal.value;
				});

				const hasShortcuts = computed(() => {
					return (shortcuts.value.functions?.length > 0) ||
						   (shortcuts.value.payments?.length > 0) ||
						   (shortcuts.value.products?.length > 0);
				});

				const filteredInvoices = computed(() => {
					if (!invoiceSearch.value) return availableInvoices.value;
					const search = invoiceSearch.value.toLowerCase();
					return availableInvoices.value.filter(inv =>
						inv.name.toLowerCase().includes(search) ||
						(inv.customer && inv.customer.toLowerCase().includes(search))
					);
				});

				// Methods
				const showToast = (message, color = 'success') => {
					snackbar.message = message;
					snackbar.color = color;
					snackbar.show = true;
				};

				const formatCurrency = (amount) => {
					return new Intl.NumberFormat('ar-DZ', {
						style: 'currency',
						currency: 'DZD',
						minimumFractionDigits: 2
					}).format(amount || 0);
				};

				const getStockColor = (qty) => {
					if (qty <= 0) return 'error';
					if (qty <= 5) return 'warning';
					return 'success';
				};

				const loadPOSProfiles = async () => {
					try {
						const response = await frappe.call({
							method: 'frappe.client.get_list',
							args: {
								doctype: 'POS Profile',
								fields: ['name', 'profile_name', 'currency', 'company_name', 'warehouse_name'],
								limit_page_length: 0
							}
						});
						posProfiles.value = response.message || [];
					} catch (error) {
						showToast(__('Error loading POS profiles'), 'error');
					}
				};

				const checkExistingSession = async () => {
					try {
						const response = await frappe.call({
							method: 'frappe.client.get_list',
							args: {
								doctype: 'POS Session',
								fields: ['name', 'pos_profile', 'status', 'opening_amount'],
								filters: [
									['pos_user', '=', frappe.session.user],
									['status', 'in', ['Opening', 'Open']]
								],
								limit_page_length: 1
							}
						});
						if (response.message && response.message.length > 0) {
							const session = response.message[0];
							// Get warehouse from POS Profile
							if (session.pos_profile) {
								const profileResponse = await frappe.call({
									method: 'frappe.client.get_value',
									args: {
										doctype: 'POS Profile',
										filters: { name: session.pos_profile },
										fieldname: ['warehouse_name']
									}
								});
								if (profileResponse.message) {
									session.warehouse = profileResponse.message.warehouse_name;
								}
							}
							currentSession.value = session;
							showSessionDialog.value = false;
							await loadPOSData();
						}
					} catch (error) {
						console.error('Error checking session:', error);
					}
				};

				const startSession = async () => {
					if (!selectedProfile.value) {
						showToast(__('Please select a POS Profile'), 'warning');
						return;
					}
					loading.value = true;
					try {
						const response = await frappe.call({
							method: 'inventory.pos.doctype.pos_session.pos_session.create_opening_entry',
							args: {
								pos_profile: selectedProfile.value,
								opening_amount: openingAmount.value
							}
						});
						if (response.message) {
							currentSession.value = response.message;
							showSessionDialog.value = false;
							showToast(__('Session started successfully!'));
							await loadPOSData();
						}
					} catch (error) {
						showToast(__('Error starting session: ') + error.message, 'error');
					} finally {
						loading.value = false;
					}
				};

				const loadPOSData = async () => {
					try {
						const warehouse = currentSession.value?.warehouse || null;
						const response = await frappe.call({
							method: 'inventory.pos.api.get_pos_items',
							args: { warehouse, search_term: '' }
						});
						products.value = (response.message || []).map(item => ({
							...item,
							available_qty: item.stock_qty || 0
						}));
					} catch (error) {
						showToast(__('Error loading products'), 'error');
					}
					await loadShortcuts();
				};

				const loadShortcuts = async () => {
					try {
						const response = await frappe.call({
							method: 'inventory.doctype.pos_shortcut.pos_shortcut.get_all_shortcuts'
						});
						shortcuts.value = response.message || {};
					} catch (error) {
						console.log('Shortcuts not available');
					}
				};

				const refreshStock = async () => {
					refreshingStock.value = true;
					try {
						await loadPOSData();
						showToast(__('Stock refreshed'));
					} finally {
						refreshingStock.value = false;
					}
				};

				const searchCustomers = async (query) => {
					if (!query || query.length < 2) return;
					try {
						const response = await frappe.call({
							method: 'inventory.pos.api.search_customers',
							args: { search_term: query }
						});
						customers.value = response.message || [];
					} catch (error) {
						console.error('Error searching customers:', error);
					}
				};

				const searchPOSClients = async (query) => {
					if (!query || query.length < 2) return;
					try {
						const response = await frappe.call({
							method: 'inventory.pos.doctype.pos_client.pos_client.search_pos_clients',
							args: { search_term: query, limit: 20 }
						});
						posClients.value = response.message || [];
					} catch (error) {
						console.error('Error searching clients:', error);
					}
				};

				const addToCart = (product) => {
					if (product.available_qty <= 0) {
						showToast(__('Item is out of stock'), 'warning');
						return;
					}
					const existing = cart.value.find(item => item.item_code === product.item_code);
					if (existing) {
						existing.qty += 1;
						existing.amount = existing.qty * existing.rate;
					} else {
						cart.value.push({
							item_code: product.item_code,
							item_name: product.item_name,
							qty: 1,
							rate: product.standard_rate || 0,
							amount: product.standard_rate || 0
						});
					}
					updatePaidAmount();
					showToast(__('Added: ') + product.item_name);
				};

				const showProductDetails = async (product) => {
					showProductDetailsModal.value = true;
					selectedProductDetails.value = null;
					loadingProductDetails.value = true;
					
					try {
						const warehouse = currentSession.value?.warehouse || null;
						const customer = selectedCustomer.value || null;
						
						const response = await frappe.call({
							method: 'inventory.pos.api.get_product_details',
							args: {
								item_code: product.item_code,
								warehouse: warehouse,
								customer: customer
							}
						});
						
						if (response.message) {
							selectedProductDetails.value = response.message;
						} else {
							showToast(__('Error loading product details'), 'error');
							showProductDetailsModal.value = false;
						}
					} catch (error) {
						console.error('Error loading product details:', error);
						showToast(__('Error loading product details: ') + error.message, 'error');
						showProductDetailsModal.value = false;
					} finally {
						loadingProductDetails.value = false;
					}
				};

				const addToCartFromDetails = () => {
					if (!selectedProductDetails.value) return;
					
					const product = {
						item_code: selectedProductDetails.value.item_code,
						item_name: selectedProductDetails.value.item_name,
						standard_rate: selectedProductDetails.value.current_selling_price || selectedProductDetails.value.standard_rate || 0,
						available_qty: selectedProductDetails.value.stock_qty || 0
					};
					
					addToCart(product);
					showProductDetailsModal.value = false;
				};

				const updateQuantity = (index, change) => {
					const item = cart.value[index];
					item.qty = Math.max(1, item.qty + change);
					item.amount = item.qty * item.rate;
					updatePaidAmount();
				};

				const removeFromCart = (index) => {
					cart.value.splice(index, 1);
					updatePaidAmount();
				};

				const clearCart = () => {
					if (modifyingInvoice.value) {
						const confirmed = confirm(__('Are you sure you want to cancel modifying this invoice?'));
						if (!confirmed) return;
					}
					cart.value = [];
					paidAmount.value = 0;
					selectedCustomer.value = null;
					selectedPOSClient.value = null;
					paymentMethod.value = 'Cash';
					modifyingInvoice.value = null;
					updatePaidAmount();
				};

				const updatePaidAmount = () => {
					if (!modifyingInvoice.value && paymentMethod.value !== 'Credit') {
						paidAmount.value = cartTotal.value;
					}
				};

				const completeSale = async () => {
					if (!canCompleteSale.value) return;
					completingSale.value = true;
					try {
						let response;
						if (modifyingInvoice.value) {
							response = await frappe.call({
								method: 'inventory.pos.api.update_pos_invoice',
								args: {
									invoice_name: modifyingInvoice.value,
									items: cart.value,
									payments: [{ payment_method: paymentMethod.value, amount: paidAmount.value }],
									customer: selectedCustomer.value || 'Walk-in Customer',
									pos_client: selectedPOSClient.value?.name || null
								}
							});
							if (response.message?.success) {
								showToast(__('Invoice updated!'));
								showReceipt({ name: response.message.new_invoice });
							}
						} else {
							response = await frappe.call({
								method: 'inventory.pos.doctype.pos_invoice.pos_invoice.create_pos_invoice',
								args: {
									pos_profile: currentSession.value.pos_profile,
									pos_session: currentSession.value.name,
									items: cart.value,
									payments: [{ payment_method: paymentMethod.value, amount: paidAmount.value }],
									customer: selectedCustomer.value || 'Walk-in Customer',
									pos_client: selectedPOSClient.value?.name || null
								}
							});
							if (response.message) {
								showToast(__('Sale completed!'));
								showReceipt(response.message);
							}
						}
						await refreshStock();
						clearCart();
					} catch (error) {
						showToast(__('Error completing sale: ') + error.message, 'error');
					} finally {
						completingSale.value = false;
					}
				};

				const showReceipt = (invoice) => {
					lastInvoice.value = invoice;
					receiptItems.value = [...cart.value];
					receiptTotal.value = cartTotal.value;
					receiptPaid.value = paidAmount.value;
					receiptChange.value = changeAmount.value;
					showReceiptModal.value = true;
				};

				const printReceipt = () => {
					const content = document.getElementById('receipt-content')?.innerHTML;
					if (!content) return;
					const win = window.open('', '_blank');
					win.document.write(`
						<html><head><title>Receipt</title>
						<style>body{font-family:Arial;margin:20px;}.text-right{text-align:right;}</style>
						</head><body>${content}</body></html>
					`);
					win.document.close();
					win.print();
				};

				const closeSession = async () => {
					const confirmed = await frappe.confirm(__('Close this session?'));
					if (!confirmed) return;
					try {
						await frappe.call({
							method: 'inventory.pos.doctype.pos_session.pos_session.close_session',
							args: { session_name: currentSession.value.name }
						});
						showToast(__('Session closed'));
						currentSession.value = null;
						showSessionDialog.value = true;
					} catch (error) {
						showToast(__('Error closing session'), 'error');
					}
				};

				const loadInvoicesForModification = async () => {
					loadingInvoices.value = true;
					try {
						const response = await frappe.call({
							method: 'inventory.pos.api.get_pos_invoices_for_modification',
							args: { 
								limit: 50,
								from_date: invoiceFromDate.value || null,
								to_date: invoiceToDate.value || null
							}
						});
						availableInvoices.value = response.message || [];
					} catch (error) {
						console.error('Error loading invoices:', error);
						showToast(__('Error loading invoices'), 'error');
					} finally {
						loadingInvoices.value = false;
					}
				};

				const loadInvoiceForModification = async (invoiceName) => {
					try {
						const response = await frappe.call({
							method: 'inventory.pos.api.get_pos_invoice_details',
							args: { invoice_name: invoiceName }
						});
						if (response.message) {
							const data = response.message;
							modifyingInvoice.value = invoiceName;
							
							// Clear current cart and load invoice items
							cart.value = data.items.map(item => ({
								item_code: item.item_code,
								item_name: item.item_name,
								qty: parseFloat(item.qty) || 1,
								rate: parseFloat(item.rate) || 0,
								amount: parseFloat(item.amount) || 0
							}));
							
							// Set customer
							if (data.invoice.customer && data.invoice.customer !== 'Walk-in Customer') {
								selectedCustomer.value = data.invoice.customer;
							} else {
								selectedCustomer.value = null;
							}
							
							// Set payment information
							if (data.payments?.length > 0) {
								const totalPaid = data.payments.reduce((sum, p) => sum + p.amount, 0);
								paidAmount.value = totalPaid;
								paymentMethod.value = data.payments[0].payment_method;
							} else {
								paidAmount.value = cartTotal.value; // Auto-set to cart total
								paymentMethod.value = 'Cash';
							}
							
							showInvoiceModal.value = false;
							showToast(__('Invoice loaded. You can now modify items and resave.'), 'success');
						}
					} catch (error) {
						showToast(__('Error loading invoice: ') + error.message, 'error');
					}
				};

				const executeShortcut = (shortcut) => {
					switch (shortcut.action_type) {
						case 'New Sale':
						case 'Clear Cart':
							clearCart();
							break;
						case 'Print Receipt':
							printReceipt();
							break;
						case 'Close Session':
							closeSession();
							break;
					}
					showToast(__('Executed: ') + shortcut.shortcut_name, 'info');
				};

				const executePaymentShortcut = (shortcut) => {
					paymentMethod.value = shortcut.shortcut_name;
					showToast(__('Payment: ') + shortcut.shortcut_name, 'info');
				};

				const executeProductShortcut = (shortcut) => {
					const product = products.value.find(p => p.item_code === shortcut.item_code);
					if (product) {
						addToCart(product);
					}
				};

				// Watch for invoice modal open
				watch(showInvoiceModal, (newVal) => {
					if (newVal) {
						// Reset dates to default (last 30 days)
						if (!invoiceFromDate.value) {
							const today = new Date();
							const thirtyDaysAgo = new Date(today);
							thirtyDaysAgo.setDate(today.getDate() - 30);
							invoiceFromDate.value = thirtyDaysAgo.toISOString().split('T')[0];
							invoiceToDate.value = today.toISOString().split('T')[0];
						}
						loadInvoicesForModification();
					}
				});
				
				// Reload invoices when date filters change
				watch([invoiceFromDate, invoiceToDate], () => {
					if (showInvoiceModal.value) {
						loadInvoicesForModification();
					}
				});

				// Watch payment method changes
				watch(paymentMethod, (newVal) => {
					if (newVal === 'Credit') {
						paidAmount.value = 0;
					} else {
						updatePaidAmount();
					}
				});

				// Lifecycle
				onMounted(async () => {
					await loadPOSProfiles();
					await checkExistingSession();
				});

				return {
					// State
					loading,
					showSessionDialog,
					posProfiles,
					selectedProfile,
					openingAmount,
					currentSession,
					products,
					productSearch,
					cart,
					customers,
					selectedCustomer,
					posClients,
					selectedPOSClient,
					paymentMethod,
					paymentMethods,
					paidAmount,
					refreshingStock,
					completingSale,
					modifyingInvoice,
					showInvoiceModal,
					availableInvoices,
					invoiceSearch,
					invoiceFromDate,
					invoiceToDate,
					loadingInvoices,
					showReceiptModal,
					showProductDetailsModal,
					selectedProductDetails,
					loadingProductDetails,
					lastInvoice,
					receiptItems,
					receiptTotal,
					receiptPaid,
					receiptChange,
					shortcuts,
					snackbar,
					// Computed
					filteredProducts,
					cartTotal,
					changeAmount,
					canCompleteSale,
					hasShortcuts,
					filteredInvoices,
					// Methods
					__,
					formatCurrency,
					getStockColor,
					startSession,
					refreshStock,
					searchCustomers,
					searchPOSClients,
					addToCart,
					updateQuantity,
					removeFromCart,
					clearCart,
					completeSale,
					printReceipt,
					closeSession,
					loadInvoiceForModification,
					showProductDetails,
					addToCartFromDetails,
					executeShortcut,
					executePaymentShortcut,
					executeProductShortcut
				};
			}
		});

		app.use(vuetify);
		
		// Clear wrapper and mount Vue app
		$(this.wrapper).html('<div id="pos-vue-app"></div>');
		app.mount('#pos-vue-app');
	}
}
