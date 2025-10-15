#!/usr/bin/env sh

set -ex

micromamba run -n my_environment_name bash -ex -c "$@"