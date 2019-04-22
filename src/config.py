import distro
import platform


# Параметры системы
OS_RELEASE = distro.lsb_release_attr('codename')
PLATFORM_ARCH = platform.machine()
OS_DISTRIBUTION = distro.lsb_release_attr('distributor_id').lower()
OS_VERSION = distro.lsb_release_attr('release')[0]

# Адрес загрузки исходного кода nginx
NGINX_URL = "http://nginx.org/download"
NGINX_SRPM_URL = "http://nginx.org/packages/mainline/centos/{}/SRPMS".format(OS_VERSION)

# Версия архива со скриптами
PACKAGE_SCRIPTS_VERSION = "1.13.9"
# Архив со скриптами для создания пакета
DEB_PACKAGE_SCRIPTS_URL = "http://nginx.org/packages/mainline/{}/pool/nginx/n/nginx/nginx_{}-1~{}.debian.tar.xz".format(
    OS_DISTRIBUTION,
    PACKAGE_SCRIPTS_VERSION,
    OS_RELEASE
)
DEB_PACKAGE_SCRIPTS_FILENAME = DEB_PACKAGE_SCRIPTS_URL[DEB_PACKAGE_SCRIPTS_URL.rfind("/") + 1:]

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
    "--with-http_gzip_static_module",
    "--with-http_v2_module",
    "--with-http_ssl_module",
    "--with-pcre-jit",
    "--with-compat",
    "--with-file-aio",
    "--with-threads",
    "--with-http_addition_module",
    "--with-http_auth_request_module",
    "--with-http_gunzip_module",
    "--with-http_realip_module",
    "--with-http_secure_link_module",
    "--with-http_slice_module",
    "--with-http_stub_status_module",
    "--with-http_sub_module",
    "--with-stream",
    "--with-stream_realip_module",
    "--with-stream_ssl_preread_module",
    "--with-cc-opt=\"$(CFLAGS)\"",
    "--with-ld-opt=\"$(LDFLAGS)\""
]

# Путь к директории с модулями для файла rules
MODULESDIR = 'export MODULESDIR = $(CURDIR)/debian/modules'

# Адрес эл. почты для указания при сборке
EMAIL_CREATOR = "nginx-builder@tinkoff.ru"

# Тип лицензии для указания при сборке
LICENSE_TYPE = "gpl"
