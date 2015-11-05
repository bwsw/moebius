import zmq
import types
import itertools
import logging
from connection import ZMQConnection
from constants import STRATEGY_REPLACE, STRATEGY_IGNORE, STRATEGY_QUEUE
from errors import \
    UnknownStrategyError, \
    HandlerProcessingError, \
    RouterProcessingError

class Handler(object):
    @staticmethod
    def run(client, data):
        pass
    
class ZMQServer(object):
    _loop = True
    _poll_forever = True
    _generator_dictionary = {}
    _socket_ids = set()
    _connections = dict()

    def __init__(self, address, router, poll_wait=5):
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
                try:
                        res = handler.run(client, message)
                        self._generator_dictionary[client.id] = res
                except Exception as e:
                        self.on_exception_msg(client.id, message, e)

                if (
                        client.id in self._generator_dictionary and
                        not isinstance(
                            self._generator_dictionary[client.id],
                            types.GeneratorType)
                ):
                    del self._generator_dictionary[client.id]
                else:
                    self._poll_forever = False

            else:
                if strategy == STRATEGY_REPLACE:

                    try:
                        res = handler.run(client, message)
                        if isinstance(res, types.GeneratorType):
                                self._generator_dictionary[client.id] = res
                    except Exception as e:
                        self.on_exception_msg(client.id, message, e)

                elif strategy == STRATEGY_QUEUE:

                    current_q = self._generator_dictionary[client.id]
                    try:
                        res = handler.run(client, message)
                        if isinstance(res, types.GeneratorType):
                            self._generator_dictionary[client.id] = \
                                itertools.chain(
                                    self._generator_dictionary[client.id], res)
                    except Exception as e:
                        self._generator_dictionary[client.id] = current_q
                        self.on_exception_msg(client.id, message, e)

                elif strategy == STRATEGY_IGNORE:
                    pass
                else:
                    raise UnknownStrategyError(
                        'Unknown strategy: "{}"'.format(strategy))
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
        for clt in self._generator_dictionary:
            try:
                result = self._generator_dictionary[clt].next()

                # if iteration result is generator, then chain it
                if isinstance(result, types.GeneratorType):
                    self._generator_dictionary[clt] = itertools.chain(
                        result, self._generator_dictionary[clt])
            except StopIteration:
                mark_delete.append(clt)
            except Exception as e:
                mark_delete.append(clt)
                self.on_exception_next(clt, self._generator_dictionary[clt], e)

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
                self._generator_dictionary['__background_process_'] = \
                    background_process
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
            logging.error('Stopped by keyboard interruption')
        except:
            raise

    def stop(self):
        self._loop = False
        pass

    def background(self, connection):
        pass

    def on_exception_msg(self, client, message, e):
        logging.error("Message processing error occured ----------------")
        logging.error("Client ID: %s" % client)
        logging.error("Message: %s" % message)
        logging.error("Exception: %s" % e)
        logging.error("-------------------------------------------------")

    def on_exception_next(self, client, gen, e):
        logging.error(
            "Next iteration error occured. Generator wiil be removed ")
        logging.error("Client ID: %s" % client)
        logging.error("Generator is: %s" % gen)
        logging.error("Exception: %s" % e)
        logging.error(
            "--------------------------------------------------------")

    @staticmethod
    def error_handler(exception, client):
        print client.id
        print exception
