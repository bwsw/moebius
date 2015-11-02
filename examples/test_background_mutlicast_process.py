import sys
sys.path.append("..")

from moebius import *
from test import *
from multiprocessing import Process


def timer(timeout):
    t = time.time()
    while time.time() - t < timeout:
        yield time.time()


class TestServer(ZMQServer):
    def background(self, connection):
        while True:
            connection.broadcast('ping')
            yield timer(1)


def start_server(port):
    router = ZMQRouter([])
    srv = TestServer('tcp://127.0.0.1:%s' % port, router)
    print 'Server started'
    srv.start()


def start_client_strategy(port, id):
    context = zmq.Context()
    req = context.socket(zmq.DEALER)
    req.setsockopt(zmq.IDENTITY, b'Client %d' % id)
    req.setsockopt(51, 1)
    req.connect('tcp://127.0.0.1:%s' % port)
    while True:
        m = req.recv()
        print("Client %d got: %s" % (id, m))


if __name__ == "__main__":
    port = 19876

    Process(target=start_server, args=(port,)).start()
    for i in xrange(3):
        Process(target=start_client_strategy, args=(port, i,)).start()
        time.sleep(5)
