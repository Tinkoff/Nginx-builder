#!/bin/sh
docker login -e $DOCKER_EMAIL -u $DOCKER_USER -p $DOCKER_PASS
if [ "$TRAVIS_BRANCH" = "master" ]; then
    TAG="latest"
else
    TAG="$TRAVIS_BRANCH"
fi

#Publish Centos
docker build -f centos -t $TRAVIS_REPO_SLUG:$TAG .
docker push $TRAVIS_REPO_SLUG

#Publish Ubuntu
docker build -f Dockerfile -t $TRAVIS_REPO_SLUG:$TAG .
docker push $TRAVIS_REPO_SLUG