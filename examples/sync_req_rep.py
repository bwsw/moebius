#------------------------------------------------------------------
# Test for synchronous client behaviour using DEALER-ROUTER pattern
#
#

import sys
sys.path.append("..")

import multiprocessing
import json
import handlers
import logging
import moebius
from moebius.constants import STRATEGY_QUEUE

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)


#-------------------------------------------------------------
# specific client which is derived from basic REQ/REP client
#
class Client(moebius.utils.ReqRepClient):
    def send(self, message):
        super(Client, self).send(message=message)

    def on_recv(self, message):
        print message
        exit(0)


def start_server(port):
    debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
    rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandler)
        }
    ]
    router = moebius.ZMQRouter(rules)
    srv = moebius.ZMQServer('tcp://127.0.0.1:%s' % port, router)
    print 'Server started'
    srv.start()


def start_sync_client_strategy(port, id):
    debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
    cl = Client(
        address='tcp://127.0.0.1:%s' % port,
        identity='Client%s' % id
    )
    message = {
        'command': 'reply'
    }
    cl.connect()
    print "Send message by %s" % cl.id
    reply = cl.send_with_reply(json.dumps(message))
    print reply


if __name__ == "__main__":
    debug("PID: %d, PPID: %d" % (os.getpid(), os.getppid()))
    port = 19876
    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []

    for i in xrange(1):
        child.append(multiprocessing.Process(
            target=start_sync_client_strategy,
            args=(port, i,)))
        child[i].start()

    for i in xrange(1):
        child[i].join()

    s.terminate()
