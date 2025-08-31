# Algeria Geographical Data

This directory contains the complete geographical data for Algeria, including all 48 wilayas (provinces) and their corresponding communes (municipalities).

## Data Structure

The data is stored in the `algeria_geography.py` file in a structured format that can be directly used in your application. The data includes:

- 48 Wilayas (Provinces)
- ~1,500+ Communes (Municipalities)

The data is provided in Arabic and includes:
- Wilaya name and code
- Commune name and code
- The relationship between Communes and their parent Wilayas

## Usage

### Import the data directly in your code

```python
from inventory.data.algeria_geography import WILAYAS, COMMUNES, get_wilaya_by_code, get_communes_by_wilaya_code

# Get all wilayas
all_wilayas = WILAYAS

# Get a specific wilaya by code
adrar = get_wilaya_by_code("01")

# Get all communes for a specific wilaya
adrar_communes = get_communes_by_wilaya_code("01")
```

### Install the data into your database

You can use the bench command to install this data into your Frappe site:

```bash
# Install the geography fixtures into your site
bench --site your-site-name inventory install-geography

# Create the fixture files (typically you don't need to do this manually)
bench inventory create-fixture-files

# Show statistics about the geographical data
bench inventory show-geography-stats
```

## Data Source

This data was originally sourced from the [DZ_cities GitHub repository](https://github.com/fromdz27/DZ_cities). 