import time
import zmq
from   zmq.eventloop import ioloop, zmqstream
from   Queue import Queue
from   moebius import *

ioloop.install()

###----------------------------------------------------------------
### utility generator which yields for specific amount of time
###
def sleep_async(timeout):
    t = time.time()
    while time.time() - t < timeout:
        yield time.time()

#-------------------------------------------------------------------------------------------
# define client to test req/rep pattern on DEALER/ROUTER
# uses tornado ioloop
# 
class ReqRepClient(object):
    _socket = None

    def __init__(self, *args, **kwargs):
        self._address = kwargs['address']
        self._socket_type = kwargs.pop('socket_type', zmq.DEALER)
        self._identity = kwargs.pop('identity', None)

    def connect(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.DEALER)
        if self._identity:
            self._socket.setsockopt(zmq.IDENTITY, self._identity)

        # ZMQ_PROBE_ROUTER
        self._socket.setsockopt(51, 1)
        self._socket.connect(self._address)

    def disconnect(self):
        raise NotImplementedError

    def send(self, message):
        self._socket.send(message)

    def _send_with_callback(self, message):

        def reply_handler(reply):
            self._message = reply
            stream.flush()
            loop.stop()

        stream = zmqstream.ZMQStream(self._socket)
        stream.on_recv(reply_handler)
        stream.send(message)

        loop = ioloop.IOLoop.instance()
        loop.start()

    def send_with_reply(self, message):
        self._send_with_callback(message)
        return self._message

    @property
    def id(self):
        return self._identity







#-------------------------------------------------------------------------------------------
# define client to test req/rep pattern on DEALER/ROUTER
# uses tornado ioloop
# 
class YieldingClient(object):
    _socket = None

    def __init__(self, *args, **kwargs):
        self._address = kwargs['address']
        self._socket_type = kwargs.pop('socket_type', zmq.DEALER)
        self._identity = kwargs.pop('identity', None)
	self._poller = zmq.Poller()


    def connect(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.DEALER)
        if self._identity:
            self._socket.setsockopt(zmq.IDENTITY, self._identity)

        # ZMQ_PROBE_ROUTER
        self._socket.setsockopt(51, 1)
        self._socket.connect(self._address)
	self._poller.register(self._socket, zmq.POLLIN)

    def disconnect(self):
        raise self._socket.close()

    def send(self, message):
        self._socket.send(message)

    def on_wait_result_async(self):
	pass

    def wait_result_async(self,timeout = None):
	t = time.time()
	self._data = None
	while (self._data is None) and ((timeout is None) or (time.time() - t < timeout)):
		sockets = dict(self._poller.poll(0))
		if len(sockets):
			self._data = self._socket.recv()
			self.on_wait_result_async()
		if self._data is None:
			yield

    def recv(self):
	if self._data:
		return self._data
	else:
		return self._socket.recv()


    def recv_no_wait(self):
	if self._data:
		return self._data
	else:
		return None

    @property
    def id(self):
        return self._identity
