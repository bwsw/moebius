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
from moebius.constants import STRATEGY_QUEUE


#-------------------------------------------------------------
# specific client which is derived from basic REQ/REP client
#
class Client(moebius.utils.YieldingClient):
    def send(self, message):
        super(Client, self).send(message=message)

    def run(self, message):
        self.send(message)
        for i in self.wait_result_async():
                time.sleep(1)
                # print "%s waiting" % self.id
        data = self.recv()
        return data


def start_server(port):

    rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandler2)
        }
    ]
    router = moebius.ZMQRouter(rules)
    srv = moebius.ZMQServer('tcp://127.0.0.1:%s' % port, router)
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
    reply = cl.run(json.dumps(message))
    print reply


if __name__ == "__main__":
    port = 19876
    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []

    for i in xrange(1000):
        child.append(multiprocessing.Process(
            target=start_sync_client_strategy,
            args=(port, i,)))
        child[i].start()

    for i in xrange(1000):
        child[i].join()

    s.terminate()
