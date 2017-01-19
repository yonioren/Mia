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

from argparse import ArgumentParser
from configparser import ConfigParser
from docker import DockerClient
from json import dumps
from re import sub
from requests import post, delete

main_parser = ArgumentParser(description="utility for updating members of MiaLB")

main_parser.add_argument("--farm", type=str, required=True, help="farm id")
main_parser.add_argument("--service", type=str, required=True, help="name/id of the docker service we're LBing")
main_parser.add_argument("--mialb-url", type=str, required=False, help="name/id of the docker service we're LBing")

kwargs = main_parser.parse_args().__dict__
last_members = []
client = DockerClient(base_url='http://localhost:2376')

conf_file_order = ['/etc/Mia/mialb.conf', '~/.Mia/mialb.conf', '/software/Mia/LB/mialb.conf']
cp = ConfigParser()
cp.read(filenames=conf_file_order)

if 'mialb-url' in kwargs:
    mialb_url = kwargs['mialb-url']
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

while True:
    service = client.services.get(kwargs['farm'])
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
