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
from pprint import pprint
import switch

from core import Core_worker
# from drivers.bbdo import Bbdo_listener

class Core_server():

    def __init__(self, options):
        #self.id = id
        self.options = options
        self.broker_input_url = self.options['input']['zmq_url']
        self.broker_output_url = self.options['output']['zmq_url']
        self.broker_state_url = self.options['state']['zmq_url']
        self.broker_admin_url = self.options['admin']['zmq_url']
        self.broker_admin_inside_url = self.options['admin_inside']['zmq_url']
        self.logger = logging.getLogger('getbbdo.server')
        self.logger.debug('init server')
        # threading.Thread.__init__(self)
        self.run()

    def run(self):
        self.logger.debug('start server')

        # Prepare our context and sockets
        context = zmq.Context.instance()

        # Socket to talk to self.broker_input
        broker_input = context.socket(zmq.ROUTER)
        # self.broker_input.setsockopt()
        broker_input.identity = 'INPUT'
        broker_input.bind(self.broker_input_url)

        # Socket to talk to self.broker_output
        broker_output = context.socket(zmq.DEALER)
        broker_output.identity = 'OUTPUT'
        broker_output.bind(self.broker_output_url)

        # Socket to talk to self.broker_output
        # broker_state = context.socket(zmq.PULL)
        # broker_state.identity = 'STATE'
        # broker_state.bind(self.broker_state_url)

        # Socket to talk to self.broker_admin
        broker_admin_inside = context.socket(zmq.PUB)
        broker_admin_inside.bind(self.broker_admin_inside_url)

        poll_input = zmq.Poller()
        poll_input.register(broker_input, zmq.POLLIN)
        # poll_inputs.register(self.broker_admin_inside, zmq.POLLIN)

        poll_output = zmq.Poller()
        poll_output.register(broker_output, zmq.POLLIN)
        # poll_outputs.register(self.broker_admin_inside, zmq.POLLIN)

        # poll_state = zmq.Poller()
        # poll_state.register(broker_state, zmq.POLLIN)

        poll_all = zmq.Poller()
        poll_all.register(broker_input, zmq.POLLIN)
        poll_all.register(broker_output, zmq.POLLIN)
        # poll_all.register(self.broker_admin_inside, zmq.POLLIN)

        # first initiate output worker
        self.outputs = []
        self.logger.debug("Starting workers")
        for i in range(self.options['output']['workers']):
            self.startWorker(i, self.options['state'], 'output', self.options['output'])
            broker_output.send_multipart(['','1'])
            msg = broker_output.recv_multipart()
            # print(msg)
            self.outputs.append(msg[1])

        # second initiate input worker
        self.inputs = []
        self.logger.debug("Starting listeners")
        for i in range(self.options['input']['workers']):
            self.startWorker(i, self.options['state'], 'input', self.options['input'])
            msg = broker_input.recv_multipart()
            broker_input.send_multipart([msg[0],'',"1"])
            self.inputs.append(msg[0])

        # self.checkWorkerReady(broker_state, poll_state)

        while True:
            # print(self.outputs)
            if self.outputs:
                self.logger.debug("Polling all workers")
                socks = dict(poll_all.poll())
            else:
                self.logger.debug("Polling output only")
                socks = dict(poll_output.poll())
            # self.logger.debug("Polling workers")
            # socks = dict(poll_all.poll())

            # Handle worker activity on self.broker_input
            if socks.get(broker_input) == zmq.POLLIN:
                self.logger.debug("getting self.broker_input")
                #  Get client request, route to first available worker
                msg = broker_input.recv_multipart()
                # if msg[2] == 'host_status':
                #     print(msg[0])
                #     print(msg)
                if not msg:
                    break
                request = [self.outputs.pop(0), ''] + msg
                broker_output.send_multipart(request)
                reply = 'ok'
                broker_input.send_multipart([msg[0], '', reply])

            # Handle worker activity on self.broker_output
            if socks.get(broker_output) == zmq.POLLIN:
                self.logger.debug("getting self.broker_output")
                msg = broker_output.recv_multipart()
                # print(msg)
                if not msg:
                    break
                address = msg[0]
                self.outputs.append(address)
                self.logger.debug("Output " + address + " ready")
            # else:
            #     self.logger.debug("self.broker_output not existing")

        broker_input.close()
        broker_output.close()
        context.term()

    def startWorker(self, worker_index, worker_state, worker_type, worker_options):
        # print(worker_state)
        worker = Core_worker(worker_index, worker_state, worker_type, worker_options)
        worker.start()
        return(worker)

    def checkWorkerReady(self, socket, poll):
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
                    if case('r') or case ('service'):
                        self.outputs.append(address)
                        self.logger.debug("Output " + address + " ready")
                        started = 1
                    if case.default:
                        started = 0

    # def manageAdmin(self):
    #
    # def manageOutput(self):
    #
    # def manageInput(self):
