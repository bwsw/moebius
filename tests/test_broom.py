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

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

#-------------------------------------------------------------
# specific client which is derived from basic REQ/REP client
#
class Client(utils.YieldingClient):
    def send(self, message):
        super(Client, self).send(message=message)

    def run(self, message):
	self.send(message)
	for i in self.wait_result_async():
		time.sleep(1)
	if self.data is None:
		print "Failed to wait"
	data = self.recv_no_wait()
	print "Data is: %s" % data
	return data


def start_server(port):

    rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandler3)
        }
    ]
    router = ZMQRouter(rules)
    broom = Broom(ZMQServer, router, 40)

    srv = BroomServer('tcp://127.0.0.1:%s' % port, broom, 1)
    print 'Server created'
    srv.start()


def start_sync_client(port, id):
    cl = Client(
        address='tcp://127.0.0.1:%s' % port,
        identity='Client%s' % id
    )
    message = {
        'command': 'reply'
    }
    cl.connect()
    print "Send message by %s" % cl.id
    reply = cl.run(json.dumps(message))
    print reply


if __name__ == "__main__":
    port = 19876
    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []

    time.sleep(10)

    for i in xrange(100):
        child.append(multiprocessing.Process(target=start_sync_client, args=(port, i,)))
	child[i].start()

    for i in xrange(100):
	child[i].join()


    #c = multiprocessing.Process(target=start_sync_client, args=(port, 1))
    #c.start()
    #c.join()

    s.terminate()
