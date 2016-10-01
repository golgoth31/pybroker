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

import zmq
import sys
import threading
import time
import json
import logging

class Core_worker(threading.Thread):
    """ServerWorker"""

    def __init__(self, id, w_state, w_type, options):
        threading.Thread.__init__(self)
        self.type = w_type
        self.options = options
        self.state = w_state
        self.id = id
        self.context = zmq.Context.instance()
        identity = "{0}_{1}".format(self.type, str(self.id))
        self.logger = logging.getLogger('getbbdo.worker.' + identity)
        self.logger.debug('init worker')
        if self.type == 'input':
            self.worker = self.context.socket(zmq.REQ)
        elif self.type == 'output':
            self.worker = self.context.socket(zmq.REP)
        else:
            self.logger.debug('unknown worker type')
            sys.exit(status="error")
        self.worker.identity = identity #identity.encode('ascii')
        self.worker.connect(self.options['zmq_url'])
        self.logger.debug("server zmq url: "+self.options['zmq_url'])
        # self.worker_state = self.context.socket(zmq.PUSH)
        # self.worker_state.connect(self.state['zmq_url'])
        self.logger.debug("state zmq url: "+self.state['zmq_url'])

    def run(self):

        self.logger.debug("start worker: " + self.worker.identity)

        driver = self.loadDriver()
        driver.run()
        # while True:
        #     self.logger.debug(identity + " receiving message")
        #     msg = worker.recv_multipart()
        #     if not msg:
        #         break
        #     # print(msg)
        #     # add centreon id
        #     self.logger.debug(identity + " sending to celery")
        #     sent_msg = insert.delay(msg)
        #     # sent_msg.get(timeout=1)
        #
        #     self.logger.debug(identity + " sending to server")
        #     worker.send(LRU_READY)
        # worker.close()
        # self.context.term()

    def loadDriver(self):
        self.logger.debug('try to load driver')
        try:
            command_module = __import__("drivers.{0}".format(self.options['drivers']), fromlist=["drivers"])
        except ImportError as e:
            # Display error message
            self.logger.debug("can't initialize module: drivers.{0}".format(self.options['drivers']))
            self.logger.debug(e)
            exit()
        self.logger.debug('exec driver')
        return command_module.Work(self.options['driver_options'], self.worker)
