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

# join swarm cluster
docker swarm join --token ${token} ${address}

# load nginx image
docker load /tmp/nginx_for_mia.tar

# set up networks
brctl addbr br1
brctl addif br1 eth1
networkId=$(docker network create --driver bridge services)
ip link set br-${networkId} up
ip link add veth-${networkId}-br1 type veth peer veth-br1-${networkId} type veth
ip link set veth-${networkId}-br1 up
ip link set veth-br1-${networkId} up
brctl addif br-${networkId} veth-${networkId}-br1
brctl addif br1 veth-br1-${networkId}

python /usr/bin/docker_networking.py setup