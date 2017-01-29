#!/usr/bin/env bash

# set up repository
cat > /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/fedora/$releasever/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF

yum install -y httpd mod_wsgi docker-engine nginx

# set up docker
#sed -i 's@^ExecStart=\([a-z/\-]*\).*$@ExecStart=\1 -H unix:///var/run/docker.sock -H 0.0.0.0:2376@' \
#  //usr/lib/systemd/system/docker.service
systemctl daemon-reload
systemctl enable docker.service ; systemctl start docker.service
swarmIp=`ip -4 addr show | grep inet | \
  sed 's/^\s*inet\s*\([0-9\.]*\).*$/\1/' | grep -v -e "127.\([0-9]*\.\)\{2\}" | head -1`

# leave existing swarm, if a member
docker swarm leave --force

docker swarm init --advertise-addr ${swarmIp}
token=`docker swarm join-token --quiet worker`
nodeId=`docker node ls | grep -e "\*" | cut -d' ' -f1`
docker node update --availability drain ${nodeId}

# set up nginx
chown apache:apache /etc/nginx/conf.d
semanage fcontext -a -t httpd_sys_rw_content_t "/etc/nginx/conf.d(/.*)?"
restorecon -R /etc/nginx/conf.d

# set up logging directory
semanage fcontext -a -t httpd_log_t "/var/log/Mia(/.*)?"
semanage port -a -t http_port_t -p tcp 666
mkdir -p /var/log/Mia
touch /var/log/Mia/mialb.log
chown --recursive apache:apache /var/log/Mia
restorecon -R /var/log/Mia/

# set up application directory
semanage fcontext -a -t httpd_sys_content_t "/software/Mia/LBManager(/.*)?"
mkdir -p /software/Mia/LB
( cd MiaLB ; tar -cf - . ) | ( cd /software/Mia/LBManager ; tar -xf - . )
cp conf/apache-mia-lb.conf /etc/httpd/conf.d/mialb.conf
cp conf/mialb.conf /software/Mia/LB/
cp conf/mialb.sudoers /etc/sudoers.d/mialb
restorecon -R /software/Mia/
chown apache:apache /software/Mia/LB

# other SELinux related permissions
setsebool -P httpd_can_network_connect 1

# build docker image
docker build -t nginx_for_mia:latest LBInstance
docker save nginx_for_mia:latest -o /tmp/nginx_for_mia.tar

# install mialb_updater
cp MiaLBUpdater/mialb_update_farm.py /usr/local/bin/
chmod ug+x /usr/local/bin/mialb_update_farm.py
chown apache:apache /usr/local/bin/mialb_update_farm.py
semanage fcontext -a -t httpd_sys_script_exec_t "/usr/local/bin/mialb_update_farm.py"
restorecon /usr/local/bin/mialb_update_farm.py

# set up docker hosts
for host in `cat conf/hosts`
do
    ssh ${host} "mkdir -p /etc/Mia/"
    scp conf/mialb.conf ${host}:/etc/Mia/
    scp install_docker_host.sh /tmp/nginx_for_mia.tar ${host}:/tmp/
    scp LBInstance/docker_networking.py ${host}:/usr/bin/
    scp -r LBInstance/MiaLBHost ${host}:/usr/lib/python2.7/site-packages/
    ssh ${host} "bash /tmp/install_docker_host.sh --token ${token} --address ${swarmIp}:2377"
    newId=`ssh ${host} docker node inspect --pretty self | grep ID | awk '{print $2}'`
    docker node update --availability active ${newId}
done
