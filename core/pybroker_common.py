"""Pybroker_common."""

from zmq.devices import ThreadDevice, Device
from zmq.utils import jsonapi
import json


class Pybroker_switch(object):

    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:
            self.fall = True
            return True
        else:
            return False


class Pybroker_zmq():

    def __init__(self, logger):
        self.logger = logger

    def startZmqDevices(self, devices):
        """Start zmq communication devices."""
        contexts = []
        device = {}
        try:
            for device_name in devices:
                self.logger.debug("Starting device: " + device_name)
                device[device_name] = ThreadDevice(
                    # device_type=devices[device_name]['dev_type'],
                    in_type=devices[device_name]['in_type'],
                    out_type=devices[device_name]['out_type']
                )
                if 'in_url' in devices[device_name]:
                    device[device_name].bind_in(devices[device_name]['in_url'])
                else:
                    self.logger.debug(device_name + ' in binding name: ' + devices[device_name]['dev_name'])
                    device[device_name].bind_in(
                        "inproc://" + devices[device_name]['dev_name'] + "_in")
                if 'out_url' in devices[device_name]:
                    device[device_name].bind_out(devices[device_name]['out_url'])
                else:
                    self.logger.debug(device_name + ' out binding name: ' + devices[device_name]['dev_name'])
                    device[device_name].bind_out(
                        "inproc://" + devices[device_name]['dev_name'] + "_out")
                ct = device[device_name].context_factory()
                # modify identity of context ....
                ct.identity = device_name+'_____1'
                device[device_name].start()
                contexts.append(device[device_name].context_factory())
                self.logger.debug("Done: " + device_name)
            self.logger.debug(contexts)
            return contexts
        except Exception as e:
            self.logger.exception(e)
            return None

    def stopZmqDevices(self, contexts):
        """Stop threaded contexts."""
        for context in contexts:
            self.logger.debug(context)
            context.term()
            context.join(timeout=1)
