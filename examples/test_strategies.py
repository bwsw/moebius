import sys
sys.path.append("..")

import zmq
import moebius
import json
import sys
import handlers
from moebius.constants import STRATEGY_REPLACE, STRATEGY_IGNORE, STRATEGY_QUEUE

from multiprocessing import Process

rules = [
    {
        'command': 'replace',
        'handler': (STRATEGY_REPLACE, handlers.TestHandler)
    },
    {
        'command': 'ignore',
        'handler': (STRATEGY_IGNORE, handlers.TestHandler)
    },
    {
        'command': 'queue',
        'handler': (STRATEGY_QUEUE, handlers.TestHandler)
    }
]


def start_server(port):
    router = moebius.ZMQRouter(rules)
    srv = moebius.ZMQServer('tcp://127.0.0.1:%s' % port, router)
    print 'Server started'
    srv.start()


def start_client_strategy(port, id, strategy):
    context = zmq.Context()
    req = context.socket(zmq.DEALER)
    req.setsockopt(zmq.IDENTITY, b'Client %d' % id)
    req.connect('tcp://127.0.0.1:%s' % port)

    for i in range(3):
        data = {
            'command': strategy,
            'message': 'number %d' % i
        }
        message = json.dumps(data)
        req.send(message)


if __name__ == "__main__":
    port = 19876

    strategy = 'dummy'
    strategies = ('queue', 'ignore', 'replace')
    if len(sys.argv) > 1:
        strategy = sys.argv[1]
    if strategy not in strategies:
        print "Please pass one of valid strategies to test: %s" % (
            ', '.join(strategies, ))
        exit(0)

    Process(target=start_server, args=(port,)).start()
    for i in xrange(3):
        Process(target=start_client_strategy, args=(port, i, strategy)).start()
