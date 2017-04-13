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
from os import popen
from re import sub
from threading import Thread
from time import sleep

from LBManager.MiaLBUpdater.MiaLB import MiaLB
from docker import Client

from suspected_obsoletes.LBManager.utils import logger, swarm_manamger, lbimage, service_create_timeout


class DockerUpdater(object):
    def __init__(self):
        self.client = Client(base_url=swarm_manamger)

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

    def remove_farm(self, farm):
        name = farm.name
        farm.remove_farm()
        if self.client.services(filters={'name': [name]}).__len__() == 1:
            self.client.remove_service(name)

    def update_farm_members(self, farm):
        docker_service = self.client.services(filters={'id': [farm.name]})[0]
        members = farm.members
        for task in self.client.tasks({'service': docker_service['ID']}):
            ip = self.wait_for_ip(task['Status']['ContainerStatus']['ContainerID'])
            if ip in members:
                members.remove(ip)
            else:
                farm.add_member(ip=ip)
        for member in members:
            farm.remove_member(ip=member)

    def create_farm(self, service_id):
        members = self.client.containers(filters={'id': [task['Status']['ContainerStatus']['ContainerID']
                                                         for task in self.client.tasks({'service': service_id})]})
        member_networks = [net['NetworkID']
                           for net in list(chain(*[container['NetworkSettings']['Networks'].values()
                                                   for container in members]))]
        svc = self.client.create_service(task_template={"ContainerSpec": {"Image": lbimage,
                                                                          "Env": ['MIA_PORT=666',
                                                                                  'MIA_HOST=0.0.0.0']},
                                                        "RestartPolicy": {"Condition": "any"}},
                                         name=service_id,
                                         labels={'MiaLB': str(service_id)},
                                         networks=[{"Target": member_network} for member_network in member_networks])

        # sleep because it takes time for docker to allocate ip
        if not self.wait_for_container(svc):
            logger.error("mialb service creation failed!")
            raise IOError("mialb service creation failed!")
        svc = self.client.services(filters={'id': svc['ID']})[0]

        ip = self.wait_for_ip(self.client.tasks({'service': svc['ID']})[0]['Status']['ContainerStatus']['ContainerID'])
        if not ip:
            logger.error("mialb service creation failed!")
            raise IOError("mialb service creation failed!")
        temp = self.client.containers(
            filters={'id': [self.client.tasks({'service': svc['ID']})[0]['Status']['ContainerStatus']['ContainerID']]}
        )[0]
        target_ports = [t_port['PrivatePort'] for t_port in temp['Ports']]
        mia = MiaLB(url="http://{ip}:{port}".format(ip=ip, port="666"))
        farm = mia.add_farm(name=str(service_id), port=target_ports)
        for member in members:
            farm.add_member(ip=self.wait_for_ip(member['Id']))
        return svc, "http://{ip}:{port}".format(ip=ip, port="666"), farm.fid

    def wait_for_container(self, svc):
        flag = True
        i = 0
        while flag and i < service_create_timeout:
            svc = self.client.services(filters={'id': svc['ID']})[0]
            x = self.client.tasks({'service': svc['ID']})
            if self.client.tasks({'service': svc['ID']})[0]['Status']['State'].lower() in ['running', 'rejected']:
                flag = False
            else:
                if i < 3:
                    i += 0.1
                    sleep(0.1)
                elif i < 15:
                    i += 1
                    sleep(1)
                else:
                    i += 10
                    sleep(i)
        return not flag

    def wait_for_ip(self, cid):
        flag = True
        i = 0
        while flag and i < service_create_timeout:
            for line in popen("docker exec -i {cid} ip route show".format(cid=cid)).readlines():
                l = line.split()
                if l[0] == '172.18.0.0/16':
                    dev = l[l.index('dev') + 1]
            try:
                l = popen("docker exec -i {cid} ip addr show {dev}".format(cid=cid, dev=dev)).read().split()
                ip = l[l.index("inet") + 1]
                if ip:
                    return sub(r'/[0-9]*', '', ip)
            except (IndexError, UnboundLocalError):
                if i < 3:
                    i += 0.1
                    sleep(0.1)
                elif i < 15:
                    i += 1
                    sleep(1)
                else:
                    i += 10
                    sleep(i)
        return False
