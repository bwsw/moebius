# Introduction

Moebius is free, light 0mq-based Dealer-Router python server. It's developed to be run under GNU/Linux environment.

Moebius is inspired by Tornado web-server, which is high performance HTTP and WebSocket server. Like Tornado, Moebius employs the approach with python generators to create light and single-threaded server.

Name "Moebius" (Möbius) is choosen because of nature of handlers which are python generators and could be run infinitely like "Möbius stripe".

## 0mq as transport

Moebius uses well known and robust ZeroMQ library to implement transport. It uses DEALER-ROUTER 0mq pattern to implement two-way communication without specific limitations. DEALER-ROUTER pattern allows to implement three types of communication:
 
* 1 request - 1 response 
* 1 request - N responses
* 1 request - 0 responses

## Architecture

Moebius is single-threaded. It uses python generators to implement parallel processing of multiple clients. Developers can use either standard python methods to implement simple fast routines which just work or python generators to implement long-living routines which can run for seconds or minutes until completion.

## Dependencies

1. Python 2.7+ (we didn't tested before 2.7)
2. libzmq 4.0.4+
3. python-zmq library
4. Tornado ioloop (Tornado framework installed)


## Platforms

Moebius is tested and works well under next GNU/Linux distributions:

1. Ubuntu 14.04.3 LTS (all from repos)
2. Debian 7 wheezy (libzmq3 from backports, python-zmq from pip - pip install pyzmq)

## Getting Started

See [tests](https://github.com/bwsw/moebius/tree/master/tests) directory for examples and Jump start.

## Performance

There is tests/sync_req_rep_perf.py script which should run like:

```bash
$ python sync_req_rep_perf.py 12
```
from tests directory, which takes amount of concurrent synchronous clients to server, so 12 in the sample above.

## License

Moebius is licensed under Apache 2.0 license.

## Author

Moebius is created by [Bitworks Software, Ltd.](http://bw-sw.com)

mailto: bitworks (at) bw-sw.com
