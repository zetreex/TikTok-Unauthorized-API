#!/usr/bin/env bash

set -e

PYTHON="python -O"
APP="exec ${PYTHON} manage.py"


case "$1" in
  run-production)
    exec gunicorn -c "config/gunicorn.py" "app.__init__:create_app()"
    ;;

  run-development)
    ${APP}
    ;;

  *)
    ${@}

esac