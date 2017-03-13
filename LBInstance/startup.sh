#!/usr/bin/env bash


my_ip=`ip -4 addr show ${default_interface} | grep -e "^\s*inet\s" | sed 's/^\s*inet\s\([0-9\.]*\)\/.*/\1/'`

/usr/bin/python2.7 /MiaLB/api_router.py --run-damn-you &

flag=0
if [ $flag -eq 0 ]
then
    nginx -g "daemon on;"
    while [ $flag -eq 0 ]
    do
        ps -ef | grep -v grep | grep -q nginx || flag=1
        sleep 5
    done
else
    logger -s -p daemon.err "nginx died. aborting"
    exit 1
fi
