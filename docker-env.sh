#!/bin/bash
[ "$1" = -x ] && shift && set -x
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${DOCKER_IMG}" ]]; then
  DOCKER_IMG=git-apollo-miraisor
fi

if [[ -z "${TAG}" ]]; then
  TAG=latest
fi

if [[ -z "${DOCKET_HUB_ACCOUNT}" ]]; then
  DOCKET_HUB_ACCOUNT=idachev
fi

DOCKER_IMG_TAG=${DOCKER_IMG}:${TAG}
