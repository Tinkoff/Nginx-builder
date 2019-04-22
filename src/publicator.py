import shutil
import os


def public_local(package_name):
    """
    Опубликовать пакет локально
    :(package_name:
    :return:
    """
    shutil.move(package_name, os.getcwd())
