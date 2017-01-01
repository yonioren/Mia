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
from docker import from_env as docker_from_env
from os import symlink, system

from LBHostConfig import get_config


class LBContainer(object):
    def __init__(self, container_id):
        """ initialize container instance and prepare host """
        self.dclient = docker_from_env()
        # convert name or short id to full id
        self.container_id = self.dclient.containers.get(container_id=container_id).id
        # set up netns, for future ues
        netns = self.dclient.containers.get(container_id=container_id).attrs['NetworkSettings']['SandboxKey']
        self.netns = netns.split('/')[-1]
        symlink(netns, '/var/run/netns/{}'.format(self.netns))

    def add_interface(self, **kwargs):
        configs = get_config()

        # connect container to network
        if 'network' in kwargs:
            network_id = self.dclient.networks.get(kwargs['network']).id
        else:
            network_id = self.dclient.networks.get(configs['network']).id
        self.dclient.networks.get(network_id=network_id).connect(self.container_id)

        # set up ip address
        subnet_mask = self.dclient.networks.get(network_id).attrs['IPAM']['Config'][0]['Subnet'].split('/')[1]
        if 'ip' in kwargs:
            ip = "{}/{}".format(kwargs['ip'], subnet_mask)
            system("ip netns exec {netns} ip addr add {ip} dev eth1".format(netns=self.netns, ip=ip))

        if 'default-network' not in kwargs or kwargs['default-network'] == True:
            gateway = kwargs['gateway'] if 'gateway' in kwargs else configs['gateway']
            system("ip netns exec {netns} ip route change default via {gateway}".format(netns=self.netns,
                                                                                        gateway=gateway))
