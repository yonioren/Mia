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
systemctl enable docker.service ; systemctl start docker.service

# join swarm cluster
docker swarm join --token $token $address

# set up networks
brctl addbr br1
docker network create --driver bridge