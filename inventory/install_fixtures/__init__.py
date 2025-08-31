from inventory.install_fixtures.uom import setup_uom_fixtures
from inventory.install_fixtures.geography import setup_geography_fixtures

def after_install():
    setup_uom_fixtures()
    setup_geography_fixtures() 