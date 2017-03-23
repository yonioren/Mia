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

from docker import Client
from os import environ
from socket import gethostbyname_ex

from MiaLB import MiaLB


class MiaUpdater(object):
    def __init__(self, target_service=None):
        self.target_service = environ.get('MIALB_TARGET_SERVICE', target_service)
        self.external_network = environ.get('MIALB_EXTERNAL_NET', 'services')
        self.external_ip = environ.get('MIALB_EXTERNAL_IP', None)
        self.target_ports = self._init_target_ports()
        self._init_external_network()
        self.farm = self.create_farm(target_service)

    def _init_target_ports(self):
        if 'MIALB_EXTERNAL_PORTS' in environ:
            return environ.get('MIALB_EXTERNAL_PORTS').split(',')
        else:
            client = Client(base_url="172.18.0.1:2376")
            return [t_port['PrivatePort'] for t_port in client.containers(
                filters={'id': [
                    client.tasks({'service': self.target_service})[0]['Status']['ContainerStatus']['ContainerID']]}
            )[0]['Ports']]

    def _init_external_network(self):
        client = Client(base_url="172.18.0.1:2376")
        client.connect_container_to_network("{self}", self.external_network, ipv4_address=self.external_ip)

    """
    def get_services(self):
        lbed_services = []
        mia_services = []
        for service in self.client.services():
            if ('Labels' in service['Spec']
                    and 'MiaLB' in service['Spec']['Labels']):
                mia_services.append(service['ID'])
            if ('Labels' in service['Spec']
                    and 'LBMe' in service['Spec']['Labels']
                    and str(service['Spec']['Labels']['LBMe']).lower() not in ['no', 'n', 'false']):
                lbed_services.append(service['ID'])
        return lbed_services, mia_services

    def update(self):
        lbed_services, mia_services = self.get_services()
        services = {'existing': [], 'new': [], 'obsoletes': {'lbs': [], 'farms': []}}
        for mia in mia_services:
            flag = False
            for farm in mia:
                if farm.name in lbed_services:
                    services['existing'].append(farm)
                    lbed_services.remove(farm.name)
                    flag = True
                else:
                    services['obsoletes']['farms'].append(farm)
            if not flag:
                services['obsoletes']['lbs'].append(mia)
        for service in lbed_services:
            services['new'].append(service)
            Thread(target=self.create_farm, kwargs={'service_id': service}).start()
    """

    def remove_farm(self, farm):
        farm.remove_farm()
        exit(0)

    def update_farm_members(self, farm):
        tasks = gethostbyname_ex("tasks.{service}".format(farm.name))
        members = farm.members
        for task in tasks:
            if task in members:
                members.remove(task)
            else:
                farm.add_member(ip=task)
        for member in members:
            farm.remove_member(ip=member)

    def create_farm(self):
        members = gethostbyname_ex("tasks.{service}".format(service=self.target_service))
        mia = MiaLB(url="http://127.0.0.1:{port}".format(port="666"))
        farm = mia.add_farm(name=str(self.target_service), port=self.target_ports)
        for member in members:
            farm.add_member(ip=member)
        return farm

