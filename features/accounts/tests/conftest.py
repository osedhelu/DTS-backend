import pytest
from django.test.utils import override_settings

from tests.gis_helpers import postgis_tests_available

ACCOUNTS_URLCONF = "features.accounts.tests.urls"


@pytest.fixture(autouse=True)
def accounts_urlconf():
    """Evita cargar analytics/stores (PostGIS) en tests accounts sin GDAL local."""
    if postgis_tests_available():
        yield
        return
    with override_settings(ROOT_URLCONF=ACCOUNTS_URLCONF):
        yield
