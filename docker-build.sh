#!/bin/bash
[ "$1" = -x ] && shift && set -x
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ${DIR}/docker-build-env.sh

set -e

GIT_SHA=$(git rev-parse --short HEAD)
DATE_TIME=$(date -u +"%Y-%m-%dT%H:%M")

rm -f version.txt
echo "${GIT_SHA}-${DATE_TIME}" > version.txt

docker build -t ${DOCKER_IMG_TAG} .
