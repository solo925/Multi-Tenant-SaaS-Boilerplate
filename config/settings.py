import os
from pathlib import Path

# BASE PATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECRET & DEBUG
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
DEBUG = True
ALLOWED_HOSTS = ['*']

# APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    

    # 3rd Party
    'rest_framework',
    'django_tenants',
    'crispy_forms',
    'crispy_bootstrap5',

    # Local apps
    'apps.users',
    'apps.tenants',
    'apps.dashboard',
    'apps.billing',
]

SHARED_APPS = (
    'django_tenants',
    'django.contrib.contenttypes',
    'apps.tenants',
)

TENANT_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'apps.users',
    'apps.dashboard',
)

TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# DB (PostgreSQL w/ schemas)
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.environ.get('DB_NAME', 'saas_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# User Model
AUTH_USER_MODEL = 'users.User'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                ...
            ],
        },
    },
]

# Static and Media
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
