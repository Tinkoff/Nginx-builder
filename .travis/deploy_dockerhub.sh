#!/bin/bash
set -eux -o pipefail

docker login -u "${DOCKER_USER}" -p "${DOCKER_PASS}"
if [ "${TRAVIS_BRANCH}" = "master" ]; then
    TAG="latest"
else
    TAG=${TRAVIS_BRANCH}
fi

lowercased_TRAVIS_REPO_SLUG=$(echo "${TRAVIS_REPO_SLUG}" | tr '[:upper:]' '[:lower:]')
lowercased_TAG=$(echo "${TAG}" | tr '[:upper:]' '[:lower:]')

#Publish Centos
docker build --no-cache -f Dockerfile.centos -t "${lowercased_TRAVIS_REPO_SLUG}:centos-${lowercased_TAG}" .
docker push "${lowercased_TRAVIS_REPO_SLUG}:centos-${lowercased_TAG}"

#Publish Ubuntu
docker build --no-cache -f Dockerfile.ubuntu -t "${lowercased_TRAVIS_REPO_SLUG}:ubuntu-${lowercased_TAG}" .
docker push "${lowercased_TRAVIS_REPO_SLUG}:ubuntu-${lowercased_TAG}"

