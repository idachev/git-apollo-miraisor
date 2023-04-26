#!/bin/bash
[ "$1" = -x ] && shift && set -x
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ${DIR}/docker-build-env.sh

${DIR}/docker-build.sh

REMOTE_DOCKER_IMG_TAG=${DOCKET_HUB_ACCOUNT}/${DOCKER_IMG_TAG}

set -e

docker tag ${DOCKER_IMG_TAG} ${REMOTE_DOCKER_IMG_TAG}

docker push ${REMOTE_DOCKER_IMG_TAG}
