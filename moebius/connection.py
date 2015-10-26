import zmq
from errors import *


class ZMQConnection(object):
    _socket = None
    _clients = dict()

    def __init__(self, address):
        self._address = address

    def create(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.ROUTER)
        # ZMQ_ROUTER_MANDATORY
        self._socket.setsockopt(33, 1)
        self._socket.bind(self._address)

    def process(self):
        client_id, message = self._socket.recv_multipart()

        if client_id not in self._clients:
            self._clients[client_id] = ZMQClient(self, client_id)

        return self._clients[client_id], message

    def send(self, client_id, message):
        try:
            self._socket.send_multipart([client_id, message], 33)
        except Exception, e:
            if client_id in self._clients:
                del self._clients[client_id]
            raise ConnectionSendError(e, client_id)

    def broadcast(self, message, filter_function = None):

	if filter_function == None:
	    filter_function = lambda client: True

        for client_id in self._clients:
	    if filter_function(self._clients[client_id]):
        	self._clients[client_id].send(message)

    def close(self, client_id):
        if client_id in self._clients:
            del self._clients[client_id]

    @property
    def socket(self):
        return self._socket

    @property
    def id(self):
        return self._socket.getsockopt(zmq.IDENTITY)


class ZMQClient(object):
    def __init__(self, connection, client_id):
        self._connection = connection
        self._client_id = client_id

    def send(self, message):
        self._connection.send(self._client_id, message)

    def broadcast(self, message, filter_function = None):
        self._connection.broadcast(message, filter_function)

    def close(self):
        self._connection.close(self._client_id)

    @property
    def id(self):
        return self._client_id
