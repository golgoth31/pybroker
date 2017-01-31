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
import uuid
import time
import json
import logging


from core import Pybroker_worker
import drivers
import pybroker_common


class Pybroker_stream():

    def __init__(self, name, stream):
        # init logger
        self.logger = logging.getLogger('pybroker.stream.' + name)
        self.logger.debug('Initializing central server')

        #
        self.stream_name = name
        self.stream = stream
        self.logger.debug(self.stream)

        # init zmq
        self.server_zmq = pybroker_common.Pybroker_zmq(self.logger)

        # define stream devices
        self.devices = {}
        self.devices['inputs'] = {
            # 'dev_type': device_type,
            'dev_name': uuid.uuid4().hex,
            'in_type': zmq.PULL,
            'out_type': zmq.PUSH,
            # 'mon_type': zmq.PUB
        }
        self.devices['outputs'] = {
            # 'dev_type': 'device',
            'dev_name': uuid.uuid4().hex,
            'in_type': zmq.PULL,
            'out_type': zmq.PUSH,
            # 'mon_type': None
        }

        # start zmq devices
        self.logger.debug('Initialising stream devices communications ...')
        self.commdevices = self.server_zmq.startZmqDevices(
            devices=self.devices)
        if self.commdevices is None:
            self.logger.critical(
                'Can\'t start Devices correctly ! Exiting ...')
            exit(1)

        # create connections for admin from server and to workers
        self.logger.debug('Initialising stream admin communications ...')
        self.context = zmq.Context.instance()

        # bind to external socket
        # self.server_external = self.context.socket(zmq.SUB)
        # self.server_external.connect(
        #     "inproc://" + ext['inputs']['dev_name'] + "_out")

        self.devices['admin'] = {
            'dev_name': uuid.uuid4().hex,
        }

        self.stream_internal = self.context.socket(zmq.PUB)
        self.stream_internal.bind(
            "inproc://" + self.devices['admin']['dev_name'])
        self.logger.debug('admin name: '+ self.devices['admin']['dev_name'])

    def run(self):
        # start worker in that order: 'caches', 'outputs', 'filters', 'inputs'
        for substream in ('caches', 'outputs', 'filters', 'inputs'):
            if self.stream[substream]['active']:
                # We can have multiple path for the stream
                # for substream_list in self.stream[substream]['list']:
                # for worker in self.stream[substream]:
                #     # self.logger.debug('substream_list: ' + str(substream_list))
                #     # start one particular path
                #     for worker in substream_list:
                        # start as many workers as requested
                worker_options = self.stream[substream]['options']
                # give the driver to use to worker
                worker_options['driver'] = self.stream[substream]['name']
                # give the strem type to use (input, filters, ...)
                worker_options['driver_type'] = substream
                admin_device = self.devices['admin']
                # give the worker the needed input/output
                for case in pybroker_common.Pybroker_switch(substream):
                    if case('caches'):
                        break
                    if case('outputs'):
                        in_device = self.devices['outputs']
                        out_device = None
                        break
                    if case('filters'):
                        in_device = self.devices['inputs']
                        out_device = self.devices['outputs']
                        break
                    if case('inputs'):
                        in_device = None
                        out_device = self.devices['inputs']
                        break
                for i in range(0, self.stream[substream]['workers']):
                    worker_name = substream + '_' + str(i)

                    self.logger.debug('starting '+worker_name)
                    self.logger.debug('In device: '+str (in_device))
                    self.logger.debug('out device: '+str (out_device))
                    worker = Pybroker_worker(worker_name, worker_options, in_device, out_device, admin_device)
                    worker.start()

    def getComDevices(self):
        self.devices['name'] = self.stream_name
        return self.devices

    # def _startWorker(self, worker_name, worker_options, in_device=None, out_device=None):
    #     # print(worker_state)
    #     for i in self.options[worker]:
    #         for options in self.options[worker][i]:
    #             self.options[worker][i]['in_device'] = in_device
    #             self.options[worker][i]['out_device'] = out_device
    #             worker = Pybroker_worker(worker_name, self.options[
    #                                      'state'], worker, self.options[worker][i])
    #             worker.start()
    #     # return(worker)

    def _checkWorkerReady(self, socket, poll):
        # wait for one worker ....
        socks = dict(poll.poll())
        if socks.get(socket) == zmq.POLLIN:
            started = 0
            while not started:
                self.logger.debug("getting self.broker_state")
                msg = socket.recv_multipart()
                # self.logger.debug(msg)
                if not msg:
                    continue
                address, state = msg
                with switch.Switch(state) as case:
                    if case('e'):
                        self.logger.debug("no worker intialized, waiting ...")
                        time.sleep(1)
                        started = 0
                    if case('r') or case('service'):
                        self.outputs.append(address)
                        self.logger.debug("Output " + address + " ready")
                        started = 1
                    if case.default:
                        started = 0

    # def _startZmqDevices(self, device_name):
#     device = zmq.devices.ThreadProxy(in_type=self.options['devices'][device_name]['in_type'], out_type=self.options[
#                                      'devices'][device_name]['out_type'], mon_type=self.options['devices'][device_name]['mon_type'])
#     device.connect_in("inproc://" + device_name + "_in")
#     device.bind_out("inproc://" + device_name + "_out")
#     device.bind_mon("inproc://" + device_name + "_mon")
#     device.start()
#     return device
#
# def _startStream(self, worker, in_device=None, out_device=None):
#     """Start worker based on options."""
#     for i in self.options[worker]:
#         for options in self.options[worker][i]:
#             self.options[worker][i]['in_device'] = in_device
#             self.options[worker][i]['out_device'] = out_device
#             worker = Pybroker_worker(
#                 options,
#                 self.options['state'],
#                 worker,
#                 self.options[worker][i]
#             )
#             worker.start()
#
# def _checkStreamReady(self, socket, poll):
#     """Check if worker is ready."""
#     # wait for one worker ....
#     socks = dict(poll.poll())
#     if socks.get(socket) == zmq.POLLIN:
#         started = 0
#         while not started:
#             self.logger.debug("getting self.broker_state")
#             msg = socket.recv_multipart()
#             # self.logger.debug(msg)
#             if not msg:
#                 continue
#             address, state = msg
#             for case in pybroker_common.Pybroker_switch(state):
#                 if case('e'):
#                     self.logger.debug("no worker intialized, waiting ...")
#                     time.sleep(1)
#                     started = 0
#                 if case('r') or case('service'):
#                     self.outputs.append(address)
#                     self.logger.debug("Output " + address + " ready")
#                     started = 1
#                 if case.default:
#                     started = 0
#
# def _startStream(self, stream, stream_type='ext'):
#     """Start a stream."""
#     # start devices
#     # if cache:
#     #     dev1 -> pull-push-pub
#     #     dev2 -> pull-push
#     # if output:
#     #     dev3 -> pull-push
#     # init internal communication devices
#     # if self.stream['cache']['active']:
#     #     device_type = 'proxy'
#     # else:
#     #     device_type = 'device'
#
#
#
#
#
#     # if stream['outputs']['active']:
#     #     for substream in stream['outputs']['list']:
#     #
#     #
#     # if stream['caches']['active']:
#     #     for substream in stream['caches']['list']:
#     #
#     # if stream['filters']['active']:
#     #     for substream in stream['filters']['list']:
#     #
#     # if stream['inputs']['active']:
#     #     for substream in stream['inputs']['list']:
