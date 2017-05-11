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

import json

from flask import request
from flask.helpers import make_response
from logging import getLogger

from mialb_entities import logger
from mialb_bl import MiaLBBL

logger = getLogger(__name__)


class MiaLBView:
    def __init__(self, model=None):
        if model is None:
            self.model = MiaLBBL()
        else:
            self.model = model

    def farms_api(self):
        if request.method == 'GET':
            farms_list = []
            for farm in self.model.get_farms():
                farms_list.append(json.dumps(str(farm)))
            return json.dumps(farms_list)
        elif request.method == 'POST':
            args = self.request_data(request)
            res = make_response(self.model.create_farm(args))
            return res.data
        else:
            logger.debug("unknown method: %s" % request.method.to_string())
            raise("in MiaLBView.farms_api, unknown method: %s" % request.method.to_string())

    def farm_api(self, farm_id):
        if request.method == 'GET':
            if self.model.get_farm(farm_id):
                response = self.model.get_farm(farm_id).to_json()
            else:
                response = json.dumps({"error": "farm not found"}), 404
        elif request.method == 'PUT':
            args = self.request_data(request)
            response = make_response(self.model.update_farm(farm_id, args))
        elif request.method == 'DELETE':
            response = make_response(self.model.delete_farm(farm_id))
        else:
            logger.debug("unknown method: %s" % request.method.to_string())
            raise("in MiaLBView.farm_api, unknown method: %s" % request.method.to_string())

        return response

    def farm_members_api(self, farm_id):
        if request.method == 'GET':
            members_json = []
            for member in self.model.get_farm_members(farm_id):
                members_json.append(json.dumps(member))
            return json.dumps(members_json)

        elif request.method == 'POST':
            kwargs = self.request_data(request)
            if 'Client-IP' in request.headers:
                kwargs['ip'] = request.headers['Client-IP']
            if 'Client-Port' in request.headers:
                kwargs['port'] = request.headers['Client-Port']
            return make_response(self.model.create_farm_member(farm_id, **kwargs))
        else:
            logger.debug("unknown method: %s" % request.method.to_string())
            raise("in MiaLBView.farm_members_api, unknown method: %s" % request.method.to_string())
        
    def farm_member_api(self, farm_id, member_id):
        if request.method == 'GET':
            return json.dumps(self.model.get_farm_member(farm_id, member_id).__dict__)
        elif request.method == 'DELETE':
            return json.dumps(self.model.delete_farm_member(farm_id, member_id))
        else:
            logger.debug("unknown method: {}".format(request.method.to_string()))
            raise("in MiaLBView.farm_member_api, unknown method: {}".format(request.method.to_string()))

    def farm_cert_api(self, farm_id):
        if request.method == 'GET':
            filename = self.model.get_farm(farm_id).ssl[pem]
            return json.dumps({filename.split('/')[-1]: open(filename).read()})
        elif request.method in ['POST', 'PUT']:
            open("/etc/nginx/conf.d/uploaded-certificate.pem", 'wb').write(request.files['cert'].read())
            open("/etc/nginx/conf.d/uploaded-certificate_key.pem", 'wb').write(request.files['key'].read())
            self.model.update_farm(farm_id, {'ssl': {'cert': "/etc/nginx/conf.d/uploaded-certificate.pem",
                                                     'key': "/etc/nginx/conf.d/uploaded-certificate_key.pem"}})
            return json.dumps(self.model.get_farm(farm_id))

    @staticmethod
    def request_data(request):
        try:
            return json.loads(request.data)
        except Exception:
            raise Exception("couldn't parse request {} as json".format(str(request.data)))

    def _extract_certs(self, args):
        if request.files and ['certificate', 'certificate_key'] in request.files:
            request.files['cert'] = request.files.pop('certificate')
            request.files['key'] = request.files.pop('certificate_key')
        if request.files and ['key', 'cert'] in request.files:
            file.save('/etc/nginx/uploaded-cert.pem', request.files['cert'])
            file.save('/etc/nginx/uploaded-key.pem', request.files['key'])
            args['ssl'] = {'certificate': '/etc/nginx/uploaded-cert.pem',
                           'certificate_key': '/etc/nginx/uploaded-key.pem'}

    def view_api(self):
        routes = [
                {'rule': '/MiaLB/farms',
                 'view_func': self.farms_api,
                 'methods': ['GET', 'POST']},
                {'rule': '/MiaLB/farms/<string:farm_id>',
                 'view_func': self.farm_api,
                 'methods': ['GET', 'PUT', 'DELETE']},
                {'rule': '/MiaLB/farms/<string:farm_id>/members',
                 'view_func': self.farm_members_api,
                 'methods': ['GET', 'POST']},
                {'rule': '/MiaLB/farms/<string:farm_id>/members/<string:member_id>',
                 'view_func': self.farm_member_api,
                 'methods': ['GET', 'DELETE']},
                {'rule': '/MiaLB/farms/<string:farm_id>/certs',
                 'view_func': self.farm_cert_api,
                 'methods': ['GET', 'POST', 'PUT']}
                ]
        return routes
