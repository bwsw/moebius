# Broom: Moebius multiprocessed offloading engine

## Purpose

Broom allows to switch from single-threaded processing model to worker-like processing model. It could give You two benefits:

1. Utilize all CPU cores on heavy services.
2. Implement slow query processing (for example slow database response) without additional asynchronous code.

If you just need to balance traffic among several Moebius and can install HAProxy then better use regular HA-Proxy rather than Broom, because it utilizes less system resources and achieves better performance, but If you need "pure" solution, use Broom.

## Status

It's alfa.

## Usage

First, ensure you have single-threaded Moebius application is designed well and works properly, so it's tested well and passes external specification. It's quite complicated to debug code which runs on multiple cores so better to test all using standard moebius programming model. 

```python

# as usual define rules.

rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandler3)
        }
]

# create router which routes rules.
router = moebius.ZMQRouter(rules)

# create broom and provide it with next parameters:
#   classname - name of server which will be used as worker instance
#   router - router instance which will be used to route messages
#   workers - amount of workers to spawn
#   tmpdir  - temporary directory to hold ZMQ "ipc://" connections between BroomServer (frontend server) and 
#             background workers
broom = moebius.Broom(
        classname=moebius.ZMQServer,
        router=router,
        workers=40,
        tmpdir="tmp")

# create special frontend server and pass broom inside
# 1st paramenter is socket to bind
# 2nd parameter is broom instance which will handle jobs
# 3rd parameter minimal sleep time for generator scheduler (1/1000 sec)
srv = moebius.BroomServer('tcp://127.0.0.1:%s' % port, broom, 1)

# start server
srv.start()
```

## Operating System tuning

Since Broom uses Yielding Client, it uses a lot of ZMQ Poller objects, so If you have high traffic to broom and slow queries, then use ```ulimit``` to tune amount of open files, eg. ```ulimit -Hn 8192```.
