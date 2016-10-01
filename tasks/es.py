# -*- coding: utf-8 -*-

# pybroker
# Copyright (c) 2016 David Sabatie <pybroker@notrenet.com>
#
# This file is part of Pybroker.
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

# generic import
import json
import switch
import re
from celery.utils.log import get_task_logger

# local import
from pybroker import pybroker
from drivers.es import *

# global definitions
elastic = Es()


@pybroker.task
def es_insert(bbdo_msg):
    # print(bbdo_msg)
    result = elastic.insertMsg(bbdo_msg)
    # if data is not None:
    #     elastic.insertData(data)


@pybroker.task
def es_update(x, y):
    return x + y
