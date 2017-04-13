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

from configparser import ConfigParser
from logging import getLogger, basicConfig


logger = getLogger(__name__)

conf_file_order = ['/etc/Mia/mialb.conf',
                   '{home}/.Mia/mialb.conf'.format(home=os.path.expanduser('~')),
                   '/software/Mia/LBManager/mialb.conf']
cp = ConfigParser()
cp.read(filenames=conf_file_order)


def read_with_default(section, option, default):
    try:
        return cp.get(section=section, option=option)
    except Exception:
        logger.info("couldn't get {section}:{option}, falling back to default {default}".format(section=section,
                                                                                                option=option,
                                                                                                default=default))
        return default

try:
    logfile = cp.get(section='default', option='logfile')
except Exception:
    logger.debug("couldn't get logfile name. falling back to mia default")
    logfile = str(os.path.dirname(os.path.abspath(__file__))) + '/../tests/unit/MiaLogs.log'
try:
    loglevel = cp.get(section='default', option='loglevel')
except Exception:
    logger.debug("couldn't get log level. falling back to mia default")
    loglevel = 'WARNING'

getLogger(__name__)
basicConfig(filename=logfile,
            format='[%(asctime)s] [%(levelname)s] %(module)s - %(funcName)s:   %(message)s',
            level=loglevel,
            datefmt='%m/%d/%Y %I:%M:%S %p')

host = read_with_default(section='server', option='host', default='localhost')
port = read_with_default(section='server', option='port', default=6669)
swarm_manamger = read_with_default(section='docker', option='manager_url', default="http://localhost:2376")
lbimage = read_with_default(section='docker', option='lb_image', default="mialb:latest")
service_network = read_with_default(section='docker', option='docker_network', default="services")
service_cidr = read_with_default(section='docker', option='cidr', default="services")
service_create_timeout = read_with_default(section='docker', option='service_create_timeout', default="300")
