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

# generic import
import json
import switch
import re
import logging
import elasticsearch
from datetime import date


class Es():

    def __init__(self, elastic_host, elastic_port):
        # TODO: get host address for config file
        self.es_conn = elasticsearch.Elasticsearch([{'host': elastic_host},])
        #self.logger = logging.Logger()
        self.perf_data_regexp = re.compile('([0-9]+\.?[0-9]*)(.*)')
        # self.index_name = 'centreon-'+str(date.today())

    def insertData(self, perf_data):
        #print('writing to es; index: '+self.index_name)
        doc_type = perf_data['doc_type']
        del perf_data['doc_type']
        for unit_metric in perf_data:
            result = self.es_conn.index(index=self.index_name, body=perf_data[unit_metric], doc_type=doc_type)

    def checkIndices(self):
        self.index_name = 'centreon-'+str(date.today())
        if not self.es_conn.indices.exists(self.index_name):
            print('no index, creating')
            body = self.read_json(
                "conf/elasticsearch_centreon_mappings.json")
            try:
                self.es_conn.indices.create(
                    index=self.index_name, body=body)
            except elasticsearch.RequestError as e:
                # TODO: check different execptions to kill if needed
                print(e)

    def insertMsg(self, msg):
        msg_recv = json.loads(msg[3], encoding=None, cls=None, object_hook=None,
                              parse_float=None, parse_int=None, parse_constant=None)
        # print(msg_recv)
        self.event_type = msg[2]
        self.checkIndices()
        with switch.Switch(msg[2]) as case:
            if case('host_status'):
                # print('host_status')
                # print(msg_recv)
                self.insertData(self.processStatusData(msg_recv))
            if case('service_status'):
                # print('service_status')
                # print(msg_recv)
                self.insertData(self.processPerfData(msg_recv, self.perf_data_regexp))
                self.insertData(self.processStatusData(msg_recv))
            if case('host') or case ('service'):
                # engine startup; should be used to keep link between id and name
                # print('host or service')
                # print(msg_recv)
                pass
            if case('host_check') or case ('service_check'):
                pass
            if case.default:
                pass

    def read_json(self, filename):
        f_in = open(filename)
        data = json.load(f_in)
        f_in.close()
        return data

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
            perf_data[i]['check_interval'] = round(float(data['check_interval']))*60
            perf_data[i]['service_id'] = data['service_id']
            try:
                perf_data[i]['metric_name'], metric_data = metric.split("=")
                while len(metric_data.split(";")) < 5:
                    metric_data = metric_data + ';'
                metric_value_full, perf_data[i]['warn'], perf_data[i]['crit'], perf_data[i]['min'], perf_data[i]['max'] = metric_data.split(";")
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
        perf_data[i]['check_interval'] = round(float(data['check_interval']))*60
        with switch.Switch(data['current_state']) as case:
            if case(0):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'ok'
                else:
                    perf_data[i]['current_state_literal'] = 'up'
            if case(1):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'warning'
                else:
                    perf_data[i]['current_state_literal'] = 'down'
            if case(2):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'critical'
                else:
                    perf_data[i]['current_state_literal'] = 'unreachable'
            if case(3):
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'unknown'
                else:
                    perf_data[i]['current_state_literal'] = 'down'
            if case.default:
                if self.event_type == 'service_status':
                    perf_data[i]['current_state_literal'] = 'critical'
                else:
                    perf_data[i]['current_state_literal'] = 'down'
        perf_data[i]['current_state'] = data['current_state']
        perf_data[i]['output'] = data['output']
        return perf_data
