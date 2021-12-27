#!/usr/bin/env python3

import argparse
import sys
from src import config_parser
from src import downloader
from src import builder
from src import publicator
import logging

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("builder")


def build(args):
    """
    Обработчик команды build
    :return:
    """
    config = config_parser.parse_yaml(args.file)
    package_name = None
    if config["output_package"] == "deb":
        package_name = build_deb(config, args.revision)
    elif config["output_package"] == "rpm":
        package_name = build_rpm(config, args.revision)
    else:
        logger.error("Output package type is not valid")
        sys.exit(1)

    for p in package_name:
        publicator.public_local(p)


def build_deb(config, revision):
    """
    Сборка deb пакета
    :param config:
    :param revision:
    :return:
    """
    scripts_archive_name = downloader.download_package_scripts_deb(config["nginx_version"])
    src_archive_name = downloader.download_source(config["nginx_version"])
    downloaded_modules = downloader.download_modules(config["modules"])
    downloader.download_dependencies_deb(config["modules"])
    patches = downloader.get_patches_list(config["modules"])
    package_name = builder.build_deb(
        config["nginx_version"],
        src_archive_name,
        downloaded_modules,
        scripts_archive_name,
        config["control"],
        revision,
        config['configure_params'],
        patches
    )

    return package_name


def build_rpm(config, revision):
    """
    Сборка rpm пакета
    :param config:
    :param revision:
    :return:
    """
    downloader.download_package_scripts_rpm()
    downloader.download_source_rpm(config["nginx_version"])
    downloaded_modules = downloader.download_modules(config["modules"])
    downloader.download_dependencies_rpm(config["modules"])
    package_name = builder.build_rpm(
        config["nginx_version"],
        downloaded_modules,
        revision,
        config['configure_params']
    )

    return package_name


def parse_args():
    """
    Парсинг передаваемых параметров запуска
    :return parser.parse_args():
    """
    parser = argparse.ArgumentParser(description="Nginx builder")
    subparsers = parser.add_subparsers()
    parser_build = subparsers.add_parser('build', help='build deb package')
    parser_build.add_argument('-f', '--file', help='Yaml config file path', default='config.yaml')
    parser_build.add_argument('-r', '--revision', help='Revision package', default='1')
    parser_build.set_defaults(func=build)
    return parser.parse_args()


def main():
    if len(sys.argv) > 1:
        args = parse_args()
        try:
            args.func(args)
        except Exception as e:
            logger.error(str(e))
            sys.exit(1)
    else:
        logger.error('error: no arguments passed: use -h to help')
    
    
if __name__ == '__main__':
    main()
