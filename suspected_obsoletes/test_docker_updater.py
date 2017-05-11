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

from os import path
from time import sleep
from unittest import TestCase

from LBManager.MiaLBUpdater.DockerUpdater import DockerUpdater
from LBManager.MiaLBUpdater.MiaLB import Farm
from docker import from_env as docker_from_env
from docker.errors import APIError, NotFound
from requests import get

from suspected_obsoletes.LBManager.utils import logger


class TestDockerUpdater(TestCase):
    @classmethod
    def setUpClass(cls):
        client = docker_from_env()
        cls.image = client.build(path=path.join(path.dirname(__file__), '../../LBInstance'),
                                        tag="mialb:test")

    def setUp(self):
        self.docker_updater = DockerUpdater()
        self.docker_client = docker_from_env()
        self._clean_docker()
        try:
            self.service_net = self.docker_client.networks(names=["unit-test-services-net"])
        except NotFound:
            self.service_net = self.docker_client.create_network(name="unit-test-services-net", driver="overlay")
        except APIError:
            logger.warning("couldn't create unit-test-services-net")

    def tearDown(self):
        self._clean_docker()

    def _clean_docker(self):
        for service in self.docker_client.services():
            self.docker_client.remove_service(resource_id=service['ID'])
        for container in self.docker_client.containers():
            try:
                self.docker_client.kill(container=container)
                self.docker_client.remove_container(container=container)
            except APIError:
                pass

    def _initialize_farm_and_lb(self):

        tblb = self.docker_client.create_service(task_template={"ContainerSpec": {"Image": "nginx"}},
                                                 labels={'LBMe': 'yes'},
                                                 networks=[{"Target": "unit-test-services-net"}],
                                                 name="unit-test-lbed-services",
                                                 mode={'Replicated': {'Replicas': 2}})
        sleep(1)
        tblb = self.docker_client.services(filters={'id': tblb['ID']})[0]
        miasvc, url, farm_id = self.docker_updater.create_farm(tblb['ID'])
        return tblb, miasvc, url, farm_id

    def test_create_farm(self):
        tblb, miasvc, url, farm_id = self._initialize_farm_and_lb()
        self.assertIsNotNone(miasvc)

        get_res = get(url="{url}/MiaLB/farms/{fid}".format(url=url, fid=farm_id))
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['members'].__len__(), 2)

    def test_update_farm_scale_up(self):
        # initialize farm
        tblb, miasvc, url, farm_id = self._initialize_farm_and_lb()

        # scale up farm service
        self.docker_client.update_service(tblb['ID'],
                                          version=self.docker_client.inspect_service(tblb['ID'])['Version']['Index'],
                                          task_template={"ContainerSpec": {"Image": "nginx"}},
                                          networks=[{"Target": "unit-test-services-net"}],
                                          name="unit-test-lbed-services",
                                          labels={'LBMe': 'yes'},
                                          mode={'Replicated': {'Replicas': 3}})
        sleep(1)
        self.docker_updater.update_farm_members(farm=Farm(fid=farm_id, url=url))

        # assert mialb was updated
        get_res = get(url="{url}/MiaLB/farms/{fid}".format(url=url, fid=farm_id))
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['members'].__len__(), 3)

    def test_update_farm_scale_down(self):
        # initialize farm
        tblb, miasvc, url, farm_id = self._initialize_farm_and_lb()

        # scale down farm service
        self.docker_client.update_service(tblb['ID'],
                                          version=self.docker_client.inspect_service(tblb['ID'])['Version']['Index'],
                                          task_template={"ContainerSpec": {"Image": "nginx"}},
                                          networks=[{"Target": "unit-test-services-net"}],
                                          name="unit-test-lbed-services",
                                          labels={'LBMe': 'yes'},
                                          mode={'Replicated': {'Replicas': 1}})
        sleep(1)
        self.docker_updater.update_farm_members(farm=Farm(fid=farm_id, url=url))

        # assert mialb was updated
        get_res = get(url="{url}/MiaLB/farms/{fid}".format(url=url, fid=farm_id))
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['members'].__len__(), 1)

    def test_remove_farm(self):
        tblb, miasvc, url, farm_id = self._initialize_farm_and_lb()
        self.docker_updater.remove_farm(farm=Farm(fid=farm_id, url=url))

        tblb = self.docker_client.services(filters={'id': tblb['ID']})
        self.assertEqual(tblb.__len__(), 0)

    def test_docker_update_single_lbed(self):
        tblb = self.docker_client.create_service(task_template={"ContainerSpec": {"Image": "nginx"}},
                                                 labels={'LBMe': 'yes'},
                                                 networks=[{"Target": "unit-test-services-net"}],
                                                 name="unit-test-lbed-services",
                                                 mode={'Replicated': {'Replicas': 2}})
        sleep(1)
        tblb = self.docker_client.services(filters={'id': tblb['ID']})[0]

        self.docker_updater.update()
        miasvc = self.docker_client.services(filters={'name': tblb['ID']})
        self.assertEqual(miasvc.__len__(), 1)
