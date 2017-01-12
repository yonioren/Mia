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

logger = getLogger(__name__)

conf_file_order = ['/etc/Mia/mialb.conf', '~/.Mia/mialb.conf', '/software/Mia/LB/mialb.conf']
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
