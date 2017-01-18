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

from zmq.devices import ThreadDevice
from pybroker_worker import Pybroker_worker
import pybroker_common


class Pybroker_server():
    """Core server of pybroker."""

    def __init__(self, options, streams):
        """Init."""
        # init our logger
        self.logger = logging.getLogger('pybroker.server')
        self.logger.debug('Initializing central server')

        # init zmq
        self.server_zmq = pybroker_common.Pybroker_zmq(self.logger)

        # get options
        self.logger.debug('Options: ' + str(options))
        self.options = options
        if options['external']['type'] == 'tcp':
            self._externalzmqurl = options['external']['type'] + '://' + options[
            'external']['bind_address'] + ':' + str(options['external']['bind_port'])
        else:
            self._externalzmqurl = "inproc://external"

        if options['monitoring']['type'] == 'tcp':
            self._monitoringzmqurl = options['monitoring']['type'] + '://' + options[
            'monitoring']['bind_address'] + ':' + str(options['monitoring']['bind_port'])
        else:
            self._monitoringzmqurl = "inproc://monitoring"

        # init internal communication devices
        self.devices = {}
        self.devices['external'] = {
            'dev_type': zmq.QUEUE,
            'in_url': self._externalzmqurl,
            'in_type': zmq.ROUTER,
            'out_type': zmq.DEALER,
            # 'mon_type': zmq.PUB
        }
        self.devices['monitoring'] = {
            'dev_type': zmq.FORWARDER,
            'in_type': zmq.SUB,
            'out_url': self._monitoringzmqurl,
            'out_type': zmq.PUB,
            # 'mon_type': zmq.PUB
        }
        self.devices['internal'] = {
            'dev_type': zmq.QUEUE,
            'in_type': zmq.ROUTER,
            'out_type': zmq.DEALER,
            # 'mon_type': zmq.PUB
        }
        self.devices['internal_monitoring'] = {
            'dev_type': zmq.FORWARDER,
            'in_type': zmq.SUB,
            'out_type': zmq.PUB,
            # 'mon_type': zmq.PUB
        }
        self.logger.debug(
            'Communication devices definition: ' + str(self.devices))

        # start zmq threads
        self.logger.debug('Initialising server devices communications ...')
        self.commdevices = self.server_zmq.startZmqDevices(
            devices=self.devices)
        if self.commdevices is None:
            self.logger.critical(
                'Can\'t start Devices correctly ! Exiting ...')
            exit(1)

        # Initiate local zmq
        self.logger.debug('Initialising server communications ...')
        self.context = zmq.Context.instance()

        # bind to external socket
        self.server_external = self.context.socket(zmq.ROUTER)
        self.server_external.bind("inproc://external_out")

        # bind to monitoring socket
        self.server_monitoring = self.context.socket(zmq.SUB)
        self.server_monitoring.bind("inproc://monitoring_out")

        # bind to internal socket
        self.server_internal = self.context.socket(zmq.DEALER)
        self.server_internal.connect("inproc://internal_in")

        self.logger.debug('Server Initialised correctly')

        self.run()

    def run(self):
        """Main function."""
        self.logger.info('Starting central server')

        poll_all = zmq.Poller()
        poll_all.register(self.server_external, zmq.POLLIN)
        poll_all.register(self.server_monitoring, zmq.POLLIN)
        poll_all.register(self.server_internal, zmq.POLLIN)

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
                    if msg[2].lower() == 'stop':
                        self.logger.info("Stop message received ! Stoping ...")
                        break

                time.sleep(2)
            except KeyboardInterrupt:
                self.logger.critical(
                    "Keyboard interrupt received, stopping...")
                break
        self.context.destroy()
        exit(1)
