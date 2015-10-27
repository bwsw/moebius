import zmq
import types
import itertools
from constants import *
from connection import ZMQConnection
from errors import *


class ZMQServer(object):
    _loop = True
    _poll_forever = True
    _generator_dictionary = {}
    _socket_ids = set()
    _connections = dict()

    def __init__(self, address, router, poll_wait = 5):
        self._address = address
        self._router = router
	self._poll_wait = poll_wait

    def _handle_request(self, connection):
        client, message = connection.process()

        if len(message) == 0:
            # it'handshake in case of ZMQ_PROBE_ROUTER socket option
            return

        try:
            strategy, handler = self._router.process(message=message)

            if client.id not in self._generator_dictionary:
                self._generator_dictionary[client.id] = handler.run(client, message)
                if not isinstance(self._generator_dictionary[client.id], types.GeneratorType):
                    del self._generator_dictionary[client.id]
                else:
                    self._poll_forever = False
            else:
                if strategy == STRATEGY_REPLACE:
                    # del self._generator_dictionary[client.id]
                    self._generator_dictionary[client.id] = handler.run(client, message)
                elif strategy == STRATEGY_QUEUE:
                    self._generator_dictionary[client.id] = itertools.chain(self._generator_dictionary[client.id],
                                                                            handler.run(client, message))
                elif strategy == STRATEGY_IGNORE:
                    pass
                else:
                    raise UnknownStrategyError('Unknown strategy')
        except HandlerProcessingError, e:
            if client.id in self._generator_dictionary:
                del self._generator_dictionary[client.id]
            self.error_handler(e, client)
        except RouterProcessingError, e:
            self.error_handler(e, client)

    def _handle_generators(self):
        if 0 == len(self._generator_dictionary):
            self._poll_forever = True
            return

        mark_delete = []
        for generator in self._generator_dictionary:
            try:
                result = self._generator_dictionary[generator].next()
                if isinstance(result, types.GeneratorType):
                    self._generator_dictionary[generator] = itertools.chain(result,
                                                                            self._generator_dictionary[generator])
            except StopIteration:
                mark_delete.append(generator)

        for generator_to_delete in mark_delete:
            del self._generator_dictionary[generator_to_delete]

    def start(self):
        poller = zmq.Poller()
        connection = ZMQConnection(self._address, self)
        connection.create()
        poller.register(connection.socket, zmq.POLLIN)

        self._connections[connection.id] = connection

        try:
            background_process = self.background(connection)
            if isinstance(background_process, types.GeneratorType):
                self._generator_dictionary['__background_process_'] = background_process
                self._poll_forever = False
        except AttributeError:
            pass

        try:
            while self._loop:
                if self._poll_forever:
                    sockets = dict(poller.poll())
                else:
                    sockets = dict(poller.poll(self._poll_wait))

                for socket in sockets:
                    if socket in sockets and sockets[socket] == zmq.POLLIN:
                        socket_id = socket.getsockopt(zmq.IDENTITY)
                        self._handle_request(self._connections[socket_id])
                self._handle_generators()
        except KeyboardInterrupt:
            print 'Stopped by interruption'
        except:
            raise

        print "STOPPED"

    def stop(self):
        self._loop = False
        pass

    def background(self, connection):
        pass

    @staticmethod
    def error_handler(exception, client):
        print client.id
        print exception
