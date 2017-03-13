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

from docker import from_env as docker_from_env
from json import loads
from os import path
from requests import get, post, delete
from time import sleep
from unittest import TestCase


class TestLBInstance(TestCase):
    @classmethod
    def setUpClass(cls):
        client = docker_from_env()
        cls.image = client.images.build(path=path.join(path.dirname(__file__), '../../LBInstance'),
                                        tag="mialb:system-test")

    def setUp(self):
        self.client = docker_from_env()
        self.mia = self.client.containers.run(image="mialb:system-test", detach=True, environment={"MIA_PORT": "777"})
        sleep(0.2)
        self.mia = self.client.containers.get(self.mia.attrs['Id'])
        self.mia_ip = self.mia.attrs['NetworkSettings']['IPAddress']

    def tearDown(self):
        self.mia.remove(force=True)

    @classmethod
    def tearDownClass(cls):
        client = docker_from_env()
        client.images.remove(str(cls.image.id))

    def test_setup(self):
        res = get(url="http://{ip}:{port}/MiaLB/farms".format(ip=str(self.mia_ip), port="777"))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), [])

    def test_add_farm(self):
        post_res = post(url="http://{ip}:{port}/MiaLB/farms".format(ip=str(self.mia_ip), port="777"),
                        headers={'Content-Type': 'text/plain'}, data='{"port": "85", "name": "test"}')
        self.assertEqual(post_res.status_code, 200)
        farm_id = loads(post_res.json()['farm'])['farm_id']

        get_res = get(url="http://{ip}:{port}/MiaLB/farms/{farm}".format(ip=str(self.mia_ip),
                                                                         port="777", farm=farm_id))

        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['port'], 85)
