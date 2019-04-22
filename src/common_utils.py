import tarfile
import zipfile
import subprocess
import sys
import os
import getpass
import logging

logger = logging.getLogger("builder")


def execute_command(command, path):
    """
    Выполнятор shell команд
    :param command:
    :param path:
    :return exit_code:
    """
    my_env = os.environ.copy()
    my_env["LOGNAME"] = getpass.getuser()
    my_env["USER"] = getpass.getuser()
    logger.info("Running command: %s", command)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        cwd=path,
        shell=True,
        env=my_env,
        universal_newlines=True
    )
    out, err = process.communicate()

    logger.info(out)
    if err:
        print("STDERR CONTENT:", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

    return out, process.returncode


def extract_archive(file_name, dest_path):
    """
    Извлечение из архива
    :param file_name:
    :param dest_path:
    :return:
    """
    extracted_file = None
    dest_file_path = os.path.join(dest_path, file_name)
    if tarfile.is_tarfile(dest_file_path) or '.xz' in file_name:
        tar = tarfile.open(dest_file_path)
        tar.extractall(path=dest_path)
        extracted_file = tar.getnames()[0]
        tar.close()
    elif zipfile.is_zipfile(dest_file_path):
        zip = zipfile.ZipFile(dest_file_path, 'r')
        zip.extractall(path=dest_path)
        extracted_file = zip.namelist()[0]
        zip.close()
    else:
        logger.error("Archive format {} is not valid".format(file_name))

    return extracted_file.rstrip('/')


def ensure_directory(path):
    """
    Создать директорию если ее нет
    :param path:
    :return:
    """
    try:
        os.mkdir(path)
    except FileExistsError:
        logger.info("%s dir already exist", path)
