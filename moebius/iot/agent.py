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

class Service(object):
	pass

#---------------------------------------------------------------------------------------
# handler is used to provide ping-pong functinality
#
class BSA_PingPongHandler(Handler):

	@staticmethod
	def run(client, data):
		client.send(dumps({
					'command': 'pong'
					'address': client.connection.server.address,
					'time'   : time(),
					'id'     : client.connection.server.id}))


#---------------------------------------------------------------------------------------
# handler is used to provide not implemented response to requester
#
class BSA_NotImplementedHandler(Handler):
	@staticmethod
	def run(client, data):
		client.send(dumps({
                                        'command': 'command-not-implemented',
					'request': data,
                                        'address': client.connection.server.address,
                                        'time'   : time(),
                                        'id'     : client.connection.server.id}))


#---------------------------------------------------------------------------------------
# Implements basic agent router
class BasicAgentRouter(ZMQRouter):
	#-------------------------------------------------------------------------------
	# constructor method
	# args:
	#       handler - handler tuple which will be called when command is received
	def __init__(self,*args,**kwargs):
		r = [{
				'command': 'ping',
				'handler': (STRATEGY_QUEUE, BSA_PingPongHandler)
				}]

		super(BasicAgentRouter, self).__init__(r)
		self._agent_router = kwargs['agent_router']

	#------------------------------------------------------------------------------
	# process method which routes agent messages (not system)
	# 
	def process(self, **kwargs):
		try:
			return super(BasicAgentRouter, self).process(**kwargs)
		except Exception as e:
			debug(e)
			try:
				return self._agent_router.process(**kwargs)
			except RouterProcessingError as e:
				return (STRATEGY_QUEUE, BSA_NotImplementedHandler)
	
		
		
class BasicServiceAgent(ZMQServer):

	def __init__(self):
		self.id = 
	
	def pub_to_subscribers(self, msg):
		pass

	def backend_process(self, connection):
		pass

	def search_svc(self, *args, **kwargs):
		pass

	def check_svc(self, svc):
		pass

	def ping_svc(self,svc):
		pass

	def send_async(self, svc, callback):
		pass

