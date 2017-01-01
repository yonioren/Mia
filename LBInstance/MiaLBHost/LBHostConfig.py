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
from configparser import ConfigParser
from re import sub


def get_config(configfiles=[]):
    configfiles += ['/etc/Mia/mialb.conf', '~/.Mia/mialb.conf', '/software/Mia/LB/mialb.conf']
    cp = ConfigParser()
    cp.read(filenames=configfiles)

    net_name = cp.get(section='services', option='docker_network') \
        if cp.has_option(section='services', option='docker_network') else 'services'
    subnet = cp.get(section='services', option='cidr') \
        if cp.has_option(section='services', option='cidr') else '192.168.1.0/24'
    gateway = cp.get(section='services', option='gateway') \
        if cp.has_option(section='services', option='gateway') else sub('\.[0-9]{1,3}/[0-9]{1,2}$', '.254', subnet)

    return {'net_name': net_name, 'subnet': subnet, 'gateway': gateway}
