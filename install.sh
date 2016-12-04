#!/usr/bin/env bash

semanage fcontext -a -t httpd_sys_content_t "/software/Mia/LB(/.*)?"
mkdir -p /software/Mia/LB
( cd MiaLB ; tar -cZf - . ) | ( cd /software/Mia/LB ; tar -xf - . )
cp conf/apache-mia-lb.conf /etc/httpd/conf.d/mialb.conf
