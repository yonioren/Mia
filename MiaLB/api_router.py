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
import logging

from flask import Flask, make_response
from mialb_configs import *
from mialb_model import MiaLBModel
from mialb_view import MiaLBView
from sys import argv


class Mia(Flask):
    def __init__(self, name):
        Flask.__init__(self, name)
        self.model = MiaLBModel()
        self.view = MiaLBView(self.model)
        self.route_view()
        self._config_logger()

    def route_view(self):
        view_routes = self.view.view_api() 
        for v_route in view_routes:
            self.add_url_rule(v_route['rule'], view_func=v_route['view_func'], methods=v_route['methods'])

    @staticmethod
    def _config_logger():
        logging.getLogger(__name__)
        logging.basicConfig(filename=logfile,
                            format='[%(asctime)s] [%(levelname)s] %(module)s - %(funcName)s:   %(message)s',
                            level=loglevel,
                            datefmt='%m/%d/%Y %I:%M:%S %p')

api_router = Mia(__name__)
api_router.debug = True


@api_router.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)


# example of how to route
@api_router.route('/', methods=['GET'])
def index():
    return json.dumps([{'index': 'main'}, {'supported methods': 'GET'}, {'apidoc': '/apidoc'}])


if __name__ == '__main__' or '--run-damn-you' in argv:
    api_router.run(host=host, port=int(port))
