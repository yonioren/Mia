#! /usr/bin/python
'''
Created on Apr 24, 2016

@author: geiger
'''

from flask import Flask, make_response
from mialb_view import MiaLBView
from mialb_model import MiaLBModel
import json


class Mia(Flask):
    def __init__(self, name):
        Flask.__init__(self, name)
        self.model = MiaLBModel()
        self.view = MiaLBView(self.model)
        self.route_view()
        
    def route_view(self):
        view_routes = self.view.view_api() 
        for v_route in view_routes:
            self.add_url_rule(v_route['rule'], view_func=v_route['view_func'], methods=v_route['methods'])

api_router = Mia(__name__)
api_router.debug = True

@api_router.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)
    
#example of how to route
@api_router.route('/', methods=['GET'])
def index():
    return json.dumps([{'index': 'main'}, {'supported methods': 'GET'}, {'apidoc': '/apidoc'}])
