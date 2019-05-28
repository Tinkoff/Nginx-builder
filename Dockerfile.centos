FROM centos:7

LABEL maintainer="devops@tinkoff.ru"

RUN yum install -y rpmdevtools gcc make automake yum-utils git redhat-lsb-core \
    openssl-devel zlib-devel pcre-devel epel-release \
    && yum install -y python36 python36-devel python36-pip \
    && yum clean all

# Set locales
ENV LANG en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8

# timezone
ENV TZ Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /nginx-builder
COPY . /nginx-builder
RUN pip3.6 install -r requirements.txt --no-cache-dir
