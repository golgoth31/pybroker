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
import influxdb
from datetime import date


class Influx():

    def __init__(self, elastic_host, elastic_port):
        # TODO: get host address for config file
        self.logger = logging.getLogger(
            'influxdb')
        self.logger.setLevel(logging.DEBUG)
        try:
            self.influx_conn = influxdb.InfluxDBClient(
                '192.168.122.1', 8086, '', '', 'centreon-metrics')
        except:
            self.logger.exception("can't connect to: " + elastic_host)
        try:
            print('create influxdb')
            self.influx_conn.create_database('centreon-metrics')
        except influxdb.InfluxDBClientError:
            print('can not create')
            self.logger.debug('influxdb database already exists')

    def insertData(self, perf_data):
        print('influx: ' + str(perf_data))
        doc_type = perf_data['doc_type']
        del perf_data['doc_type']
        json_perf = [
            {
                "measurement": "",
                "tags": {},
                "time": "",
                "fields": {}
            }
        ]
        for unit_metric in perf_data:
            json_perf[0]['measurement'] = str(perf_data[unit_metric]['service_id'])
            json_perf[0]['tags']['host_id'] = str(perf_data[unit_metric]['host_id'])
            json_perf[0]['tags'][perf_data[unit_metric]['metric_name']] = perf_data[unit_metric]['unit']
            json_perf[0]['time'] = perf_data[unit_metric]['@timestamp']
            json_perf[0]['fields'][perf_data[unit_metric]['metric_name']] = float(perf_data[unit_metric]['value'])
            json_perf[0]['tags']['current_state'] = int(perf_data[unit_metric]['current_state'])
            json_perf[0]['fields']['current_state'] = int(perf_data[unit_metric]['current_state'])
            # json_perf = [
            #     {
            #         "measurement": perf_data[unit_metric]['metric_name'],
            #         "tags": {
            #             "host_id": str(perf_data[unit_metric]['host_id']),
            #             "service_id": str(perf_data[unit_metric]['service_id']),
            #             "unit": perf_data[unit_metric]['unit']
            #         },
            #         "time": perf_data[unit_metric]['@timestamp'],
            #         "fields": {
            #             "value": float(perf_data[unit_metric]['value'])
            #         }
            #     }
            # ]
            self.logger.debug('writing to influxdb: ' + str(json_perf))
            self.influx_conn.write_points(json_perf, time_precision='s')
