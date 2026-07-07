from pathlib import Path
import os
import mimetypes
import dj_database_url

# Load environment variables dari file .env (untuk PythonAnywhere & development lokal)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv tidak wajib jika env vars sudah diset manual

BASE_DIR = Path(__file__).resolve().parent.parent

# =======================
# ✅ SECURITY
# =======================
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS += [h.strip() for h in ALLOWED_HOSTS_ENV.split(',') if h.strip()]

# Izinkan subdomain PythonAnywhere secara otomatis
PYTHONANYWHERE_HOST = os.environ.get('PYTHONANYWHERE_HOST')
if PYTHONANYWHERE_HOST:
    ALLOWED_HOSTS.append(PYTHONANYWHERE_HOST)
else:
    # Fallback: izinkan semua subdomain pythonanywhere.com
    ALLOWED_HOSTS.append('.pythonanywhere.com')

# Izinkan subdomain Render (jika suatu saat pindah ke Render)
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'storages',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← tepat setelah SecurityMiddleware
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

# =======================
# ✅ DATABASE
# =======================
# Di production (PythonAnywhere/Render): baca dari env var DATABASE_URL → PostgreSQL Supabase
# Di local: fallback ke SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =======================
# ✅ LANGUAGE & TIME
# =======================
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# =======================
# ✅ STATIC FILES (Whitenoise)
# =======================
STATIC_URL = 'static/'

_CORE_STATIC = BASE_DIR / 'core' / 'static'
STATICFILES_DIRS = [_CORE_STATIC] if _CORE_STATIC.exists() else []

STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise: kompres & cache static files di production
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# =======================
# ✅ MEDIA FILES (Supabase S3-compatible Storage)
# =======================
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')            # e.g. https://xxxx.supabase.co
SUPABASE_S3_KEY = os.environ.get('SUPABASE_S3_KEY', '')      # Access Key dari Supabase Storage
SUPABASE_S3_SECRET = os.environ.get('SUPABASE_S3_SECRET', '') # Secret Key dari Supabase Storage
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'media') # Nama bucket di Supabase
SUPABASE_REGION = os.environ.get('SUPABASE_REGION', 'ap-southeast-1')

USE_SUPABASE_STORAGE = os.environ.get('USE_SUPABASE_STORAGE', 'False') == 'True'

if USE_SUPABASE_STORAGE and SUPABASE_S3_KEY:
    # Supabase menyediakan S3-compatible endpoint
    SUPABASE_PROJECT_REF = SUPABASE_URL.replace('https://', '').split('.')[0] if SUPABASE_URL else ''
    AWS_ACCESS_KEY_ID = SUPABASE_S3_KEY
    AWS_SECRET_ACCESS_KEY = SUPABASE_S3_SECRET
    AWS_STORAGE_BUCKET_NAME = SUPABASE_BUCKET
    AWS_S3_REGION_NAME = SUPABASE_REGION
    AWS_S3_ENDPOINT_URL = f'https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/s3'
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }

    MEDIA_URL = f'{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/'
else:
    # Local development: simpan file di folder media/ lokal
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }
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

# =========================================
# ✅ Security tambahan di production
# =========================================
if not DEBUG:
    # PythonAnywhere menangani SSL termination sendiri di proxy mereka,
    # sehingga SECURE_SSL_REDIRECT harus False (hindari redirect loop).
    # HTTPS tetap dipaksakan melalui SECURE_PROXY_SSL_HEADER.
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =================================================
# ✅ Tambahan saat DEBUG agar tipe MIME tersetting
# =================================================
if DEBUG:
    mimetypes.add_type("application/javascript", ".js", True)
    mimetypes.add_type("text/css", ".css", True)
