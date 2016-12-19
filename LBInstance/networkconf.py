#! /usr/bin/python2.7
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
from ipaddress import IPv4Interface
from os import environ


class DInterface(IPv4Interface):
    def __init__(self, *args, **kwargs):
        if args:
            address = args[0]
            self.gateway = args[1] if args.__len__() > 1 else None
        elif kwargs:
            address = kwargs['address'] if 'address' in kwargs else None
            self.gateway = kwargs['gateway'] if 'gateway' in kwargs else None
        super(DInterface, self).__init__(address)


class MiaDockerInstance(object):
    """ represent this host

    attributes:
    - internal interface
    - public interface
    """
    def __init__(self):
        self.internalIface = IPv4Interface()
        self.publicIface = IPv4Interface()

    @staticmethod
    def get_external_ip(self):
        with open("/etc/nginx/conf.d/{}.conf".format(environ['FARMID'])) as conffile:
            configs = conffile.read().split()
            external_uri = configs[configs.index('listen') + 1]
            conffile.close()
        return external_uri.split(':')[0]

def set_external_interface():
    pass

def set_routes():
    pass