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
from json import loads
from re import sub

from requests import get, post, delete

from suspected_obsoletes.LBManager.utils import get_ip
from suspected_obsoletes.LBManager.utils import logger


class MiaLB(object):
    def __init__(self, url):
        self.farms = []
        self.url = url
        farms = get(url="{url}/MiaLB/farms".format(url=self.url))
        if farms.status_code != 200:
            logger.warning("failed to get farms from {url}. got HTTP {code}".format(url=self.url,
                                                                                    code=farms.status_code))
            logger.debug("HTTP response was {text}".format(text=farms.text))
        for farm in farms.json():
            self.farms.append(Farm(farm, self.url))

    def add_farm(self, name, **kwargs):
        if set(kwargs.keys()) - {'name', 'location', 'ip', 'port', 'lb_method', 'protocol', 'members'}:
            logger.error("unknown keyword(s): {kw}".format(
                kw=str(set(kwargs.keys()) - {'name', 'location', 'ip', 'port', 'lb_method', 'protocol', 'members'})
            ))
            raise KeyError("got unknown parameter")

        kwargs['name'] = name
        res = post(url="{url}/MiaLB/farms".format(url=self.url),
                   headers={'Content-Type': 'application/json'},
                   json=kwargs)
        if 200 <= res.status_code < 300:
            fid = loads(res.json()['farm'])['farm_id']
            self.farms.append(Farm(fid=fid, url=self.url, name=name))
            return self.farms[-1]
        else:
            logger.warning("failed to create farm {name}, got HTTP {code}".format(name=name, code=res.status_code))
            logger.debug("full response was {}".format(res.text))
            raise IndexError("failed to create farm {}".format(name))

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

    def add_member(self, ip=None, url=None, port=None):
        url = self._get_url(ip=ip, url=url, port=port)
        res = post(url="{mia_url}/MiaLB/farms/{farm}/members".format(mia_url=self.url, farm=self.fid),
                   headers={'Content-Type': 'application/json'},
                   json={'url': url})
        if 200 <= res.status_code < 300:
            return True
        else:
            logger.warning("failed to add member {member} to farm {farm}, "
                           "got HTTP {code}".format(member=url, farm=self.fid, code=res.status_code))
            logger.debug("full response was {}".format(res.text))
            raise IndexError("failed to member {member} to farm {farm}".format(member=url, farm=self.fid,))

    def remove_member(self, ip=None, url=None, port=None):
        member_url = self._get_url(ip=ip, url=url, port=port)
        get_res = get("{mia_url}/MiaLB/farms/{farm}/members".format(mia_url=self.url, farm=self.fid))
        if 200 <= get_res.status_code < 300:
            for url in get_res.json():
                if url == '"{member_url}"'.format(member_url=member_url):
                    delete("{mia_url}/MiaLB/farms/{farm}/members/{member}".format(
                        mia_url=self.url,
                        farm=self.fid,
                        member=member_url
                    ))
                    return True
        return False

    def remove_farm(self):
        del_res = delete("{mia_url}/MiaLB/farms/{farm}".format(mia_url=self.url, farm=self.fid))
        if 200 <= del_res.status_code < 300:
            return True
        return False

    @staticmethod
    def _get_url(ip=None, url=None, port=None):
        if not ip and not url:
            raise AttributeError("must accept either ip or url")
        elif not url:
            if not port:
                url = ip
            else:
                url = "{ip}:{port}".format(ip=ip, port=port)
        return url

    def _get_params(self):
        if self.url == "":
            return None
        raw = get(url="{url}/MiaLB/farms/{farm}".format(url=self.url, farm=self.fid))
        self.name = raw.json()['name']
        ###   DEBUG   ###
        members = raw.json()['members']
        ### END DEBUG ###
        for member in raw.json()['members'].values():
            self.members.append(get_ip(sub(r'^([a-zA-Z0-9]*://)?([a-zA-Z0-9\.]*)(:[0-9]+)(/.*)', r'\2', member['url'])))
