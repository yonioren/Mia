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
from re import sub
from requests import get

from LBManager.utils.mialb_manager_config import logger
from LBManager.utils.mialb_useful import get_ip


class MiaLB(object):
    def __init__(self, url):
        self.url = url
        farms = get(url="{url}/MiaLB/farms".format(url=self.url))
        if farms.status_code != 200:
            logger.warning("failed to get farms from {url}. got HTTP {code}".format(url=self.url,
                                                                                    code=farms.status_code))
            logger.debug("HTTP response was {text}".format(text=farms.text))
        for farm in farms.json():
            self.farms.append(Farm(farm, self.url))

    def get_farm_by_name(self, name):
        for farm in self.farms:
            if farm.name == name:
                return farm


class Farm(object):
    def __init__(self, fid, url="", name=None, members=[]):
        self.fid = fid
        self.url = url
        self.name = name
        self.members = members
        self._get_params()

    def _get_params(self):
        if self.url == "":
            return None
        raw = get(url="{url}/MiaLB/farms/{farm}".format(url=self.url, farm=self.fid))
        self.name = raw.json()['name']
        for member in raw.json()['members']:
            get_ip(sub(r'^([a-zA-Z0-9]*://)?([a-zA-Z0-9\.]*)(:[0-9]+)(/.*)', r'\2', member['url']))