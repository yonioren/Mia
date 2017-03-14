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
from logging import getLogger
from uuid import uuid4

logger = getLogger(__name__)


class SingleInstanceController(object):
    def __init__(self):
        self.relation = {}

    def set_instance(self, **kwargs):
        logger.debug("SingleInstanceController.set_instance({kwargs})".format(kwargs=str(kwargs)))
        farm_id = kwargs.pop('farm_id')
        if 'instance_id' not in kwargs:
            instance_id = self._create_instance(farm_id)
        else:
            instance_id = self._update_instance(farm_id, **kwargs)
        self.relation[farm_id] = [instance_id]

    def rem_instance(self, farm_id=None, instance_id=None):
        if farm_id and instance_id:
            if self.relation[farm_id] == instance_id:
                self._remove_instance(farm_id)
            else:
                raise IndexError(message="{} not in {}".format(instance_id, farm_id))
        elif farm_id:
            self._remove_instance(farm_id)
        elif instance_id:
            for key, value in self.relation.items():
                if value == instance_id:
                    self._remove_instance(key, instance_id)
            raise IndexError(message="instance not found")
        else:
            raise TypeError(message="at least one of farm_id or instance_id must be given")

    def extract_args(self, farm_id, args):
        return args

    def _remove_instance(self, farm_id):
        logger.debug("SingleInstanceController._remove_instance({farm_id})".format(farm_id=str(farm_id)))
        try:
            return self.relation.pop(farm_id)
        except KeyError:
            logger.error("key error popping {farm_id}. relatiation: {relation}".format(
                farm_id = farm_id, relation = str(self.relation)
        ))

    def _create_instance(self, farm_id):
        logger.debug("SingleInstanceController._create_instance({farm_id})".format(farm_id=str(farm_id)))
        return str(uuid4())

    def _update_instance(self, farm_id, **kwargs):
        logger.debug("SingleInstanceController._update_instance({farm_id}, {kwargs})".format(
            instance_id=str(farm_id), kwargs=str(kwargs)
        ))
        return self.relation[farm_id]
