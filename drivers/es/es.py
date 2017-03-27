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
import re
import logging
import elasticsearch
from datetime import date


class Es():

    def __init__(self, elastic_host, elastic_port):
        # TODO: get host address for config file
        self.logger = logging.getLogger(
            'elasticsearch')
        self.logger.setLevel(logging.DEBUG)
        try:
            self.es_conn = elasticsearch.Elasticsearch(
                [{'host': elastic_host}, ])
        except:
            self.logger.exception("can't connect to: " + elastic_host)

    def insertData(self, perf_data):
        self.checkIndices()
        # doc_type = perf_data['doc_type']
        # del perf_data['doc_type']
        print(perf_data)
        if perf_data['doc_type'] == 'metrics':
            for unit_metric in perf_data['metrics']:
                metric = {}
                metric['host_id'] = perf_data['info']['host_id']
                metric['@timestamp'] = perf_data['info']['@timestamp']
                metric['check_interval'] = perf_data['info']['check_interval']
                metric['service_id'] = perf_data['info']['service_id']
                metric['service_description'] = perf_data['info']['service_description']
                metric['state'] = perf_data['info']['current_state']

                metric['metric_name'] = unit_metric['metric_name']
                metric['warn'] = unit_metric['warn']
                metric['crit'] = unit_metric['crit']
                metric['min'] = unit_metric['min']
                metric['max'] = unit_metric['max']
                metric['value'] = unit_metric['value']
                metric['unit'] = unit_metric['unit']
                result = self.es_conn.index(
                    index=self.index_name,
                    body=metric,
                    doc_type=perf_data['doc_type'])

    def checkIndices(self):
        d = date.today()
        self.index_name = 'centreon-' + d.strftime("%Y.%m.%d")
        if not self.es_conn.indices.exists(self.index_name):
            print('no index, creating')
            body = self.read_json(
                "conf/elasticsearch_centreon_mappings.json")
            try:
                self.es_conn.indices.create(
                    index=self.index_name, body=body)
            except elasticsearch.RequestError as e:
                # TODO: check different execptions to kill if needed
                self.logger.exception(e)

    def read_json(self, filename):
        f_in = open(filename)
        data = json.load(f_in)
        f_in.close()
        return data
