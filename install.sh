#!/usr/bin/env bash

yum install -y httpd
semanage fcontext -a -t httpd_sys_content_t "/software/Mia/LB(/.*)?"
mkdir -p /software/Mia/LB
( cd MiaLB ; tar -cf - . ) | ( cd /software/Mia/LB ; tar -xf - . )
cp conf/apache-mia-lb.conf /etc/httpd/conf.d/mialb.conf
