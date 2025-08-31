### Inventory

An inventory management application with enhanced geographical features for Algeria.

## Features

### Geographic Data for Algeria
- **Wilaya DocType**: Manages administrative divisions of Algeria (provinces/states)
- **Commune DocType**: Manages sub-divisions within wilayas (municipalities)
- **Customer DocType**: Enhanced with geographic data and location features

### Reports
- **Customers by Region**: View and analyze customers grouped by wilaya and commune

## Geographic Data Management

### Commands
```bash
# Extract geography data from source files
bench inventory extract-geography

# Install geography data into your site
bench inventory install-geography
```

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app inventory
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/inventory
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
