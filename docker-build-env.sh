#!/bin/bash
[ "$1" = -x ] && shift && set -x
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${DOCKER_IMG}" ]]; then
  export DOCKER_IMG=git-apollo-miraisor
fi

if [[ -z "${TAG}" ]]; then
  export TAG=latest
fi

if [[ -z "${DOCKET_HUB_ACCOUNT}" ]]; then
  export DOCKET_HUB_ACCOUNT=idachev
fi

export DOCKER_IMG_TAG=${DOCKER_IMG}:${TAG}
