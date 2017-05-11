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
import OpenSSL

from docker import from_env as docker_from_env
from json import loads
from os import path
from requests import get, post, delete, ConnectionError
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
        sleep(0.5)
        self.mia = self.client.containers.get(self.mia.attrs['Id'])
        self.mia_ip = self.mia.attrs['NetworkSettings']['IPAddress']

        # wait for the farm to respond (up to 1 min)
        for i in xrange(0, 600):
            try:
                get(url="http://{ip}:{port}/MiaLB/farms".format(ip=str(self.mia_ip), port="777"))
                i = 601
            except ConnectionError:
                sleep(0.1)

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
        self.assertEqual(int(get_res.json()[u'port']), 85)
        self.assertEqual(get_res.json()[u'name'], u'test')

    @staticmethod
    def _init_cert_and_key():
        import OpenSSL

        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

        ca = OpenSSL.crypto.X509()
        ca.set_version(2)
        ca.set_serial_number(1)
        ca.get_subject().CN = "localhost.localdomain"
        ca.gmtime_adj_notBefore(0)
        ca.gmtime_adj_notAfter(24 * 60 * 60)
        ca.set_issuer(ca.get_subject())
        ca.set_pubkey(key)
        ca.add_extensions([
            OpenSSL.crypto.X509Extension("basicConstraints", True, "CA:TRUE, pathlen:0"),
            OpenSSL.crypto.X509Extension("keyUsage", True, "keyCertSign, cRLSign"),
            OpenSSL.crypto.X509Extension("subjectKeyIdentifier", False, "hash", subject=ca),
        ])
        ca.add_extensions([
            OpenSSL.crypto.X509Extension("authorityKeyIdentifier", False, "keyid:always", issuer=ca)
        ])
        ca.sign(key, "sha1")

        open("/tmp/tempcert.pem", "w").write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, ca))
        open("/tmp/tempkey.pem", "w").write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))

    def test_ssl_certs(self):
        self._init_cert_and_key()
        post_res = post(url="http://{ip}:{port}/MiaLB/farms".format(ip=str(self.mia_ip), port="777"),
                        headers={'Content-Type': 'application/json'},
                        json={'listen': [{'port': 4443, 'ip': '0.0.0.0', 'ssl': True}],
                              'name': "test", 'server_name': 'localhost.localdomain'})
        self.assertEqual(post_res.status_code, 200)
        farm_id = loads(post_res.json()['farm'])['farm_id']
        post_res = post(url="http://{ip}:{port}/MiaLB/farms/{farm_id}/certs".format(ip=str(self.mia_ip),
                                                                                    port="777",
                                                                                    farm_id=farm_id),
                        files={'cert': open('/tmp/tempcert.pem', 'r'),
                               'key': open('/tmp/tempkey.pem', 'r')})
        self.assertEqual(post_res.status_code, 200)
