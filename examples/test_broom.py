#------------------------------------------------------------------
# Test for synchronous client behaviour using DEALER-ROUTER pattern
#
#

import sys
sys.path.append("..")

import multiprocessing
import time
import json
import handlers
import moebius

import logging
import sys
import os
from moebius.constants import STRATEGY_QUEUE

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


#-------------------------------------------------------------
# specific client which is derived from basic REQ/REP client
#
class Client(moebius.utils.YieldingClient):
    def send(self, message):
        super(Client, self).send(message=message)

    def run(self, message):
        logger.debug("Entering Client.run - %s" % os.getpid())
        self.send(message)
        logger.debug("Sent msg at Client.run - %s" % os.getpid())
        for i in self.wait_result_async():
                time.sleep(1)
        if self.data is None:
                print "Failed to wait"
        data = self.recv_no_wait()
        print "Data is: %s" % data
        return data


def start_server(port):
    logger.debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
    rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandler3)
        }
    ]
    router = moebius.ZMQRouter(rules)
    broom = moebius.Broom(
        classname=moebius.ZMQServer,
        router=router,
        workers=5,
        tmpdir="tmp")
    broom.run()

    srv = moebius.BroomServer('tcp://127.0.0.1:%s' % port, broom, 1)
    print 'Server created'
    srv.start()


def start_sync_client(port, id):
    logger.debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
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
    logger.debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []
    time.sleep(2)
    children = 10
    for i in xrange(children):
        child.append(multiprocessing.Process(
            target=start_sync_client,
            args=(port, i,)))
        child[i].start()

    for i in xrange(children):
        child[i].join()

    #c = multiprocessing.Process(target=start_sync_client, args=(port, 1))
    #c.start()
    #c.join()

    s.terminate()
