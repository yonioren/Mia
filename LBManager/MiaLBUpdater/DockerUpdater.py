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
from itertools import chain
from json import dumps
from logging import getLogger
from re import sub
from threading import Thread
from time import sleep

from docker import DockerClient
from requests import get, post, delete

from LBInstance.MiaLB.mialb_configs import guess_MiaLB_url
from LBManager.utils.mialb_useful import get_ip

logger = getLogger(__name__)


class DockerUpdater(object):
    def __init__(self, mialb_url=None, sleep_duration=15):
        self.client = DockerClient(base_url='http://localhost:2376')
        self.mialb_url = mialb_url if mialb_url else guess_MiaLB_url()
        self.sleep_duration = sleep_duration
        self.members = {}

    def get_services(self):
        docker_services = []
        mia_services = get(url="{mialb_url}/MiaLB/farms".format(mialb_url=self.mialb_url))
        for service in self.client.services.list():
            docker_services.append(service.id)
        return set(docker_services).intersection(mia_services)

    def compare_service(self, service_id):
        docker_tasks = self._get_service_tasks(service=service_id)
        mia_members = self._get_miafarm_members(farm=service_id)

        for task, addresses in docker_tasks['forward']:
            # if there's a member who already existed
            if set(addresses).intersection(mia_members['reverse'].keys()):
                # pop it from mia
                address = set(addresses).intersection(mia_members['reverse'].keys())
                member = mia_members['reverse'].pop(address)
                mia_members['forward'].pop(member)
                # and from docker
                for address in docker_tasks.pop(task):
                    docker_tasks['reverse'].pop(address)
            # else, its a new member
            else:
                # figure out what's the port
                post(url="{mialb_url}/MiaLB/Farms/{farm_id}/members/{member_id}".format(
                    mialb_url=self.mialb_url,
                    farm_id=service_id,
                    member_id=str(task)),
                    headers={'Content-Type': 'text/plain'},
                    data=dumps({"member_id": str(task),
                                "ip": str(addresses[0])}))
        # what ever left are obsolete members, and we'll delete them
        for member in mia_members['forward']
            delete(url="{mialb_url}/MiaLB/Farms/{farm_id}/members/{member_id}".format(
                mialb_url=self.mialb_url,
                farm_id=service_id,
                member_id=str(member)
            ))


        docker_tasks = set(docker_tasks)
        mia_members = set(mia_members)
        return {'added': docker_tasks - mia_members,
                'removed': mia_members - docker_tasks}

    def _get_service_tasks(self, service):
        docker_service = self.client.services.get(service)
        forward = {}
        reverse = {}
        for task in docker_service.tasks():
            for container_id in task['Status']['ContainerStatus']['ContainerID']:
                forward[container_id] = []
                container = self.client.containers.get(container_id=container_id)
                net = docker_service.attrs['Endpoint']['VirtualIPs'][0]['NetworkID']
                for net in task['NetworksAttachments']:
                    net_id = net['Network']['ID']
                    try:
                        forward[task['ID']].append(container.attrs['NetworkSettings']['Networks'][net]['IPAddress'])
                    except IndexError:
                        pass
                if not forward[task['ID']]:
                    forward[task['ID']].append(container.attrs['NetworkSettings']['Networks'][0]['IPAddress'])
                forward[container_id] = list(chain.from_iterable(forward[container_id]))
                for address in forward[task[container_id]]:
                    reverse[address] = container_id
        return {"forward": forward, "reverse": reverse}

    def _get_miafarm_members(self, farm):
        mia_service = get(url="{mialb_url}/MiaLB/farms/{farm}".format(mialb_url=self.mialb_url, farm=farm))
        forward = {}
        reverse = {}
        for member, data in mia_service['members'].items():
            member_ip = get_ip(sub(r'^([a-zA-Z0-9]*://)?([a-zA-Z0-9\.]*)(:[0-9]+)(/.*)', r'\2', data['url']))
            forward[member] = member_ip
            reverse[member_ip] = member
        return {"forward": forward, "reverse": reverse}

    def background_update(self):
        Thread(target=self.update_service, args=[self])
        sleep(self.sleep_duration)