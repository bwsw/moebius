import os
import time
import multiprocessing
import logging
import random
from constants import STRATEGY_QUEUE
from server import ZMQServer
from router import ZMQRouter
from utils import YieldingClient, sleep_async


logger = logging.getLogger(__name__)


def exit_checker(obj):
    parent_pid = os.getppid()
    while True:
        logger.debug("Background PID: %d, PPID: %d, %s" %
                      (os.getpid(), os.getppid(), obj.__class__.__name__))
            # check if died                                                                                                                                               
        if os.kill(os.getppid(), 0) or os.getppid() <> parent_pid:
            logger.debug("Parent is offline PID: %d, PPID: %d" %
                          (os.getpid(), parent_pid))
            # died, then exit                                                                                                                                         
            exit(0)

        yield sleep_async(1)


#-------------------------------------------------------------
# broom proxy
#
class BroomHandler(object):

    @staticmethod
    def run(client, data):
        logger.debug("Entering BroomHandler.run")
        broom = client.connection.server.broom
        # broom.run()
        r = broom.relay(client, data)
        logger.debug("BroomHandler.run - relay is %s" % r)
        logger.debug("Leaving BroomHandler.run")
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
        logger.debug("Entering BroomClient.__init__")
        super(BroomClient, self).__init__(*args, **kwargs)
        self._client = kwargs['src_client']
        logger.debug("Leaving BroomClient.__init__")

    def send(self, message):
        logger.debug("Entering BroomClient.send")
        super(BroomClient, self).send(message=message)
        logger.debug("Leaving BroomClient.send")

    def on_wait_result_async(self):
        logger.debug("Entering BroomClient.on_wait_result_async")
        super(BroomClient, self).on_wait_result_async()
        logger.debug(
            "BroomClient.on_wait_result_async - sending data '%s' to %s" % (
                self.data, self._client.id))
        self._client.send(self.data)
        logger.debug("Leaving BroomClient.on_wait_result_async")


#-------------------------------------------------------------
# broom
#
class Broom(object):

    def __init__(self, *args, **kwargs):
        logger.debug("Entering Broom.__init__")
        self._classname = kwargs["classname"]
        self._router = kwargs["router"]
        self._cnt = kwargs["workers"]
        self._tmpdir = kwargs["tmpdir"].rstrip("/")
        self._is_run = False
        logger.debug("Leaving Broom.__init__")

    def run(self):
        logger.debug("Entering Broom.run")
        if self._is_run:
            logger.debug("Leaving Broom.run - already run")
            return

        random.seed()
        # function to launch server
        logger.debug("Broom.run - create mq")
        q = multiprocessing.Queue()

        logger.debug("Broom.run - create _start_server handler")

        def _start_server(q):
            logger.debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
            logger.debug("Entering Broom.run._start_server")
            path = 'ipc:///%s/%s-%s.sock' % (
                self._tmpdir, os.getpid(), time.time())
            srv = self._classname(path, self._router, 1)
            q.put(path)
            logger.debug("Lauching Broom svr %s / %s" % (
                self._classname, path))
            srv.add_background_generator(exit_checker(srv))
            srv.start()

        # run all processes
        logger.debug("Broom.run - launching worker processes")
        self.processes = []
        for i in xrange(self._cnt):
            p = multiprocessing.Process(
                target=_start_server, args=(q,))
            p.start()
            self.processes.append(p)
        # gather path from all processes
        logger.debug("Broom.run - receiving worker sockets")
        self._workers = []
        for p in self.processes:
            sock = q.get()
            self._workers.append(sock)
            logger.debug(
                "Broom.run - receiving worker socket %s" % sock)
        self._is_run = True
        logger.debug("Leaving Broom.run - completed")

    def shutdown(self):
        for p in self.processes:
            p.terminate()

    def relay(self, clt, command):
        logger.debug(
            "Entering Broom.relay with command '%s'" % command)
        broom_clt = "%010d" % random.randint(0, 100000000)
        logger.debug("Broom.relay - generate id '%s'" % broom_clt)

        c = BroomClient(
            address=random.choice(self._workers),
            identity=broom_clt,
            src_client=clt)

        c.connect()
        logger.debug("Broom.relay - send command to %s : %s" % (
            clt, command))
        c.send(command)
        logger.debug("Leaving Broom.relay")
        return c.wait_result_async()

#-------------------------------------------------------------
# broom proxy server class. Always relays messages to broom
#
class BroomServer(ZMQServer):

    def __init__(self, address, broom, poll_wait=1):
        router = BroomProxyRouter()
        super(BroomServer, self).__init__(address, router, poll_wait)
        self._broom = broom

    @property
    def broom(self):
        return self._broom

    def background(self, connection):
        return exit_checker(self)

