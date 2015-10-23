import json
from errors import *


class ZMQRouter(object):
    def __init__(self, rules):
        self._rules = rules

    def process(self, **kwargs):
        data = json.loads(kwargs['message'])
        for rule in self._rules:
            if 'command' in data and data['command'] == rule['command']:
                return rule['handler']
        raise RouterProcessingError('Command not found')
