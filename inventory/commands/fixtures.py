import os
import click
import frappe
import json
from frappe.commands import get_site, pass_context
from inventory.install_fixtures.geography import setup_geography_fixtures, ensure_fixture_files_exist
from inventory.data.algeria_geography import WILAYAS, COMMUNES

@click.command('install-geography')
@click.option('--site', help='site name')
@pass_context
def install_geography_fixtures_command(context, site=None):
    """Install Wilaya and Commune fixtures for Algeria using offline data"""
    site = get_site(context, site=site)
    with frappe.init_site(site):
        frappe.connect()
        print(f"Setting up geography fixtures for site: {site}")
        setup_geography_fixtures()
        frappe.db.commit()
        print("Geography fixtures have been installed.")

@click.command('create-fixture-files')
@pass_context
def create_fixture_files_command(context):
    """Create fixture files from the embedded geographical data
    
    This command generates the fixture files in the fixtures directory
    using the data that's permanently stored in the app.
    """
    print("Creating fixture files from embedded geographical data...")
    try:
        # Initialize Frappe environment
        frappe.init(site="")
        
        # Create the fixture files
        ensure_fixture_files_exist()
        
        print("Fixture files created successfully!")
    except Exception as e:
        print(f"Error creating fixture files: {e}")
        exit(1)

@click.command('show-geography-stats')
@pass_context
def show_geography_stats_command(context):
    """Display statistics about the embedded geographical data"""
    print("Algeria Geography Data Statistics:")
    print(f"- Total Wilayas (Provinces): {len(WILAYAS)}")
    print(f"- Total Communes (Municipalities): {len(COMMUNES)}")
    
    # Count communes by wilaya
    communes_by_wilaya = {}
    for commune in COMMUNES:
        wilaya_name = commune["wilaya"]
        if wilaya_name not in communes_by_wilaya:
            communes_by_wilaya[wilaya_name] = 0
        communes_by_wilaya[wilaya_name] += 1
    
    # Show top 5 wilayas by commune count
    print("\nTop 5 Wilayas by number of communes:")
    sorted_wilayas = sorted(communes_by_wilaya.items(), key=lambda x: x[1], reverse=True)
    for i, (wilaya_name, count) in enumerate(sorted_wilayas[:5]):
        print(f"{i+1}. {wilaya_name}: {count} communes")

commands = [
    install_geography_fixtures_command,
    create_fixture_files_command,
    show_geography_stats_command
] 