import os
import sys
import shutil
from collections import OrderedDict
from src import config
from src import config_parser
from src import common_utils
import logging

logger = logging.getLogger("builder")


def build_deb(version, src_archive_name, downloaded_modules,
              scripts_archive_name, control_file_params, revision, configure_params, patches):
    """
    Сборка deb пакета
    :param version:
    :param src_archive_name:
    :param downloaded_modules:
    :param scripts_archive_name:
    :param control_file_params:
    :param revision:
    :param configure_params:
    :param patches:
    :return:
    """
    logger.info("Building .deb package")
    common_utils.extract_archive(src_archive_name, config.SRC_PATH)
    common_utils.extract_archive(scripts_archive_name, config.SRC_PATH)

    source_dir = os.path.join(config.SRC_PATH, "nginx-{}".format(version))
    modules_dir = os.path.join(config.SRC_PATH, "modules")
    scripts_dir = os.path.join(config.SRC_PATH, "debian")
    shutil.move(modules_dir, scripts_dir)
    shutil.move(scripts_dir, source_dir)

    scripts_dir = os.path.join(source_dir, "debian")
    modules_dir = os.path.join(scripts_dir, "modules")

    apply_patch(modules_dir, source_dir, patches)
    prepare_changelog(scripts_dir, version, revision)
    prepare_rules(scripts_dir, downloaded_modules, configure_params)
    prepare_nginx_dirs(scripts_dir)

    change_control(scripts_dir, control_file_params)

    logger.info("Running 'dh_make'...")
    dh_make_command = "dh_make --copyright {} -e {} --createorig -s -y -p nginx_{}".format(
        config.LICENSE_TYPE,
        config.EMAIL_CREATOR,
        version
    )
    common_utils.execute_command(dh_make_command, source_dir)

    logger.info("Running 'dpkg-buildpackage'...")
    build_package = "dpkg-buildpackage -b -us -uc"
    response, rc = common_utils.execute_command(build_package, source_dir)
    if rc == config.DPKG_FAIL_EXIT_CODE:
        sys.exit(1)

    package_name = None
    for file in os.listdir(config.SRC_PATH):
        if file.startswith("nginx_{}".format(version)) and file.endswith(".deb"):
            package_name = file

    return os.path.join(config.SRC_PATH, package_name)


def build_rpm(version, downloaded_modules, revision, configure_params):
    """
    Сборка rpm пакета
    :param version:
    :param downloaded_modules:
    :param revision:
    :param configure_params:
    :return:
    """
    logger.info("Building .rpm package")
    modules_dir = os.path.join(config.SRC_PATH, "modules")
    response, rc = common_utils.execute_command("rpm --eval '%{_topdir}'", os.getcwd())
    top_dir = response.rstrip("\n")
    scripts_dir = os.path.join(top_dir, "SOURCES")
    specs_dir = os.path.join(top_dir, "SPECS")
    rpms_dir = os.path.join(top_dir, "RPMS")

    shutil.move(modules_dir, scripts_dir)
    modules_dir = os.path.join(scripts_dir, "modules")

    prepare_rules_rpm(specs_dir, downloaded_modules, modules_dir, revision, configure_params)
    common_utils.execute_command("rpmbuild -bb nginx.spec", specs_dir)
    package_name = None
    for file in os.listdir(os.path.join(rpms_dir, config.PLATFORM_ARCH)):
        if file.startswith("nginx-{}".format(version)) and file.endswith(".rpm"):
            package_name = file
    return os.path.join(rpms_dir, config.PLATFORM_ARCH, package_name)


def prepare_changelog(source_dir, version, revision):
    """
    Внесение имени нужной версии nginx для именования пакета
    :param source_dir:
    :param version:
    :param revision:
    :return:
    """
    with open('{}/changelog'.format(source_dir), 'r') as input_file:
        content_file = input_file.readlines()
    with open('{}/changelog'.format(source_dir), 'w') as output_file:
        replace_line = "nginx ({}-1~".format(version)
        for line in content_file:
            if replace_line in line:
                line = "nginx ({}-{}) {}; urgency=low\n".format(version, revision, config.OS_RELEASE)
            output_file.write(line)


def prepare_rules(source_dir, downloaded_modules, configure_params):
    """
    Внесение нужных параметров в файл rules
    :param source_dir:
    :param downloaded_modules:
    :param configure_params:
    :return:
    """
    configure_command = ["./configure"] + config.DEFAULT_CONFIGURE_PARAMS
    for configure_param in configure_params:
        configure_command.append(configure_param)
    for module in downloaded_modules:
        configure_command.append("--add-module=$(MODULESDIR)/{}".format(module))
    configure_command = " ".join(configure_command)

    with open('{}/rules'.format(source_dir), 'r') as input_file:
        content_file = input_file.readlines()
    with open('{}/rules'.format(source_dir), 'w') as output_file:
        for line in content_file:
            if "CFLAGS=" in line:
                line = 'CFLAGS="" {}'.format(configure_command + "\n")
            if "default.conf" in line:
                continue
            output_file.write(line)
            if "#!/usr/bin/make -f" in line:
                output_file.write(config.MODULESDIR)


def prepare_rules_rpm(source_dir, downloaded_modules, modules_dir, revision, configure_params):
    """
    Внесение правил сборки в spec файл
    :param source_dir:
    :param downloaded_modules:
    :param modules_dir:
    :param revision:
    :param configure_params:
    :return:
    """
    configure_command = ["./configure"] + config.DEFAULT_CONFIGURE_PARAMS
    for configure_param in configure_params:
        configure_command.append(configure_param)
    for module in downloaded_modules:
        configure_command.append("--add-module={}/{}".format(modules_dir, module))
    configure_command = " ".join(configure_command)

    with open('{}/nginx.spec'.format(source_dir), 'r') as input_file:
        content_file = input_file.readlines()
    with open('{}/nginx.spec'.format(source_dir), 'w') as output_file:
        for line in content_file:
            if "./configure" in line:
                line = configure_command
            if "%define main_release" in line:
                line = "%define main_release {}.ngx".format(revision)
            output_file.write(line)


def prepare_nginx_dirs(source_dir):
    """
    Добавление директорий установки nginx
    :param source_dir:
    :return:
    """
    with open('{}/nginx.dirs'.format(source_dir), 'r') as input_file:
        content_file = input_file.readlines()
    with open('{}/nginx.dirs'.format(source_dir), 'w') as output_file:
        for line in content_file:
            output_file.write(line)
            if "/var/log/nginx" in line:
                output_file.write("/etc/nginx/geoip")


def change_control(source_dir, control_changes):
    """
    Изменение файла control
    :param source_dir:
    :param control_changes:
    :return:
    """
    if not control_changes:
        return False
    parsed_control_file = config_parser.parse_control_file('{}/control'.format(source_dir))
    repaired_keys = repair_keys(control_changes)
    merged_dict = merge_dicts(parsed_control_file, repaired_keys)

    with open('{}/control'.format(source_dir), 'w') as output_file:
        for key in merged_dict:
            for k in merged_dict[key]:
                output_file.write("{}: {}\n".format(k, merged_dict[key][k]))
            output_file.write("\n")
    return True


def repair_keys(block):
    """
    Преобразованиие формата названий параметров
    :param block:
    :return repaired_keys_dict:
    """
    repaired_keys_dict = OrderedDict()
    for block_part in block:
        repaired_keys = OrderedDict()
        for key in block_part:
            z = ''.join(x for x in key.title() if not x.isspace()).replace('_', '-')
            repaired_keys[z] = block_part[key]
        index = list(repaired_keys)[0]
        index_q = '{}_{}'.format(index, repaired_keys[index])
        repaired_keys_dict[index_q] = repaired_keys
    return repaired_keys_dict


def merge_dicts(control_file_dict, control_changes_dict):
    """
    Объединение параметров в файле control и передаваемых в конфигурационном
    :param control_file_dict:
    :param control_changes_dict:
    :return control_file_dict:
    """
    for key in control_changes_dict:
        try:
            state = control_changes_dict[key]['State']
            changes = control_changes_dict[key]
            index = list(changes)[0]
            index_q = '{}_{}'.format(index, changes[index])
            if state == 'present':
                del changes['State']
                control_file_dict[index_q] = changes
            elif state == 'append':
                for k in changes:
                    if k not in ['State', 'Source', 'Package'] and control_file_dict[index_q][k]:
                        control_file_dict[index_q][k] = str.join(', ', (control_file_dict[index_q][k], changes[k]))
        except:
            logger.error('Не указан параметр state для {}'.format(key))
            sys.exit(1)
    return control_file_dict


def apply_patch(modules_dir, source_dir, patches):
    """
    Применение патча
    :param modules_dir:
    :param source_dir:
    :param patches:
    :return:
    """
    for patch in patches:
        logger.info("Apply patch {}".format(patch))
        patch_command = "patch -p1 < {}".format(os.path.join(modules_dir, patch))
        common_utils.execute_command(patch_command, source_dir)
