from pathlib import Path
import os
import mimetypes

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'change-me'
DEBUG = True

# ✅ Izinkan akses dari localhost
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'WebMasjid.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'core' / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'WebMasjid.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# =======================
# ✅ STATIC & MEDIA FILES
# =======================
STATIC_URL = 'static/'

# Hindari warning STATICFILES_DIRS kalau folder belum ada
_CORE_STATIC = BASE_DIR / 'core' / 'static'
STATICFILES_DIRS = [_CORE_STATIC] if _CORE_STATIC.exists() else []

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =======================
# ✅ AUTENTIKASI
# =======================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================
# ✅ Izinkan embed PDF di <object>/<iframe>
# =========================================
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# =================================================
# ✅ Tambahan saat DEBUG agar tipe MIME tersetting
# =================================================
if DEBUG:
    mimetypes.add_type("application/javascript", ".js", True)
    mimetypes.add_type("text/css", ".css", True)
