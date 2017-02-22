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
import yaml
import logging
import socket
import array
import zmq
import json
import threading
import SocketServer
import cPickle as pickle
from struct import *
import base64

# project imports
from .bbdo import Bbdo

READY = "r"
ERROR = "e"


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        self.host_status = 0
        self.server.logger.debug('Connected by '+ str(self.client_address))
        # Get negotiation data
        data = self.request.recv(1024)
        # Send it back (like mirror)
        self.request.sendall(data)
        self.server.logger.debug(str("data sent back"))

        # read bbdo yaml file
        with open("conf/bbdo_proto_v"+str(self.server.options['version'])+".yml", 'r') as stream:
            self.server.logger.debug('open bbdo proto: conf/bbdo_proto_v'+str(self.server.options['version'])+".yml")
            try:
                bbdo_matrix = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        head_size = calcsize(bbdo_matrix['header']['fmt'])

        # Start to get data from broker (master or module)
        # while True:
        # wait for reply before sending data stream
        while True:
            # Get bbdo header
            header_stream = self.request.recv(head_size)
            self.server.logger.debug("Header")
            self.server.logger.debug(str(header_stream))
            if not header_stream:
                break
            # Compute header to download full data stream
            data = {}
            if len(header_stream) > head_size:
                print('not a valid header')
                exit(1)
            # TODO: add check for bbdo protocol version
            # if header 8 bytes => v1
            # if header 16 bytes => v2

            if self.server.options['version'] == 1:
                # 8 bytes
                data['checksum'], data['stream_size'], event_id = unpack_from(
                    bbdo_matrix['header']['fmt'], header_stream)
            else:
                # 16 bytes
                data['checksum'], data['stream_size'], event_id, data['source_id'], data['destination_id'] = unpack_from(
                    bbdo_matrix['header']['fmt'], header_stream)
            data['event_cat'] = event_id / 65536
            data['event_type'] = event_id - (data['event_cat'] * 65536)

            data['payload'] = base64.b64encode(self.request.recv(data['stream_size']))
            self.server.logger.debug("Payload")
            self.server.logger.debug(str(data['payload']))
            if not data['payload']:
                continue
            self.server.logger.debug("Sending data to the filters")

            # host_status is received 2 times form engine, avoid resend the second time
            if self.host_status == 0:
                # self.server.worker.send_multipart([data])
                self.server.worker.send_json(data)

class ThreadedTCPServer(SocketServer.ThreadingTCPServer):

    def __init__(self, server_address, handlerClass, logger, options, worker):
        SocketServer.ThreadingTCPServer.__init__(self, server_address, handlerClass)
        self.logger = logger
        self.options = options
        self.worker = worker

class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.output = worker['out']
        self.logger = logging.getLogger(
            'pybroker.driver.bbdo.inputs.' + self.output.identity)
        self.begin = 0

    def run(self):
        # Startup message sequence
        self.logger.debug("Saying hello to the server from "+self.output.identity)

        # Port 0 means to select an arbitrary unused port
        HOST, PORT = self.options["listen_ip"], self.options["listen_port"]

        binded = 0
        while not binded:
            try:
                server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler, self.logger, self.options, self.output)
                binded = 1
            except socket.error as e:
                self.logger.warning("can't bind to socket; waiting")
                time.sleep(self.options['wait_socket'])

        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request

        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        self.logger.debug("Server loop running in thread: " + str(server_thread.name))
        #
