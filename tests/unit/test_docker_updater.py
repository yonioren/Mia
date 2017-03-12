from docker import from_env as docker_from_env
from json import loads
from requests import get, post, delete
from unittest import TestCase

from LBManager.MiaLBUpdater.DockerUpdater import DockerUpdater


class TestDockerUpdater(TestCase):

    def setUp(self):
        self.mialb_url="http://localhost:666"
        self.docker_updater = DockerUpdater(mialb_url=self.mialb_url, sleep_duration=15)
        self.docker_client = docker_from_env()
        self._clean_docker()
        self._clean_mia()
        try:
            self.docker_client.networks.create(name="shit-net", driver="overlay")

    def tearDown(self):
        self._clean_docker()
        self._clean_mia()

    def test_get_services_identical(self):
        pass

    def _clean_docker(self):
        for service in self.docker_client.services.list():
            service.remove()
        for container in self.docker_client.containers.list():
            container.remove()

    def _clean_mia(self):
        for farm in get(url="{mialb_url}/MiaLB/farms".format(mialb_url=self.mialb_url)):
            delete(url="{mialb_url}/MiaLB/farms/{farm}".format(mialb_url=self.mialb_url, farm=farm))
