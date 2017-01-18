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
import threading
import SocketServer


# project imports
from .bbdo_proto import Bbdo_proto

READY = "r"
ERROR = "e"


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        self.host_status = 0
        bbdo_stream = Bbdo_proto(self.server.logger, self.server.options)
        print('Connected by ', self.client_address)
        # Get negotiation data
        data = self.request.recv(1024)
        # Send it back (like mirror)
        self.request.sendall(data)
        self.server.logger.debug(str("data sent back"))

        # Start to get data from broker (master or module)
        # while True:
        # wait for reply before sending data stream
        while True:
            # Get bbdo header
            header = self.request.recv(bbdo_stream.head_size)
            self.server.logger.debug(str("header"))
            self.server.logger.debug(str(header))
            if not header:
                break
            # Compute header to download full data stream
            bbdo_stream.ComputeHeader(header)
            data_stream = self.request.recv(bbdo_stream.stream_size)
            self.server.logger.debug(str("data_stream"))
            self.server.logger.debug(str(data_stream))
            if not data_stream:
                continue
            bbdo_stream.ExtractData(data_stream)
            self.server.logger.debug("Sending data to the server")

            # host_status is received 2 times form engine, avoid resend the second time
            if self.host_status == 0:
                self.server.worker.send_multipart([bbdo_stream.GetEventTypeName(), bbdo_stream.GetBbdoMatrixOutput()])
                self.server.logger.debug("getting answer from server")
                msg = self.server.worker.recv_multipart()
            if bbdo_stream.GetEventTypeName() == 'host_status':
                if self.host_status == 0:
                    self.host_status = 1
                else:
                    self.host_status = 0
            # print(msg)

class ThreadedTCPServer(SocketServer.ThreadingTCPServer):

    def __init__(self, server_address, handlerClass, logger, options, worker):
        SocketServer.ThreadingTCPServer.__init__(self, server_address, handlerClass)
        self.logger = logger
        self.options = options
        self.worker = worker
    # self.logger = logger
    # self.options = options
    # self.worker = worker
    # pass

class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.worker = worker
        self.logger = logging.getLogger(
            'getbbdo.driver.bbdo.' + self.worker.identity)
        self.begin = 0

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

        # Port 0 means to select an arbitrary unused port
        HOST, PORT = self.options["listen_ip"], self.options["listen_port"]

        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler, self.logger, self.options, self.worker)
        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print "Server loop running in thread:", server_thread.name
        #
