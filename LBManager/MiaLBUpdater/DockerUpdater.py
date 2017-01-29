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
from docker import DockerClient
from json import dumps
from logging import getLogger
from requests import get, post, delete
from time import sleep
from threading import Thread

from LBManager.utils.mialb_configs import guess_MiaLB_url

logger = getLogger(__name__)


class DockerUpdater(object):
    def __init__(self, mialb_url=None, sleep_duration=15):
        self.client = DockerClient(base_url='http://localhost:2376')
        self.mialb_url = mialb_url if mialb_url else guess_MiaLB_url()
        self.sleep_duration = sleep_duration
        self.members = {}

    def update_service(self, farm_id):
        service = how_do_i_get_service_name()
        if farm_id not in self.members:
            self.members[farm_id] = []
        last_members = self.members[farm_id]
        members = service.tasks()
        obsoletes = set(last_members) - set(members)
        for member in obsoletes:
            delete(url="{mialb_url}/MiaLB/Farms/{farm_id}/members/{member_id}".format(
                mialb_url=self.mialb_url,
                farm_id=farm_id,
                member_id=str(member['ID'])
            ))
        news = set(members) - set(last_members)
        for member in news:
            container_id = member['Status']['ContainerStatus']['ContainerID']
            net = service.attrs['Endpoint']['VirtualIPs'][0]['NetworkID']
            container_ip = \
                self.client.containers.get(container_id).attrs['NetworkSettings']['Networks'][net]['IPAddress']
            post(url="{mialb_url}/MiaLB/Farms/{farm_id}/members/{member_id}".format(
                mialb_url=self.mialb_url,
                farm_id=farm_id,
                member_id=str(member['ID'])),
                 headers={'Content-Type': 'text/plain'},
                 data=dumps({"member_id": str(member['ID']),
                             "ip": str(container_ip)}))
        self.members[farm_id] = members

    def update_farms(self):
        for farm in get(url="{mialb}/MiaLB/farms".format(mialb=self.mialb_url)):
            self.update_service(str(farm['id']))

    def background_update(self):
        Thread(target=self.update_service, args=[self])
        sleep(self.sleep_duration)