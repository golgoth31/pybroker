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

READY = "r"
ERROR = "e"


class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.worker = worker
        self.logger = logging.getLogger(
            'getbbdo.worker.driver.celery_tasks.' + self.worker.identity)
        self.logger.debug('init task worker')
        # project imports
        self.locMod = {}
        for task in self.options['tasks']:
            self.locMod[task] = importlib.import_module('tasks.'+task, package=None)
        self.begin = 0

    def run(self):
        # Startup message sequence
        self.logger.debug("Waiting for begin message")
        while not self.begin:
            msg = self.worker.recv_multipart()
            self.begin = msg[0]
        self.worker.send_multipart([self.worker.identity, READY])
        self.logger.debug("Begin received, starting to get data")
        # End of startup message sequence

        while True:
            self.logger.debug("receiving message")
            msg = self.worker.recv_multipart()
            # print(msg)
            if msg[0] != "1":

                # if msg[2] == 'host_status':
                #     print(self.worker.identity)
                #     print(msg)
                if not msg:
                    break
                self.logger.debug("sending to celery")
                try:
                    sent_msg = self.locMod['es'].es_insert.delay(msg)
                except:
                    self.worker.send_multipart(ERROR)
                    self.logger.critical("can't send data to celery")
            self.logger.debug("sending to server")
            self.worker.send_multipart([self.worker.identity,'', READY])
            # self.worker_state.send_multipart([self.worker.identity, READY])
        self.worker.close()
        self.context.term()
