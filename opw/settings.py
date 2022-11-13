import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = '71ic+-tfsl2ie0aq76yx+j8&2&zqe^y(d6-cl05(!-$%5is-0j'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'opw.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'opw.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

JAZZMIN_SETTINGS = {
    'site_title': 'OJO',
    'site_header': 'OJO PISOWIFI',
    'site_brand': 'OJO PISOWIFI',
    'copyright': 'OJO PISOWIFI',
    'show_ui_builder': False,
    'order_with_respect_to': ['app', 'app.Clients', 'app.Whitelist', 'app.Rates', 'app.Vouchers', 'app.CoinSlot', 'app.CoinQueue', 'app.Ledger', 'app.Hardware', 'app.Device', 'app.Network', 'app.PushNotifications', 'app.Settings'],
    'icons': {
        'app.clients': 'fas fa-users',
        'app.coinqueue': 'fas fa-coins',
        'app.coinslot': 'fas fa-donate',
        'app.device': 'fas fa-laptop',
        'app.ledger': 'fa fa-address-book',
        'app.network': 'fas fa-network-wired',
        'app.settings': 'fas fa-wifi',
        'app.pushnotifications': 'fas fa-bell',
        'app.rates': 'fas fa-dollar-sign',
        'app.vouchers': 'fas fa-address-card',
        'app.Whitelist': 'fas fa-clipboard-check', 
    },
    'custom_css': '/build/css/dashboard.css',
    "use_google_fonts_cdn": False
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": True,
    "brand_small_text": True,
    "brand_colour": "navbar-navy",
    "accent": "accent-navy",
    "navbar": "navbar-navy navbar-dark",
    "no_navbar_border": True,
    "sidebar": "sidebar-dark-danger",
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": True,
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MQTT_CONFIG = {
    # 'hostname': 'public.mqtthq.com',
    # 'port': 8083,
    'hostname': '127.0.0.1',
    'port': 1883,
    'client_id': '=)d-i9u3349btm+3%7!szma=6r__oawc!el@^$k#g9ob3y-7wt',
    'qos': 0
}

MQTT_TOPICS = {
    'important_topic': 'topic/important'
}