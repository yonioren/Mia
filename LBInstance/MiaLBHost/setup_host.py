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
from docker.types import IPAMConfig, IPAMPool

from LBHostConfig import get_config


def setup(**kwargs):
    dclient = docker_from_env()

    if 'conf-file' in kwargs:
        conffiles = kwargs['conf-file']
    else:
        conffiles = []
    configs = get_config(conffiles)

    poolargs = {}

    net_name = kwargs['docker_network'] if 'docker_network' in kwargs else configs['net_name']
    poolargs['subnet'] = kwargs['cidr'] if 'cidr' in kwargs else configs['subnet']
    poolargs['gateway'] = kwargs['gateway'] if 'gateway' in kwargs else configs['gateway']

    dclient.networks.create(name=net_name, driver="bridge", ipam=IPAMConfig(pool_configs=[IPAMPool(**poolargs)]))
