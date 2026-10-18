import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-troque-em-producao")
DEBUG = os.environ.get("DEBUG", "True") == "True"


def _lista_env(nome, padrao=""):
    """Lê uma variável de ambiente separada por vírgulas como lista."""
    return [v.strip() for v in os.environ.get(nome, padrao).split(",") if v.strip()]


ALLOWED_HOSTS = _lista_env("ALLOWED_HOSTS", "*")
# O Render define esta variável automaticamente com o domínio do serviço
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # GeoDjango
    "django.contrib.gis",
    # Terceiros
    "rest_framework",
    "rest_framework_gis",
    "corsheaders",
    # App do projeto
    "queimadas",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Banco PostGIS via variável de ambiente
DATABASES = {
    "default": dj_database_url.config(
        default="postgis://queimadas_user:queimadas_pass@localhost:5432/queimadas",
        conn_max_age=600,
    )
}
# Garante o motor GIS caso a URL não comece explicitamente com 'postgis://'
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
# Em produção sem worker/Redis (ex.: plano grátis do Render), as tasks rodam
# de forma síncrona dentro do próprio processo web.
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False") == "True"
CELERY_TASK_EAGER_PROPAGATES = True

# CORS — permite o frontend Vue acessar a API
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Domínios do frontend em produção, ex.: https://ignisgeo.vercel.app
    *_lista_env("CORS_ALLOWED_ORIGINS"),
]
# Permite também os deploys de preview do Vercel (ex.: ignisgeo-git-xyz.vercel.app)
CORS_ALLOWED_ORIGIN_REGEXES = _lista_env("CORS_ALLOWED_ORIGIN_REGEXES")
CSRF_TRUSTED_ORIGINS = _lista_env("CSRF_TRUSTED_ORIGINS")
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Atrás do proxy HTTPS do Render
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Upload de CSV do INPE pela API: acima de 5 MB o arquivo vai para disco temporário
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [],   # ← adicione
    "DEFAULT_PERMISSION_CLASSES": [],       # ← adicione
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
