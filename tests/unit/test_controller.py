import os
import unittest

import requests
from MiaLB.mialb_model import MiaLBModel
from nose.tools import *


class TestMatchMaker(unittest.TestCase):

    @staticmethod
    def setup_func():
        # change directory
        os.chdir("/etc/nginx/conf.d/")

        # remove all conf files
        f = os.popen("yes | rm *.conf")
        f.read().strip()

    def test_text_plain_json(self):
        model = MiaLBModel()
        farms_len_before = len(model.get_farms())

        requests.post('http://localhost:666/Emily/farms',
                      [('Content-Type', 'application/json')],
                      {'lb_method': 'round_robin'})

        model.load_farms()
        farms_len_after = len(model.get_farms())

        eq_(farms_len_before + 1, farms_len_after)

    def test_add_farm(self):
        model = MiaLBModel()
        farms_len_before = len(model.get_farms())

        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()
        farms_len_after = len(model.get_farms())

        eq_(farms_len_before + 1, farms_len_after)

    def test_get_farms(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        # add one farm
        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})

        # get farms
        requests.get('http://localhost:666/Emily/farms')

        model.load_farms()

        eq_(1, len(model.get_farms()))

    def test_unknown_method(self):
        # request with not allowed method
        res = requests.delete(url='http://localhost:666/Emily/farms',
                              data="{\"lb_method\": \"round_robin\"}",
                              headers={'Content-Type': 'text/plain'})

        # 405-method not allowed
        eq_(res.status_code, 405)

    def test_get_farm_by_id(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()

        res = model.get_farms().items()[0]
        farm_id = res[1].farm_id
        req_res = requests.get('http://localhost:666/Emily/farms/' + farm_id)

        eq_(req_res.status_code, 200)

    def test_get_farm_with_not_exist_id(self):
        req_res = requests.get('http://localhost:666/Emily/farms/123')

        # 404-farm not found
        eq_(req_res.status_code, 404)

    def test_delete_farm_by_id(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})

        model.load_farms()

        res = model.get_farms().items()[0]
        farm_id = res[1].farm_id
        req_res = requests.delete('http://localhost:666/Emily/farms/' + farm_id)

        # 200-deleted
        eq_(req_res.status_code, 200)

    def test_update_farm_by_id(self):
        port = str(8080)
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})

        model.load_farms()

        res = model.get_farms().items()[0]
        farm_id = res[1].farm_id
        requests.put('http://localhost:666/Emily/farms/' + farm_id,
                     data="{\"port\": "+port+"}",
                     headers={'Content-Type': 'text/plain'})

        eq_(model.get_farm(farm_id).port, port)

    def test_create_farm_member(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()

        res = model.get_farms().items()[0][1]
        farm_id = res.farm_id
        farm_members_before = res.members

        # create farm member
        requests.post(url='http://localhost:666/Emily/farms/'+str(farm_id)+'/members',
                      data="{\"url\": \"217684fa-b9c8-406a-b338-5387b3d4f371\","
                           " \"weight\": \"3\"}", headers={'Content-Type': 'text/plain'})
        farm_members_after = model.get_farm(farm_id).members

        eq_(len(farm_members_before) + 1, len(farm_members_after))

    def test_create_more_then_one_member(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()

        res = model.get_farms().items()[0][1]
        farm_id = res.farm_id
        farm_members_before = res.members

        # create farm member
        requests.post(url='http://localhost:666/Emily/farms/' + str(farm_id) + '/members',
                      data="{\"url\": \"217684fa-b9c8-406a-b338-5387b3d4f371\","
                           " \"weight\": \"3\"}", headers={'Content-Type': 'text/plain'})
        requests.post(url='http://localhost:666/Emily/farms/' + str(farm_id) + '/members',
                      data="{\"url\": \"217684fa-b9c8-406a-b338-5387b3d4f372\","
                           " \"weight\": \"3\"}", headers={'Content-Type': 'text/plain'})

        farm_members_after = model.get_farm(farm_id).members

        eq_(len(farm_members_before) + 2, len(farm_members_after))

    def test_get_members(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        # create farm
        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()

        res = model.get_farms().items()[0][1]
        farm_id = res.farm_id

        # create farm member
        requests.post(url='http://localhost:666/Emily/farms/' + str(farm_id) + '/members',
                      data="{\"url\": \"217684fa-b9c8-406a-b338-5387b3d4f371\","
                           " \"weight\": \"3\"}", headers={'Content-Type': 'text/plain'})

        req_res = requests.get(url='http://localhost:666/Emily/farms/' + str(farm_id) + '/members')

        eq_(req_res.status_code, 200)

    def test_get_farm_member(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        # create farm
        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()

        res = model.get_farms().items()[0][1]
        farm_id = str(res.farm_id)

        # create farm member
        requests.post(url='http://localhost:666/Emily/farms/' + farm_id + '/members',
                      data="{\"url\": \"217684fa-b9c8-406a-b338-5387b3d4f371\","
                           " \"weight\": \"3\"}", headers={'Content-Type': 'text/plain'})

        member_url = str(model.get_farm(farm_id).members.values()[0].url)

        req_res = requests.get(url='http://localhost:666/Emily/farms/' + farm_id + '/members/' + member_url)

        eq_(req_res.status_code, 200)

    def test_delete_farm_member(self):
        model = MiaLBModel()

        # remove all conf files
        self.setup_func()

        # create farm
        requests.post(url='http://localhost:666/Emily/farms',
                      data="{\"lb_method\": \"round_robin\"}",
                      headers={'Content-Type': 'text/plain'})
        model.load_farms()

        res = model.get_farms().items()[0][1]
        farm_id = str(res.farm_id)

        # create farm member
        requests.post(url='http://localhost:666/Emily/farms/' + farm_id + '/members',
                      data="{\"url\": \"217684fa-b9c8-406a-b338-5387b3d4f371\","
                           " \"weight\": \"3\"}", headers={'Content-Type': 'text/plain'})

        member_url = str(model.get_farm(farm_id).members.values()[0].url)

        req_res = requests.delete(url='http://localhost:666/Emily/farms/' + farm_id + '/members/' + member_url)

        eq_(req_res.status_code, 200)
