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

BROKER_URL = 'amqp://celery:celery@192.168.122.1'
#CELERY_RESULT_BACKEND = 'amqp://celery:celery@192.168.122.1'
#CELERY_RESULT_BACKEND = 'redis://'
# CELERY_RESULT_BACKEND = 'mongodb://'
# CELERY_MONGODB_BACKEND_SETTINGS = {
#     'database': 'celery',
#     'taskmeta_collection': 'celery_collection',
# }
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Europe/Paris'
CELERY_ENABLE_UTC = True
CELERY_IMPORTS = ('tasks', )
