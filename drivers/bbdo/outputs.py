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

import sys
import time
import json
import logging
import zmq
import importlib

# project imports
from drivers.es import *
# from drivers.influx import *

READY = "r"
ERROR = "e"


class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.input = worker['in']
        self.output = worker['out']
        self.logger = logging.getLogger(
            'pybroker.driver.bbdo.outputs.' + self.input.identity)
        self.begin = 0
        self.elastic = Es(
            self.options["elastic_host"], self.options["elastic_port"])
        # self.inf = Influx(self.options["elastic_host"], self.options["elastic_port"])

    def run(self):

        while True:
            self.logger.debug("receiving message")
            msg = self.input.recv_json()

            if not msg:
                break
            self.logger.debug("sending to database: " + str(msg))
            sent_msg = self.elastic.insertData(msg)
            # if msg['doc_type'] != 'metrics':
            #     sent_msg = self.elastic.insertData(msg)
            # else:
            #     self.logger.debug("sending to influxdb database")
            #     sent_msg = self.inf.insertData(msg)

        self.worker.close()
        self.context.term()
