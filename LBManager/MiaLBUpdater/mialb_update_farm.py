#!/usr/bin/python2.7

# Copyright (C) 2016 Eitan Geiger
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
"""
#first of all, daemonize
try:
    pid = os.fork()
    if pid > 0:
        # exit first parent
        sys.exit(0)
except OSError, e:
    sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
    sys.exit(1)

# decouple from parent environment
os.chdir("/")
os.setsid()
os.umask(0)

# do second fork
try:
    pid = os.fork()
    if pid > 0:
        # exit from second parent
        sys.exit(0)
except OSError, e:
    sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
    sys.exit(1)


# redirect standard file descriptors
sys.stdout.flush()
sys.stderr.flush()
si = file('/dev/null', 'r')
so = file('/dev/null', 'a+')
se = file('/dev/null', 'a+', 0)
os.dup2(si.fileno(), sys.stdin.fileno())
os.dup2(so.fileno(), sys.stdout.fileno())
os.dup2(se.fileno(), sys.stderr.fileno())
"""
from argparse import ArgumentParser
from configparser import ConfigParser
from docker import DockerClient
from json import dumps
from logging import getLogger, basicConfig
from requests import post, delete
from time import sleep


logger = getLogger(__name__)
basicConfig(filename="/var/log/Mia/mialb-update.log",
            format='[%(asctime)s] [%(levelname)s] %(module)s - %(funcName)s:   %(message)s',
            level='DEBUG',
            datefmt='%m/%d/%Y %I:%M:%S %p')

main_parser = ArgumentParser(description="utility for updating members of MiaLB")

main_parser.add_argument("--farm", type=str, required=True, help="farm id")
main_parser.add_argument("--service", type=str, required=True, help="name/id of the docker service we're LBing")
main_parser.add_argument("--mialb-url", type=str, required=False, help="name/id of the docker service we're LBing")

logger.debug("configured parser")

try:
    kwargs = main_parser.parse_args().__dict__
except Exception, e:
    logger.warn("got error tring to parse args!")
    logger.debug("%d (%s)\n" % (e.errno, e.strerror))
logger.debug("parsed args")
last_members = []
client = DockerClient(base_url='http://localhost:2376')
logger.debug("configured docker client")

conf_file_order = ['/etc/Mia/mialb.conf', '~/.Mia/mialb.conf', '/software/Mia/LBManager/mialb.conf']
cp = ConfigParser()
cp.read(filenames=conf_file_order)
logger.debug("read configureations")

if 'mialb_url' in kwargs:
    mialb_url = kwargs['mialb_url']
else:
    try:
        host = cp.get(section='server', option='host')
        port = cp.get(section='server', option='port')
    except Exception:
        host = 'localhost'
        port = 6669
    local_addr = "{host}:{port}".format(host=host, port=port)
    print("http://{}".format(local_addr))
    mialb_url = "http://{}".format(local_addr)
logger.debug("mialb url: {}".format(mialb_url))
service = client.services.get(kwargs['farm'])

while True:
    logger.debug("starting endless loop")

    try:
        members = service.tasks()
        obsoletes = set(last_members) - set(members)
        for member in obsoletes:
            delete(url="{mialb_url}/MiaLB/Farms/{farm_id}/members/{member_id}".format(mialb_url=mialb_url,
                                                                                      farm_id=kwargs['farm'],
                                                                                      member_id=str(member['ID'])
            ))
        news = set(members) - set(last_members)
        for member in news:
            container_id = member['Status']['ContainerStatus']['ContainerID']
            net = service.attrs['Endpoint']['VirtualIPs'][0]['NetworkID']
            container_ip = client.containers.get(container_id).attrs['NetworkSettings']['Networks'][net]['IPAddress']
            post(url="{mialb_url}/MiaLB/Farms/{farm_id}/members/{member_id}".format(mialb_url=mialb_url,
                                                                                    farm_id=kwargs['farm'],
                                                                                    member_id=str(member['ID'])),
                 headers={'Content-Type': 'text/plain'},
                 data=dumps({"member_id": str(member['ID']),
                             "ip": str(container_ip)}))
        last_members = members
    except Exception:
        pass
    logger.debug("starting sleep")
    sleep(3)

logger.debug("peace out")
