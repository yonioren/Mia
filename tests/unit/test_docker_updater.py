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
from docker.errors import APIError, NotFound
from json import loads
from os import path
from requests import get, post, delete
from time import sleep
from unittest import TestCase

from LBManager.MiaLBUpdater.DockerUpdater import DockerUpdater
from LBManager.utils.mialb_manager_config import logger


class TestDockerUpdater(TestCase):
    @classmethod
    def setUpClass(cls):
        client = docker_from_env()
        cls.image = client.images.build(path=path.join(path.dirname(__file__), '../../LBInstance'),
                                        tag="mialb:test")

    def setUp(self):
        self.docker_updater = DockerUpdater()
        self.docker_client = docker_from_env()
        self._clean_docker()
        try:
            self.service_net = self.docker_client.networks.get("unit-test-services-net")
        except NotFound:
            self.service_net = self.docker_client.networks.create(name="unit-test-services-net", driver="overlay")
        except APIError:
            logger.warning("couldn't create unit-test-services-net")

    def tearDown(self):
        self._clean_docker()

    def test_create_farm(self):
        tblb = self.docker_client.services.create(image="nginx", labels={'LBMe': 'yes'},
                                                  networks=["unit-test-services-net"])
        sleep(1)
        miasvc, url, farm_id = self.docker_updater.create_farm(tblb.id)
        self.assertIsNotNone(miasvc)

        # get_res = get()

    def _clean_docker(self):
        for service in self.docker_client.services.list():
            service.remove()
        for container in self.docker_client.containers.list():
            try:
                container.kill()
                container.remove()
            except APIError:
                pass
