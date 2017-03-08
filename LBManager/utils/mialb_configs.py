#! /usr/bin/python
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
from logging import getLogger
from re import sub

logger = getLogger(__name__)

conf_file_order = ['/etc/Mia/mialb.conf', '~/.Mia/mialb.conf', '/software/Mia/LBManager/mialb.conf']
cp = ConfigParser()
cp.read(filenames=conf_file_order)

try:
    logfile = cp.get(section='default', option='logfile')
except Exception:
    logger.debug("couldn't get logfile name. falling back to mia default")
    logfile = str(os.path.dirname(os.path.abspath(__file__))) + '/../tests/unit/MiaLogs.log'
try:
    loglevel = cp.get(section='default', option='loglevel')
except Exception:
    logger.debug("couldn't get log level. falling back to mia default")
    loglevel = 'WARNNING'
try:
    host = cp.get(section='server', option='host')
    port = cp.get(section='server', option='port')
except Exception:
    logger.debug("couldn't get bind address. falling back to mia default")
    host = 'localhost'
    port = 6669


def guess_MiaLB_url():
    print("my pid is {}".format(str(os.getpid())))
    try:
        protocol, inq, outq, local_addr, foreign_addr, state, process = \
            os.popen("netstat -4 -tlnp | grep -e '\s{}/'".format(str(os.getpid()))).readlines()[0].split()
    except IndexError:
        protocol, inq, outq, local_addr, foreign_addr, state, process = \
            os.popen("netstat -4 -tlnp | grep -e ':{}\s'".format(port)).readlines()[0].split()
    # guess my public ip
    temp = os.popen("ip route show | grep default").read().split()
    public_device = temp[temp.index('dev') + 1]
    temp = os.popen("ip -4 addr show {} | grep inet".format(public_device)).read().split()
    public_address = temp[temp.index('inet') + 1].split('/')[0]
    local_addr = sub('(0.0.0.0|127.0.0.1)', public_address, local_addr)
    print("http://{}".format(local_addr))
    return "http://{}".format(local_addr)
