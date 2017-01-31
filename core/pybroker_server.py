"""Core server of pybroker."""
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
import time
import json
import logging
import uuid

from zmq.devices import ThreadDevice
# from pybroker_worker import Pybroker_worker
from pybroker_stream import Pybroker_stream
import pybroker_common

# Some default variables

class Pybroker_server():
    """Core server of pybroker."""

    def __init__(self, options, hidden_streams, streams = None):
        """Init."""
        # init our logger
        self.logger = logging.getLogger('pybroker.server')
        self.logger.debug('Initializing central server')

        # init zmq
        self.server_zmq = pybroker_common.Pybroker_zmq(self.logger)

        # pouet
        self.hidden_streams = hidden_streams
        self.streams = streams

        # start hidden streams
        self.hidden_devices = {}
        for stream in self.hidden_streams:
            if self.hidden_streams[stream]['active']:
                self.hidden_devices[stream] = Pybroker_stream(stream, self.hidden_streams[stream])
                self.logger.debug('Created devices: ' + str(self.hidden_devices[stream].getComDevices()))

        # start functional streams
        self.stream_devices = {}
        for stream in self.streams:
            if self.streams[stream]['active']:
                self.stream_devices[stream] = Pybroker_stream(stream, self.streams[stream])
                self.logger.debug('Created devices: ' + str(self.stream_devices[stream].getComDevices()))

        # # generate random names of communication devices
        # self._externalname = uuid.uuid4().hex
        # self._internalname = uuid.uuid4().hex
        # self._monitoringname = uuid.uuid4().hex
        #
        # # get options
        # self.logger.debug('Options: ' + str(options))
        # self.options = options
        # if options['external']['type'] == 'tcp':
        #     self._externalurl = options['external']['type'] + '://' + options[
        #         'external']['bind_address'] + ':' + str(options['external']['bind_port'])
        # else:
        #     self._externalurl = "inproc://external"
        #
        # if options['monitoring']['type'] == 'tcp':
        #     self._monitoringurl = options['monitoring']['type'] + '://' + options[
        #         'monitoring']['bind_address'] + ':' + str(options['monitoring']['bind_port'])
        # else:
        #     self._monitoringurl = "inproc://monitoring"
        #
        # # init internal communication devices
        # self.devices = {}
        # self.devices['external'] = {
        #     'dev_type': zmq.QUEUE,
        #     'in_url': self._externalurl,
        #     'dev_name': self._externalname,
        #     'in_type': zmq.ROUTER,
        #     'out_type': zmq.DEALER,
        #     # 'mon_type': zmq.PUB
        # }
        # self.devices['monitoring'] = {
        #     'dev_type': zmq.FORWARDER,
        #     'dev_name': self._monitoringname,
        #     'in_type': zmq.SUB,
        #     'out_url': self._monitoringurl,
        #     'out_type': zmq.PUB,
        #     # 'mon_type': zmq.PUB
        # }
        # self.devices['internal'] = {
        #     'dev_name': self._internalname,
        #     'dev_type': zmq.QUEUE,
        #     'in_type': zmq.ROUTER,
        #     'out_type': zmq.DEALER,
        #     # 'mon_type': zmq.PUB
        # }
        # # self.devices['internal_monitoring'] = {
        # #     'dev_type': zmq.FORWARDER,
        # #     'in_type': zmq.SUB,
        # #     'out_type': zmq.PUB,
        # #     # 'mon_type': zmq.PUB
        # # }
        # self.logger.debug(
        #     'Communication devices definition: ' + str(self.devices))
        #
        # # start zmq threads
        # self.logger.debug('Initialising server devices communications ...')
        # self.commdevices = self.server_zmq.startZmqDevices(
        #     devices=self.devices)
        # if self.commdevices is None:
        #     self.logger.critical(
        #         'Can\'t start Devices correctly ! Exiting ...')
        #     exit(1)

        # Initiate local zmq
        self.logger.debug('Initialising server communications ...')
        self.context = zmq.Context.instance()

        # bind to external socket
        ext = self.hidden_devices['external'].getComDevices()
        self.server_external = self.context.socket(zmq.ROUTER)
        self.server_external.connect(
            "inproc://" + ext['inputs']['dev_name'] + "_out")

        # # bind to monitoring socket
        # self.server_monitoring = self.context.socket(zmq.SUB)
        # self.server_monitoring.bind(
        #     "inproc://" + self.devices['monitoring']['dev_name'] + "_out")
        #
        # # bind to internal socket
        # self.server_internal = self.context.socket(zmq.DEALER)
        # self.server_internal.connect(
        #     "inproc://" + self.devices['internal']['dev_name'] + "_in")

        self.logger.debug('Server Initialised correctly')

        self.run()

    def run(self):
        """Main function."""
        self.logger.info('Starting central server')

        # Start the streams
        self.hidden_devices['external'].run()
        for stream in self.stream_devices:
            self.stream_devices[stream].run()

        poll_all = zmq.Poller()
        poll_all.register(self.server_external, zmq.POLLIN)
        # poll_all.register(self.server_monitoring, zmq.POLLIN)
        # poll_all.register(self.server_internal, zmq.POLLIN)

        while True:
            try:
                self.logger.debug('Entering main loop ...')

                self.logger.debug("Polling queues ...")
                socks = dict(poll_all.poll(timeout=0))

                self.logger.debug("Looking for data ...")
                # Handle worker activity on self.broker_input
                if socks.get(self.server_external) == zmq.POLLIN:
                    self.logger.debug("getting external message")
                    #  Get client request
                    msg = self.server_external.recv_multipart()
                    self.logger.debug(msg)
                    if not msg:
                        break

                    # Stop action !
                    if msg[3].lower() == 'stop':
                        self.logger.info("Stop message received ! Stoping ...")
                        break

                time.sleep(2)
            except KeyboardInterrupt:
                self.logger.critical(
                    "Keyboard interrupt received, stopping...")
                break
        self.context.destroy()
        exit(1)
