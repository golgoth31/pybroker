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
import base64
from struct import *
import yaml
import re

from .bbdo import Bbdo
from core import pybroker_common

class Work():
    """ServerWorker"""

    def __init__(self, options, worker):
        self.options = options
        self.input = worker['in']
        self.output = worker['out']
        self.logger = logging.getLogger(
            'pybroker.driver.bbdo.filters.' + self.input.identity)
        self.begin = 0

        self.perf_data_regexp = re.compile('([0-9]+\.?[0-9]*)(.*)')
        # read bbdo yaml file
        with open("conf/bbdo_proto_v" + str(self.options['version']) + ".yml", 'r') as stream:
            self.logger.debug('open bbdo proto: conf/bbdo_proto_v' +
                              str(self.options['version']) + ".yml")
            try:
                self.bbdo_matrix = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def run(self):
        # Startup message sequence
        # self.logger.debug("Saying hello to the server from "+self.worker.identity)
        # bbdo_stream = Bbdo(self.logger, self.options)

        while True:
            # get data stream message
            # get msg from input
            msg = self.input.recv_json()
            self.logger.debug('Full msg: ' + str(msg))

            # decode payload
            data = base64.b64decode(msg['payload'])
            self.logger.debug('Payload: ' + data)

            offset = 0
            output = {}

            # decode bbdo payload
            try:
                local_event = self.bbdo_matrix['events'][
                    msg['event_cat']][msg['event_type']]['fields']
                event_type_name = self.bbdo_matrix['events'][
                    msg['event_cat']][msg['event_type']]['name']
                self.logger.debug("event cat => " + str(msg['event_cat']))
                self.logger.debug(
                    "event type => " + str(msg['event_type']) + " (" + event_type_name + ")")
                output['bbdo_state'] = 'ok'
                for field in local_event:
                    output[local_event[field]['name']] = ""
                    if local_event[field]['type'] == 's':
                        string = ""
                        c = [""]
                        while c[0] != '\x00':
                            c = unpack_from('>c', data, offset)
                            offset = offset + 1
                            if c[0] == '\x00':
                                break
                            string = string + c[0]
                        if string == '\x00':
                            string = ""
                        output[local_event[field]['name']] = string
                    else:
                        fmt = '>' + local_event[field]['type']
                        val = unpack_from(fmt, data, offset)
                        output[local_event[field]['name']] = val[0]
                        offset = offset + calcsize(fmt)
            except KeyError as e:
                output['event_type'] = e[0]
                output['bbdo_state'] = 'unknown'
                event_type_name = 'unknown'
            self.insertMsg(event_type_name, output)
            self.logger.debug(output)

            # prepare data for insertion

    def insertMsg(self, event_type, msg):
        # msg_recv = json.loads(msg, encoding=None, cls=None, object_hook=None,
        #                       parse_float=None, parse_int=None, parse_constant=None)
        # print(msg_recv)
        self.event_type = event_type

        for case in pybroker_common.Pybroker_switch(event_type):
            if case('host_status'):
                # print('host_status')
                # print(msg_recv)
                # self.insertData(self.processStatusData(msg_recv))
                self.output.send_json(self.processStatusData(msg))
                break
            if case('service_status'):
                # print('service_status')
                # print(msg_recv)
                # self.insertData(self.processPerfData(msg_recv, self.perf_data_regexp))
                self.output.send_json(
                    self.processPerfData(msg, self.perf_data_regexp))
                # self.insertData(self.processStatusData(msg_recv))
                self.output.send_json(self.processStatusData(msg))
                break
            if case('host') or case('service'):
                # engine startup; should be used to keep link between id and name
                # print('host or service')
                # print(msg_recv)
                pass
            if case('host_check') or case('service_check'):
                pass
            # if case.default:
            #     pass

    # Refactor this function to only append things; no more index ....
    def processPerfData(self, data, regexp):
        perf_data = {}
        metrics = data['perf_data'].split(" ")
        i = 0
        perf_data['doc_type'] = 'metrics'
        for metric in metrics:
            perf_data[i] = {}
            perf_data[i]['host_id'] = data['host_id']
            perf_data[i]['@timestamp'] = data['last_check']
            perf_data[i]['check_interval'] = round(
                float(data['check_interval'])) * 60
            perf_data[i]['service_id'] = data['service_id']
            perf_data[i]['current_state'] = data['current_state']
            try:
                metric_name, metric_data = metric.split("=")
                perf_data[i]['metric_name'] = metric_name.strip("'\"")
                while len(metric_data.split(";")) < 5:
                    metric_data = metric_data + ';'
                metric_value_full, perf_data[i]['warn'], perf_data[i]['crit'], perf_data[
                    i]['min'], perf_data[i]['max'] = metric_data.split(";")
                val = self.perf_data_regexp.match(metric_value_full)
                perf_data[i]['value'] = val.group(1)
                perf_data[i]['unit'] = val.group(2)
            except ValueError:
                perf_data.pop(i)
            # print(perf_data)
            i += 1
        return perf_data

    def processStatusData(self, data):
        i = 0
        perf_data = {}
        perf_data[i] = {}
        if self.event_type == 'service_status':
            perf_data['doc_type'] = self.event_type
            perf_data[i]['host_name'] = data['host_name']
            perf_data[i]['service_id'] = data['service_id']
            perf_data[i]['service_description'] = data['service_description']
        else:
            perf_data['doc_type'] = self.event_type
        perf_data[i]['host_id'] = data['host_id']
        perf_data[i]['@timestamp'] = data['last_check']
        perf_data[i]['check_interval'] = round(
            float(data['check_interval'])) * 60
        for case in pybroker_common.Pybroker_switch(data['current_state']):
            if case(0):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'ok'
                else:
                    perf_data[i]['current_state_literal'] = 'up'
                break
            if case(1):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'warning'
                else:
                    perf_data[i]['current_state_literal'] = 'down'
                break
            if case(2):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'critical'
                else:
                    perf_data[i]['current_state_literal'] = 'unreachable'
                break
            if case(3):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'unknown'
                else:
                    perf_data[i]['current_state_literal'] = 'down'
                break
            # if case.default:
            #     if self.event_type == 'service_status':
            #         perf_data[i]['current_state_literal'] = 'critical'
            #     else:
            #         perf_data[i]['current_state_literal'] = 'down'
        perf_data[i]['current_state'] = data['current_state']
        perf_data[i]['output'] = data['output']
        return perf_data
