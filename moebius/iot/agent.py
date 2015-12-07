# communication DEALER-ROUTER
# ping-pong feature
# features
# agent lookup feature (REGISTRY)
# agent registration feature
# communication PUB-SUB 
# subscription feature
# protocol agnostic (excluding JSON service protocol)

from moebius.server import ZMQServer, Handler
from moebius.router import ZMQRouter
from moebius.constants import STRATEGY_QUEUE
from json import dumps
from time import time
from logging import debug, error

DEFAULT_TICK = 5


# ---------------------------------------------------------------------------------------
# is raised when 
class BSA_RouterIncompatibleError(Exception):
    pass


class Service(object):
    pass


# ---------------------------------------------------------------------------------------
# handler is used to provide ping-pong functinality
#
class BSA_PingPongHandler(Handler):
    @staticmethod
    def run(client, data):
        client.send(dumps({
            'command': 'pong',
            'address': client.connection.server.address,
            'time': time(),
            'id': client.connection.server.id}))


# ---------------------------------------------------------------------------------------
# handler is used to provide not implemented response to requester
#
class BSA_NotImplementedHandler(Handler):
    @staticmethod
    def run(client, data):
        client.send(dumps({
            'command': 'command-not-implemented',
            'request': data,
            'address': client.connection.server.address,
            'time': time(),
            'id': client.connection.server.id}))


# ---------------------------------------------------------------------------------------
# Implements basic agent router
class BSA_Router(ZMQRouter):
    # -------------------------------------------------------------------------------
    # constructor method
    # args:
    #       handler - handler tuple which will be called when command is received
    def __init__(self, *args, **kwargs):
        r = [{
            'command': 'ping',
            'handler': (STRATEGY_QUEUE, BSA_PingPongHandler)
        }]

        super(BasicAgentRouter, self).__init__(r)
        self._agent_router = kwargs['agent_router']

    # ------------------------------------------------------------------------------
    # process method which routes agent messages (not system)
    #
    def process(self, **kwargs):
        try:
            return super(BasicAgentRouter, self).process(**kwargs)
        except Exception as e:
            debug("---------------------------------------------------")
            debug(e)
            try:
                return self._agent_router.process(**kwargs)
            except Exception as e:
                debug("---------------------------------------------------")
                debug(e)
                return (STRATEGY_QUEUE, BSA_NotImplementedHandler)


# --------------------------------------------------------------------------------
# Implements basic service agent
# args:
#    id - agent id
#    address - router interface (ROUTER)
#    broadcast_address - broadcast interface for subscribers (PUB)
#    router - router object which routes incoming messages (should be descendant of BSA_Router)
#    

class BasicServiceAgent(ZMQServer):
    def __init__(self, *args, **kwargs):
        self.id = kwargs['id']
        self.router_addr = kwargs['address']
        if 'broadcast_address' in kwargs:
            self.broadcast_addr = kwargs['broadcast_address']
        else:
            self.broadcast_addr = None

        router = kwargs['router']

        tick = DEFAULT_TICK
        if 'tick' in kwargs:
            tick = kwargs['tick']
            if int(tick) == 0:
                tick = DEFAULT_TICK

        # tick time greater than 1000 has no sense, so just limit it to 5000 for eg.
        if tick > 5000:
            raise ValueError(
                'BasicServiceAgent constructor `tick` parameter should be greater than 0 and less-equal than 5000')

        # check if router subclassed from BSA_Router
        if not issubclass(router, BSA_Router):
            raise BSA_RouterIncompatibleError(
                'Router object `%s` is not derived from BSA_Router class, but should be.' % router)

        # call for parent constructor
        super(BasicServiceAgent, self).__init__(self.router_intf, router, tick)

    def pub_to_subscribers(self, msg):
        pass

    def backend_process(self, connection):
        pass

    def search_svc(self, *args, **kwargs):
        pass

    def check_svc(self, svc):
        pass

    def ping_svc(self, svc):
        pass

    def send_async(self, svc, callback):
        pass
