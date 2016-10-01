#!/usr/bin/python
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

# import standard modules modules
import logging
import yaml
import multiprocessing

# import pybroker modules
from core import Core_server

# logging.basicConfig(filename='logs/getbbdo',level=logging.DEBUG)
# logger = logging.Logger('getbbdo')
logger = logging.getLogger('getbbdo')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('logs/getbbdo')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

options = {}


def readConf():
    global options
    with open("conf/pybroker.yml", 'r') as stream:
        try:
            logger.debug('load conf file')
            options = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            exit()


def main():
    """main function"""
    logger.info(
        '******************** Starting bbdo broker daemon *******************')
    readConf()
    logger.debug('Start server')
    try:
        server = multiprocessing.Process(target=Core_server, args=(options,))
        server.start()
    except (KeyboardInterrupt, SystemExit):
        print('exiting....')
    print "in parent process after child process start"
    #client = bbdo.Bbdo_listener(1)
    # client.start()
    # logger.debug('Join server thread')
    # server.join()

if __name__ == "__main__":
    main()
