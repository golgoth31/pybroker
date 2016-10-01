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
import socket
import array
import zmq
import json

# project imports
from .bbdo_proto import Bbdo_proto
READY = "r"
ERROR = "e"

class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.worker = worker
        self.logger = logging.getLogger('getbbdo.driver.bbdo.' + self.worker.identity)
        self.begin = 0
        self.host_status = 0

    def run(self):
        # Startup message sequence
        self.logger.debug("Saying hello to the server")
        self.worker.send_multipart(READY)
        self.logger.debug("Waiting for begin message")
        while not self.begin:
            msg = self.worker.recv_multipart()
            self.begin = msg[0]
        self.logger.debug("Begin received, starting to get data")
        # End of startup message sequence

        # Start the bbdo socket and listen
        HOST = ''                 # Symbolic name meaning all available interfaces
        PORT = 50007              # Arbitrary non-privileged port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        binded = 0
        while not binded:
            try:
                s.bind((HOST, PORT))
                binded =1
            except socket.error as e:
                self.logger.warning("can't bind to socket; waiting")
                time.sleep(self.options['wait_socket'])
        s.listen(1)
        conn, addr = s.accept()
        bbdo_stream = Bbdo_proto(self.logger)
        print('Connected by', addr)
        # Get negotiation data
        data = conn.recv(1024)
        # Send it back (like mirror)
        conn.sendall(data)

        # Start to get data from broker (master or module)
        # while True:
        # wait for reply before sending data stream
        while True:
            # Get bbdo header
            header = conn.recv(bbdo_stream.head_size)
            if not header:
                continue
            # Compute header to download full data stream
            bbdo_stream.ComputeHeader(header)
            data_stream = conn.recv(bbdo_stream.stream_size)
            if not data_stream:
                continue
            bbdo_stream.ExtractData(data_stream)
            self.logger.debug("Sending data to the server")

            # host_status is received 2 times form engine, avoid resend the second time
            if self.host_status == 0:
                self.worker.send_multipart([bbdo_stream.GetEventTypeName(), bbdo_stream.GetBbdoMatrixOutput()])
                self.logger.debug("getting answer from server")
                msg = self.worker.recv_multipart()
            if bbdo_stream.GetEventTypeName() == 'host_status':
                if self.host_status == 0:
                    self.host_status = 1
                else:
                    self.host_status = 0
            # print(msg)
