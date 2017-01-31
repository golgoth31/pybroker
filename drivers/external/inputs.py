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
import logging
import socket
import zmq
import json
import threading
from zmq.devices import Device

class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.worker = worker['out']
        self.logger = logging.getLogger(
            'pybroker.driver.external.inputs.' + self.worker.identity)
        self.begin = 0

        # Initiate the external socket
        self.logger.debug("Starting external socket")
        self._external = zmq.Context.instance()

        # bind to external socket
        self.worker_external = self._external.socket(zmq.ROUTER)
        self.worker_external.bind(
            self.options['type']+"://" + self.options['bind_address'] + ":"+str(self.options['bind_port']))

        # poll_all = zmq.Poller()
        # poll_all.register(self.worker_external, zmq.POLLIN)

    def run(self):
        # Startup message sequence
        # self.logger.debug("Saying hello to the server from "+self.worker.identity)

        zmq.proxy(self.worker_external, self.worker)

        # self.worker.send_multipart(['toto'])
        # while True:
        #     try:
        #         self.logger.debug('Entering main loop ...')
        #
        #         self.logger.debug("Polling queues ...")
        #         socks = dict(poll_all.poll(timeout=0))
        #
        #         self.logger.debug("Looking for data from the outside world ...")
        #         # Handle worker activity on self.broker_input
        #         if socks.get(self.worker_external) == zmq.POLLIN:
        #             self.logger.debug("getting external message")
        #             #  Get client request
        #             msg = self.worker_external.recv_multipart()
        #             self.logger.debug(msg)
        #             if not msg:
        #                 break
        #
        #             # Stop action !
        #             if msg[3].lower() == 'stop':
        #                 self.logger.info("Stop message received ! Stoping ...")
        #                 break
        #
        #         time.sleep(2)
        #     except KeyboardInterrupt:
        #         self.logger.critical(
        #             "Keyboard interrupt received, stopping...")
        #         break
        self.context.destroy()
        exit(1)
