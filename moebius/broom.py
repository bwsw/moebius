import zmq
import types
import os
import time
import multiprocessing
import logging
import random
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
		logging.debug("Entering BroomHandler.run")
		broom = client.connection.server.broom
		broom.run()
		r = broom.relay(client,data)
		logging.debug("BroomHandler.run - relay is %s" % r)
		logging.debug("Leaving BroomHandler.run")
		return r

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
	logging.debug("Entering BroomClient.__init__")
	super(BroomClient, self).__init__(*args,**kwargs)
	self._client = kwargs['src_client']
	logging.debug("Leaving BroomClient.__init__")


    def send(self, message):
	logging.debug("Entering BroomClient.send")
        super(BroomClient, self).send(message=message)
	logging.debug("Leaving BroomClient.send")


    def on_wait_result_async(self):
	logging.debug("Entering BroomClient.on_wait_result_async")
	super(BroomClient, self).on_wait_result_async()
	logging.debug("BroomClient.on_wait_result_async - sending data '%s' to %s" % (self.data, self._client.id))
	self._client.send(self.data)
	logging.debug("Leaving BroomClient.on_wait_result_async")


#-------------------------------------------------------------
# broom
# 
class Broom(object):
	def __init__(self, *args,**kwargs): 
		logging.debug("Entering Broom.__init__")
		self._classname = kwargs["classname"]
		self._router 	= kwargs["router"]
		self._cnt 	= kwargs["workers"]
		self._tmpdir	= kwargs["tmpdir"].rstrip("/")
		self._is_run	= False
		logging.debug("Leaving Broom.__init__")


	def run(self):
		logging.debug("Entering Broom.run")
		if self._is_run:
			logging.debug("Leaving Broom.run - already run")
			return

		random.seed()
		# function to launch server
		logging.debug("Broom.run - create mq")
		q = multiprocessing.Queue()

		logging.debug("Broom.run - create _start_server handler")
		def _start_server(q):
			logging.debug("Entering Broom.run._start_server")
			path = 'ipc://%s/%s-%s.sock' % (self._tmpdir, os.getpid() , time.time())
			srv = self._classname(path, self._router, 1)
			q.put(path)
			logging.debug("Lauching Broom svr %s / %s" % (self._classname, path))
			srv.start()

		# run all processes
		logging.debug("Broom.run - launching worker processes")
		processes = []
		for i in xrange(self._cnt):
			p = multiprocessing.Process(target = _start_server, args=(q,))
			p.start()
			processes.append(p)
		# gather path from all processes
		logging.debug("Broom.run - receiving worker sockets")
		self._workers 	= []
		for p in processes:
			sock = q.get()
			self._workers.append(sock)
			logging.debug("Broom.run - receiving worker socket %s" % sock)
		self._is_run = True
		logging.debug("Leaving Broom.run - completed")

	def shutdown(self):
		for p in processes:
			p.terminate()

	def relay(self, clt, command):
		logging.debug("Entering Broom.relay with command '%s'" % command)
		broom_clt = "%010d" % random.randint(0,100000000)
		logging.debug("Broom.relay - generate id '%s'" % broom_clt)

		c = BroomClient(
			address 	= random.choice(self._workers),
			identity 	= broom_clt,
			src_client 	= clt)

		c.connect()
		logging.debug("Broom.relay - send command to %s : %s" % (clt, command))
		c.send(command)
		logging.debug("Leaving Broom.relay")
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


