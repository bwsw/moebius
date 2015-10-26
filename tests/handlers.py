import time
import json
import random
from moebius.errors import *
from moebius.utils import sleep_async

class StartHandler(object):
    @staticmethod
    def run(client, data):
        for i in range(10):
            try:
                print 'send reply %d' % i
                client.send('hey hoy %d' % i)
                time.sleep(1)
            except ConnectionSendError:
                print 'send error'
                break
            except Exception, e:
                raise HandlerProcessingError(e)


class StopHandler(object):
    @staticmethod
    def run(client, data):
        print 'stop'
        pass


class TestHandler(object):
    @staticmethod
    def run(client, data):
        d = json.loads(data)
        for i in range(3):
            print "%d: Got %s from [%s]" % (i, d['message'],  client.id)
            yield sleep_async(1)

class ReplyHandler(object):
    @staticmethod
    def run(client, data):
        random.seed()
        yield sleep_async(random.randint(0,3))
        client.send('Reply to %s' % client.id)


class ReplyHandler2(object):
    @staticmethod
    def run(client, data):
        random.seed()
        yield sleep_async(5+random.randint(0,5))
        client.send('Reply to %s' % client.id)


class ReplyHandlerEchoNoWait(object):
    @staticmethod
    def run(client, data):
        client.send('Reply to %s' % client.id)

