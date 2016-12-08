#! /usr/bin/python
'''
Created on Apr 26, 2016

@author: geiger
'''
import json
import logging
import os
import re
import socket
import uuid


logger = logging.getLogger(__name__)
logging.basicConfig(filename=str(os.path.dirname(os.path.abspath(__file__))) + '/tests/unit/MiaLogs.log',
                    format='[%(asctime)s] [%(levelname)s] %(module)s - %(funcName)s:   %(message)s',
                    level=logging.DEBUG,
                    datefmt='%m/%d/%Y %I:%M:%S %p')

PROTOCOLS = ['HTTP', 'HTTPS' 'FTP']
MIN_PORT = 0
MAX_PORT = 65535
LB_METHOD = 'round_robin'


class Farm:
    def __init__(self, farm_id, args={}):
        self.farm_id = str(farm_id)
        # set defaults
        self.lb_method = 'round_robin'
        self.port = 80
        self.location = '/'
        self.protocol = 'http'
        self.members = {}
        self.ip = '0.0.0.0'
        self.name = ""
        # so long defaults
        self.update_farm(args)

    def update_farm(self, args):
        if 'lb_method' in args:
            lb_method = args.pop('lb_method')
            if lb_method == LB_METHOD:
                self.lb_method = lb_method
        if 'port' in args:
            port = int(args.pop('port'))
            if MIN_PORT <= port <= MAX_PORT:
                self.port = port
        if 'location' in args:
            self.location = args.pop('location')
        if 'protocol' in args:
            protocol = args.pop('protocol')
            if protocol in PROTOCOLS:
                self.protocol = protocol
        if 'members' in args:
            self.members = args.pop('members')
        if 'ip' in args:
            ip = args.pop('ip')
            # check if ip is legal address
            try:
                socket.inet_aton(ip)
                self.ip = ip
            except socket.error:
                # Not legal ip
                pass
        if 'name' in args:
            self.name = args.pop('name')
        else:
            # name should not be empty
            self.name = str(self.ip) + ":" + str(self.port) + '-' + str(self.location)
            self.name = self.name.replace('/', '-')
        for key in args.keys():
            logger.debug("received unknown argument %s" % str(key))

    def get_members(self):
        logger.debug("getting members")
        return self.members
    
    def get_member(self, member_id):
        if self.members.has_key(member_id):
            return self.members[member_id]
        else:
            return None
    
    def add_member(self, farm_member):
        member_id = self.generate_farm_member_id()
        if self.get_member(member_id) is None:
            self.members[member_id] = FarmMember(farm_member)
        else:
            logger.warning("member_id: " + str(member_id) + " already exists")
    
    def delete_member(self, member_id):
        return self.members.pop(member_id)
    
    def generate_farm_member_id(self):
        uid = uuid.uuid4()
        while self.get_member(uid) is not None:
            uid = uuid.uuid4()
        return uid
    
    def __str__(self):
        representation = ""
        representation = representation + "name: " + str(self.name) + "\n"
        representation = representation + "protocol: " + str(self.protocol) + "\n"
        representation = representation + "ip: " + str(self.ip) + "\n"
        representation = representation + "port: " + str(self.port) + "\n"
        representation = representation + "location: " + str(self.location) + "\n"
        representation = representation + "lb_method: " + str(self.lb_method) + "\n"
        representation += "members: \n"
        for member in self.members.values():
            representation = representation + "\t" + str(member)
        return representation

    def to_json(self):
        farm_dict = self.__dict__
        for key in farm_dict['members'].keys():
            farm_dict['members'][key] = farm_dict['members'][key].__dict__
        return json.dumps(farm_dict)


class FarmMember:
    def __init__(self, args):
        if isinstance(args, str):
            self.url = args
        else:
            self.url = None
            if 'url' in args and self.is_url_valid(args['url']):
                self.url = args['url']
            self.weight = args['weight'] if 'weight' in args else 1

    @staticmethod
    def is_url_valid(url):
        pattern = re.compile(
            r'^((?:http|ftp)s?://)?'  # optional protocol
            r'(?:(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+(?:[A-Za-z]{2,6}\.?|[A-Za-z0-9-]{2,}\.?)|'  # domain...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return pattern.match(url)

    def __str__(self):
        representation = ""
        representation = representation + "{url: " + str(self.url) + ",\n"
        if self.weight is not None and self.weight != "":
            representation = representation + "weight: " + str(self.weight) + "}\n"
        return representation

    def __repr__(self):
        return str(self)

if __name__ == '__main__':
    farm = Farm(farm_id = uuid.uuid4(),
                args = {'lb_method': 'round_robin',
                 'port': 443,
                 'location': '/right/here',
                 'protocol': 'https',
                 'ip': '190.20.18.139'})
    print(str(farm))
    print(" adding member")
    member = FarmMember({'url': 'lnx-int-yum-1:6793',
                          'weight': 2})
    farm.add_member(member)
    print(member)
    print(str(farm))