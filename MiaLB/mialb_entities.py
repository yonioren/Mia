#! /usr/bin/python
'''
Created on Apr 26, 2016

@author: geiger
'''
import json
import logging
import os
import uuid


logger = logging.getLogger(__name__)
logging.basicConfig(filename=str(os.path.dirname(os.path.abspath(__file__))) + '/tests/unit/MiaLogs.log',
                    format='[%(asctime)s] [%(levelname)s] %(module)s - %(funcName)s:   %(message)s',
                    level=logging.DEBUG,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


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
        # name should not be empty
        if self.name == "":
            self.name = str(self.ip) + ":" + str(self.port) + '-' + str(self.location)
            self.name = self.name.replace('/','-')

    def update_farm(self, args):
        if 'lb_method' in args:
            self.lb_method = args.pop('lb_method')
        if 'port' in args:
            self.port = args.pop('port')
        if 'location' in args:
            self.location = args.pop('location')
        if 'protocol' in args:
            self.protocol = args.pop('protocol')
        if 'members' in args:
            self.members = args.pop('members')
        if 'ip' in args:
            self.ip = args.pop('ip')
        if 'name' in args:
            self.name = args.pop('name')
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
            self.url = args['url']
            self.weight = args['weight'] if 'weight' in args else 1

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