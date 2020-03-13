# Nginx-builder
[![Build Status](https://travis-ci.com/TinkoffCreditSystems/Nginx-builder.svg?branch=master)](https://travis-ci.com/TinkoffCreditSystems/Nginx-builder)

## Description/Описание
### ENG
Tool for building `deb` or `rpm` package [Nginx] (http://nginx.org/) of the required version from the source code, with the ability to connect third-party modules.
Nginx parameters are set in the configuration file of yaml format.

### RU
Инструмент для сборки `deb` или `rpm` пакета [Nginx](http://nginx.org/) требуемой  версии из исходных кодов, с возможностью подключения сторонних модулей.
Параметры Nginx задаются в конфигурационном файле формата yaml.

## Docker
### ENG
Now we are at the Docker hub:
https://cloud.docker.com/repository/docker/tinkoffcreditsystems/nginx-builder

### RU
Теперь мы есть и на Docker hub:
https://cloud.docker.com/repository/docker/tinkoffcreditsystems/nginx-builder

## Execution options/Параметры запуска
### ENG
You can start the assembler both directly on the host machine and in the docker container, for example

### RU
Запускать сборщик можно, как непосредственно на хост машине, так и в docker контейнере, например

### Example run/Пример запуска в docker образе "ubuntu-latest" или "centos-latest
```bash
docker run --rm -it -v $(pwd):/nginx-builder:rw tinkoffcreditsystems/nginx-builder:centos-latest /bin/bash
docker run --rm -it -v $(pwd):/nginx-builder:rw tinkoffcreditsystems/nginx-builder:ubuntu-latest /bin/bash
```

## Конфигурация
### ENG
The main configuration file is in yaml format. Description of parameters:
```yaml
---
nginx_version: the necessary version of nginx
output_package: type of output package deb or rpm
modules:
  - module:
      name: The name of the module. If not specified, taken from the last part of the URL
      git_url: git file URL
      git_tag: The name of the tag. (Optional)
      git_branch: The name of the branch. (Optional). If neither tag nor branch is specified, the master branch is taken by default
      dependencies: 
        - list of dependencies for building the module (Optional)
    module:
      name: The name of the module. If not specified, taken from the last part of the URL
      web_url: Link to the archive with the module source code
    module:
      name: The name of the module. If not specified, taken from the last part of the URL
      local_url: Path to the module source code archive
    module:
      name: The name of the embedded module
      type: embedded  
```
The configuration file with advanced settings is located in `src/config.py`. In most cases it does not need to be changed.

### RU
Основной конфигурационный файл в yaml формате. Описание параметров:
```yaml
---
nginx_version: необходимая версия nginx
output_package: тип выходного пакета deb или rpm
modules:
  - module:
      name: Название модуля. Если не указано, берется из последней части URL
      git_url: URL git файла
      git_tag: название тэга. (Не обязательно)
      git_branch: название ветки. (Не обязательно). Если не указан ни tag, ни branch по умолчанию берется master ветка
      dependencies: 
        - список зависимостей для сборки модуля (Не обязательно)
    module:
      name: Название модуля. Если не указано, берется из последней части URL
      web_url: Ссылка на архив с исходным кодом модуля
    module:
      name: Название модуля. Если не указано, берется из последней части URL
      local_url: Путь к архиву с исходным кодом модуля
    module:
      name: Название модуля встроенного модуля
      type: embedded  
```
Конфигурационный файл с расширенными настройками расположен в `src/config.py`. В большинстве случаев менять его не нужно.


## Manual script execution/Ручной запуск скрипта

### Requirements/Требования
* python >= 3.5

### ENG
You will also need packages to compile Nginx. Their list can be seen in the Dockerfile.
```bash
pip3 install -r requirements.txt
./main.py build -f [config_file].yaml -r [revision_number]
```
* revision number optional parameter, used to version assemblies

### RU
Также потребуются пакеты для компиляции Nginx. Их перечень можно увидеть в Dockerfile
```bash
pip3 install -r requirements.txt
./main.py build -f [конфиг_файл].yaml -r [номер_ревизии]
```
* номер ревизии опциональный параметр, служит для версионирования сборок
