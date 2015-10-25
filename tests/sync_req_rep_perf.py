#------------------------------------------------------------------
# Test for synchronous client behaviour using DEALER-ROUTER pattern
#
#

import sys
sys.path.append("..")

import multiprocessing
import time
import zmq
import json
import handlers
from   zmq.eventloop import ioloop, zmqstream
from   Queue import Queue
from   moebius import *


import time

class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print 'elapsed time: %f ms' % self.msecs

#-------------------------------------------------------------
# specific client which is derived from basic REQ/REP client
#
class Client(utils.ReqRepClient):
    def send(self, message):
        super(Client, self).send(message=message)

    def on_recv(self, message):
        print message
	exit(0)


def start_server(port):

    rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandlerEchoNoWait)
        }
    ]
    router = ZMQRouter(rules)
    srv = ZMQServer('tcp://127.0.0.1:%s' % port, router)
    print 'Server started'
    srv.start()


def start_sync_client_strategy(port, id):
    cl = Client(
        address='tcp://127.0.0.1:%s' % port,
        identity='Client%s' % id
    )
    message = {
        'command': 'reply'
    }
    cl.connect()
    print "Send message by %s" % cl.id
    m = json.dumps(message)
    
    cnt = 10000
    with Timer() as t:
	for i in range(cnt):
		reply = cl.send_with_reply(m)
    print "=> elasped time is: %s s" % t.secs
    print "=> performance (q/s): %d" % (cnt/t.secs)
    #print reply


if __name__ == "__main__":
    port = 19876
    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []

    for i in xrange(5):
        child.append(multiprocessing.Process(target=start_sync_client_strategy, args=(port, i,)))
	child[i].start()

    for i in xrange(5):
	child[i].join()

    s.terminate()

