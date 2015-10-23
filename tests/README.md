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
