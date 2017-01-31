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


class Pybroker_worker(threading.Thread):
    """ServerWorker"""

    def __init__(self, name, options, in_device=None, out_device=None, admin_device=None):
        threading.Thread.__init__(self)

        self.name = name
        self.options = options
        self.in_device = in_device
        self.out_device = out_device
        self.admin_device = admin_device

        self.logger = logging.getLogger(
            'pybroker.stream.' + self.options['driver'] + '.' + name)

        self.logger.debug('Initialising worker communications ...')
        self.context = zmq.Context.instance()

        self.logger.debug('In device: ' + str(in_device))
        self.logger.debug('Out device: ' + str(out_device))
        # connect to sockets
        self.worker = {}

        if in_device is not None:
            self.worker['in'] = self.context.socket(zmq.PULL)
            self.worker['in'].connect(
                "inproc://" + in_device['dev_name'] + "_out")
        else:
            self.worker['in'] = None

        if out_device is not None:
            self.worker['out'] = self.context.socket(zmq.PUSH)
            self.logger.debug('Connecting to: ' + out_device['dev_name'])
            self.worker['out'].connect(
                "inproc://" + out_device['dev_name'] + "_in")
        else:
            self.worker['out'] = None

        if admin_device is not None:
            self.worker['admin'] = self.context.socket(zmq.SUB)
            self.worker['admin'].set(
                zmq.SUBSCRIBE, self.options['driver_type'])
            self.logger.debug(
                'Subscribing to: ' + admin_device['dev_name'] + ' with name ' + self.options['driver_type'])
            self.worker['admin'].connect(
                "inproc://" + admin_device['dev_name'])
        else:
            self.worker['admin'] = None
        # self.logger.debug("state zmq url: " + self.state['zmq_url'])

    def run(self):
        self.logger.debug("start worker: " + self.name)
        driver = self.loadDriver()
        driver.run()

    def loadDriver(self):
        self.logger.debug('try to load driver')
        try:
            command_module = __import__("drivers.{0}".format(
                self.options['driver'] + '.' + self.options['driver_type']), fromlist=["drivers"])
        except ImportError as e:
            # Display error message
            self.logger.debug(
                "can't initialize module: drivers.{0}".format(self.name))
            self.logger.debug(e)
            exit()
        self.logger.debug('exec driver')
        return command_module.Work(self.options, self.worker)
