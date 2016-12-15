#!/usr/bin/env bash

# TODO: re-get conf file
# TODO: send update signal to nginx
curl "${MIALBURI}/${FARMID}.conf" -o /etc/nginx/conf.d/${FARMID}.conf
/usr/sbin/nginx -s reload