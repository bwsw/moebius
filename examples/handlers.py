import time
import json
import random
from moebius.utils import sleep_async
from moebius.errors import \
    ConnectionSendError, \
    HandlerProcessingError
from moebius.server import Handler


class StartHandler(Handler):
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


class StopHandler(Handler):
    @staticmethod
    def run(client, data):
        print 'stop'
        pass


class TestHandler(Handler):
    @staticmethod
    def run(client, data):
        d = json.loads(data)
        for i in range(3):
            print "%d: Got %s from [%s]" % (i, d['message'], client.id)
            yield sleep_async(1)


class ReplyHandler(Handler):
    @staticmethod
    def run(client, data):
        random.seed()
        yield sleep_async(random.randint(0, 3))
        client.send('Reply to %s' % client.id)


class ReplyHandlerErr(Handler):
    @staticmethod
    def run(client, data):
        random.seed()
        yield sleep_async(random.randint(0, 3))
        client.send('Reply to %s' % client.id)


class ReplyHandlerErr2(Handler):
    @staticmethod
    def run(client, data):
        ggr
        random.seed()
        client.send('Reply to %s' % client.id)


class ReplyHandler2(Handler):
    @staticmethod
    def run(client, data):
        random.seed()
        yield sleep_async(5 + random.randint(0, 5))
        client.send('Reply to %s' % client.id)


class ReplyHandler3(Handler):
    @staticmethod
    def run(client, data):
        random.seed()
        yield sleep_async(3 + random.randint(0, 5))
        client.send('Reply to %s' % client.id)


class ReplyHandlerEchoNoWait(Handler):
    @staticmethod
    def run(client, data):
        client.send('Reply to %s' % client.id)
