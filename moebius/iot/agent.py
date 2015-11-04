# communication DEALER-ROUTER
	# ping-pong feature
	# features
# agent lookup feature (REGISTRY)
	# agent registration feature
# communication PUB-SUB 
	# subscription feature
# protocol agnostic (excluding JSON service protocol)

from moebius.server import ZMQServer


class Service(object):
	pass

class ServiceAgent(ZMQServer):
	
	def pub_to_subscribers(self, msg):
		pass

	def backend_process(self, connection):
		pass

	def search_svc(self, *args, **kwargs):
		pass

	def check_svc(self, svc):
		pass

	def send_async(self, svc, callback):
		pass

