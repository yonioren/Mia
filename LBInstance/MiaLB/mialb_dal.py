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
import errno

from io import open
from logging import getLogger
from os import remove, system, listdir
from re import sub

from mialb_entities import FarmMember, Farm, logger

logger = getLogger(__name__)
DEFAULT_CONF_DIR = "/etc/nginx/conf.d/"


class MiaLBDAL(object):
    def __init__(self):
        """ Constructor """

        self.conf_dir = DEFAULT_CONF_DIR

    def load_farms(self):
        logger.debug("loading farms")
        farms={}
        conf_files = listdir(self.conf_dir)
        for conf in conf_files:
            if conf.endswith('.conf'):
                farm_id=conf[:-5]
                farms[farm_id] = self.load_farm(farm_id)
        return farms
    
    def load_farm(self, farm_id):
        filename = str(self.conf_dir) + str(farm_id) + ".conf"
        try:
            conf_file = open(filename, 'r')
        except IOError:
            logger.info("In MiaLB_Controller.load_farm(farm_id: {} ): file not found".format(farm_id))
            return False

        file_content = str(conf_file.read()).split()
        conf_file.close()
        farm_args, members_args = self.parse_configuration(file_content)
        members = {}
        while members_args.__len__() > 0:
            item = members_args.popitem()
            members[item[0]] = FarmMember(url=item[0], weight=item[1])
        farm_args['members'] = members
        return Farm(farm_id, **farm_args)

    def commit_farm(self, farm):
        file_content = self.configuration_string(farm)
        destination = open(self.conf_dir + str(farm.farm_id) + ".conf", 'w')
        destination.write(unicode(file_content))
        destination.close()
        # infrom nginx about the changes
        if farm.get_members():
            system("nginx -s reload")
    
    def delete_farm(self, farm_id):
        filename = str(self.conf_dir) + str(farm_id) + ".conf"
        try:
            remove(filename)
        except OSError as e:
            # file not found error
            if e.errno == errno.ENOENT:
                logger.info("In MiaLB_Controller.delete_farm(farm_id: {} ): file not found".format(farm_id))
            else:
                raise e
        # infrom nginx about the changes
        system("nginx -s reload")

    @staticmethod
    def configuration_string(farm):
        file_content = ""
        # build the farm members configuration section
        file_content += file_content + 'upstream ' + str(farm.name) + ' {\n'
        if farm.lb_method not in ["", "round_robin"]:
            file_content += '\t' + farm.lb_method + ';\n'
        for member in farm.members.values():
            file_content += '\tserver ' + member.conf_representation() + ';\n'
        file_content += '}\n'
        # build the farm configuration section
        file_content += 'server {\n'
        for bind in farm.listen:
            file_content += '\tlisten ' + \
                            (str(bind['ip']) + ':' if 'ip' in bind else "") + \
                            str(bind['port']) + \
                            (' ssl' if 'ssl' in bind and str(bind['ssl']) else "") + \
                            ';\n'
        if farm.server_name:
            file_content += '\tserver_name ' + str(farm.server_name) + ';\n'
        if farm.ssl != {}:
            file_content += '\tssl_certificate ' + str(farm.ssl['certificate']) + ';\n'
            file_content += '\tssl_certificate_key ' + str(farm.ssl['certificate_key']) + ';\n'
        file_content += '\tlocation ' + str(farm.location) + ' {\n'
        file_content += '\t\tproxy_pass ' + str(farm.protocol) + '://' + str(farm.name) + ';\n'
        file_content += '\t}\n'
        file_content += '}\n'

        return file_content
    
    # I chose to parse using an automate, sorry if its too big a hustle
    def parse_configuration(self, content):
        farm_args = {}
        members_args = {}
        # Reversing the order of the array, because working with pop is so much easier
        content.reverse()
        self.parsing_begin(content, farm_args, members_args)
        return farm_args, members_args
    
    def parsing_begin(self, content, farm_args, members_args):
        while content:
            head = str(content.pop())
            if head == 'upstream':
                farm_args['name'] = content.pop()
                if str(content.pop()) == '{':
                    self.parsing_upstream(content, farm_args, members_args)
                else:
                    logger.debug("after upstream expected {, instead got %s ".format(head))
                    raise "In MiaLB_Controller.parsing_begin: after upstream expected {, instead got {} ".format(head)
            elif head == 'server':
                if str(content.pop()) == '{':
                    self.parsing_server(content, farm_args, members_args)
                else:
                    logger.debug("after server expected {, instead got %s " % head)
                    raise "In MiaLB_Controller.parsing_begin: after server expected {, instead got {}".format(head)
            else:
                logger.debug("unknown word {} ".format(head))
                raise "In MiaLB_Controller.parsing_begin: unknown word {} ".format(head)

    def parsing_upstream(self, content, farm_args, members_args):
        while content:
            head = str(content.pop())
            if head in ['round_robin;', 'ip_hash;', 'least_conn;']:
                farm_args['lb_method'] = head[:-1]
            elif head == "server":
                self.parsing_member(content, farm_args, members_args)
            elif head == "}":
                return True
            else:
                logger.debug("unknown word {} ".format(head))
                raise("In MiaLB_Controller.parsing_upstream: unknown word {} ".format(head))
    
    @staticmethod
    def parsing_member(content, farm_args, members_args):
        head = str(content.pop())
        if head[head.__len__()-1] == ';':
            members_args[head[:-1]] = 1
            return True
        else:
            weight = str(content.pop()) 
            if weight.startswith('weight='):
                members_args[head] = weight.split('=')[1]
            else:
                logger.debug("unknown word {} , expected ; or weight".format(weight))
                raise("In MiaLB_Controller.parsing_member: unknown word {} , expected ; or weight".format(weight))
    
    def parsing_server(self, content, farm_args, members_args):
        while content:
            head = str(content.pop())
            if head == 'listen':
                listen = str(content.pop())
                if listen[-1] == ';':
                    listen = sub(r';$', '', listen)
                    ssl = False
                elif sub(r';$', '', str(content[-1])) == 'ssl':
                    ssl = content.pop() or True
                elif str(content[-1]) == ';':
                    ssl = content.pop() and False
                else:
                    logger.debug("after listen expected ;, instead got {} ".format(
                        str(listen) + '\n' + str(content.pop())
                    ))
                    raise "In MiaLBDAL.parsing_server: after listen expected ;, instead got {} ".format(
                        str(listen) + '\n' + str(content.pop())
                    )
                if 'listen' not in farm_args:
                    farm_args['listen'] = []
                if ':' in listen:
                    farm_args['listen'].append({'ip': listen.split(':')[0], 'port': listen.split(':')[1], 'ssl': ssl})
                else:
                    farm_args['listen'].append({'ip': '0.0.0.0', 'port': listen, 'ssl': ssl})

            elif head == 'server_name':
                name = str(content.pop())
                if name[-1] == ';':
                    name = sub(r';$', '', name)
                elif str(content[-1]) == ';':
                    content.pop()
                else:
                    logger.debug("after server_name expected ;, instead got {} ".format(
                        str(listen) + '\n' + str(content.pop())
                    ))
                    raise "In MiaLBDAL.parsing_server: after server_name expected ;, instead got {} ".format(
                        str(listen) + '\n' + str(content.pop())
                    )
                farm_args['server_name'] = name

            elif head == 'ssl_certificate':
                cert = str(content.pop())
                if cert[-1] == ';':
                    cert = sub(r';$', '', cert)
                elif str(content[-1]) == ';':
                    content.pop()
                else:
                    logger.debug("after ssl_certificate expected ;, instead got {} ".format(
                        str(cert) + '\n' + str(content.pop())
                    ))
                    raise "In MiaLBDAL.parsing_server: after ssl_certificate expected ;, instead got {} ".format(
                        str(cert) + '\n' + str(content.pop())
                    )
                if 'ssl' not in farm_args:
                    farm_args['ssl'] = {}
                farm_args['ssl']['certificate'] = cert

            elif head == 'ssl_certificate_key':
                key = str(content.pop())
                if key[-1] == ';':
                    key = sub(r';$', '', key)
                elif str(content[-1]) == ';':
                    content.pop()
                else:
                    logger.debug("after ssl_certificate_key expected ;, instead got {} ".format(
                        str(key) + '\n' + str(content.pop())
                    ))
                    raise "In MiaLBDAL.parsing_server: after ssl_certificate_key expected ;, instead got {} ".format(
                        str(key) + '\n' + str(content.pop())
                    )
                if 'ssl' not in farm_args:
                    farm_args['ssl'] = {}
                farm_args['ssl']['certificate_key'] = key

            elif head == 'location':
                farm_args['location'] = str(content.pop())
                if str(content.pop()) == '{':
                    self.parsing_location(content, farm_args, members_args)
                else:
                    logger.debug("after location expected {, instead got {} ".format(head))
                    raise "In MiaLBDAL.parsing_server: after location expected {, instead got {} ".format(head)
            elif head == '}':
                return True
            else:
                logger.debug("unknown word {} ".format(head))
                raise "In MiaLBDAL.parsing_server: unknown word {} ".format(head)

    @staticmethod
    def parsing_location(content, farm_args, members_args):
        while content:
            head = str(content.pop())
            if head == 'proxy_pass':
                head = str(content.pop())
                if "://" in head:
                    farm_args['protocol'] = head.split("://")[0]
            elif head == '}':
                return True
            else:
                logger.debug("expected proxy_pass, instead got {} ".format(head))
                raise "In MiaLB_Controller.parsing_location: expected proxy_pass, instead got {} ".format(head)

# unit tests
if __name__ == '__main__':
    controller = MiaLBDAL()
    farms = controller.load_farms()
    print(str(farms))
    for farm in farms.values():
        print("\t" + str(farm))
    farms['me'].location="/over/there"
    controller.commit_farm(farms['me'])
