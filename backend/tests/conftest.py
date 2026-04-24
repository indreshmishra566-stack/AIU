import django
from django.conf import settings

def pytest_configure(config):
    if not settings.configured:
        settings.configure()
