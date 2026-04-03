#!/bin/sh
set -e
ORIGIN="${BACKEND_ORIGIN:-http://backend:8000}"
sed "s|__BACKEND_ORIGIN__|${ORIGIN}|g" /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
