import platform

import distro

# Параметры системы
OS_RELEASE = distro.codename().split(' ')[0].lower()
PLATFORM_ARCH = platform.machine()
OS_DISTRIBUTION = distro.id().lower()
OS_VERSION = distro.major_version()

# Адрес загрузки исходного кода nginx
NGINX_URL = "http://nginx.org/download"
NGINX_SRPM_URL_MAINLINE = f"http://nginx.org/packages/mainline/centos/{OS_VERSION}/SRPMS"
NGINX_SRPM_URL_STABLE = f"http://nginx.org/packages/centos/{OS_VERSION}/SRPMS"

# Архив со скриптами для создания пакета
DEB_PACKAGE_SCRIPTS_URL_MAINLINE = f"http://nginx.org/packages/mainline/{OS_DISTRIBUTION}/pool/nginx/n/nginx"
DEB_PACKAGE_SCRIPTS_URL_STABLE = f"http://nginx.org/packages/{OS_DISTRIBUTION}/pool/nginx/n/nginx"

# Путь до директории сборки пакета
SRC_PATH = "/usr/src/nginx"

# Error build code
DPKG_FAIL_EXIT_CODE = 29

# Параметры компиляции nginx
DEFAULT_CONFIGURE_PARAMS = [
    "--prefix=/etc/nginx",
    "--sbin-path=/usr/sbin/nginx",
    "--conf-path=/etc/nginx/nginx.conf",
    "--modules-path=/usr/lib/nginx/modules",
    "--error-log-path=/var/log/nginx/error.log",
    "--pid-path=/var/run/nginx.pid",
    "--lock-path=/var/lock/nginx.lock",
    "--http-log-path=/var/log/nginx/access.log",
    "--http-client-body-temp-path=/var/cache/nginx/client_temp",
    "--http-proxy-temp-path=/var/cache/nginx/proxy_temp",
    "--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp",
    "--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp",
    "--http-scgi-temp-path=/var/cache/nginx/scgi_temp",
    "--with-debug",
    "--user=nginx",
    "--group=nginx",
    "--with-pcre-jit",
    "--with-compat",
    "--with-file-aio",
    "--with-threads",
    "--with-stream",
    "--with-cc-opt=\"${CFLAGS}\"",
    "--with-ld-opt=\"${LDFLAGS}\""
]

# Путь к директории с модулями для файла rules
MODULESDIR = 'export MODULESDIR = $(CURDIR)/debian/modules'

# Адрес эл. почты для указания при сборке
EMAIL_CREATOR = "nginx-builder@tinkoff.ru"

# Тип лицензии для указания при сборке
LICENSE_TYPE = "gpl"
