import zmq
import types
import os
import time
import multiprocessing
from constants import *
from connection import ZMQConnection
from server import ZMQServer
from router import ZMQRouter
from errors import *
from utils import YieldingClient

#-------------------------------------------------------------
# broom proxy
#
class BroomHandler(object):
	@staticmethod
	def run(client, data):
		broom = client.connection.server.broom
		broom.run()
		return broom.relay(client,data)

#-------------------------------------------------------------
# broom proxy router class. Always sends messages to BroomHandler
#
class BroomProxyRouter(ZMQRouter):
	def __init__(self):
		super(BroomProxyRouter, self).__init__(None)

	def process(self, **kwargs):
		return (STRATEGY_QUEUE, BroomHandler)

#-------------------------------------------------------------
# broom client
#
class BroomClient(YieldingClient):

    def __init__(self, *args, **kwargs):
	super(YieldingClient, self).__init__(*args,**kwargs)
	self._client = kwargs['client']

    def send(self, message):
        super(YieldingClient, self).send(message=message)

    def on_wait_result_async(self):
	super(YieldingClient, self).on_wait_result_async(self)
	self._client.send(data)


#-------------------------------------------------------------
# broom
# 
class Broom(object):
	def __init__(self,  classname, router, cnt):
		self._classname = classname
		self._router 	= router
		self._cnt 	= cnt
		self._mapping  	= []
		self._is_run	= False
		# self._iter 	= None

	def run(self):
		if self._is_run:
			return
		# function to launch server
		q = multiprocessing.Queue()
		def _start_server(q):
			path = 'ipc://%s-%s' % (os.getpid() , time.time())
			srv = self._classname(path, self._router, 1)
			srv.start()
			q.put(path)
		# run all processes
		processes = []
		for i in xrange(self._cnt):
			p = multiprocessing.Process(target = _start_server, args=(q,))
			p.start()
			processes.append(p)
		# gather path from all processes
		self._workers 	= []
		for p in processes:
			self._workers.append(q.get())

		self._is_run = True

	def shutdown(self):
		for p in processes:
			p.terminate()

	def relay(self, clt, command):
		broom_clt = "%f" % random.random()
		c = BroomClient(
			address 	= random.choice(self._workers),
			identity 	= broom_clt,
			client 		= clt)
		
		self._mapping[broom_clt] = clt
		c.send(command)
		return c.wait_result_async()


#-------------------------------------------------------------
# broom proxy server class. Always relays messages to broom
#
class BroomServer(ZMQServer):
	def __init__(self, address, broom, poll_wait = 1):
		router = BroomProxyRouter()
		super(BroomServer, self).__init__(address, router, poll_wait)
		self._broom = broom

	@property
	def broom(self):
		return self._broom


