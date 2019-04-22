import yaml
import sys
from collections import OrderedDict
import logging

logger = logging.getLogger("builder")


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """
    Получение сортированного словаря
    :param stream:
    :param Loader:
    :param object_pairs_hook:
    :return:
    """
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def parse_yaml(file_name):
    """
    Парсинг yaml файла
    :param file_name:
    :return config:
    """
    logger.info("Parse yaml file: {}".format(file_name))
    with open(file_name, 'r') as stream:
        try:
            config = ordered_load(stream, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            logger.error(str(exc))
    if not config.get('nginx_version'):
        logger.error("ERROR: nginx_version not specified")
        sys.exit(1)
    if not config.get('output_package'):
        logger.error("ERROR: output package not specified")
        sys.exit(1)
    if not config.get('control'):
        config['control'] = None
    if not config.get('modules'):
        config['modules'] = None
    return config


def parse_control_file(control_file):
    """
    Парсинг control файла
    :param control_file:
    :return parsed_paragraph_dict:
    """
    parsed_paragraph_dict = OrderedDict()
    with open(control_file, 'r') as stream:
        data = stream.read().split('\n\n')
    for paragraph in data:
        try:
            parsed_paragraph = ordered_load(paragraph, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            logger.error(exc)
        index = list(parsed_paragraph)[0]
        index_q = '{}_{}'.format(index, parsed_paragraph[index])
        parsed_paragraph_dict[index_q] = parsed_paragraph
    return parsed_paragraph_dict
