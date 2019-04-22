FROM ubuntu:16.04

LABEL maintainer="devops@tinkoff.ru"

RUN apt-get update && \
    apt-get install -y tzdata locales wget build-essential autogen automake autoconf \
    autotools-dev libreadline-dev libncurses5-dev libpcre3 libpcre3-dev libpng-dev \
    dh-make quilt lsb-release debhelper dpkg-dev dh-systemd pkg-config \
    zlib1g-dev libssl-dev openssl git  perl libtool tar unzip xutils-dev \
    python3-pip python3-apt

# Set locales
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8

# timezone
ENV TZ Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /nginx-builder
COPY . /nginx-builder
RUN pip3 install -r requirements.txt
