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

from struct import *
import yaml
import json
import logging
from PyCRC.CRCCCITT import CRCCCITT
from PyCRC.CRC16 import CRC16


class Bbdo_proto():

    def __init__(self, logger, options):
        # Load bbdo matrix definition
        self.options = options
        with open("conf/bbdo_proto_v"+str(self.options['version'])+".yml", 'r') as stream:
            try:
                self.bbdo_matrix = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        self.head_size = calcsize(self.bbdo_matrix['header']['fmt'])
        self.logger = logger

    def ComputeHeader(self, data):
        if len(data) > self.head_size:
            print('not a valid header')
            exit()
        # TODO: add check for bbdo protocol version
        # if header 8 bytes => v1
        # if header 16 bytes => v2

        # 8 bytes
        self.checksum, self.stream_size, event_id = unpack_from(
            self.bbdo_matrix['header']['fmt'], data)
        # 16 bytes
        self.checksum, self.stream_size, event_id, self.source_id, self.destination_id = unpack_from(
            self.bbdo_matrix['header']['fmt'], data)
        self.event_cat = event_id / 65536
        self.event_type = event_id - (self.event_cat * 65536)

    def ExtractData(self, data):
        offset = 0
        output = {}
        # print('event cat: ' + str(self.event_cat))
        # print('event type: ' + str(self.event_type))
        try:
            local_event = self.bbdo_matrix['events'][
                self.event_cat][self.event_type]['fields']
            self.event_type_name = self.bbdo_matrix['events'][
                self.event_cat][self.event_type]['name']
            self.logger.debug("event cat => "+str(self.event_cat))
            self.logger.debug("event type => "+str(self.event_type)+"("+self.event_type_name+")")
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
            self.event_type_name = 'unknown'
        self.output = json.dumps(output)

    def GetEventTypeName(self):
        return self.event_type_name

    def GetBbdoMatrixOutput(self):
        return self.output
