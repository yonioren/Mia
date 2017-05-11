import uuid
import unittest

from nose.tools import *

from LBInstance.MiaLB.mialb_entities import Farm, FarmMember


class TestMiaEntities(unittest.TestCase):

    def test_farm_port_valid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    port=65535)
        eq_(farm.port, 65535)

    def test_farm_port_invalid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    port=65536)
        eq_(farm.port, 80)

    def test_farm_lb_method_valid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    lb_method='round_robin')
        eq_(farm.lb_method, 'round_robin')

    def test_farm_lb_method_invalid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    lb_method='round_robinn')
        eq_(farm.lb_method, 'round_robin')

    def test_farm_protocol_valid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    protocol='http')
        eq_(farm.protocol, 'http')

    def test_farm_protocol_invalid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    protocol='sdfsdf')
        eq_(farm.protocol, 'http')

    def test_farm_ip_valid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    ip='190.20.18.139')
        eq_(farm.ip, '190.20.18.139')

    def test_farm_ip_invalid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    ip='sdfsdf')
        eq_(farm.ip, '0.0.0.0')

    def test_farm_ip_invalid2(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    ip='-8.0.0.0')
        eq_(farm.ip, '0.0.0.0')

    def test_farm_name_valid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    name='blabla')
        eq_(farm.name, 'blabla')

    def test_farm_name_invalid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    port='8080',
                    ip='190.20.18.139',
                    location='/right/here')
        eq_(farm.name, '190.20.18.139:8080--right-here')

    def test_farm_location_valid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    name='blabla')
        eq_(farm.name, 'blabla')

    def test_farm_location_invalid(self):
        farm = Farm(farm_id=uuid.uuid4(),
                    location='/right/here')
        eq_(farm.location, '/right/here')

    def test_farm_member_url_valid(self):
        farm_member = FarmMember(url='http://sdf.sdf:234',
                                 weight=2)
        eq_(farm_member.url, 'http://sdf.sdf:234')

    def test_farm_member_url_valid2(self):
        farm_member = FarmMember(url='http://DF.WER',
                                 weight=2)
        eq_(farm_member.url, 'http://DF.WER')

    def test_farm_member_url_valid3(self):
        farm_member = FarmMember(url='DF.WER:345',
                                 weight=2)
        eq_(farm_member.url, 'DF.WER:345')

    @raises(AttributeError)
    def test_farm_member_url_invalid(self):
        FarmMember(url='http://DF.WER:sf', weight=2)

    @raises(AttributeError)
    def test_farm_member_no_url(self):
        FarmMember(weight=2)
