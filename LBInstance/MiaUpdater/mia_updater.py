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

from docker import APIClient
from docker.errors import APIError
from os import environ
from requests.exceptions import ReadTimeout
from socket import gethostbyname_ex

from MiaClient import MiaClient
from MiaUtils.mialb_useful import find_host_address

class MiaUpdater(object):
    def __init__(self, target_service=None):
        self.target_service = environ.get('MIALB_TARGET_SERVICE', target_service)
        self.external_network = environ.get('MIALB_EXTERNAL_NET', 'services')
        self.external_ip = environ.get('MIALB_EXTERNAL_IP', None)
        self.target_ports = self._init_target_ports()
        try:
            self._init_external_network()
        except (APIError, ReadTimeout):
            pass
        self.farm = self.create_farm()

    def _init_target_ports(self):
        if 'MIALB_EXTERNAL_PORTS' in environ:
            return environ.get('MIALB_EXTERNAL_PORTS').split(',')
        else:
            client = APIClient(base_url="{host}:2376".format(host=find_host_address()))
            return [t_port['PrivatePort'] for t_port in client.containers(
                filters={'id': [
                    client.tasks({'service': self.target_service})[0]['Status']['ContainerStatus']['ContainerID']]}
            )[0]['Ports']]

    def _init_external_network(self):
        client = APIClient(base_url="{host}:2376".format(host=find_host_address()))
        client.connect_container_to_network("{self}".format(self=environ.get('HOSTNAME')),
                                            self.external_network, ipv4_address=self.external_ip)

    def remove_farm(self):
        self.farm.remove_farm()
        exit(0)

    def update_farm_members(self):
        tasks = set(gethostbyname_ex("tasks.{service}".format(service=self.farm.name))[2])
        members = set(self.farm.members)
        for task in tasks - members:
            self.farm.add_member(ip=task)
        for task in members - tasks:
            self.farm.remove_member(ip=task)


    def create_farm(self):
        members = gethostbyname_ex("tasks.{service}".format(service=self.target_service))[2]
        mia = MiaClient(url="http://127.0.0.1:{port}".format(port="666"))
        farm = mia.add_farm(name=str(self.target_service), port=self.target_ports)
        for member in members:
            farm.add_member(ip=member)
        return farm

