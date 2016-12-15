#!/usr/bin/env bash

yum install -y httpd mod_wsgi docker-engine nginx

# set up docker
sed -i 's@^\(ExecStart=.*$\)@\1 -H unix:///var/run/docker.sock -H 0.0.0.0:2376@' \
  //usr/lib/systemd/system/docker.service

# set up nginx
chown apache:apache /etc/nginx/conf.d
semanage fcontext -a -t httpd_sys_rw_content_t "/etc/nginx/conf.d(/.*)?"
restorecon -R /etc/nginx/conf.d

# set up logging directory
semanage fcontext -a -t httpd_log_t "/var/log/Mia(/.*)?"
semanage port -a -t http_port_t -p tcp 666
mkdir -p /var/log/Mia
chown apache:apache /var/log/Mia
restorecon -R /var/log/Mia/

# set up application directory
semanage fcontext -a -t httpd_sys_content_t "/software/Mia/LB(/.*)?"
mkdir -p /software/Mia/LB
( cd MiaLB ; tar -cf - . ) | ( cd /software/Mia/LB ; tar -xf - . )
cp conf/apache-mia-lb.conf /etc/httpd/conf.d/mialb.conf
cp conf/mialb.conf /software/Mia/LB/
restorecon -R /software/Mia/
chown apache:apache /software/Mia/LB

# other SELinux related permissions
setsebool -P httpd_can_network_connect 1
