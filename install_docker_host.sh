#!/usr/bin/env bash

# parse arguments
while [ $# -gt 0 ]
do
    case $1 in
    '--token')
        token=$2
        shift 2 ;;
    '--address')
        address=$2
        shift 2 ;;
    *)
        logger -p user.error "install docker host failed: argument error"
        logger -p user.debug "$@"
        exit 1
    esac
done

# install docker
cat > /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/fedora/$releasever/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF

yum install -y docker-engine
sed -i 's@^ExecStart=.*$@ExecStart=/usr/bin/dockerd -H unix:///var/run/docker.sock -H 0.0.0.0:2376@' \
  //usr/lib/systemd/system/docker.service
systemctl daemon-reload
systemctl enable docker.service ; systemctl start docker.service

# install pip and dockerpy
which pip || ( curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" ; python get-pip.py )
pip install docker || yum install -y python-docker
pip install configparser

# clean previous shit
docker network rm services
docker swarm leave
find /usr/lib/python2.7/site-packages/MiaLBHost -name "*.pyc" -exec rm -f {} \;

# join swarm cluster
docker swarm join --token ${token} ${address}

# load nginx image
docker load -i /tmp/nginx_for_mia.tar

python /usr/bin/docker_networking.py setup

# set up networks
brctl addbr br1
brctl addif br1 eth1
networkId=$(docker network list | awk '$2=="services" {print $1}')
ip link set br-${networkId} up
ip link add veth-svcs-br1 type veth peer name veth-br1-svcs type veth
ip link set veth-svcs-br1 up
ip link set veth-br1-svcs up
brctl addif br-${networkId} veth-svcs-br1
brctl addif br1 veth-br1-svcs
