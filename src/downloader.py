from requests import get
from packaging import version
from src import config
from src import common_utils
import git
import os
import sys
import shutil
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("builder")


def download_source(src_version):
    """
    Загрузка архива с исходным кодом требуемой версии nginx
    Возвращает имя скаченного файла
    :param src_version:
    :return file_name:
    """
    logger.info("Downloading nginx src...")
    file_name = "nginx-{}.tar.gz".format(src_version)
    url = "{}/{}".format(config.NGINX_URL, file_name)
    logger.info("--> {}".format(url))
    with open(os.path.join(config.SRC_PATH, file_name), "wb") as file:
        response = get(url)
        file.write(response.content)

    return file_name


def get_src_rpm_filename(url, src_version):
    try:
        response = requests.get(url, timeout=5)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    if response.ok:
        response_text = response.text
        soup = BeautifulSoup(response_text, 'html.parser')
        for node in soup.find_all('a'):
            if node.get('href').endswith('rpm') and "nginx-{}-".format(src_version) in node.get('href'):
                file_name = node.get('href')

    elif 400 <= response.status_code < 500:
        logger.error(u"{} Client Error: {} for url: {}".format(response.status_code, response.reason, url))
        sys.exit(1)
    elif 500 <= response.status_code < 600:
        logger.error(u"{} Server Error: {} for url: {}".format(response.status_code, response.reason, url))
        sys.exit(1)

    if 'file_name' in locals():
        return file_name
    else:
        logger.error("Cannot find nginx source rpm(SRPM) with version {} in url {}".format(src_version, url))
        sys.exit(1)


def download_source_rpm(src_version):
    """
    Загрузка пакета с исходным кодом требуемой версии nginx
    :param src_version:
    :return:
    """
    logger.info("Downloading nginx src...")
    nginx_srpm_url = config.NGINX_SRPM_URL_MAINLINE
    if version.parse(src_version).release[1] % 2 == 0:
        nginx_srpm_url = config.NGINX_SRPM_URL_STABLE

    file_name = get_src_rpm_filename(nginx_srpm_url, src_version)
    common_utils.execute_command("rpm --upgrade --verbose --hash {}/{}".format(
        nginx_srpm_url,
        file_name
    ), os.getcwd())


def download_modules(modules):
    """
    Загрузка модулей
    :param modules:
    :return nginx_modules:
    """
    logger.info("Downloading 3d-party modules...")
    nginx_modules = []
    if modules:
        common_utils.ensure_directory(os.path.join(config.SRC_PATH, "modules"))
        for module in modules:
            module = module.get('module')
            if module.get('git_url') is not None:
                nginx_modules.append(download_module_from_git(module))
            elif module.get('web_url') is not None:
                nginx_modules.append(download_module_from_web(module))
            elif module.get('local_url') is not None:
                nginx_modules.append(download_module_from_local(module))
            elif module.get('type') == "embedded":
                download_module_embedded(module)
            else:
                logger.error("Module {} have not valid key url")

    return nginx_modules


def download_module_from_git(module):
    """
    Загрузка репозитория с модулем
    :param module:
    :return:
    """
    repo = git.Repo()
    downloaded_git_branchortag = "master"
    git_url = module.get('git_url')
    if not git_url:
        logger.error("git_url is undefined")
        sys.exit(1)

    module_name = set_module_name(module.get('name'), git_url)
    git_branch = module.get('git_branch')
    git_tag = module.get('git_tag')

    if git_tag:
        logger.info("Module {} will download by tag".format(module_name))
        downloaded_git_branchortag = git_tag
    elif git_branch:
        logger.info("Module {} will download by branch".format(module_name))
        downloaded_git_branchortag = git_branch

    module_dir = os.path.join(config.SRC_PATH, "modules", module_name)
    r = repo.clone_from(git_url, module_dir, branch=downloaded_git_branchortag)
    logger.info("-- Done: {}".format(module_name))

    if r.submodules:
        logger.info("-- Checking for {}/submodules...".format(module_name))
        for submodule in r.submodules:
            logger.info("-- Downloading: {}...".format(submodule))
            submodule.update(init=True)
            logger.info("---- Done: {}/{}".format(module_name, submodule))
    return module_name


def download_module_from_web(module):
    """
    Загрузка архива с модулем из web
    :param module:
    :return:
    """
    web_url = module.get('web_url')
    if not web_url:
        logger.error("web_url is undefined")
        sys.exit(1)

    module_name = set_module_name(module.get('name'), web_url)
    file_name = web_url[web_url.rfind("/") + 1:]
    logger.info("Module {} will downloading".format(module_name))
    with open(os.path.join(config.SRC_PATH, "modules", file_name), "wb") as file:
        response = get(web_url)
        file.write(response.content)
    module_name = common_utils.extract_archive(file_name, os.path.join(config.SRC_PATH, "modules"))
    return module_name


def download_module_from_local(module):
    """
    Загрузка модуля из локального архива
    :param module:
    :return:
    """
    local_url = module.get('local_url')
    if not local_url:
        logger.error("local_url is undefined")
        sys.exit(1)

    module_name = set_module_name(module.get('name'), local_url)
    file_name = local_url[local_url("/") + 1:]
    shutil.copy(local_url, os.path.join(config.SRC_PATH, "modules", file_name))
    module_name = common_utils.extract_archive(file_name, os.path.join(config.SRC_PATH, "modules"))
    return module_name


def download_module_embedded(module):
    """
    Установка втроенного модуля
    :param module:
    :return:
    """
    if module.get('name') is not None:
        config.DEFAULT_CONFIGURE_PARAMS.append("--with-{}".format(module.get('name')))


def download_package_scripts_deb(src_version):
    """
    Загрузка вспомогательных скриптов для сборки deb пакета
    :return file_name:
    """
    common_utils.ensure_directory(config.SRC_PATH)
    deb_package_scripts_filename = "nginx_{}-1~{}.debian.tar.xz".format(
        src_version,
        config.OS_RELEASE
    )
    deb_package_scripts_url = "{}/{}".format(
        config.DEB_PACKAGE_SCRIPTS_URL_MAINLINE,
        deb_package_scripts_filename
    )
    if version.parse(src_version).release[1] % 2 == 0:
        deb_package_scripts_url = "{}/{}".format(
            config.DEB_PACKAGE_SCRIPTS_URL_STABLE,
            deb_package_scripts_filename
        )

    logger.info("Download scripts for build deb package")
    with open(os.path.join(config.SRC_PATH, deb_package_scripts_filename), "wb") as file:
        response = get(deb_package_scripts_url)
        if 400 <= response.status_code < 500:
            logger.error(u"{} Client Error: {} for url: {}".format(response.status_code, response.reason, deb_package_scripts_url))
            sys.exit(1)
        elif 500 <= response.status_code < 600:
            logger.error(u"{} Server Error: {} for url: {}".format(response.status_code, response.reason, deb_package_scripts_url))
            sys.exit(1)
        file.write(response.content)

    return deb_package_scripts_filename


def download_package_scripts_rpm():
    """
    Загрузка вспомогательных скриптов для сборки rpm пакета
    :return file_name:
    """
    common_utils.ensure_directory(config.SRC_PATH)

    file_name = None
    logger.info("Download scripts for build rpm package")
    common_utils.execute_command("rpmdev-setuptree", os.getcwd())
    return file_name


def install_deb_packages(all_deps):
    """
    Установка deb пакетов
    :param all_deps:
    :return:
    """
    import apt

    cache = apt.cache.Cache()
    cache.update()
    cache.open(None)

    for dependency in all_deps:
        pkg = cache[dependency]
        if pkg.is_installed:
            logger.warning("'{}' already installed".format(dependency))
            continue

        pkg.mark_install()
        try:
            cache.commit()
        except SystemError as err:
            logger.error("Failed to download %s. Cause %s",
                         (dependency, err))


def download_dependencies_deb(modules):
    """
    Установка зависимостей, если они есть
    :param modules:
    :return dependencies_all:
    """
    logger.info("Downloading dependencies")
    dependencies_all = set()
    if not modules:
        return list(dependencies_all)

    for module in modules:
        module = module.get('module', {})
        dependencies = module.get('dependencies', [])
        dependencies_all.update(dependencies)

    dependencies_list = list(dependencies_all)
    if dependencies_list:
        install_deb_packages(dependencies_list)

    return dependencies_list


def install_rpm_packages(all_deps):
    """
    Установка rpm пакетов
    :param all_deps:
    :return:
    """

    install_command = ['yum', 'install', '--assumeyes']
    install_command.extend(all_deps)
    common_utils.execute_command(
        " ".join(install_command),
        os.getcwd()
    )


def download_dependencies_rpm(modules):
    """
    Установка зависимостей
    :param modules:
    :return:
    """
    logger.info("Download dependencies")
    dependencies_all = set()
    if not modules:
        return list(dependencies_all)
    for module in modules:
        module = module.get('module', {})
        dependencies = module.get('dependencies', [])
        dependencies_all.update(dependencies)

    dependencies_list = list(dependencies_all)
    if dependencies_list:
        install_rpm_packages(dependencies_list)

    return dependencies_list


def set_module_name(module_name, url):
    """
    Установка имени модуля из имеющихся данных
    :param module_name:
    :param url:
    :return:
    """
    if not module_name:
        module_name = url[url.rfind("/") + 1:].rsplit(".", 1)[0]

    return module_name
