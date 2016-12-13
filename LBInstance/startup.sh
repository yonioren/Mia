#!/usr/bin/env bash

uid=`hostname`
default_interface=`ip -4 route show | grep default | sed 's/^.*\sdev\s\([^ ]*\)\s.*$/\1/'`
my_ip=`ip -4 addr show ${default_interface} | grep -e "^\s*inet\s" | sed 's/^\s*inet\s\([0-9\.]*\)\/.*/\1/'`

curl -H "Content-Type: application/json, Client-IP: ${my_ip}" -X POST -d '{"docker_uid": "'${uid}'"}' \
 "${MIALBURI}/MiaLB/farms/${FARMID}/instances"
curl "${MIALBURI}/${FARMID}.conf" -o /etc/nginx/conf.d/${FARMID}.conf
flag=1
for i in {1..5}
do
    if ip addr show eth1 2> /dev/null
    then
        flag=0
        break
    else
        sleep 5
    fi
done
if flag
then
    nginx
    while flag
    do
        ps -ef | grep -v grep | grep -q nginx || flag=1
        sleep 5
    done
else
    logger -s -p daemon.err "couldnt find eth1 after 25 seconds. aborting"
fi