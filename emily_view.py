#! /usr/bin/python
'''
Created on Apr 24, 2016

@author: geiger
'''
from emily_entities import logger
from emily_model import Emily_Model
from flask import request
import json
from flask.helpers import make_response


class Emily_view:
    def __init__(self, model=None):
        if model is None:
            self.model = Emily_Model()
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
            raise("in Emily_View.farms_api, unknown method: %s" % request.method.to_string())

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
            raise("in Emily_View.farm_api, unknown method: %s" % request.method.to_string())

        return response

    def farm_members_api(self, farm_id):
        if request.method == 'GET':
            members_json = []
            for member in self.model.get_farm_members(farm_id):
                members_json.append(json.dumps(member))
            return json.dumps(members_json)

        elif request.method == 'POST':
            args = self.request_data(request)
            return make_response(self.model.create_farm_member(farm_id, args))
        else:
            logger.debug("unknown method: %s" % request.method.to_string())
            raise("in Emily_View.farm_members_api, unknown method: %s" % request.method.to_string())
        
    def farm_member_api(self, farm_id, member_id):
        if request.method == 'GET':
            return json.dumps(self.model.get_farm_member(farm_id, member_id).__dict__)
        elif request.method == 'DELETE':
            return json.dumps(self.model.delete_farm_member(farm_id, member_id))
        else:
            logger.debug("unknown method: {}".format(request.method.to_string()))
            raise("in Emily_View.farm_member_api, unknown method: {}".format(request.method.to_string()))
        
    def request_data(self, request):
        if request.headers['Content-Type'] == 'application/json':
            return json.loads(request.data)
            # return request.json()
        elif request.headers['Content-Type'] == 'text/plain':
            try:
                return json.loads(request.data)
            except Exception:
                raise Exception("couldn't parse request {} as json".format(str(request.data)))
        else:
            logger.debug("unknown content type: %s" % request.headers['Content-Type'])
            raise("unknown content type: %s" % request.headers['Content-Type'])
        
    def view_api(self):
        routes = [
                {'rule': '/Emily/farms',
                 'view_func': self.farms_api,
                 'methods': ['GET', 'POST']},
                {'rule': '/Emily/farms/<string:farm_id>',
                 'view_func': self.farm_api,
                 'methods': ['GET', 'PUT', 'DELETE']},
                {'rule': '/Emily/farms/<string:farm_id>/members',
                 'view_func': self.farm_members_api,
                 'methods': ['GET', 'POST']},
                {'rule': '/Emily/farms/<string:farm_id>/members/<string:member_id>',
                 'view_func': self.farm_member_api,
                 'methods': ['GET', 'DELETE']}
                ]
        return routes
