#!/usr/bin/python2.7

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
from argparse import ArgumentParser

from MiaLBHost.LBContainer import LBContainer
from MiaLBHost.setup_host import setup as setup_host

main_parser = ArgumentParser(description="utility for manipulating interfaces for MiaLB")
main_subparsers = main_parser.add_subparsers()
main_subparsers.dest = "command"

addif = main_subparsers.add_parser("connect")
addif.add_argument("--container", type=str, required=True, help="container id")
addif.add_argument("--network", type=str, default="services", help="network id or name")
addif.add_argument("--default-network", type=bool, default=True, help="make this a default gw network")
addif.add_argument("--default-gw", type=str, required=False, help="default gw address")
addif.add_argument("--ip", type=str, required=True, help="ip address to set for the interface")

setup = main_subparsers.add_parser("setup")
setup.add_argument("--conf-file", '-f', type=str, required=False)
setup.add_argument("--network", type=str, required=False, help="name for the docker network")
setup.add_argument("--cidr", type=str, required=False, help="ipv4 cidr")
setup.add_argument("--gateway", type=str, required=False, help="address for the bridge")

commands = {"setup": setup_host}

kwargs = main_parser.parse_args().__dict__
if 'container' in kwargs:
    container_id = kwargs.pop('container')
    lb_container = LBContainer(container_id=container_id)
    commands['connect'] = lb_container.add_interface

command = commands[kwargs.pop('command')]
command(**kwargs)
