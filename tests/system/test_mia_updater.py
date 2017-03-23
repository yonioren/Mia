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
from docker.errors import APIError
from docker.types.networks import IPAMConfig, IPAMPool
from logging import getLogger
from os import path
from requests import get
from time import sleep
from unittest import TestCase

logger = getLogger(__name__)


class TestMiaUpdater(TestCase):
    @classmethod
    def setUpClass(cls):
        client = docker_from_env()
        cls.image = client.build(path=path.join(path.dirname(__file__), '../../LBInstance'),
                                        tag="mialb:test")

    @classmethod
    def tearDownClass(cls):
        client = docker_from_env()
        client.images.remove(str(cls.image.id))

    def _clean_docker(self):
        for service in self.docker_client.services():
            self.docker_client.remove_service(resource_id=service['ID'])
        for container in self.docker_client.containers():
            try:
                self.docker_client.kill(container=container)
                self.docker_client.remove_container(container=container)
            except APIError:
                pass

    def setUp(self):
        self.docker_client = docker_from_env()
        self._clean_docker()
        try:
            if self.docker_client.networks(names=["system-test-services"]):
                self.service_net = self.docker_client.networks(names=["system-test-services"])
            else:
                conf = IPAMConfig(driver='default', pool_configs=[IPAMPool(subnet='172.168.52.0/24',
                                                                           gateway='172.168.52.254')])
                self.external_net = self.docker_client.create_network(name="system-test-services", driver="bridge",
                                                                     ipam=conf)
        except APIError:
            logger.warning("couldn't create system-test-services")
        try:
            if self.docker_client.networks(names=["unit-test-services-net"]):
                self.service_net = self.docker_client.networks(names=["unit-test-services-net"])
            else:
                self.service_net = self.service_net = self.docker_client.create_network(name="unit-test-services-net",
                                                                                        driver="overlay")
        except APIError:
            logger.warning("unit-test-services-net")


    def tearDown(self):
        self._clean_docker()

    def test_setup(self):
        tblb = self.docker_client.create_service(task_template={"ContainerSpec": {"Image": "nginx"}},
                                                 labels={'LBMe': 'yes'},
                                                 networks=[{"Target": "unit-test-services-net"}],
                                                 name="system-test-lbed-services",
                                                 mode={'Replicated': {'Replicas': 2}})
        sleep(1)
        mia = self.docker_client.create_service(task_template={"ContainerSpec": {"Image": "mialb:system-test",
                                                                          "Env": ['MIA_PORT=666',
                                                                                  'MIA_HOST=0.0.0.0',
                                                                                  'MIALB_TARGET_SERVICE=system-test-lbed-services',
                                                                                  'MIALB_EXTERNAL_NET=system-test-services',
                                                                                  'MIALB_EXTERNAL_IP=172.168.52.101']},
                                                               "RestartPolicy": {"Condition": "any"}},
                                                name=tblb['ID'],
                                                labels={'MiaLB': str(tblb['ID'])},
                                                networks=[{"Target": "unit-test-services-net"}])
        sleep(1)
        self.assertEqual(get(url="http://172.168.52.101:666/MiaLB/farms").status_code, 200)
