import os
from pathlib import Path

# BASE PATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent


from django_tenants.utils import get_tenant_domain_model

if os.environ.get('SCHEMA_NAME', 'public') == 'public':
    AUTH_USER_MODEL = 'shared_users.PublicUser'
else:
    AUTH_USER_MODEL = 'users.User'


SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


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

    # Local
    'apps.users',
    'apps.tenants',
    'apps.dashboard',
    'apps.billing',
    'apps.shared_users',
]

# Django Tenants
SHARED_APPS = (
    'django_tenants',    
    'django.contrib.contenttypes',
    'apps.tenants', 
    'apps.shared_users',               
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

TENANT_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd Party
    'crispy_forms',
    'crispy_bootstrap5',

    # Local tenant-specific apps
    'apps.users',
    'apps.dashboard',
    'apps.billing',
)

TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.environ.get('DB_NAME', 'multitenant_saas'),
        'USER': os.environ.get('DB_USER', 'saasadmin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'supersecret123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)


AUTH_USER_MODEL = 'users.User'


MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # Django Tenants Middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Important for auth views
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
