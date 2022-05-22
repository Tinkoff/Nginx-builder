import logging
import os
import shutil
import sys
from collections import OrderedDict

from src import common_utils
from src import config
from src import config_parser

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

    source_dir = os.path.join(config.SRC_PATH, f"nginx-{version}")
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
    dh_make_command = (
        f"dh_make --copyright {config.LICENSE_TYPE} -e {config.EMAIL_CREATOR} --createorig -s -y -p nginx_{version}"
    )
    common_utils.execute_command(dh_make_command, source_dir)

    logger.info("Running 'dpkg-buildpackage'...")
    build_package = "dpkg-buildpackage -b -us -uc"
    response, rc = common_utils.execute_command(build_package, source_dir)
    if rc == config.DPKG_FAIL_EXIT_CODE:
        sys.exit(1)

    package_name = None
    for file in os.listdir(config.SRC_PATH):
        if file.startswith(f"nginx_{version}") and file.endswith(".deb"):
            package_name = file

    return [os.path.join(config.SRC_PATH, package_name)]


def build_rpm(version, downloaded_modules, revision, configure_params, patches):
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

    spec_file = "nginx.spec"

    if not patches is None:
        # Patch spec file
        spec_path = os.path.join(specs_dir, spec_file)
        spec_path_patched = os.path.join(specs_dir, "nginx_patched.spec")
        with open(os.path.join(specs_dir, spec_path_patched), 'w') as outfile:
            i = 0
            for patch in patches:
                patch_file = patch.replace("/", "_")
                shutil.move(os.path.join(modules_dir, patch), os.path.join(scripts_dir, patch_file))
                outfile.write(f"Patch{i}: {patch_file}\n")
                i += 1

            with open(spec_path) as infile:
                for line in infile:
                    outfile.write(line)

        # replace spec file with patched version
        os.unlink(spec_path)
        os.rename(spec_path_patched, spec_path)

    shutil.move(modules_dir, scripts_dir)
    modules_dir = os.path.join(scripts_dir, "modules")

    prepare_rules_rpm(specs_dir, downloaded_modules, modules_dir, revision, configure_params)
    common_utils.execute_command(f"rpmbuild -bb {spec_file}", specs_dir)
    package_name = None
    package_debuginfo_name = None
    for file in os.listdir(os.path.join(rpms_dir, config.PLATFORM_ARCH)):
        if file.startswith(f"nginx-{version}") and file.endswith(".rpm"):
            package_name = file
        elif file.startswith(f"nginx-debuginfo-{version}") and file.endswith(".rpm"):
            package_debuginfo_name = file
    return [
        os.path.join(rpms_dir, config.PLATFORM_ARCH, package_name),
        os.path.join(rpms_dir, config.PLATFORM_ARCH, package_debuginfo_name),
    ]


def prepare_changelog(source_dir, version, revision):
    """
    Внесение имени нужной версии nginx для именования пакета
    :param source_dir:
    :param version:
    :param revision:
    :return:
    """
    with open(f'{source_dir}/changelog', 'r') as input_file:
        content_file = input_file.readlines()
    with open(f'{source_dir}/changelog', 'w') as output_file:
        replace_line = f"nginx ({version}-1~"
        for line in content_file:
            if replace_line in line:
                line = f"nginx ({version}-{revision}) {config.OS_RELEASE}; urgency=low\n"
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
        configure_command.append(f"--add-module=$(MODULESDIR)/{module}")
    configure_command = " ".join(configure_command)

    with open(f'{source_dir}/rules', 'r') as input_file:
        content_file = input_file.readlines()
    with open(f'{source_dir}/rules', 'w') as output_file:
        for line in content_file:
            if "CFLAGS=" in line:
                line = f'CFLAGS="" {configure_command}\n'
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
        configure_command.append(f"--add-module={modules_dir}/{module}")
    configure_command = " ".join(configure_command)

    with open(f'{source_dir}/nginx.spec', 'r') as input_file:
        content_file = input_file.readlines()
    with open(f'{source_dir}/nginx.spec', 'w') as output_file:
        for line in content_file:
            if "./configure" in line:
                line = configure_command
            if "%define main_release" in line:
                line = f"%define main_release {revision}.ngx"
            output_file.write(line)


def prepare_nginx_dirs(source_dir):
    """
    Добавление директорий установки nginx
    :param source_dir:
    :return:
    """
    with open(f'{source_dir}/nginx.dirs', 'r') as input_file:
        content_file = input_file.readlines()
    with open(f'{source_dir}/nginx.dirs', 'w') as output_file:
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
    parsed_control_file = config_parser.parse_control_file(f'{source_dir}/control')
    repaired_keys = repair_keys(control_changes)
    merged_dict = merge_dicts(parsed_control_file, repaired_keys)

    with open(f'{source_dir}/control', 'w') as output_file:
        for key in merged_dict:
            for k in merged_dict[key]:
                output_file.write(f"{k}: {merged_dict[key][k]}\n")
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
        index_q = f'{index}_{repaired_keys[index]}'
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
            index_q = f'{index}_{changes[index]}'
            if state == 'present':
                del changes['State']
                control_file_dict[index_q] = changes
            elif state == 'append':
                for k in changes:
                    if k not in ['State', 'Source', 'Package'] and control_file_dict[index_q][k]:
                        control_file_dict[index_q][k] = str.join(', ', (control_file_dict[index_q][k], changes[k]))
        except:
            logger.error(f'Не указан параметр state для {key}')
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
        logger.info(f"Apply patch {patch}")
        patch_command = f"patch -p1 < {os.path.join(modules_dir, patch)}"
        common_utils.execute_command(patch_command, source_dir)
