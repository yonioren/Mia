'''
Created on Apr 26, 2016

@author: geiger
'''
import errno

from io import open
from logging import getLogger
from os import remove, system, listdir

from .mialb_entities import FarmMember, Farm, logger

logger = getLogger(__name__)
DEFAULT_CONF_DIR = "/etc/nginx/conf.d/"


class MiaLBController(object):
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
            logger.info("In MiaLB_Controller.load_farm(farm_id: %s ): file not found" % farm_id)
            return False

        file_content = str(conf_file.read()).split()
        conf_file.close()
        farm_args, members_args = self.parse_configuration(file_content)
        members = {}
        while members_args.__len__() > 0:
            item = members_args.popitem()
            members[item[0]] = FarmMember(url=item[0], weight=item[1])
        farm_args['members'] = members
        return Farm(farm_id, farm_args)

    def commit_farm(self, farm):
        file_content = self.configuration_string(farm)
        destination = open(self.conf_dir + str(farm.farm_id) + ".conf", 'w')
        destination.write(unicode(file_content))
        destination.close()
        # infrom nginx about the changes
        system("nginx -s reload")
    
    def delete_farm(self, farm_id):
        filename = str(self.conf_dir) + str(farm_id) + ".conf"
        try:
            remove(filename)
        except OSError as e:
            # file not found error
            if e.errno == errno.ENOENT:
                logger.info("In MiaLB_Controller.delete_farm(farm_id: %s ): file not found" % farm_id)
            else:
                raise e
        # infrom nginx about the changes
        system("nginx -s reload")

    @staticmethod
    def configuration_string(farm):
        file_content = ""
        # build the farm members configuration section
        file_content += file_content + 'upstream ' + str(farm.farm_id) + ' {\n'
        if farm.lb_method not in ["", "round_robin"]:
            file_content += '\t' + farm.lb_method + ';\n'
        for member in farm.members.values():
            file_content += '\tserver ' + member.conf_representation() + ';\n'
        file_content += '}\n'
        # build the farm configuration section
        file_content += 'server {\n'
        file_content += '\tlisten ' + str(farm.ip) + ':' + str(farm.port) + ';\n'
        file_content += '\tlocation ' + str(farm.location) + ' {\n'
        file_content += '\t\tproxy_pass ' + str(farm.protocol) + '://' + str(farm.farm_id) + ';\n'
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
                    logger.debug("after upstream expected {, instead got %s " % head)
                    raise "In MiaLB_Controller.parsing_begin: after upstream expected {, instead got %s " % head
            elif head == 'server':
                if str(content.pop()) == '{':
                    self.parsing_server(content, farm_args, members_args)
                else:
                    logger.debug("after server expected {, instead got %s " % head)
                    raise "In MiaLB_Controller.parsing_begin: after server expected {, instead got %s " % head
            else:
                logger.debug("unknown word %s " % head)
                raise "In MiaLB_Controller.parsing_begin: unknown word %s " % head

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
                logger.debug("unknown word %s " % head)
                raise("In MiaLB_Controller.parsing_upstream: unknown word %s " % head)
    
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
                logger.debug("unknown word %s , expected ; or weight" % weight)
                raise("In MiaLB_Controller.parsing_member: unknown word %s , expected ; or weight" % weight)
    
    def parsing_server(self, content, farm_args, members_args):
        while content:
            head = str(content.pop())
            if head == 'listen':
                listen = str(content.pop())
                if listen.endswith(';'):
                    listen = listen[:-1]
                if ':' in listen:
                    listen = listen.split(':')
                    farm_args['ip'] = listen[0]
                    farm_args['port'] = listen[1]
                else:
                    farm_args['port'] = listen
            elif head == 'location':
                farm_args['location'] = str(content.pop())
                if str(content.pop()) == '{':
                    self.parsing_location(content, farm_args, members_args)
                else:
                    logger.debug("after location expected {, instead got %s " % head)
                    raise "In MiaLB_Controller.parsing_server: after location expected {, instead got %s " % head
            elif head == '}':
                return True
            else:
                logger.debug("unknown word %s " % head)
                raise "In MiaLB_Controller.parsing_server: unknown word %s " % head

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
                logger.debug("expected proxy_pass, instead got %s " % head)
                raise "In MiaLB_Controller.parsing_location: expected proxy_pass, instead got %s " % head

# unit tests
if __name__ == '__main__':
    controller = MiaLBController()
    farms = controller.load_farms()
    print(str(farms))
    for farm in farms.values():
        print("\t" + str(farm))
    farms['me'].location="/over/there"
    controller.commit_farm(farms['me'])
