# Getting Started with Moebius

## Programming style

First one should know about Moebius is that it's single threaded, so if one handler works, then other handlers stop which in turn means that requests are delayed. So program design should avoid long-running pieces of code which can not be interrupted. 

For example, if You would like to sort very big array of data, you could find that It will take a lot of time to complete it all. So If You just will try to run it in direct way You will find that concurrency stops to work because other clients unable to send queries and server unable to process requests.

You could overcome this limitations using next techniques (for sort):

1. Split array on some parts and run sort for every part, do return management to server in order it could run another handlers and when server will return back management to this handler, continue to do sort of next part of array. Finally, You just merge sorted parts together.
2. Complete offload to external service and just wait until it completes sorting.

Both these methods can be implemented in Moebius effectively using python *generators*. Next in this tutorial I'll explain how to do it.

*NB:* To effectively use Moebius you should understand python [*generators*](https://wiki.python.org/moin/Generators) and able to write your own generators.

*Since Moebius is single-threaded this means that overall request bandwidth/second = 1/req-time, where req-time is average time request takes to succeed.*

## Handlers available

Moebius allows to use two types of handlers:

1. Python function handler
2. Python-generator handler

Python function shoud be used when You need just to do something right now and reply back to client. It could be expressed like written in example below:

```python
class FunctionHandler(object):
    @staticmethod
    def run(client, data):
        client.send('Hello, world')
```

Here is just class with one static method run which takes two arguments:
1. client - connection to direct speach to peer and broadcast
2. data - request payload, transferred to the server from client.

Next, you could se generator handler which sends back to client 3000 messages.

```python

class GeneratorHandler(object):
    @staticmethod
    def run(client, data):
        for i in range(30000):
            client.send(Send %s to [%s]" % (i,  client.id))
            yield
```

It's implemented as generator (not as function) because it should give another clients space to work. You could see _yield_ keyword in the loop which allows to return management to server and let another handlers to work and continue when server will give this handler next turn.

```python

class GeneratorHandler(object):
    @staticmethod
    def run(client, data):
        for i in range(30000):
            client.send(Send %s to [%s]" % (i,  client.id))
            yield
```

Let's move forward and learn how to implement non-blocking sleep using generator handler. Using non-blocking sleep you will be able to keep your handler as soon as possible until some event will occure. Here goes an example:

```python

import moebius.utils

class SleepGeneratorHandler(object):
    @staticmethod
    def run(client, data):
        d = json.loads(data)
        for i in range(300):
            client.send(Send %s to [%s]" % (i,  client.id))
            yield utils.sleep_async(1)
```

What happens above? Quite easy - we are yielding here generator (moebius.utils.sleep_async is generator) and thus our method will send one message to client every 1 second and will give other clients to work. If you will use here standard python time.sleep(1) then until You will send 300 messages other clients will not able to communicate to server.

Moebius understands when you return from your handler generator and places it in front of your method until it will be completed, so the picture looks like:

|Step                                     | State                                                   |
|-----------------------------------------|--------------------------------------------------------- |
|Before yield utils.sleep_async           | Queue = SleepGeneratorHandler.run |
|After yield  utils.sleep_async           | Queue = utils.sleep_async, SleepGeneratorHandler.run |
|After end of generator utils.sleep_async | Queue = SleepGeneratorHandler.run (next) |

So, yielding generators from generators we create stack of generators which should be completed one after another.

Now, we are familiar with the way to create handlers, let's introduce strategies.

## Strategies of handling supported by Moebius

Moebius supports 3 strategies which defines how new requests build queue of handlers. They are:

1. _Replace (moebius.constants.STRATEGY_REPLACE)_ - replaces current handler for client if client sends new request;
2. _Ignore (moebius.constants.STRATEGY_IGNORE)_ - ignores new requests from client if handler for that client is not yet completed;
3. _Queue (moebius.constants.STRATEGY_QUEUE)_ - appends new handler to the tail of current handler, so it will be run after current handler completed.
 
In general one should use _queue_ strategy because it allows to handle all request from client, but in some cases another strategies could make sence, eg.

1. _Replace_ could be used when server will not responded in awaited timeframe and client sends new request because old one is already outdated;
2. _Ignore_ could be used to deny new requests from client until server will respond to current request.

## Defining Rules for Moebius

Rules are managed by Routers. Default router is ZMQRouter, which assumes that data between client and server is JSON. It uses next format of rules:

```python

rules = [
        {
            'command': 'reply',
            'handler': (moebius.constants.STRATEGY_QUEUE, handlers.ReplyHandler)
        }, ...
]

```

Here routing decision is made on 'command' argument in JSON with some value (here, 'reply'). So, the rule above will call for handlers.ReplyHandler in queue strategy mode when it will get in request from client JSON with 'command' = 'reply'.

Next, it's necessary to create router which will handle rules:

```python

router = moebius.router.ZMQRouter(rules)

```

If you would like to use non-JSON protocol or implement more complicated routing mechanism, You should derive your class from [moebius.router.ZMQRouter](https://github.com/bwsw/moebius/blob/master/moebius/router.py) and override process method:

```python
def process(self, **kwargs):
```

Server passes keyword argument "message" which holds 0mq message. If your implementation unable to route some message, you can (should) raise exception as shown below or just use some default handler like HandlerNotFound:

```python
raise moebius.errors.RouterProcessingError(msg)
```

Default router looks like shown below:

```python

import json
from errors import *

class ZMQRouter(object):
    def __init__(self, rules):
        self._rules = rules

    def process(self, **kwargs):
        data = json.loads(kwargs['message'])
        for rule in self._rules:
            if 'command' in data and data['command'] == rule['command']:
                return rule['handler']
        raise RouterProcessingError('Command not found')
        
```

So, just derive class from ZMQRouter and override process method.

## Gathering all pieces in one place

Let's develop simple client server "echo" application using Moebius. The code could be found under tests/sync_req_rep.py. It starts server process and 3 client processes.

```python

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
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandler)
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
    reply = cl.send_with_reply(json.dumps(message))
    print reply


if __name__ == "__main__":
    port = 19876
    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []

    for i in xrange(3):
        child.append(multiprocessing.Process(target=start_sync_client_strategy, args=(port, i,)))
	child[i].start()

    for i in xrange(3):
	child[i].join()

    s.terminate()

```

## Client broadcasting

Moebius gives you a way to broadcast information to all or part of connected clients. To do it You can use

```python

def run(client, data):
	client.broadcast(message)
```

to do broadcasting to all clients. Or use function filter to broadcast to subset of clients:

```python

def filter_broadcast(client):
	if client.id == "Client1" or client.id == "Client2":
		return True
	return False

def run(client, data):
	client.broadcast(message, filter_broadcast)
```

## Background tasks

Sometimes it's necessary to do some background activity even there are no requests. You can achieve this in Moebius defining and overriding "background" method:

```python

class TestServer(ZMQServer):
    def background(self, connection):
        while True:
            connection.broadcast('ping')
            yield timer(1)

```

This generator will be run during server start and will be triggered every server iteration. Generator takes "connection" object of "ZMQConnection" type and the only useful method of "connection" is "iterate" which allows You to pass handler and operate with every object, see next code block:

```python

def iterate_handler(client):
	client.send("test")

class TestServer(ZMQServer):
    def background(self, connection):
        while True:
            connection.iterate(iterate_handler)
            yield timer(1)

```

## Exception handling

There are two exception handlers available inside ZMQServer:

1. ```def on_exception_msg(self, client, message, e)```
2. ```def on_exception_next(self,client, gen, e)```

First is called when an exception occures during initial message processing (eg, creating generator or handling message if regular function is used as handler). The second is called when generator does next iteration and an exception occures during this operation. If you want to do custom processing, override this handlers.



## ZeroMQ yielding dealer client

To use effectively DEALER connections to remote ROUTERs (for eg. another Moebius instances) inside of Moebius handlers we have to use yielding client implementation which doesn't block Moebius server and gives effective way to serve another clients. There as moebius.utils.YieldingClient which solves this problem. Below an example of how to use it.

```python

class Client(utils.YieldingClient):
    def send(self, message):
        super(Client, self).send(message=message)


class SomeHandler(object):
    @staticmethod
    def run(client, data):
    	# open DEALER connection to remote ROUTER server
	c = Client(address='tcp://127.0.0.1:%s' % port, identity='Client%s' % id)
	# send message
	c.send(message)
	# wait nonblocking until we get response
	yield c.wait_result_async()
	# read response
	data = c.recv()
	# send response to our client
	client.send(data)

```

So, magis is inside ```	yield c.wait_result_async()``` which takes care about nonblocking awaiting of response from remote executor. After it receives response You just read it using ```c.recv()```.

Method ```YieldingClient.wait_result_async(timeout = None)``` allows to specify timeout argument to avoid infinite waiting for response.

## Additional modules

1. [Broom](./contrib/broom.md)
